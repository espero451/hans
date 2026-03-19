import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import delete
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
from hans.instruments import Instrument
from hans.owners.models import Owner
from hans.owners.routers import router as owners_router
from hans.patients.models import Patient, Species
from hans.patients.routers import router as patients_router, species_router
from hans.services.routers import router as services_router
from hans.specimens.models import SpecimenType
from hans.specimens.routers import router as specimens_router
from hans.tests.routers import router as tests_router
from hans.tubes.models import TubeType
from hans.tubes.routers import router as tubes_router
from hans.users.models import User


# --- Helpers ----------------------------------------------------------

def _run(coro: Any) -> Any:
    # Execute async setup/teardown from sync pytest fixtures.
    return asyncio.run(coro)


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


@pytest.fixture(scope="session")
def setup_engine(test_database_url: str) -> Generator[AsyncEngine, None, None]:
    # Keep setup operations on dedicated one-shot DB connections.
    engine = create_async_engine(test_database_url, poolclass=NullPool)

    async def _prepare_schema() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    _run(_prepare_schema())
    yield engine

    async def _dispose() -> None:
        await engine.dispose()

    _run(_dispose())


@pytest.fixture(scope="session")
def setup_session_factory(
    setup_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    # Share a setup session factory for data seed/cleanup steps.
    return async_sessionmaker(setup_engine, expire_on_commit=False)


@pytest.fixture(autouse=True)
def clean_database(setup_session_factory: async_sessionmaker[AsyncSession]) -> None:
    # Keep each test isolated by clearing mutable tables.
    async def _clean() -> None:
        async with setup_session_factory() as session:
            await session.execute(delete(Patient))
            await session.execute(delete(Owner))
            await session.execute(delete(User))
            await session.execute(delete(Species))
            await session.execute(delete(SpecimenType))
            await session.execute(delete(TubeType))
            await session.execute(delete(Instrument))
            await session.commit()

    _run(_clean())


# --- App And Auth -----------------------------------------------------

@pytest.fixture()
def app(
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[FastAPI, None, None]:
    # Use a separate app engine to avoid sharing asyncpg loop-bound state.
    app_engine = create_async_engine(test_database_url, poolclass=NullPool)
    app_session_factory = async_sessionmaker(app_engine, expire_on_commit=False)

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with app_session_factory() as session:
            yield session

    monkeypatch.setattr("hans.owners.routers.audit_log", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("hans.patients.routers.audit_log", lambda *_args, **_kwargs: None)

    app_instance = _build_app()
    app_instance.dependency_overrides[get_db] = _override_get_db
    yield app_instance

    async def _dispose() -> None:
        await app_engine.dispose()

    _run(_dispose())


@pytest.fixture()
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers(
    client: TestClient,
    setup_session_factory: async_sessionmaker[AsyncSession],
    clean_database: None,
) -> dict[str, str]:
    # Seed admin user and get auth token from the real login endpoint.
    async def _seed_user() -> None:
        async with setup_session_factory() as session:
            session.add(
                User(
                    username="admin",
                    email="admin@example.com",
                    role="admin",
                    hashed_password=hash_password("adminpass"),
                )
            )
            await session.commit()

    _run(_seed_user())

    response = client.post(
        "/auth/token",
        data={"username": "admin", "password": "adminpass"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
