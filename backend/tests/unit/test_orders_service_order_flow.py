from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from fastapi import HTTPException
import pytest

from hans.orders.models import OrderUrgency
from hans.orders.schemas import OrderCreate, OrderUpdate
from hans.orders.services import (
    create_order,
    get_patient_orders,
    load_order,
    toggle_order_archive,
    update_order,
)


# --- Helpers ----------------------------------------------------------

def _db_mock() -> AsyncMock:
    # Build an async DB session mock with methods used by services.
    db = AsyncMock()
    db.add = Mock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _patch_order_models(monkeypatch: pytest.MonkeyPatch) -> None:
    # Replace SQLAlchemy models with plain classes for isolated unit tests.
    class _FakeEntity:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class FakeOrder(_FakeEntity):
        pass

    class FakeSpecimen(_FakeEntity):
        pass

    class FakeTestRun(_FakeEntity):
        pass

    class FakeServiceRun(_FakeEntity):
        pass

    monkeypatch.setattr("hans.orders.services.Order", FakeOrder)
    monkeypatch.setattr("hans.orders.services.Specimen", FakeSpecimen)
    monkeypatch.setattr("hans.orders.services.TestRun", FakeTestRun)
    monkeypatch.setattr("hans.orders.services.ServiceRun", FakeServiceRun)


# --- Order Service Tests ----------------------------------------------

@pytest.mark.asyncio
async def test_load_order_returns_order_read_when_order_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    # Return a rich order shape that can be validated by OrderRead.
    order = SimpleNamespace(
        id=1,
        patient_id=10,
        created_by=2,
        created_at="2026-03-13T12:00:00",
        archived=False,
        urgency=OrderUrgency.ROUTINE,
        comment="ok",
        specimens=[],
        test_runs=[],
        service_runs=[],
    )
    monkeypatch.setattr("hans.orders.services.fetch_order", AsyncMock(return_value=order))

    result = await load_order(1, _db_mock())

    assert result.id == 1
    assert result.patient_id == 10


@pytest.mark.asyncio
async def test_load_order_raises_404_when_order_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hans.orders.services.fetch_order", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_ctx:
        await load_order(404, _db_mock())

    assert exc_ctx.value.status_code == 404


@pytest.mark.asyncio
async def test_create_order_creates_order_with_default_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    # Build a no-tests/no-services payload to validate base creation flow.
    _patch_order_models(monkeypatch)
    data = OrderCreate(patient_id=101)
    db = _db_mock()

    async def flush_side_effect() -> None:
        # Simulate generated PK after flush.
        for added in db.add.call_args_list:
            obj = added.args[0]
            if hasattr(obj, "patient_id") and not getattr(obj, "id", None):
                obj.id = 777

    db.flush.side_effect = flush_side_effect
    monkeypatch.setattr("hans.orders.services.fetch_test_catalogs", AsyncMock(return_value=[]))
    monkeypatch.setattr("hans.orders.services.fetch_service_catalogs", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        "hans.orders.services.load_order",
        AsyncMock(
            return_value=SimpleNamespace(
                id=777,
                patient_id=101,
                created_by=9,
                created_at="2026-03-13T12:00:00",
                archived=False,
                urgency=OrderUrgency.ROUTINE,
                comment=None,
                specimens=[],
                test_runs=[],
                service_runs=[],
            )
        ),
    )

    result = await create_order(data, db, user_id=9)

    db.flush.assert_awaited_once()
    db.commit.assert_awaited_once()
    assert result.id == 777


