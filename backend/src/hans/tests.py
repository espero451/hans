from datetime import datetime
from typing import Optional, List
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import ForeignKey

from hans.db import Base, get_db
from hans.auth import get_current_user, User
from hans.core import app, audit_log


# ---------------- MODELS ----------------

class TestRead(BaseModel):
    id: int
    name: str
    description: str
    cost: float
    specimen_id: int

    class Config:
        from_attributes = True

class TestCreate(BaseModel):
    name: str
    description: str
    cost: float
    specimen_id: int


# ---------------- SCHEMAS ----------------

class Test(Base):
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    cost: Mapped[float]
    description: Mapped[str]
    specimen_id: Mapped[int] = mapped_column(ForeignKey("specimens.id"))


# ---------------- ROUTES ----------------

@app.get("/tests", response_model=List[TestRead])
async def get_tests(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Test).order_by(Test.name))
    return result.scalars().all()

@app.post("/tests", response_model=TestRead)
async def create_test(data: TestCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    test = Test(**data.dict())
    db.add(test)
    await db.commit()
    audit_log(user.id, f"Created test {test.id}")
    return test

@app.put("/tests/{test_id}", response_model=TestCreate)
async def update_test(test_id: int, data: TestCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result_obj = await db.execute(select(Test).where(Test.id == test_id))
    test = result_obj.scalar_one_or_none()
    if not test:
        raise HTTPException(404, "Test not found")
    for key, value in data.dict().items():
        setattr(test, key, value)
    await db.commit()
    audit_log(user.id, f"Updated test {test_id}")
    return test

@app.delete("/tests/{test_id}")
async def delete_test(test_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result_obj = await db.execute(select(Test).where(Test.id == test_id))
    test = result_obj.scalar_one_or_none()
    if not test:
        raise HTTPException(404, "Test not found")
    await db.delete(test)
    await db.commit()
    audit_log(user.id, f"Deleted test {test_id}")
    return {"ok": True}
