from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .repositories import fetch_tubes
from .schemas import TubeTypeRead


# --- TUBE FLOWS -------------------------------------------------------

async def get_tubes(db: AsyncSession) -> list[TubeTypeRead]:
    tubes = await fetch_tubes(db)
    return [TubeTypeRead.model_validate(tube) for tube in tubes]
