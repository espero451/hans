from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Patient, Species


# --- PATIENT QUERIES --------------------------------------------------

async def fetch_patients(
    skip: int,
    limit: int,
    q: str | None,
    db: AsyncSession,
) -> list[Patient]:
    query = select(Patient)
    if q:
        # Filter patients by name directly in SQL.
        query = query.where(Patient.name.ilike(f"%{q}%"))
    result = await db.execute(query.offset(skip).limit(limit).order_by(Patient.name))
    return result.scalars().all()


async def fetch_patient(patient_id: int, db: AsyncSession) -> Optional[Patient]:
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    return result.scalar_one_or_none()


async def count_patients(q: str | None, db: AsyncSession) -> int:
    query = select(func.count()).select_from(Patient)
    if q:
        # Keep total count aligned with the active search filter.
        query = query.where(Patient.name.ilike(f"%{q}%"))
    result = await db.execute(query)
    return result.scalar_one()


# --- SPECIES QUERIES --------------------------------------------------

async def fetch_species(db: AsyncSession) -> list[Species]:
    result = await db.execute(select(Species).order_by(Species.name))
    return result.scalars().all()
