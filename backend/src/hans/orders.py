from datetime import datetime
from typing import List, Optional
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import ForeignKey, Table, Column, Integer, insert, func, select, String

from hans.db import Base, get_db
from hans.auth import get_current_user, User
from hans.core import app, audit_log

from hans.patients import Patient
from hans.tests import Test
from hans.services import Service
from hans.specimens import Specimen


# ---------------- SCHEMAS ----------------

class ResultCreate(BaseModel):
    specimen_id: int
    test_id: int
    order_id: int
    value: str
    units: str
    flags: str  # normal / abnormal / custom


class ResultRead(BaseModel):
    id: int
    test_id: int
    specimen_id: int
    value: Optional[str] = None
    units: Optional[str] = None
    flags: Optional[str] = None
    specimen_status: Optional[str] = "N"
    verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class OrderRead(BaseModel):
    id: int
    patient_id: int
    comment: Optional[str] = None
    test_ids: List[int] = []
    service_ids: List[int] = []
    created_at: datetime
    results: List[ResultRead] = [] # new

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    patient_id: int
    test_ids: List[int] = []
    service_ids: List[int] = []
    comment: Optional[str] = None


# ---------------- MODELS ----------------

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    comment: Mapped[Optional[str]]

class Result(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"))
    specimen_id: Mapped[int] = mapped_column(ForeignKey("specimens.id"))
    value: Mapped[str]
    units: Mapped[str]
    flags: Mapped[str]
    specimen_status: Mapped[str] = mapped_column(String(1), nullable=False)  # N / C / R
    collected_at: Mapped[datetime] = mapped_column(default=None, nullable=True)
    verified: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


# --- Many-to-many association tables ---

order_tests = Table(
    "order_tests", Base.metadata,
    Column("order_id", Integer, ForeignKey("orders.id"), primary_key=True),
    Column("test_id", Integer, ForeignKey("tests.id"), primary_key=True)
)

order_services = Table(
    "order_services", Base.metadata,
    Column("order_id", Integer, ForeignKey("orders.id"), primary_key=True),
    Column("service_id", Integer, ForeignKey("services.id"), primary_key=True)
)

Order.tests = relationship("Test", secondary=order_tests, backref="orders", lazy="joined")
Order.services = relationship("Service", secondary=order_services, backref="orders", lazy="joined")
Order.results = relationship("Result", backref="order", lazy="selectin")


# ---------------- ROUTES ----------------

@app.post("/orders", response_model=OrderRead)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    order = Order(
        patient_id=data.patient_id,
        created_by=user.id,
        comment=data.comment
    )
    db.add(order)
    await db.flush()  # Obtain order.id for association

    test_ids_out: List[int] = []

    ### <

    if data.test_ids:
        test_ids = list(set(data.test_ids))  # protection from dubles

    tests_result = await db.execute(
        select(Test).where(Test.id.in_(test_ids))
    )
    tests = tests_result.scalars().all()

    if len(tests) != len(test_ids):
        raise HTTPException(400, "One or more tests not found")

    for test in tests:
        # realtion order <-> test (ONE-TIME)
        await db.execute(
            insert(order_tests).values(
                order_id=order.id,
                test_id=test.id
            )
        )

        # Write to TABLE results
        db.add(
            Result(
                order_id=order.id,
                test_id=test.id,
                specimen_id=test.specimen_id,
                value="",
                units="",
                flags="",
                specimen_status="N",
                verified=False
            )
        )
    else:
        test_ids_out = []
    
    test_ids_out = test_ids

    ### >

    service_ids_out: List[int] = []
    if data.service_ids:
        # Validation: check if all service_ids exist
        count_result = await db.execute(
            select(func.count()).select_from(Service).where(Service.id.in_(data.service_ids))
        )
        if count_result.scalar() != len(data.service_ids):
            raise HTTPException(status_code=400, detail="Один или несколько service_ids не существуют")

        # Inserts to order_services
        for service_id in data.service_ids:
            await db.execute(
                insert(order_services).values(order_id=order.id, service_id=service_id)
            )
        service_ids_out = data.service_ids

    await db.commit()
    await db.refresh(order)  # Refresh scalar fields if needed

    audit_log(user.id, f"Created order {order.id} for patient {data.patient_id}")

    return OrderRead(
        id=order.id,
        patient_id=order.patient_id,
        comment=order.comment,
        test_ids=test_ids_out,
        service_ids=service_ids_out,
        created_at=order.created_at
    )


@app.get("/patients/{patient_id}/orders", response_model=List[OrderRead])
async def get_patient_orders(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Order)
        .where(Order.patient_id == patient_id)
        .options(
            selectinload(Order.tests),
            selectinload(Order.services),
            selectinload(Order.results)  # NEW
        )
    )
    orders = result.scalars().all()

    orders_out = []
    for o in orders:
        orders_out.append(
            OrderRead(
                id=o.id,
                patient_id=o.patient_id,
                comment=o.comment,
                test_ids=[t.id for t in o.tests],
                service_ids=[s.id for s in o.services],
                created_at=o.created_at,
                results=[           # new
                    ResultRead(
                        id=r.id,
                        test_id=r.test_id,
                        specimen_id=r.specimen_id,
                        value=r.value,
                        units=r.units,
                        flags=r.flags,
                        specimen_status=r.specimen_status,
                        verified=r.verified,
                        created_at=r.created_at
                    )
                    for r in o.results
                ]
            )
        )
    return orders_out
