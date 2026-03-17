from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from hans.core.auth import AuthPrincipal, require_staff_or_admin
from hans.core.db import get_db

from .schemas import TestCatalogRead
from .services import (
    get_tests as get_tests_service,
)


# --- ROUTES -----------------------------------------------------------

router = APIRouter(prefix="/tests", tags=["tests"])


@router.get("/", response_model=list[TestCatalogRead])
async def get_tests(
    db: AsyncSession = Depends(get_db),
    user: AuthPrincipal = Depends(require_staff_or_admin),
) -> list[TestCatalogRead]:
    return await get_tests_service(db)
