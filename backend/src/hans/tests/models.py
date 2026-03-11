from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hans.core.db import Base


# --- MODELS -----------------------------------------------------------

class TestCatalog(Base):
    __tablename__ = "test_catalog"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[Optional[str]]
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    specimen_type_id: Mapped[int] = mapped_column(ForeignKey("specimen_types.id"))
    # Load specimen type eagerly for admin list rendering.
    specimen_type = relationship("SpecimenType", lazy="joined")
