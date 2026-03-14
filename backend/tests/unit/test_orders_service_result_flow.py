from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from fastapi import HTTPException
import pytest

from hans.orders.schemas import ResultCreate, ResultUpdate
from hans.orders.services import create_result, toggle_result_verify, update_result


# --- Helpers ----------------------------------------------------------

def _db_mock() -> AsyncMock:
    # Build an async DB session mock with methods used by services.
    db = AsyncMock()
    db.add = Mock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _patch_result_model(monkeypatch: pytest.MonkeyPatch) -> None:
    # Replace SQLAlchemy result model with a plain class for unit tests.
    class FakeResult:
        def __init__(self, **kwargs):
            self.id = None
            self.value = None
            self.units = None
            self.flags = None
            self.reference_range = None
            self.abnormal_flag = None
            self.verified_by = None
            self.verified_at = None
            self.comment = None
            self.completed_at = None
            self.verified = False
            for key, value in kwargs.items():
                setattr(self, key, value)

    monkeypatch.setattr("hans.orders.services.Result", FakeResult)


def _result_obj(result_id: int, verified: bool = False) -> SimpleNamespace:
    # Create a minimal result entity compatible with ResultRead.
    return SimpleNamespace(
        id=result_id,
        test_run_id=77,
        value=None,
        units=None,
        flags=None,
        reference_range=None,
        abnormal_flag=None,
        verified_by=None,
        verified_at=None,
        comment=None,
        completed_at=None,
        verified=verified,
    )


# --- Result Service Tests ---------------------------------------------

@pytest.mark.asyncio
async def test_create_result_creates_and_returns_result(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_result_model(monkeypatch)
    db = _db_mock()
    monkeypatch.setattr(
        "hans.orders.services.fetch_test_run",
        AsyncMock(return_value=SimpleNamespace(id=77)),
    )

    async def refresh_side_effect(result: SimpleNamespace) -> None:
        # Simulate DB generated id after commit.
        result.id = 500

    db.refresh.side_effect = refresh_side_effect
    payload = ResultCreate(value="5.2", units="mmol/L", comment="manual")

    result = await create_result(77, payload, db)

    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    assert result.id == 500
    assert result.value == "5.2"


@pytest.mark.asyncio
async def test_create_result_raises_404_when_test_run_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hans.orders.services.fetch_test_run", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_ctx:
        await create_result(999, ResultCreate(value="x"), _db_mock())

    assert exc_ctx.value.status_code == 404


@pytest.mark.asyncio
async def test_update_result_updates_only_provided_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    db = _db_mock()
    result_obj = _result_obj(1)
    result_obj.value = "old"
    result_obj.units = "mg/dL"
    monkeypatch.setattr("hans.orders.services.fetch_result", AsyncMock(return_value=result_obj))

    result = await update_result(1, ResultUpdate(value="new"), db)

    assert result_obj.value == "new"
    assert result_obj.units == "mg/dL"
    db.commit.assert_awaited_once()
    assert result.id == 1


@pytest.mark.asyncio
async def test_update_result_raises_404_when_result_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hans.orders.services.fetch_result", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_ctx:
        await update_result(404, ResultUpdate(comment="x"), _db_mock())

    assert exc_ctx.value.status_code == 404


@pytest.mark.asyncio
async def test_toggle_result_verify_sets_verified_fields_when_unverified(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = _db_mock()
    result_obj = _result_obj(10, verified=False)
    monkeypatch.setattr("hans.orders.services.fetch_result", AsyncMock(return_value=result_obj))

    result = await toggle_result_verify(10, user_id=22, db=db)

    assert result_obj.verified is True
    assert result_obj.verified_by == 22
    assert result_obj.verified_at is not None
    assert result.verified is True


@pytest.mark.asyncio
async def test_toggle_result_verify_clears_verified_fields_when_verified(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = _db_mock()
    result_obj = _result_obj(11, verified=True)
    result_obj.verified_by = 22
    result_obj.verified_at = "2026-03-13T10:00:00"
    monkeypatch.setattr("hans.orders.services.fetch_result", AsyncMock(return_value=result_obj))

    result = await toggle_result_verify(11, user_id=22, db=db)

    assert result_obj.verified is False
    assert result_obj.verified_by is None
    assert result_obj.verified_at is None
    assert result.verified is False


@pytest.mark.asyncio
async def test_toggle_result_verify_raises_404_when_result_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("hans.orders.services.fetch_result", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_ctx:
        await toggle_result_verify(404, user_id=1, db=_db_mock())

    assert exc_ctx.value.status_code == 404
