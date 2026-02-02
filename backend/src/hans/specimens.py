from datetime import datetime
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

class SpecimenRead(BaseModel):
    id: int
    name: str
    type: str
    tube: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class SpecimenCreate(BaseModel):
    name: str
    type: str
    tube: Optional[str] = None
    description: Optional[str] = None


# ---------------- MODELS ----------------

class Specimen(Base):
    __tablename__ = "specimens"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str]
    description: Mapped[str]
    name: Mapped[str] = mapped_column(String, nullable=False) 
    tube: Mapped[str] = mapped_column(String, nullable=False)


# ---------------- ROUTES ----------------

@app.get("/specimens", response_model=List[SpecimenRead])
async def get_specimens(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Specimen).order_by(Specimen.id))
    return result.scalars().all()

@app.post("/specimens", response_model=SpecimenCreate)
async def create_specimen(data: SpecimenCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    specimen = Specimen(**data.dict())
    db.add(specimen)
    await db.commit()
    audit_log(user.id, f"Created specimen {specimen.id}")
    return specimen

@app.put("/specimens/{specimen_id}", response_model=SpecimenCreate)
async def update_specimen(specimen_id: int, data: SpecimenCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result_obj = await db.execute(select(Specimen).where(Specimen.id == specimen_id))
    specimen = result_obj.scalar_one_or_none()
    if not specimen:
        raise HTTPException(404, "Specimen not found")
    for key, value in data.dict().items():
        setattr(specimen, key, value)
    await db.commit()
    audit_log(user.id, f"Updated specimen {specimen_id}")
    return specimen

@app.delete("/specimens/{specimen_id}")
async def delete_specimen(specimen_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result_obj = await db.execute(select(Specimen).where(Specimen.id == specimen_id))
    specimen = result_obj.scalar_one_or_none()
    if not specimen:
        raise HTTPException(404, "Specimen not found")
    await db.delete(specimen)
    await db.commit()
    audit_log(user.id, f"Deleted specimen {specimen_id}")
    return {"ok": True}

