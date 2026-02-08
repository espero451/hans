from typing import Optional, List

from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import ForeignKey, String

from hans.core.db import Base, get_db
from hans.core.auth import get_current_user, User
from hans.core.core import app, audit_log


# ---------------- SCHEMAS ----------------

class InstrumentCreate(BaseModel):
    code: str
    name: str
    model: Optional[str] = None
    location: Optional[str] = None


class InstrumentRead(BaseModel):
    id: int
    code: str
    name: str
    model: Optional[str] = None
    location: Optional[str] = None

    class Config:
        from_attributes = True


class WorkstationCreate(BaseModel):
    name: str
    instrument_id: Optional[int] = None


class WorkstationRead(BaseModel):
    id: int
    name: str
    instrument_id: Optional[int] = None

    class Config:
        from_attributes = True


# ---------------- MODELS ----------------

class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[Optional[str]]
    location: Mapped[Optional[str]]


class Workstation(Base):
    __tablename__ = "workstations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    instrument_id: Mapped[Optional[int]] = mapped_column(ForeignKey("instruments.id"))


# ---------------- ROUTES ----------------

@app.get("/instruments", response_model=List[InstrumentRead])
async def get_instruments(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Instrument).order_by(Instrument.name))
    return result.scalars().all()


@app.post("/instruments", response_model=InstrumentRead)
async def create_instrument(data: InstrumentCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    instrument = Instrument(**data.dict())
    db.add(instrument)
    await db.commit()
    audit_log(user.id, f"Created instrument {instrument.id}")
    return instrument


@app.put("/instruments/{instrument_id}", response_model=InstrumentRead)
async def update_instrument(instrument_id: int, data: InstrumentCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result_obj = await db.execute(select(Instrument).where(Instrument.id == instrument_id))
    instrument = result_obj.scalar_one_or_none()
    if not instrument:
        raise HTTPException(404, "Instrument not found")
    for key, value in data.dict().items():
        setattr(instrument, key, value)
    await db.commit()
    audit_log(user.id, f"Updated instrument {instrument_id}")
    return instrument


@app.delete("/instruments/{instrument_id}")
async def delete_instrument(instrument_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result_obj = await db.execute(select(Instrument).where(Instrument.id == instrument_id))
    instrument = result_obj.scalar_one_or_none()
    if not instrument:
        raise HTTPException(404, "Instrument not found")
    await db.delete(instrument)
    await db.commit()
    audit_log(user.id, f"Deleted instrument {instrument_id}")
    return {"ok": True}


@app.get("/workstations", response_model=List[WorkstationRead])
async def get_workstations(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Workstation).order_by(Workstation.name))
    return result.scalars().all()


@app.post("/workstations", response_model=WorkstationRead)
async def create_workstation(data: WorkstationCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    workstation = Workstation(**data.dict())
    db.add(workstation)
    await db.commit()
    audit_log(user.id, f"Created workstation {workstation.id}")
    return workstation


@app.put("/workstations/{workstation_id}", response_model=WorkstationRead)
async def update_workstation(workstation_id: int, data: WorkstationCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result_obj = await db.execute(select(Workstation).where(Workstation.id == workstation_id))
    workstation = result_obj.scalar_one_or_none()
    if not workstation:
        raise HTTPException(404, "Workstation not found")
    for key, value in data.dict().items():
        setattr(workstation, key, value)
    await db.commit()
    audit_log(user.id, f"Updated workstation {workstation_id}")
    return workstation


@app.delete("/workstations/{workstation_id}")
async def delete_workstation(workstation_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result_obj = await db.execute(select(Workstation).where(Workstation.id == workstation_id))
    workstation = result_obj.scalar_one_or_none()
    if not workstation:
        raise HTTPException(404, "Workstation not found")
    await db.delete(workstation)
    await db.commit()
    audit_log(user.id, f"Deleted workstation {workstation_id}")
    return {"ok": True}
