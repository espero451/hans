from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from hans.core.auth import require_admin, require_staff_or_admin
from hans.core.core import audit_log
from hans.core.db import get_db
from hans.users import User

from .schemas import TestCatalogCreate, TestCatalogRead
from .services import (
    create_test as create_test_service,
    delete_test as delete_test_service,
    get_tests as get_tests_service,
    update_test as update_test_service,
)


# --- ROUTES -----------------------------------------------------------

router = APIRouter(prefix="/tests", tags=["tests"])


@router.get("/", response_model=List[TestCatalogRead])
async def get_tests(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
) -> List[TestCatalogRead]:
    return await get_tests_service(db)


@router.post("/", response_model=TestCatalogRead)
async def create_test(
    data: TestCatalogCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> TestCatalogRead:
    test = await create_test_service(data, db)
    audit_log(user.id, f"Created test {test.id}")
    return test


@router.put("/{test_id}", response_model=TestCatalogRead)
async def update_test(
    test_id: int,
    data: TestCatalogCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> TestCatalogRead:
    test = await update_test_service(test_id, data, db)
    audit_log(user.id, f"Updated test {test_id}")
    return test


@router.delete("/{test_id}")
async def delete_test(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict[str, bool]:
    await delete_test_service(test_id, db)
    audit_log(user.id, f"Deleted test {test_id}")
    return {"ok": True}
