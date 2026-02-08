from typing import Optional, List
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import Numeric, String

from hans.db import Base, get_db
from hans.auth import get_current_user, User
from hans.core import app, audit_log


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

@app.get("/services", response_model=List[ServiceCatalogRead])
async def get_services(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(ServiceCatalog).order_by(ServiceCatalog.name))
    return result.scalars().all()

@app.post("/services", response_model=ServiceCatalogRead)
async def create_service(data: ServiceCatalogCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    service = ServiceCatalog(**data.dict())
    db.add(service)
    await db.commit()
    audit_log(user.id, f"Created service {service.id}")
    return service

@app.put("/services/{service_id}", response_model=ServiceCatalogRead)
async def update_service(service_id: int, data: ServiceCatalogCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result_obj = await db.execute(select(ServiceCatalog).where(ServiceCatalog.id == service_id))
    service = result_obj.scalar_one_or_none()
    if not service:
        raise HTTPException(404, "Service not found")
    for key, value in data.dict().items():
        setattr(service, key, value)
    await db.commit()
    audit_log(user.id, f"Updated service {service_id}")
    return service

@app.delete("/services/{service_id}")
async def delete_service(service_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result_obj = await db.execute(select(ServiceCatalog).where(ServiceCatalog.id == service_id))
    service = result_obj.scalar_one_or_none()
    if not service:
        raise HTTPException(404, "Service not found")
    await db.delete(service)
    await db.commit()
    audit_log(user.id, f"Deleted service {service_id}")
    return {"ok": True}
