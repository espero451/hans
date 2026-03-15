from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from hans.core.auth import require_staff_or_admin
from hans.core.db import get_db
from hans.users import User

from .schemas import TestCatalogRead
from .services import (
    get_tests as get_tests_service,
)


# --- ROUTES -----------------------------------------------------------

router = APIRouter(prefix="/tests", tags=["tests"])


@router.get("/", response_model=List[TestCatalogRead])
async def get_tests(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
) -> List[TestCatalogRead]:
    return await get_tests_service(db)
