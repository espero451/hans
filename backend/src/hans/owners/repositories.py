from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Owner


# --- OWNER QUERIES ----------------------------------------------------

async def fetch_owners(skip: int, limit: int, db: AsyncSession) -> list[Owner]:
    result = await db.execute(
        select(Owner).offset(skip).limit(limit).order_by(Owner.last_name, Owner.first_name)
    )
    return result.scalars().all()


async def fetch_owner(owner_id: int, db: AsyncSession) -> Optional[Owner]:
    result = await db.execute(select(Owner).where(Owner.id == owner_id))
    return result.scalar_one_or_none()
