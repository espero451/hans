from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .models import TestCatalog
from .repositories import fetch_test_by_id, fetch_tests
from .schemas import TestCatalogCreate, TestCatalogRead


# --- TEST FLOWS -------------------------------------------------------

async def get_tests(db: AsyncSession) -> list[TestCatalogRead]:
    tests = await fetch_tests(db)
    return [TestCatalogRead.model_validate(test) for test in tests]


async def create_test(data: TestCatalogCreate, db: AsyncSession) -> TestCatalogRead:
    test = TestCatalog(**data.dict())
    db.add(test)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Test code already exists")
    await db.refresh(test)
    return TestCatalogRead.model_validate(test)


async def update_test(test_id: int, data: TestCatalogCreate, db: AsyncSession) -> TestCatalogRead:
    test = await fetch_test_by_id(test_id, db)
    if not test:
        raise HTTPException(404, "Test not found")
    # Replace all editable fields with payload values.
    for key, value in data.dict().items():
        setattr(test, key, value)
    await db.commit()
    await db.refresh(test)
    return TestCatalogRead.model_validate(test)


async def delete_test(test_id: int, db: AsyncSession) -> None:
    test = await fetch_test_by_id(test_id, db)
    if not test:
        raise HTTPException(404, "Test not found")
    await db.delete(test)
    await db.commit()
