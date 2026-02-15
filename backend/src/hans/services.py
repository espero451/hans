from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from hans.core.db import Base, get_db
from hans.core.auth import User, require_admin, require_staff_or_admin
from hans.core.core import audit_log


# ---------------- MODELS ----------------

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


# ---------------- SCHEMAS ----------------

class ServiceCatalog(Base):
    __tablename__ = "service_catalog"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[Optional[str]]


# ---------------- ROUTES ----------------

router = APIRouter(prefix="/services")

@router.get("/", response_model=List[ServiceCatalogRead])
async def get_services(db: AsyncSession = Depends(get_db), user: User = Depends(require_staff_or_admin)):
    result = await db.execute(select(ServiceCatalog).order_by(ServiceCatalog.name))
    return result.scalars().all()

@router.post("/", response_model=ServiceCatalogRead)
async def create_service(data: ServiceCatalogCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    service = ServiceCatalog(**data.dict())
    db.add(service)
    await db.commit()
    audit_log(user.id, f"Created service {service.id}")
    return service

@router.put("/{service_id}", response_model=ServiceCatalogRead)
async def update_service(service_id: int, data: ServiceCatalogCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    result_obj = await db.execute(select(ServiceCatalog).where(ServiceCatalog.id == service_id))
    service = result_obj.scalar_one_or_none()
    if not service:
        raise HTTPException(404, "Service not found")
    for key, value in data.dict().items():
        setattr(service, key, value)
    await db.commit()
    audit_log(user.id, f"Updated service {service_id}")
    return service

@router.delete("/{service_id}")
async def delete_service(service_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    result_obj = await db.execute(select(ServiceCatalog).where(ServiceCatalog.id == service_id))
    service = result_obj.scalar_one_or_none()
    if not service:
        raise HTTPException(404, "Service not found")
    await db.delete(service)
    await db.commit()
    audit_log(user.id, f"Deleted service {service_id}")
    return {"ok": True}
