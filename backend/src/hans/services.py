from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from hans.core.db import Base, get_db
from hans.core.core import audit_log
from hans.core.auth import require_admin, require_staff_or_admin
from hans.users import User


# --- MODELS ----------------------------------------------------------

class ServiceCatalogCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float


class ServiceCatalogRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float

    class Config:
        from_attributes = True


# --- SCHEMAS ---------------------------------------------------------

class ServiceCatalog(Base):
    __tablename__ = "service_catalog"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[Optional[str]]


# --- ROUTES ----------------------------------------------------------

router = APIRouter(prefix="/services")

@router.get("/", response_model=List[ServiceCatalogRead])
async def get_services(db: AsyncSession = Depends(get_db), user: User = Depends(require_staff_or_admin)):
    result = await db.execute(select(ServiceCatalog).order_by(ServiceCatalog.name))
    return result.scalars().all()
