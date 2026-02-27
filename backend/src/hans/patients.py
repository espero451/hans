from datetime import date, datetime
from typing import Optional, List, Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import ForeignKey, Date, String, Boolean, BigInteger, Float

from hans.core.core import audit_log
from hans.core.db import Base, get_db
from hans.core.auth import get_current_user, User
from hans.owners import Owner


# ---------------- SCHEMAS ----------------

class PatientCreate(BaseModel):
    # Core patient identification fields.
    name: str
    species: str
    owner_id: int
    breed: Optional[str] = None
    birth_date: Optional[date] = None
    comment: Optional[str] = None
    sex: Literal["male", "female", "unknown"]
    weight: Optional[float] = None
    microchip_number: Optional[str] = None
    species_id: int


# Partial update schema
class PatientUpdate(BaseModel):
    # Optional identity updates.
    name: Optional[str] = None
    species: Optional[str] = None
    owner_id: Optional[int] = None
    breed: Optional[str] = None
    birth_date: Optional[date] = None
    comment: Optional[str] = None
    sex: Optional[Literal["male", "female", "unknown"]] = None
    weight: Optional[float] = None
    microchip_number: Optional[str] = None
    species_id: Optional[int] = None


class PatientRead(BaseModel):
    id: int
    name: str
    species: str
    owner_id: int
    breed: Optional[str] = None
    birth_date: Optional[date] = None
    created_at: datetime
    comment: Optional[str] = None
    sex: Literal["male", "female", "unknown"]
    weight: Optional[float] = None
    microchip_number: Optional[str] = None
    species_id: int

    class Config:
        from_attributes = True


class SpeciesRead(BaseModel):
    # Species data for UI dropdowns.
    id: int
    code: str
    name: str
    latin_name: Optional[str] = None
    active: bool

    class Config:
        from_attributes = True


# ---------------- MODELS ----------------

class Species(Base):
    __tablename__ = "species"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    latin_name: Mapped[Optional[str]] = mapped_column(String(128))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    species: Mapped[str]
    species_id: Mapped[int] = mapped_column(ForeignKey("species.id"))
    breed: Mapped[Optional[str]]
    sex: Mapped[str] = mapped_column(String(16), nullable=False)
    weight: Mapped[Optional[float]] = mapped_column(Float)
    microchip_number: Mapped[Optional[str]] = mapped_column(String(64))
    comment: Mapped[Optional[str]]
    birth_date: Mapped[Optional[date]] = mapped_column(Date)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id"))
    owner = relationship("Owner", lazy="joined")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


# ---------------- ROUTES ----------------

router = APIRouter(prefix="/patients")
species_router = APIRouter(prefix="/species")


@species_router.get("/", response_model=List[SpeciesRead])
async def get_species(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Return species list for selectors.
    result = await db.execute(select(Species).order_by(Species.name))
    return result.scalars().all()

@router.get("/", response_model=List[PatientRead])
async def get_patients(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 100):
    result = await db.execute(select(Patient).offset(skip).limit(limit).order_by(Patient.name))
    return result.scalars().all()

@router.post("/", response_model=PatientRead)
async def create_patient(data: PatientCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    patient = Patient(**data.dict())
    db.add(patient)
    await db.commit()
    audit_log(user.id, f"Created patient {patient.id}")
    return patient

@router.put("/{patient_id}", response_model=PatientRead)
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

@router.patch("/{patient_id}", response_model=PatientRead)
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

@router.get("/{patient_id}", response_model=PatientRead)
async def get_patient(patient_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(404, "Patient not found")
    return patient
