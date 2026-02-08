from typing import Optional, List
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import String, ForeignKey

from hans.core.db import Base, get_db
from hans.core.auth import get_current_user, User
from hans.core.core import app, audit_log


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

class SpecimenType(Base):
    __tablename__ = "specimen_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tube_type_id: Mapped[int] = mapped_column(ForeignKey("tube_types.id"))
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class TubeType(Base):
    __tablename__ = "tube_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)


# ---------------- ROUTES ----------------

@app.get("/specimens", response_model=List[SpecimenTypeRead])
async def get_specimens(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(SpecimenType).order_by(SpecimenType.id))
    return result.scalars().all()

@app.post("/specimens", response_model=SpecimenTypeRead)
async def create_specimen(data: SpecimenTypeCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    specimen_type = SpecimenType(**data.dict())
    db.add(specimen_type)
    await db.commit()
    audit_log(user.id, f"Created specimen_type {specimen_type.id}")
    return specimen_type

@app.put("/specimens/{specimen_id}", response_model=SpecimenTypeRead)
async def update_specimen(specimen_id: int, data: SpecimenTypeCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result_obj = await db.execute(select(SpecimenType).where(SpecimenType.id == specimen_id))
    specimen_type = result_obj.scalar_one_or_none()
    if not specimen_type:
        raise HTTPException(404, "Specimen type not found")
    for key, value in data.dict().items():
        setattr(specimen_type, key, value)
    await db.commit()
    audit_log(user.id, f"Updated specimen_type {specimen_id}")
    return specimen_type

@app.delete("/specimens/{specimen_id}")
async def delete_specimen(specimen_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result_obj = await db.execute(select(SpecimenType).where(SpecimenType.id == specimen_id))
    specimen_type = result_obj.scalar_one_or_none()
    if not specimen_type:
        raise HTTPException(404, "Specimen type not found")
    await db.delete(specimen_type)
    await db.commit()
    audit_log(user.id, f"Deleted specimen_type {specimen_id}")
    return {"ok": True}



@app.get("/tubes", response_model=List[TubeTypeRead])
async def get_tube(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(TubeType).order_by(TubeType.id))
    return result.scalars().all()

@app.post("/tubes", response_model=TubeTypeRead)
async def create_tube(data: TubeTypeCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    tube_type = TubeType(**data.dict())
    db.add(tube_type)
    await db.commit()
    audit_log(user.id, f"Created tube_type {tube_type.id}")
    return tube_type

@app.put("/tubes/{tube_id}", response_model=TubeTypeRead)
async def update_tube(tube_id: int, data: TubeTypeCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result_obj = await db.execute(select(TubeType).where(TubeType.id == tube_id))
    tube_type = result_obj.scalar_one_or_none()
    if not tube_type:
        raise HTTPException(404, "Tube type not found")
    for key, value in data.dict().items():
        setattr(tube_type, key, value)
    await db.commit()
    audit_log(user.id, f"Updated tube_type {tube_id}")
    return tube_type

@app.delete("/tubes/{tube_id}")
async def delete_tube(tube_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result_obj = await db.execute(select(TubeType).where(TubeType.id == tube_id))
    tube_type = result_obj.scalar_one_or_none()
    if not tube_type:
        raise HTTPException(404, "Tube type not found")
    await db.delete(tube_type)
    await db.commit()
    audit_log(user.id, f"Deleted tube_type {tube_id}")
    return {"ok": True}