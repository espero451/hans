from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import String, ForeignKey
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from hans.core.db import Base, get_db
from hans.core.auth import User, require_admin, require_staff_or_admin
from hans.core.core import audit_log


# ---------------- SCHEMAS ----------------

class SpecimenTypeCreate(BaseModel):
    code: str
    name: str
    type: str
    tube_type_id: int
    description: Optional[str] = None


class SpecimenTypeRead(BaseModel):
    id: int
    code: str
    name: str
    type: Optional[str] = None
    tube_type_id: int
    description: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------- MODELS ----------------

class SpecimenType(Base):
    __tablename__ = "specimen_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tube_type_id: Mapped[int] = mapped_column(ForeignKey("tube_types.id"))
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)


# ---------------- ROUTES ----------------

router = APIRouter(prefix="/specimens")

@router.get("/", response_model=List[SpecimenTypeRead])
async def get_specimens(db: AsyncSession = Depends(get_db), user: User = Depends(require_staff_or_admin)):
    result = await db.execute(select(SpecimenType).order_by(SpecimenType.id))
    return result.scalars().all()

@router.post("/", response_model=SpecimenTypeRead)
async def create_specimen(data: SpecimenTypeCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    specimen_type = SpecimenType(**data.dict())
    db.add(specimen_type)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Specimen code already exists")
    audit_log(user.id, f"Created specimen_type {specimen_type.id}")
    return specimen_type

@router.put("/{specimen_id}", response_model=SpecimenTypeRead)
async def update_specimen(specimen_id: int, data: SpecimenTypeCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    result_obj = await db.execute(select(SpecimenType).where(SpecimenType.id == specimen_id))
    specimen_type = result_obj.scalar_one_or_none()
    if not specimen_type:
        raise HTTPException(404, "Specimen type not found")
    for key, value in data.dict().items():
        setattr(specimen_type, key, value)
    await db.commit()
    audit_log(user.id, f"Updated specimen_type {specimen_id}")
    return specimen_type

@router.delete("/{specimen_id}")
async def delete_specimen(specimen_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    result_obj = await db.execute(select(SpecimenType).where(SpecimenType.id == specimen_id))
    specimen_type = result_obj.scalar_one_or_none()
    if not specimen_type:
        raise HTTPException(404, "Specimen type not found")
    await db.delete(specimen_type)
    await db.commit()
    audit_log(user.id, f"Deleted specimen_type {specimen_id}")
    return {"ok": True}
