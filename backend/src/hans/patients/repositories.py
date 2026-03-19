from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Patient, Species


# --- PATIENT QUERIES --------------------------------------------------

def build_patients_query(
    q: str | None,
    species_id: int | None,
    owner_id: int | None,
):
    query = select(Patient)
    if q:
        # Filter patients by name directly in SQL.
        query = query.where(Patient.name.ilike(f"%{q}%"))
    if species_id is not None:
        query = query.where(Patient.species_id == species_id)
    if owner_id is not None:
        query = query.where(Patient.owner_id == owner_id)
    return query.order_by(Patient.name)


async def fetch_patient(patient_id: int, db: AsyncSession) -> Optional[Patient]:
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    return result.scalar_one_or_none()


# --- SPECIES QUERIES --------------------------------------------------

async def fetch_species(db: AsyncSession) -> list[Species]:
    result = await db.execute(select(Species).order_by(Species.name))
    return result.scalars().all()
