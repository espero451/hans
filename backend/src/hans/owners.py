from typing import Optional, List
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from hans.db import Base, get_db
from hans.auth import get_current_user, User
from hans.core import app, audit_log


# ---------------- SCHEMAS ----------------

class OwnerCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    comment: Optional[str] = None


class OwnerRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    comment: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------- MODELS ----------------

class Owner(Base):
    __tablename__ = "owners"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    email: Mapped[Optional[str]]
    phone: Mapped[Optional[str]]
    comment: Mapped[Optional[str]]


# ---------------- ROUTES ----------------

@app.get("/owners", response_model=List[OwnerRead])
async def get_owners(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 100):
    result = await db.execute(select(Owner).offset(skip).limit(limit).order_by(Owner.last_name, Owner.first_name))
    return result.scalars().all()

@app.get("/owners/{owner_id}", response_model=OwnerRead)
async def get_owner(owner_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Owner).where(Owner.id == owner_id))
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(404, "Owner not found")
    return owner

@app.post("/owners")
async def create_owner(data: OwnerCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    owner = Owner(**data.dict())
    db.add(owner)
    await db.commit()
    audit_log(user.id, f"Created owner {owner.id}")
    return owner

@app.put("/owners/{owner_id}")
async def update_owner(owner_id: int, data: OwnerCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Owner).where(Owner.id == owner_id))
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(404, "Owner not found")
    for key, value in data.dict().items():
        setattr(owner, key, value)
    await db.commit()
    audit_log(user.id, f"Updated owner {owner_id}")
    return owner

@app.delete("/owners/{owner_id}")
async def delete_owner(owner_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Owner).where(Owner.id == owner_id))
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(404, "Owner not found")
    await db.delete(owner)
    await db.commit()
    audit_log(user.id, f"Deleted owner {owner_id}")
    return {"ok": True}

