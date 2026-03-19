from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Owner


# --- OWNER QUERIES ----------------------------------------------------

def build_owners_query(
    first_name: str | None,
    last_name: str | None,
    email: str | None,
    phone: str | None,
):
    query = select(Owner)
    if first_name:
        query = query.where(Owner.first_name.ilike(f"%{first_name}%"))
    if last_name:
        query = query.where(Owner.last_name.ilike(f"%{last_name}%"))
    if email:
        query = query.where(Owner.email.ilike(f"%{email}%"))
    if phone:
        query = query.where(Owner.phone.ilike(f"%{phone}%"))
    return query.order_by(Owner.last_name, Owner.first_name)


async def fetch_owner(owner_id: int, db: AsyncSession) -> Optional[Owner]:
    result = await db.execute(select(Owner).where(Owner.id == owner_id))
    return result.scalar_one_or_none()