@pytest.mark.asyncio
async def test_create_order_deduplicates_test_catalog_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    # Duplicate IDs should be collapsed before catalog fetch.
    _patch_order_models(monkeypatch)
    data = OrderCreate(patient_id=1, test_catalog_ids=[1, 1, 2])
    db = _db_mock()

    async def flush_side_effect() -> None:
        for added in db.add.call_args_list:
            obj = added.args[0]
            if hasattr(obj, "patient_id") and not getattr(obj, "id", None):
                obj.id = 10

    db.flush.side_effect = flush_side_effect
    fetch_tests = AsyncMock(
        return_value=[
            SimpleNamespace(id=1, specimen_type_id=7, price=10.0),
            SimpleNamespace(id=2, specimen_type_id=8, price=20.0),
        ]
    )
    monkeypatch.setattr("hans.orders.services.fetch_test_catalogs", fetch_tests)
    monkeypatch.setattr("hans.orders.services.fetch_service_catalogs", AsyncMock(return_value=[]))
    monkeypatch.setattr("hans.orders.services.next_barcode", AsyncMock(side_effect=["B1", "B2"]))
    monkeypatch.setattr(
        "hans.orders.services.load_order",
        AsyncMock(
            return_value=SimpleNamespace(
                id=10,
                patient_id=1,
                created_by=4,
                created_at="2026-03-13T12:00:00",
                archived=False,
                urgency=OrderUrgency.ROUTINE,
                comment=None,
                specimens=[],
                test_runs=[],
                service_runs=[],
            )
        ),
    )

    await create_order(data, db, user_id=4)

    fetched_ids = set(fetch_tests.await_args.args[0])
    assert fetched_ids == {1, 2}


@pytest.mark.asyncio
async def test_create_order_raises_400_when_some_test_catalogs_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_order_models(monkeypatch)
    data = OrderCreate(patient_id=1, test_catalog_ids=[10, 11])
    db = _db_mock()

    async def flush_side_effect() -> None:
        for added in db.add.call_args_list:
            obj = added.args[0]
            if hasattr(obj, "patient_id") and not getattr(obj, "id", None):
                obj.id = 5

    db.flush.side_effect = flush_side_effect
    monkeypatch.setattr(
        "hans.orders.services.fetch_test_catalogs",
        AsyncMock(return_value=[SimpleNamespace(id=10, specimen_type_id=1, price=1)]),
    )
    monkeypatch.setattr("hans.orders.services.fetch_service_catalogs", AsyncMock(return_value=[]))

    with pytest.raises(HTTPException) as exc_ctx:
        await create_order(data, db, user_id=1)

    assert exc_ctx.value.status_code == 400
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_order_raises_400_when_some_service_catalogs_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_order_models(monkeypatch)
    data = OrderCreate(patient_id=1, service_catalog_ids=[20, 21])
    db = _db_mock()

    async def flush_side_effect() -> None:
        for added in db.add.call_args_list:
            obj = added.args[0]
            if hasattr(obj, "patient_id") and not getattr(obj, "id", None):
                obj.id = 5

    db.flush.side_effect = flush_side_effect
    monkeypatch.setattr("hans.orders.services.fetch_test_catalogs", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        "hans.orders.services.fetch_service_catalogs",
        AsyncMock(return_value=[SimpleNamespace(id=20, price=5)]),
    )

    with pytest.raises(HTTPException) as exc_ctx:
        await create_order(data, db, user_id=1)

    assert exc_ctx.value.status_code == 400
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_order_creates_single_specimen_per_specimen_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Two tests of same specimen type should share one generated barcode.
    _patch_order_models(monkeypatch)
    data = OrderCreate(patient_id=1, test_catalog_ids=[1, 2])
    db = _db_mock()

    async def flush_side_effect() -> None:
        for added in db.add.call_args_list:
            obj = added.args[0]
            if hasattr(obj, "patient_id") and not getattr(obj, "id", None):
                obj.id = 99

    db.flush.side_effect = flush_side_effect
    monkeypatch.setattr(
        "hans.orders.services.fetch_test_catalogs",
        AsyncMock(
            return_value=[
                SimpleNamespace(id=1, specimen_type_id=3, price=11),
                SimpleNamespace(id=2, specimen_type_id=3, price=12),
            ]
        ),
    )
    monkeypatch.setattr("hans.orders.services.fetch_service_catalogs", AsyncMock(return_value=[]))
    next_barcode_mock = AsyncMock(return_value="000000000123")
    monkeypatch.setattr("hans.orders.services.next_barcode", next_barcode_mock)
    monkeypatch.setattr(
        "hans.orders.services.load_order",
        AsyncMock(
            return_value=SimpleNamespace(
                id=99,
                patient_id=1,
                created_by=7,
                created_at="2026-03-13T12:00:00",
                archived=False,
                urgency=OrderUrgency.ROUTINE,
                comment=None,
                specimens=[],
                test_runs=[],
                service_runs=[],
            )
        ),
    )

    await create_order(data, db, user_id=7)

    assert next_barcode_mock.await_count == 1


