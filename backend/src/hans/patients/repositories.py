from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Patient, Species


# --- PATIENT QUERIES --------------------------------------------------

async def fetch_patients(skip: int, limit: int, db: AsyncSession) -> List[Patient]:
    result = await db.execute(select(Patient).offset(skip).limit(limit).order_by(Patient.name))
    return result.scalars().all()


async def fetch_patient(patient_id: int, db: AsyncSession) -> Optional[Patient]:
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    return result.scalar_one_or_none()


async def count_patients(db: AsyncSession) -> int:
    result = await db.execute(select(func.count()).select_from(Patient))
    return result.scalar_one()


# --- SPECIES QUERIES --------------------------------------------------

async def fetch_species(db: AsyncSession) -> List[Species]:
    result = await db.execute(select(Species).order_by(Species.name))
    return result.scalars().all()
