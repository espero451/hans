from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import SpecimenType


# --- SPECIMEN QUERIES -------------------------------------------------

async def fetch_specimen_type(specimen_id: int, db: AsyncSession) -> Optional[SpecimenType]:
    result = await db.execute(select(SpecimenType).where(SpecimenType.id == specimen_id))
    return result.scalar_one_or_none()
