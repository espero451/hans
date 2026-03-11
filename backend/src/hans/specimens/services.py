from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .repositories import fetch_specimen_type
from .schemas import SpecimenTypeRead


# --- SPECIMEN FLOWS ---------------------------------------------------

async def get_specimen_type(specimen_id: int, db: AsyncSession) -> SpecimenTypeRead:
    specimen = await fetch_specimen_type(specimen_id, db)
    if specimen is None:
        raise HTTPException(status_code=404, detail="Specimen not found")
    return SpecimenTypeRead.model_validate(specimen)
