import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Prevent pydantic Settings from failing on extra test-only env var.
_TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if _TEST_DATABASE_URL:
    os.environ["DATABASE_URL"] = _TEST_DATABASE_URL
    os.environ.pop("TEST_DATABASE_URL", None)
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "20"

from hans.core.auth import hash_password, router as auth_router
from hans.core.core import create_app
from hans.core.db import Base, get_db
from hans.dashboard.routers import router as dashboard_router
from hans.instruments import Instrument, Workstation
from hans.owners.routers import router as owners_router
from hans.patients.routers import router as patients_router, species_router
from hans.services.routers import router as services_router
from hans.specimens.routers import router as specimens_router
from hans.tests.routers import router as tests_router
from hans.tubes.routers import router as tubes_router
from hans.users.models import User


# --- Helpers ----------------------------------------------------------

def _build_app() -> FastAPI:
    # Build an API app without runtime workers and admin side effects.
    app = create_app()
    app.include_router(auth_router)
    app.include_router(owners_router)
    app.include_router(patients_router)
    app.include_router(species_router)
    app.include_router(dashboard_router)
    app.include_router(tests_router)
    app.include_router(services_router)
    app.include_router(specimens_router)
    app.include_router(tubes_router)
    return app


# --- Database ---------------------------------------------------------

@pytest.fixture(scope="session")
def test_database_url() -> str:
    # Force explicit test DB to avoid accidental writes to dev/prod DB.
    url = _TEST_DATABASE_URL
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run integration tests")
    return url


@pytest_asyncio.fixture(scope="session")
async def engine(test_database_url: str) -> AsyncGenerator[AsyncEngine, None]:
    # Use one async engine for tests to keep fixture flow deterministic.
    db_engine = create_async_engine(test_database_url, poolclass=NullPool)
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield db_engine
    await db_engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    # Share session factory across test fixtures and app dependency override.
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def clean_database(session_factory: async_sessionmaker[AsyncSession]) -> None:
    # Clear all tables in FK-safe order before each test.
    async with session_factory() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


# --- App And Auth -----------------------------------------------------

@pytest_asyncio.fixture()
async def app(
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> FastAPI:
    # Route all app DB calls through the shared test session factory.
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    monkeypatch.setattr("hans.owners.routers.audit_log", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("hans.patients.routers.audit_log", lambda *_args, **_kwargs: None)

    app_instance = _build_app()
    app_instance.dependency_overrides[get_db] = _override_get_db
    return app_instance


@pytest_asyncio.fixture()
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    # Drive the ASGI app in the same event loop as async fixtures/tests.
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


@pytest_asyncio.fixture()
async def admin_user(session_factory: async_sessionmaker[AsyncSession]) -> User:
    # Create one admin user to authenticate protected endpoint calls.
    async with session_factory() as session:
        user = User(
            username="admin",
            email="admin@example.com",
            role="admin",
            hashed_password=hash_password("adminpass"),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture()
async def auth_headers(client: AsyncClient, admin_user: User) -> dict[str, str]:
    # Use real login flow to produce Authorization header for tests.
    response = await client.post(
        "/auth/token",
        data={"username": admin_user.username, "password": "adminpass"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
