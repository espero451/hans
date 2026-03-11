from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from hans.core.db import Base


# --- MODELS -----------------------------------------------------------

# Stores credentials and role metadata for authentication and authorization.
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str]
    hashed_password: Mapped[str]
    role: Mapped[str]
    # Stores current refresh token JTI (for rotation validation)
    refresh_jti: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
