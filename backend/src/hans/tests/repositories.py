from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import TestCatalog


# --- TEST QUERIES -----------------------------------------------------

async def fetch_tests(db: AsyncSession) -> list[TestCatalog]:
    result = await db.execute(select(TestCatalog).order_by(TestCatalog.code))
    return result.scalars().all()


async def fetch_test_by_id(test_id: int, db: AsyncSession) -> Optional[TestCatalog]:
    result = await db.execute(select(TestCatalog).where(TestCatalog.id == test_id))
    return result.scalar_one_or_none()
