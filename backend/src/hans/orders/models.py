from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hans.core.db import Base


# --- MODELS -----------------------------------------------------------

class OrderUrgency(str, Enum):
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    STAT = "STAT"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    archived: Mapped[bool] = mapped_column(default=False)
    comment: Mapped[Optional[str]]
    urgency = mapped_column(
        SAEnum(OrderUrgency, name="order_urgency"),
        nullable=False,
        default=OrderUrgency.ROUTINE,
        server_default=OrderUrgency.ROUTINE.value,
    )


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
    # Store reference ranges and verification metadata when available.
    reference_range = mapped_column(String, nullable=True)
    abnormal_flag = mapped_column(String, nullable=True)
    verified_by = mapped_column(ForeignKey("users.id"), nullable=True)
    verified_at = mapped_column(DateTime, nullable=True)
    comment = mapped_column(String, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(default=None, nullable=True)
    verified: Mapped[bool] = mapped_column(default=False)


Order.specimens = relationship("Specimen", backref="order", lazy="selectin")
Order.test_runs = relationship("TestRun", backref="order", lazy="selectin")
Order.service_runs = relationship("ServiceRun", backref="order", lazy="selectin")
TestRun.results = relationship("Result", backref="test_run", lazy="selectin")
TestRun.test_catalog = relationship("TestCatalog", lazy="joined")
ServiceRun.service_catalog = relationship("ServiceCatalog", lazy="joined")
# Load related entities for admin list rendering.
Order.patient = relationship("Patient", lazy="joined")
Order.creator = relationship(
    "User",
    lazy="joined",
    foreign_keys=[Order.created_by],
)
Specimen.specimen_type = relationship("SpecimenType", lazy="joined")
TestRun.workstation = relationship("Workstation", lazy="joined")
TestRun.instrument = relationship("Instrument", lazy="joined")
