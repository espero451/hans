from datetime import date, datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hans.core.db import Base


# --- MODELS -----------------------------------------------------------

class Species(Base):
    __tablename__ = "species"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    latin_name: Mapped[Optional[str]] = mapped_column(String(128))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    species: Mapped[str]
    species_id: Mapped[int] = mapped_column(ForeignKey("species.id"))
    breed: Mapped[Optional[str]]
    sex: Mapped[str] = mapped_column(String(16), nullable=False)
    weight: Mapped[Optional[float]] = mapped_column(Float)
    microchip_number: Mapped[Optional[str]] = mapped_column(String(64))
    comment: Mapped[Optional[str]]
    birth_date: Mapped[Optional[date]] = mapped_column(Date)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id"))
    owner = relationship("Owner", lazy="joined")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