@pytest.mark.asyncio
async def test_create_order_creates_test_runs_with_prices_from_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_order_models(monkeypatch)
    data = OrderCreate(patient_id=1, test_catalog_ids=[1])
    db = _db_mock()

    async def flush_side_effect() -> None:
        for added in db.add.call_args_list:
            obj = added.args[0]
            if hasattr(obj, "patient_id") and not getattr(obj, "id", None):
                obj.id = 42

    db.flush.side_effect = flush_side_effect
    monkeypatch.setattr(
        "hans.orders.services.fetch_test_catalogs",
        AsyncMock(return_value=[SimpleNamespace(id=1, specimen_type_id=9, price=12.34)]),
    )
    monkeypatch.setattr("hans.orders.services.fetch_service_catalogs", AsyncMock(return_value=[]))
    monkeypatch.setattr("hans.orders.services.next_barcode", AsyncMock(return_value="B-9"))
    monkeypatch.setattr(
        "hans.orders.services.load_order",
        AsyncMock(
            return_value=SimpleNamespace(
                id=42,
                patient_id=1,
                created_by=7,
                created_at="2026-03-13T12:00:00",
                archived=False,
                urgency=OrderUrgency.ROUTINE,
                comment=None,
                specimens=[],
                test_runs=[],
                service_runs=[],
            )
        ),
    )

    await create_order(data, db, user_id=7)

    created_runs = [c.args[0] for c in db.add.call_args_list if hasattr(c.args[0], "test_catalog_id")]
    assert len(created_runs) == 1
    assert created_runs[0].price == pytest.approx(12.34)


@pytest.mark.asyncio
async def test_create_order_creates_service_runs_with_prices_from_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_order_models(monkeypatch)
    data = OrderCreate(patient_id=1, service_catalog_ids=[55])
    db = _db_mock()

    async def flush_side_effect() -> None:
        for added in db.add.call_args_list:
            obj = added.args[0]
            if hasattr(obj, "patient_id") and not getattr(obj, "id", None):
                obj.id = 43

    db.flush.side_effect = flush_side_effect
    monkeypatch.setattr("hans.orders.services.fetch_test_catalogs", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        "hans.orders.services.fetch_service_catalogs",
        AsyncMock(return_value=[SimpleNamespace(id=55, price=9.99)]),
    )
    monkeypatch.setattr(
        "hans.orders.services.load_order",
        AsyncMock(
            return_value=SimpleNamespace(
                id=43,
                patient_id=1,
                created_by=7,
                created_at="2026-03-13T12:00:00",
                archived=False,
                urgency=OrderUrgency.ROUTINE,
                comment=None,
                specimens=[],
                test_runs=[],
                service_runs=[],
            )
        ),
    )

    await create_order(data, db, user_id=7)

    created_runs = [
        c.args[0]
        for c in db.add.call_args_list
        if hasattr(c.args[0], "service_catalog_id")
    ]
    assert len(created_runs) == 1
    assert created_runs[0].price == pytest.approx(9.99)


