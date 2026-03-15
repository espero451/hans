from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .repositories import fetch_tests
from .schemas import TestCatalogRead


# --- TEST FLOWS -------------------------------------------------------

async def get_tests(db: AsyncSession) -> list[TestCatalogRead]:
    tests = await fetch_tests(db)
    return [TestCatalogRead.model_validate(test) for test in tests]
