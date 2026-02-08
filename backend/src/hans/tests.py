from typing import Optional, List
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import ForeignKey, String, Numeric

from hans.db import Base, get_db
from hans.auth import get_current_user, User
from hans.core import app, audit_log


# ---------------- MODELS ----------------

class TestCatalogCreate(BaseModel):
    code: str
    description: Optional[str] = None
    price: float
    specimen_type_id: int


class TestCatalogRead(BaseModel):
    id: int
    code: str
    description: Optional[str] = None
    price: float
    specimen_type_id: int

    class Config:
        from_attributes = True


# ---------------- SCHEMAS ----------------

class TestCatalog(Base):
    __tablename__ = "test_catalog"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[Optional[str]]
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    specimen_type_id: Mapped[int] = mapped_column(ForeignKey("specimen_types.id"))


# ---------------- ROUTES ----------------

@app.get("/tests", response_model=List[TestCatalogRead])
async def get_tests(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(TestCatalog).order_by(TestCatalog.code))
    return result.scalars().all()

@app.post("/tests", response_model=TestCatalogRead)
async def create_test(data: TestCatalogCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    test = TestCatalog(**data.dict())
    db.add(test)
    await db.commit()
    audit_log(user.id, f"Created test {test.id}")
    return test

@app.put("/tests/{test_id}", response_model=TestCatalogRead)
async def update_test(test_id: int, data: TestCatalogCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result_obj = await db.execute(select(TestCatalog).where(TestCatalog.id == test_id))
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
    result_obj = await db.execute(select(TestCatalog).where(TestCatalog.id == test_id))
    test = result_obj.scalar_one_or_none()
    if not test:
        raise HTTPException(404, "Test not found")
    await db.delete(test)
    await db.commit()
    audit_log(user.id, f"Deleted test {test_id}")
    return {"ok": True}