@pytest.mark.asyncio
async def test_update_order_updates_only_provided_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    order = SimpleNamespace(id=5, comment="old", urgency=OrderUrgency.ROUTINE)
    db = _db_mock()
    monkeypatch.setattr("hans.orders.services.fetch_order_basic", AsyncMock(return_value=order))
    monkeypatch.setattr(
        "hans.orders.services.load_order",
        AsyncMock(
            return_value=SimpleNamespace(
                id=5,
                patient_id=1,
                created_by=2,
                created_at="2026-03-13T12:00:00",
                archived=False,
                urgency=OrderUrgency.STAT,
                comment="old",
                specimens=[],
                test_runs=[],
                service_runs=[],
            )
        ),
    )

    result = await update_order(5, OrderUpdate(urgency=OrderUrgency.STAT), db)

    assert order.urgency == OrderUrgency.STAT
    assert order.comment == "old"
    db.commit.assert_awaited_once()
    assert result.id == 5


@pytest.mark.asyncio
async def test_update_order_allows_setting_comment_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    order = SimpleNamespace(id=6, comment="to-clear", urgency=OrderUrgency.ROUTINE)
    db = _db_mock()
    monkeypatch.setattr("hans.orders.services.fetch_order_basic", AsyncMock(return_value=order))
    monkeypatch.setattr(
        "hans.orders.services.load_order",
        AsyncMock(
            return_value=SimpleNamespace(
                id=6,
                patient_id=2,
                created_by=2,
                created_at="2026-03-13T12:00:00",
                archived=False,
                urgency=OrderUrgency.ROUTINE,
                comment=None,
                specimens=[],
                test_runs=[],
                service_runs=[],
            )
        ),
    )

    await update_order(6, OrderUpdate(comment=None), db)

    assert order.comment is None


@pytest.mark.asyncio
async def test_update_order_raises_404_when_order_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hans.orders.services.fetch_order_basic", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_ctx:
        await update_order(1, OrderUpdate(comment="x"), _db_mock())

    assert exc_ctx.value.status_code == 404


@pytest.mark.asyncio
async def test_toggle_order_archive_switches_false_to_true(monkeypatch: pytest.MonkeyPatch) -> None:
    order = SimpleNamespace(id=11, archived=False)
    db = _db_mock()
    monkeypatch.setattr("hans.orders.services.fetch_order_basic", AsyncMock(return_value=order))

    result = await toggle_order_archive(11, db)

    assert order.archived is True
    assert result.archived is True


@pytest.mark.asyncio
async def test_toggle_order_archive_switches_true_to_false(monkeypatch: pytest.MonkeyPatch) -> None:
    order = SimpleNamespace(id=12, archived=True)
    db = _db_mock()
    monkeypatch.setattr("hans.orders.services.fetch_order_basic", AsyncMock(return_value=order))

    result = await toggle_order_archive(12, db)

    assert order.archived is False
    assert result.archived is False


@pytest.mark.asyncio
async def test_toggle_order_archive_raises_404_when_order_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hans.orders.services.fetch_order_basic", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_ctx:
        await toggle_order_archive(404, _db_mock())

    assert exc_ctx.value.status_code == 404


@pytest.mark.asyncio
async def test_get_patient_orders_returns_mapped_order_read_list(monkeypatch: pytest.MonkeyPatch) -> None:
    # Service should map repository entities into OrderRead schemas.
    orders = [
        SimpleNamespace(
            id=1,
            patient_id=33,
            created_by=2,
            created_at="2026-03-13T12:00:00",
            archived=False,
            urgency=OrderUrgency.ROUTINE,
            comment=None,
            specimens=[],
            test_runs=[],
            service_runs=[],
        ),
        SimpleNamespace(
            id=2,
            patient_id=33,
            created_by=2,
            created_at="2026-03-13T12:01:00",
            archived=True,
            urgency=OrderUrgency.URGENT,
            comment="a",
            specimens=[],
            test_runs=[],
            service_runs=[],
        ),
    ]
    monkeypatch.setattr("hans.orders.services.fetch_patient_orders", AsyncMock(return_value=orders))

    result = await get_patient_orders(33, _db_mock())

    assert [o.id for o in result] == [1, 2]
