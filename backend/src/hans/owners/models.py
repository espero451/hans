from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from hans.core.db import Base


# --- MODELS -----------------------------------------------------------

class Owner(Base):
    __tablename__ = "owners"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    email: Mapped[Optional[str]]
    phone: Mapped[Optional[str]]
    comment: Mapped[Optional[str]]
