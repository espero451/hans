from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Owner


# --- OWNER QUERIES ----------------------------------------------------

async def fetch_owners(
    skip: int,
    limit: int,
    first_name: str | None,
    last_name: str | None,
    email: str | None,
    phone: str | None,
    db: AsyncSession,
) -> list[Owner]:
    query = select(Owner)
    if first_name:
        query = query.where(Owner.first_name.ilike(f"%{first_name}%"))
    if last_name:
        query = query.where(Owner.last_name.ilike(f"%{last_name}%"))
    if email:
        query = query.where(Owner.email.ilike(f"%{email}%"))
    if phone:
        query = query.where(Owner.phone.ilike(f"%{phone}%"))
    result = await db.execute(
        query.offset(skip).limit(limit).order_by(Owner.last_name, Owner.first_name)
    )
    return result.scalars().all()


async def count_owners(
    first_name: str | None,
    last_name: str | None,
    email: str | None,
    phone: str | None,
    db: AsyncSession,
) -> int:
    query = select(func.count()).select_from(Owner)
    if first_name:
        query = query.where(Owner.first_name.ilike(f"%{first_name}%"))
    if last_name:
        query = query.where(Owner.last_name.ilike(f"%{last_name}%"))
    if email:
        query = query.where(Owner.email.ilike(f"%{email}%"))
    if phone:
        query = query.where(Owner.phone.ilike(f"%{phone}%"))
    result = await db.execute(query)
    return result.scalar_one()


async def fetch_owner(owner_id: int, db: AsyncSession) -> Optional[Owner]:
    result = await db.execute(select(Owner).where(Owner.id == owner_id))
    return result.scalar_one_or_none()
