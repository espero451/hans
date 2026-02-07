from datetime import datetime
from typing import List, Optional, Dict

from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import ForeignKey, select, text, String, Numeric, Enum as SAEnum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from hans.auth import User, get_current_user
from hans.core import app, audit_log
from hans.db import Base, get_db
from hans.tests import TestCatalog
from hans.services import ServiceCatalog


# ---------------- SCHEMAS ----------------

class ResultRead(BaseModel):
    id: int
    test_run_id: int
    value: Optional[str] = None
    units: Optional[str] = None
    flags: Optional[str] = None
    completed_at: Optional[datetime] = None
    verified: bool

    class Config:
        from_attributes = True


class SpecimenRead(BaseModel):
    specimen_id: str
    order_id: int
    specimen_type_id: int
    status: str
    collected_at: Optional[datetime] = None
    received_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestRunRead(BaseModel):
    id: int
    order_id: int
    test_catalog_id: int
    specimen_id: str
    workstation_id: Optional[int] = None
    instrument_id: Optional[int] = None
    status: str
    price: float
    results: List[ResultRead] = []

    class Config:
        from_attributes = True


class ServiceRunRead(BaseModel):
    id: int
    order_id: int
    service_catalog_id: int
    status: str
    price: float
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderRead(BaseModel):
    id: int
    patient_id: int
    created_by: Optional[int] = None
    created_at: datetime
    archived: bool
    comment: Optional[str] = None
    specimens: List[SpecimenRead] = []
    test_runs: List[TestRunRead] = []
    service_runs: List[ServiceRunRead] = []

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    patient_id: int
    test_catalog_ids: List[int] = []
    service_catalog_ids: List[int] = []
    comment: Optional[str] = None


# ---------------- MODELS ----------------

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    archived: Mapped[bool] = mapped_column(default=False)
    comment: Mapped[Optional[str]]


class Specimen(Base):
    __tablename__ = "specimens"

    specimen_id: Mapped[str] = mapped_column(String, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    specimen_type_id: Mapped[int] = mapped_column(ForeignKey("specimen_types.id"))
    status: Mapped[str] = mapped_column(
        SAEnum(
            "NEW",
            "COLLECTED",
            "RECEIVED",
            "CANCELED",
            name="specimen_status",
        ),
        default="NEW",
    )
    collected_at: Mapped[Optional[datetime]] = mapped_column(default=None, nullable=True)
    received_at: Mapped[Optional[datetime]] = mapped_column(default=None, nullable=True)


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    test_catalog_id: Mapped[int] = mapped_column(ForeignKey("test_catalog.id"))
    specimen_id: Mapped[str] = mapped_column(ForeignKey("specimens.specimen_id"))
    workstation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workstations.id"), nullable=True)
    instrument_id: Mapped[Optional[int]] = mapped_column(ForeignKey("instruments.id"), nullable=True)
    status: Mapped[str] = mapped_column(
        SAEnum(
            "NEW",
            "SENT",
            "RECEIVED",
            name="test_run_status",
        ),
        default="NEW",
    )
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)


class ServiceRun(Base):
    __tablename__ = "service_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    service_catalog_id: Mapped[int] = mapped_column(ForeignKey("service_catalog.id"))
    status: Mapped[str] = mapped_column(
        SAEnum(
            "NEW",
            "COMPLETED",
            "CANCELED",
            name="service_run_status",
        ),
        default="NEW",
    )
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(default=None, nullable=True)


