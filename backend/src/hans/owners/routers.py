from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from hans.core.auth import get_current_user
from hans.core.core import audit_log
from hans.core.db import get_db
from hans.users import User
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

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


@router.get("/", response_model=Page[OwnerRead])
async def get_owners(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    params: Params = Depends(),
    first_name: str | None = Query(None, min_length=1),
    last_name: str | None = Query(None, min_length=1),
    email: str | None = Query(None, min_length=1),
    phone: str | None = Query(None, min_length=1),
) -> Page[OwnerRead]:
    query = await get_owners_service(first_name, last_name, email, phone)
    return await paginate(db, query, params=params)


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
