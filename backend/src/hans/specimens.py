from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import String, ForeignKey
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from hans.core.db import Base, get_db
from hans.core.auth import User, require_admin, require_staff_or_admin
from hans.core.core import audit_log


# ---------------- SCHEMAS ----------------

class SpecimenTypeCreate(BaseModel):
    code: str
    name: str
    type: str
    tube_type_id: int
    description: Optional[str] = None


class SpecimenTypeRead(BaseModel):
    id: int
    code: str
    name: str
    type: Optional[str] = None
    tube_type_id: int
    description: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------- MODELS ----------------

class SpecimenType(Base):
    __tablename__ = "specimen_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tube_type_id: Mapped[int] = mapped_column(ForeignKey("tube_types.id"))
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Load tube type details for admin list rendering.
    tube_type = relationship("TubeType", lazy="joined")

    # Provide readable labels in admin dropdowns.
    def __str__(self) -> str:
        return self.code


# ---------------- ROUTES ----------------

router = APIRouter(prefix="/specimens")

# @router.get("/", response_model=List[SpecimenTypeRead])
# async def get_specimens(db: AsyncSession = Depends(get_db), user: User = Depends(require_staff_or_admin)):
#     result = await db.execute(select(SpecimenType).order_by(SpecimenType.id))
#     return result.scalars().all()

