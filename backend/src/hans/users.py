from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from hans.core.db import get_db
from hans.core.auth import User, hash_password, require_admin
from hans.core.core import audit_log


# ---------------- SCHEMAS ----------------

class UserCreate(BaseModel):
    username: str
    email: str
    role: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    role: str
    # created_at: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------- MODELS ----------------

# Imported from hans.core.auth


# ---------------- ROUTES ----------------

router = APIRouter(prefix="/settings/users")

@router.get("/", response_model=List[UserRead])
async def get_users(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin), skip: int = 0, limit: int = 100):
    result = await db.execute(select(User).offset(skip).limit(limit).order_by(User.username))
    return result.scalars().all()

@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    return user

@router.post("/")
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    # Hash the raw password
    hashed_password = hash_password(data.password)
    user = User(
        username=data.username,
        email=data.email,
        role=data.role,
        hashed_password=hashed_password,
    )
    db.add(user)
    await db.commit()
    audit_log(current_user.id, f"Created user ID: {user.id}, username: {user.username}")
    return user

# @app.put("/owners/{owner_id}")
# async def update_owner(owner_id: int, data: OwnerCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
#     result = await db.execute(select(Owner).where(Owner.id == owner_id))
#     owner = result.scalar_one_or_none()
#     if not owner:
#         raise HTTPException(404, "Owner not found")
#     for key, value in data.dict().items():
#         setattr(owner, key, value)
#     await db.commit()
#     audit_log(user.id, f"Updated owner {owner_id}")
#     return owner

# @app.delete("/owners/{owner_id}")
# async def delete_owner(owner_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
#     result = await db.execute(select(Owner).where(Owner.id == owner_id))
#     owner = result.scalar_one_or_none()
#     if not owner:
#         raise HTTPException(404, "Owner not found")
#     await db.delete(owner)
#     await db.commit()
#     audit_log(user.id, f"Deleted owner {owner_id}")
#     return {"ok": True}
