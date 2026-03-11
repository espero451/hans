from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import TubeType


# --- TUBE QUERIES -----------------------------------------------------

async def fetch_tubes(db: AsyncSession) -> List[TubeType]:
    result = await db.execute(select(TubeType).order_by(TubeType.id))
    return result.scalars().all()


async def fetch_tube_by_id(tube_id: int, db: AsyncSession) -> Optional[TubeType]:
    result = await db.execute(select(TubeType).where(TubeType.id == tube_id))
    return result.scalar_one_or_none()