class Result(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_run_id: Mapped[int] = mapped_column(ForeignKey("test_runs.id"))
    value: Mapped[Optional[str]]
    units: Mapped[Optional[str]]
    flags: Mapped[Optional[str]]
    completed_at: Mapped[Optional[datetime]] = mapped_column(default=None, nullable=True)
    verified: Mapped[bool] = mapped_column(default=False)


Order.specimens = relationship("Specimen", backref="order", lazy="selectin")
Order.test_runs = relationship("TestRun", backref="order", lazy="selectin")
Order.service_runs = relationship("ServiceRun", backref="order", lazy="selectin")
TestRun.results = relationship("Result", backref="test_run", lazy="selectin")
TestRun.test_catalog = relationship("TestCatalog", lazy="joined")
ServiceRun.service_catalog = relationship("ServiceCatalog", lazy="joined")


# ---------------- ROUTES ----------------

@app.post("/orders", response_model=OrderRead)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = Order(
        patient_id=data.patient_id,
        created_by=user.id,
        comment=data.comment,
    )
    db.add(order)
    await db.flush()

    test_catalogs: List[TestCatalog] = []
    if data.test_catalog_ids:
        test_ids = list(set(data.test_catalog_ids))
        tests_result = await db.execute(
            select(TestCatalog).where(TestCatalog.id.in_(test_ids))
        )
        test_catalogs = tests_result.scalars().all()
        if len(test_catalogs) != len(test_ids):
            raise HTTPException(400, "One or more tests not found")
    else:
        test_ids = []

    service_catalogs: List[ServiceCatalog] = []
    if data.service_catalog_ids:
        services_result = await db.execute(
            select(ServiceCatalog).where(ServiceCatalog.id.in_(data.service_catalog_ids))
        )
        service_catalogs = services_result.scalars().all()
        if len(service_catalogs) != len(data.service_catalog_ids):
            raise HTTPException(400, "One or more services not found")

    specimen_map: Dict[int, str] = {}
    for test in test_catalogs:
        if test.specimen_type_id in specimen_map:
            continue
        barcode = await _next_barcode(db)
        specimen = Specimen(
            specimen_id=barcode,
            order_id=order.id,
            specimen_type_id=test.specimen_type_id,
            status="NEW",
        )
        db.add(specimen)
        specimen_map[test.specimen_type_id] = barcode

    for test in test_catalogs:
        specimen_id = specimen_map[test.specimen_type_id]
        db.add(
            TestRun(
                order_id=order.id,
                test_catalog_id=test.id,
                specimen_id=specimen_id,
                status="NEW",
                price=float(test.price),
            )
        )

    for service in service_catalogs:
        db.add(
            ServiceRun(
                order_id=order.id,
                service_catalog_id=service.id,
                status="NEW",
                price=float(service.price),
            )
        )

    await db.commit()

    audit_log(user.id, f"Created order {order.id} for patient {data.patient_id}")

    return await _load_order(order.id, db)


@app.get("/orders/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = await _fetch_order(order_id, db)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderRead.model_validate(order)


@app.get("/patients/{patient_id}/orders", response_model=List[OrderRead])
async def get_patient_orders(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Order)
        .where(Order.patient_id == patient_id)
        .options(
            selectinload(Order.specimens),
            selectinload(Order.test_runs).selectinload(TestRun.results),
            selectinload(Order.service_runs),
        )
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().unique().all()
    return [OrderRead.model_validate(order) for order in orders]


@app.get("/orders/barcode/{barcode}", response_model=SpecimenRead)
async def get_order_by_barcode(
    barcode: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Specimen).where(Specimen.specimen_id == barcode)
    )
    specimen = result.scalar_one_or_none()
    if not specimen:
        raise HTTPException(status_code=404, detail="Specimen not found")
    return SpecimenRead.model_validate(specimen)


# Mark specimen as collected
@app.patch("/orders/barcode/{specimen_id}/collect", response_model=SpecimenRead)
async def collect_specimen(
    specimen_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Specimen).where(Specimen.specimen_id == specimen_id)
    )
    specimen = result.scalar_one_or_none()
    if not specimen:
        raise HTTPException(404, "Specimen not found")

    if specimen.status == "CANCELED":
        raise HTTPException(400, "Specimen is canceled")

    if specimen.status in ("COLLECTED", "RECEIVED"):
        return SpecimenRead.model_validate(specimen)

    specimen.status = "COLLECTED"
    specimen.collected_at = datetime.utcnow()
    await db.commit()
    await db.refresh(specimen)

    audit_log(user.id, f"Specimen collected {specimen_id}")
    return SpecimenRead.model_validate(specimen)


async def _fetch_order(order_id: int, db: AsyncSession) -> Optional[Order]:
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.specimens),
            selectinload(Order.test_runs).selectinload(TestRun.results),
            selectinload(Order.service_runs),
        )
    )
    return result.scalar_one_or_none()


async def _load_order(order_id: int, db: AsyncSession) -> OrderRead:
    order = await _fetch_order(order_id, db)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderRead.model_validate(order)


async def _next_barcode(db: AsyncSession) -> str:
    result = await db.execute(
        text("select lpad(nextval('specimen_barcode_seq')::text, 12, '0')")
    )
    return result.scalar_one()
