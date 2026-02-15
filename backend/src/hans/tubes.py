from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import String, ForeignKey
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from hans.core.db import Base, get_db
from hans.core.auth import User, require_admin, require_staff_or_admin
from hans.core.core import audit_log


# ---------------- SCHEMAS ----------------

class TubeTypeCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None


class TubeTypeRead(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------- MODELS ----------------

class TubeType(Base):
    __tablename__ = "tube_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)


# ---------------- ROUTES ----------------

router = APIRouter(prefix="/tubes")

@router.get("/", response_model=List[TubeTypeRead])
async def get_tube(db: AsyncSession = Depends(get_db), user: User = Depends(require_staff_or_admin)):
    result = await db.execute(select(TubeType).order_by(TubeType.id))
    return result.scalars().all()

@router.post("/", response_model=TubeTypeRead)
async def create_tube(data: TubeTypeCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    tube_type = TubeType(**data.dict())
    db.add(tube_type)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "TUbe code already exists")
    audit_log(user.id, f"Created tube_type {tube_type.id}")
    return tube_type

@router.put("/{tube_id}", response_model=TubeTypeRead)
async def update_tube(tube_id: int, data: TubeTypeCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    result_obj = await db.execute(select(TubeType).where(TubeType.id == tube_id))
    tube_type = result_obj.scalar_one_or_none()
    if not tube_type:
        raise HTTPException(404, "Tube type not found")
    for key, value in data.dict().items():
        setattr(tube_type, key, value)
    await db.commit()
    audit_log(user.id, f"Updated tube_type {tube_id}")
    return tube_type

@router.delete("/{tube_id}")
async def delete_tube(tube_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    result_obj = await db.execute(select(TubeType).where(TubeType.id == tube_id))
    tube_type = result_obj.scalar_one_or_none()
    if not tube_type:
        raise HTTPException(404, "Tube type not found")
    await db.delete(tube_type)
    await db.commit()
    audit_log(user.id, f"Deleted tube_type {tube_id}")
    return {"ok": True}
