from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from hans.core.auth import AuthPrincipal, require_staff_or_admin
from hans.core.db import get_db

from .schemas import TubeTypeRead
from .services import (
    get_tubes as get_tubes_service,
)


# --- ROUTES -----------------------------------------------------------

router = APIRouter(prefix="/tubes", tags=["tubes"])


@router.get("/", response_model=list[TubeTypeRead])
async def get_tube(
    db: AsyncSession = Depends(get_db),
    user: AuthPrincipal = Depends(require_staff_or_admin),
) -> list[TubeTypeRead]:
    return await get_tubes_service(db)
