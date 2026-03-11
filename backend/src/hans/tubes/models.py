from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from hans.core.db import Base


# --- MODELS -----------------------------------------------------------

class TubeType(Base):
    __tablename__ = "tube_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
