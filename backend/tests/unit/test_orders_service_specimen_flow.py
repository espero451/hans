from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import HTTPException
import pytest

from hans.orders.services import collect_specimen, receive_specimen


# --- Helpers ----------------------------------------------------------

@pytest.fixture
def db() -> AsyncMock:
    # Provide a reusable async DB session mock for specimen flow tests.
    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    return mock_db


@pytest.fixture
def mock_fetch_specimen(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    # Patch repository access once and override return values per test.
    mock = AsyncMock()
    monkeypatch.setattr("hans.orders.services.fetch_specimen", mock)
    return mock


def _specimen(status: str) -> SimpleNamespace:
    # Create a minimal specimen object used by transition tests.
    return SimpleNamespace(
        specimen_id="000000000123",
        order_id=1,
        specimen_type_id=1,
        status=status,
        collected_at=None,
        received_at=None,
    )


# --- Specimen Service Tests -------------------------------------------

@pytest.mark.asyncio
async def test_collect_specimen_sets_status_and_collected_at_for_new(
    db: AsyncMock,
    mock_fetch_specimen: AsyncMock,
) -> None:
    specimen = _specimen("NEW")
    mock_fetch_specimen.return_value = specimen

    result = await collect_specimen(specimen.specimen_id, db)

    assert specimen.status == "COLLECTED"
    assert isinstance(specimen.collected_at, datetime)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(specimen)
    assert result.status == "COLLECTED"


@pytest.mark.asyncio
async def test_collect_specimen_returns_as_is_for_collected(
    db: AsyncMock,
    mock_fetch_specimen: AsyncMock,
) -> None:
    specimen = _specimen("COLLECTED")
    mock_fetch_specimen.return_value = specimen

    result = await collect_specimen(specimen.specimen_id, db)

    assert result.status == "COLLECTED"
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_collect_specimen_returns_as_is_for_received(
    db: AsyncMock,
    mock_fetch_specimen: AsyncMock,
) -> None:
    specimen = _specimen("RECEIVED")
    mock_fetch_specimen.return_value = specimen

    result = await collect_specimen(specimen.specimen_id, db)

    assert result.status == "RECEIVED"
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_collect_specimen_raises_400_for_canceled(
    db: AsyncMock,
    mock_fetch_specimen: AsyncMock,
) -> None:
    specimen = _specimen("CANCELED")
    mock_fetch_specimen.return_value = specimen

    with pytest.raises(HTTPException) as exc_ctx:
        await collect_specimen(specimen.specimen_id, db)

    assert exc_ctx.value.status_code == 400


@pytest.mark.asyncio
async def test_collect_specimen_raises_404_when_missing(
    db: AsyncMock,
    mock_fetch_specimen: AsyncMock,
) -> None:
    mock_fetch_specimen.return_value = None

    with pytest.raises(HTTPException) as exc_ctx:
        await collect_specimen("missing", db)

    assert exc_ctx.value.status_code == 404


@pytest.mark.asyncio
async def test_receive_specimen_sets_status_and_received_at_for_collected(
    db: AsyncMock,
    mock_fetch_specimen: AsyncMock,
) -> None:
    specimen = _specimen("COLLECTED")
    mock_fetch_specimen.return_value = specimen

    result = await receive_specimen(specimen.specimen_id, db)

    assert specimen.status == "RECEIVED"
    assert isinstance(specimen.received_at, datetime)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(specimen)
    assert result.status == "RECEIVED"


@pytest.mark.asyncio
async def test_receive_specimen_returns_as_is_for_received(
    db: AsyncMock,
    mock_fetch_specimen: AsyncMock,
) -> None:
    specimen = _specimen("RECEIVED")
    mock_fetch_specimen.return_value = specimen

    result = await receive_specimen(specimen.specimen_id, db)

    assert result.status == "RECEIVED"
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_receive_specimen_raises_400_for_new_specimen(
    db: AsyncMock,
    mock_fetch_specimen: AsyncMock,
) -> None:
    specimen = _specimen("NEW")
    mock_fetch_specimen.return_value = specimen

    with pytest.raises(HTTPException) as exc_ctx:
        await receive_specimen(specimen.specimen_id, db)

    assert exc_ctx.value.status_code == 400


@pytest.mark.asyncio
async def test_receive_specimen_raises_400_for_canceled(
    db: AsyncMock,
    mock_fetch_specimen: AsyncMock,
) -> None:
    specimen = _specimen("CANCELED")
    mock_fetch_specimen.return_value = specimen

    with pytest.raises(HTTPException) as exc_ctx:
        await receive_specimen(specimen.specimen_id, db)

    assert exc_ctx.value.status_code == 400


@pytest.mark.asyncio
async def test_receive_specimen_raises_404_when_missing(
    db: AsyncMock,
    mock_fetch_specimen: AsyncMock,
) -> None:
    mock_fetch_specimen.return_value = None

    with pytest.raises(HTTPException) as exc_ctx:
        await receive_specimen("missing", db)

    assert exc_ctx.value.status_code == 404
