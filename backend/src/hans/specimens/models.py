from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hans.core.db import Base


# --- MODELS -----------------------------------------------------------

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
