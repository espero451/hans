from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .models import TubeType
from .repositories import fetch_tube_by_id, fetch_tubes
from .schemas import TubeTypeCreate, TubeTypeRead


# --- TUBE FLOWS -------------------------------------------------------

async def get_tubes(db: AsyncSession) -> list[TubeTypeRead]:
    tubes = await fetch_tubes(db)
    return [TubeTypeRead.model_validate(tube) for tube in tubes]


async def create_tube(data: TubeTypeCreate, db: AsyncSession) -> TubeTypeRead:
    tube_type = TubeType(**data.dict())
    db.add(tube_type)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Tube code already exists")
    await db.refresh(tube_type)
    return TubeTypeRead.model_validate(tube_type)


async def update_tube(tube_id: int, data: TubeTypeCreate, db: AsyncSession) -> TubeTypeRead:
    tube_type = await fetch_tube_by_id(tube_id, db)
    if not tube_type:
        raise HTTPException(404, "Tube type not found")
    # Replace editable tube fields from payload.
    for key, value in data.dict().items():
        setattr(tube_type, key, value)
    await db.commit()
    await db.refresh(tube_type)
    return TubeTypeRead.model_validate(tube_type)


async def delete_tube(tube_id: int, db: AsyncSession) -> None:
    tube_type = await fetch_tube_by_id(tube_id, db)
    if not tube_type:
        raise HTTPException(404, "Tube type not found")
    await db.delete(tube_type)
    await db.commit()
