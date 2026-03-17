from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from hans.core.auth import get_current_user
from hans.core.core import audit_log
from hans.core.db import get_db
from hans.users import User
from hans.owners.models import Owner

from .schemas import OwnerCreate, OwnerRead
from .services import (
    create_owner as create_owner_service,
    delete_owner as delete_owner_service,
    get_owner as get_owner_service,
    get_owners as get_owners_service,
    update_owner as update_owner_service,
)


# --- ROUTES -----------------------------------------------------------

router = APIRouter(prefix="/owners", tags=["owners"])


@router.get("/{owner_id}", response_model=OwnerRead)
async def get_owner(
    owner_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OwnerRead:
    return await get_owner_service(owner_id, db)


@router.get("/", response_model=list[OwnerRead])
async def get_owners(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    q: str | None = Query(None, min_length=1),
    skip: int = 0,
    limit: int = Query(20, le=100),
):
    query = select(Owner)
    if q:
        query = query.where(
            or_(
                Owner.first_name.ilike(f"%{q}%"),
                Owner.last_name.ilike(f"%{q}%"),
            )
        )
    query = query.order_by(Owner.last_name).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=OwnerRead)
async def create_owner(
    data: OwnerCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OwnerRead:
    owner = await create_owner_service(data, db)
    audit_log(user.id, f"Created owner {owner.id}")
    return owner


@router.put("/{owner_id}", response_model=OwnerRead)
async def update_owner(
    owner_id: int,
    data: OwnerCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OwnerRead:
    owner = await update_owner_service(owner_id, data, db)
    audit_log(user.id, f"Updated owner {owner_id}")
    return owner


@router.delete("/{owner_id}")
async def delete_owner(
    owner_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, bool]:
    await delete_owner_service(owner_id, db)
    audit_log(user.id, f"Deleted owner {owner_id}")
    return {"ok": True}
