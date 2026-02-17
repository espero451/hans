from datetime import date, datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import ForeignKey, Date

from hans.core.core import audit_log
from hans.core.db import Base, get_db
from hans.core.auth import get_current_user, User
from hans.owners import Owner


# ---------------- SCHEMAS ----------------

class PatientCreate(BaseModel):
    name: str
    species: str
    owner_id: int
    breed: Optional[str] = None
    birth_date: Optional[date] = None
    comment: Optional[str] = None


# Partial update schema
class PatientUpdate(BaseModel):
    comment: Optional[str] = None


class PatientRead(BaseModel):
    id: int
    name: str
    species: str
    owner_id: int
    breed: Optional[str] = None
    birth_date: Optional[date] = None
    created_at: datetime
    comment: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------- MODELS ----------------

class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    species: Mapped[str]
    breed: Mapped[Optional[str]]
    comment: Mapped[Optional[str]]
    birth_date: Mapped[Optional[date]] = mapped_column(Date)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


# ---------------- ROUTES ----------------

router = APIRouter(prefix="/patients")

@router.get("/", response_model=List[PatientRead])
async def get_patients(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 100):
    result = await db.execute(select(Patient).offset(skip).limit(limit).order_by(Patient.name))
    return result.scalars().all()

@router.post("/")
async def create_patient(data: PatientCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    patient = Patient(**data.dict())
    db.add(patient)
    await db.commit()
    audit_log(user.id, f"Created patient {patient.id}")
    return patient

@router.put("/{patient_id}")
async def update_patient(patient_id: int, data: PatientCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(404, "Patient not found")
    for key, value in data.dict().items():
        setattr(patient, key, value)
    await db.commit()
    audit_log(user.id, f"Updated patient {patient_id}")
    return patient

@router.patch("/{patient_id}")
async def patch_patient(patient_id: int, data: PatientUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    # Load patient
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(404, "Patient not found")
    # Apply changes
    for key, value in data.dict(exclude_unset=True).items():
        setattr(patient, key, value)
    await db.commit()
    audit_log(user.id, f"Patched patient {patient_id}")
    return patient

@router.delete("/{patient_id}")
async def delete_patient(patient_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(404, "Patient not found")
    await db.delete(patient)
    await db.commit()
    audit_log(user.id, f"Deleted patient {patient_id}")
    return {"ok": True}

@router.get("/{patient_id}")
async def get_patient(patient_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(404, "Patient not found")
    return patient
