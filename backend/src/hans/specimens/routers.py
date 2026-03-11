from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from hans.core.auth import require_staff_or_admin
from hans.core.db import get_db
from hans.users import User

from .schemas import SpecimenTypeRead
from .services import get_specimen_type


# --- ROUTES -----------------------------------------------------------

router = APIRouter(prefix="/specimens", tags=["specimens"])


@router.get("/{id}", response_model=SpecimenTypeRead)
async def get_specimen(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
) -> SpecimenTypeRead:
    return await get_specimen_type(id, db)
