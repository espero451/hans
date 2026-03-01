from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
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

# Hash a plain-text password before storing it in the database.
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Check whether a plain-text password matches its stored hash.
def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

# Create a signed JWT access token with an expiration time.
# The token "sub" claim is stored as a string (username).
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode["exp"] = int(expire.timestamp())
    to_encode["sub"] = str(to_encode["sub"])
    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )

# Login endpoint: validates credentials and returns a bearer token.
# OAuth2PasswordRequestForm provides "username" and "password" from the request body.
@app.post("/auth/token")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.username}, timedelta(minutes=settings.access_token_expire_minutes))
    return {"access_token": token, "token_type": "bearer"}


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
        username: str = payload["sub"]
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

@router.get("/auth/me")
async def read_current_user(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
    }
