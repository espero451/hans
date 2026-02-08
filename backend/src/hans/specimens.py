from typing import Optional, List
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import String

from hans.db import Base, get_db
from hans.auth import get_current_user, User
from hans.core import app, audit_log


# ---------------- SCHEMAS ----------------

class SpecimenTypeCreate(BaseModel):
    code: str
    name: str
    tube: Optional[str] = None
    description: Optional[str] = None


class SpecimenTypeRead(BaseModel):
    id: int
    code: str
    name: str
    tube: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------- MODELS ----------------

class SpecimenType(Base):
    __tablename__ = "specimen_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    tube: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)


# ---------------- ROUTES ----------------

@app.get("/specimens", response_model=List[SpecimenTypeRead])
async def get_specimens(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(SpecimenType).order_by(SpecimenType.id))
    return result.scalars().all()

@app.post("/specimens", response_model=SpecimenTypeRead)
async def create_specimen(data: SpecimenTypeCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    specimen_type = SpecimenType(**data.dict())
    db.add(specimen_type)
    await db.commit()
    audit_log(user.id, f"Created specimen_type {specimen_type.id}")
    return specimen_type

@app.put("/specimens/{specimen_id}", response_model=SpecimenTypeRead)
async def update_specimen(specimen_id: int, data: SpecimenTypeCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result_obj = await db.execute(select(SpecimenType).where(SpecimenType.id == specimen_id))
    specimen_type = result_obj.scalar_one_or_none()
    if not specimen_type:
        raise HTTPException(404, "Specimen type not found")
    for key, value in data.dict().items():
        setattr(specimen_type, key, value)
    await db.commit()
    audit_log(user.id, f"Updated specimen_type {specimen_id}")
    return specimen_type

@app.delete("/specimens/{specimen_id}")
async def delete_specimen(specimen_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result_obj = await db.execute(select(SpecimenType).where(SpecimenType.id == specimen_id))
    specimen_type = result_obj.scalar_one_or_none()
    if not specimen_type:
        raise HTTPException(404, "Specimen type not found")
    await db.delete(specimen_type)
    await db.commit()
    audit_log(user.id, f"Deleted specimen_type {specimen_id}")
    return {"ok": True}
