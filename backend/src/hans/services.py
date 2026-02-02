from datetime import datetime
from typing import Optional, List
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from hans.db import Base, get_db
from hans.auth import get_current_user, User
from hans.core import app, audit_log



# ---------------- MODELS ----------------

class ServiceRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    class Config:
        from_attributes = True


class ServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: Optional[float] = None


# ---------------- SCHEMAS ----------------

class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    price: Mapped[Optional[float]]
    description: Mapped[Optional[str]]


# ---------------- ROUTES ----------------

@app.get("/services", response_model=List[ServiceRead])
async def get_services(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Service).order_by(Service.name))
    return result.scalars().all()

@app.post("/services", response_model=ServiceCreate)
async def create_service(data: ServiceCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    service = Service(**data.dict())
    db.add(service)
    await db.commit()
    audit_log(user.id, f"Created service {service.id}")
    return service

@app.put("/services/{service_id}", response_model=ServiceCreate)
async def update_service(service_id: int, data: ServiceCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result_obj = await db.execute(select(Service).where(Service.id == service_id))
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
    result_obj = await db.execute(select(Service).where(Service.id == service_id))
    service = result_obj.scalar_one_or_none()
    if not service:
        raise HTTPException(404, "Service not found")
    await db.delete(service)
    await db.commit()
    audit_log(user.id, f"Deleted service {service_id}")
    return {"ok": True}
