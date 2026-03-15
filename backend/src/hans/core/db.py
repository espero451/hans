from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from hans.core.settings import settings


# --- Engine -----------------------------------------------------------

# Create a single async engine for the application.
# engine = create_async_engine(settings.database_url, echo=False)
engine = create_async_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
)


# --- Sessions ---------------------------------------------------------

# Session factory used by request-scoped dependencies.
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# Yield a database session per request.
async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session

# async def get_db() -> AsyncSession:
#     async with SessionLocal() as session:
#         async with session.begin():
#             yield session