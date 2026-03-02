from datetime import datetime, timedelta
import secrets
import time
from fastapi import Depends, HTTPException, APIRouter, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Mapped, mapped_column

# Core application objects and settings (FastAPI app instance + env config)
from hans.core.core import app
from hans.core.settings import settings
# Database session factory and SQLAlchemy declarative base
from hans.core.db import get_db, Base, AsyncSession


# Password hashing context (bcrypt). Used both to hash new passwords
# and to verify user-submitted passwords during login.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 bearer token extraction dependency.
# FastAPI will read the Authorization: Bearer <token> header.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Role names used for authorization checks.
ROLE_ADMIN = "admin"
ROLE_STAFF = "staff"

# --- AUTH LIMITS ------------------------------------------------------

# In-memory login throttling settings.
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 60
LOGIN_BLOCK_SECONDS = 10
# Tracks failed login attempts by username and IP.
_login_failures = {}

# Hash a plain-text password before storing it in the database.
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Check whether a plain-text password matches its stored hash.
def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

# Create a signed JWT token with a type and expiration time.
def _create_token(data: dict, expires_delta: timedelta, token_type: str) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode["exp"] = int(expire.timestamp())
    to_encode["type"] = token_type
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )

# Create a signed JWT access token with an expiration time.
def create_access_token(data: dict, expires_delta: timedelta) -> str:
    return _create_token(data, expires_delta, "access")

# Create a refresh token and return it with its rotation id.
def create_refresh_token(username: str) -> tuple[str, str]:
    refresh_jti = secrets.token_urlsafe(16)
    refresh_token = _create_token(
        {"sub": username, "jti": refresh_jti},
        timedelta(minutes=settings.refresh_token_expire_minutes),
        "refresh",
    )
    return refresh_token, refresh_jti

# Build a rate-limit key from username and client IP.
def _login_key(username: str, request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    elif request.client:
        client_ip = request.client.host
    else:
        client_ip = "unknown"
    return f"{username}:{client_ip}"

# Check whether a client is temporarily blocked.
def _is_login_blocked(key: str, now_ts: float) -> bool:
    entry = _login_failures.get(key)
    if not entry:
        return False
    blocked_until = entry.get("blocked_until")
    if blocked_until and blocked_until > now_ts:
        return True
    return False

# Record a failed login attempt and apply temporary blocks.
def _record_login_failure(key: str, now_ts: float) -> None:
    entry = _login_failures.get(key)
    if not entry or now_ts - entry["first_ts"] > LOGIN_WINDOW_SECONDS:
        _login_failures[key] = {"count": 1, "first_ts": now_ts, "blocked_until": None}
        return
    entry["count"] += 1
    if entry["count"] >= LOGIN_MAX_ATTEMPTS:
        entry["blocked_until"] = now_ts + LOGIN_BLOCK_SECONDS

# Clear stored failures after a successful login.
def _clear_login_failures(key: str) -> None:
    if key in _login_failures:
        del _login_failures[key]

# Login endpoint: validates credentials and returns a bearer token.
# OAuth2PasswordRequestForm provides "username" and "password" from the request body.
@app.post("/auth/token")
async def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    # Apply in-memory throttling before hitting the database.
    now_ts = time.time()
    key = _login_key(form.username, request)
    if _is_login_blocked(key, now_ts):
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")
    result = await db.execute(select(User).where(User.username == form.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        _record_login_failure(key, now_ts)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    _clear_login_failures(key)
    access_token = create_access_token(
        {"sub": user.username},
        timedelta(minutes=settings.access_token_expire_minutes),
    )
    refresh_token, refresh_jti = create_refresh_token(user.username)
    user.refresh_jti = refresh_jti
    await db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


# --- MODELS ----------------------------------------------------------

# SQLAlchemy model for application users.
# Stores credentials and role metadata for authentication and authorization.
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str]
    hashed_password: Mapped[str]
    role: Mapped[str]
    # Stores current refresh token JTI (for rotation validation)
    refresh_jti: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

# Public user data returned by auth endpoints.
class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- DEPENDENCIES ----------------------------------------------------

# FastAPI dependency to extract and validate the current user from a JWT.
# Used by protected endpoints to enforce authentication.
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Decode and verify the JWT signature and claims.
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        # Reject refresh tokens for access-protected routes.
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token")
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    # Load the user from the database by username stored in the token.
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Enforce that the current user has an allowed role.
def require_roles(*allowed_roles: str):
    async def _require(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user

    return _require

# Role dependencies.
require_admin = require_roles(ROLE_ADMIN)
require_staff_or_admin = require_roles(ROLE_ADMIN, ROLE_STAFF)


# --- ROUTES ----------------------------------------------------------

router = APIRouter()

# Refresh token request payload.
class RefreshIn(BaseModel):
    refresh_token: str

# Rotate refresh tokens and issue a new access token.
@router.post("/auth/refresh")
async def refresh_tokens(payload: RefreshIn, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    try:
        decoded = jwt.decode(
            payload.refresh_token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token")
    username = decoded.get("sub")
    refresh_jti = decoded.get("jti")
    if not username or not refresh_jti:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or user.refresh_jti != refresh_jti:
        raise HTTPException(status_code=401, detail="Invalid token")
    access_token = create_access_token(
        {"sub": user.username},
        timedelta(minutes=settings.access_token_expire_minutes),
    )
    new_refresh_token, new_refresh_jti = create_refresh_token(user.username)
    user.refresh_jti = new_refresh_jti
    await db.commit()
    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}

@router.get("/auth/me")
async def read_current_user(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
    }
