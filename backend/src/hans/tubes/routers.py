from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from hans.core.auth import require_admin, require_staff_or_admin
from hans.core.core import audit_log
from hans.core.db import get_db
from hans.users import User

from .schemas import TubeTypeCreate, TubeTypeRead
from .services import (
    create_tube as create_tube_service,
    delete_tube as delete_tube_service,
    get_tubes as get_tubes_service,
    update_tube as update_tube_service,
)


# --- ROUTES -----------------------------------------------------------

router = APIRouter(prefix="/tubes", tags=["tubes"])


@router.get("/", response_model=List[TubeTypeRead])
async def get_tube(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
) -> List[TubeTypeRead]:
    return await get_tubes_service(db)


@router.post("/", response_model=TubeTypeRead)
async def create_tube(
    data: TubeTypeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> TubeTypeRead:
    tube_type = await create_tube_service(data, db)
    audit_log(user.id, f"Created tube_type {tube_type.id}")
    return tube_type


@router.put("/{tube_id}", response_model=TubeTypeRead)
async def update_tube(
    tube_id: int,
    data: TubeTypeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> TubeTypeRead:
    tube_type = await update_tube_service(tube_id, data, db)
    audit_log(user.id, f"Updated tube_type {tube_id}")
    return tube_type


@router.delete("/{tube_id}")
async def delete_tube(
    tube_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict[str, bool]:
    await delete_tube_service(tube_id, db)
    audit_log(user.id, f"Deleted tube_type {tube_id}")
    return {"ok": True}
