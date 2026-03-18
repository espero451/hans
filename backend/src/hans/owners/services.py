from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Owner
from .repositories import count_owners, fetch_owner, fetch_owners
from .schemas import OwnerCreate, OwnerRead


# --- OWNER FLOWS ------------------------------------------------------

async def get_owners(
    skip: int,
    limit: int,
    first_name: str | None,
    last_name: str | None,
    email: str | None,
    phone: str | None,
    db: AsyncSession,
) -> tuple[list[OwnerRead], int]:
    owners = await fetch_owners(skip, limit, first_name, last_name, email, phone, db)
    total = await count_owners(first_name, last_name, email, phone, db)
    return [OwnerRead.model_validate(owner) for owner in owners], total


async def get_owner(owner_id: int, db: AsyncSession) -> OwnerRead:
    owner = await fetch_owner(owner_id, db)
    if not owner:
        raise HTTPException(404, "Owner not found")
    return OwnerRead.model_validate(owner)


async def create_owner(data: OwnerCreate, db: AsyncSession) -> OwnerRead:
    owner = Owner(**data.dict())
    db.add(owner)
    await db.commit()
    await db.refresh(owner)
    return OwnerRead.model_validate(owner)


async def update_owner(owner_id: int, data: OwnerCreate, db: AsyncSession) -> OwnerRead:
    owner = await fetch_owner(owner_id, db)
    if not owner:
        raise HTTPException(404, "Owner not found")
    # Update all editable owner fields from payload.
    for key, value in data.dict().items():
        setattr(owner, key, value)
    await db.commit()
    await db.refresh(owner)
    return OwnerRead.model_validate(owner)


async def delete_owner(owner_id: int, db: AsyncSession) -> None:
    owner = await fetch_owner(owner_id, db)
    if not owner:
        raise HTTPException(404, "Owner not found")
    await db.delete(owner)
    await db.commit()
