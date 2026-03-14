from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from fastapi import HTTPException
import pytest

from hans.orders.services import print_specimen


# --- Specimen Print Tests ---------------------------------------------

@pytest.mark.asyncio
async def test_print_specimen_sends_zpl_and_returns_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    # Simulate an existing specimen fetched from the repository.
    specimen = SimpleNamespace(
        specimen_id="000000000123",
        order_id=7,
        specimen_type_id=3,
        status="NEW",
        collected_at=None,
        received_at=None,
    )
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    fetch_specimen_mock = AsyncMock(return_value=specimen)
    generate_zpl_mock = Mock(return_value="^XA^XZ")
    send_zpl_mock = Mock()
    to_thread_mock = AsyncMock()

    monkeypatch.setattr("hans.orders.services.fetch_specimen", fetch_specimen_mock)
    monkeypatch.setattr("hans.orders.services.generate_zpl_label", generate_zpl_mock)
    monkeypatch.setattr("hans.orders.services.send_zpl", send_zpl_mock)
    monkeypatch.setattr("hans.orders.services.asyncio.to_thread", to_thread_mock)
    monkeypatch.setattr("hans.orders.services.settings.barcode_printer_ip", "10.0.0.5")
    monkeypatch.setattr("hans.orders.services.settings.barcode_printer_port", 9100)
    monkeypatch.setattr("hans.orders.services.settings.barcode_printer_timeout", 2.5)

    result = await print_specimen(specimen.specimen_id, db)

    generate_zpl_mock.assert_called_once_with("000000000123")
    to_thread_mock.assert_awaited_once_with(
        send_zpl_mock,
        "^XA^XZ",
        "10.0.0.5",
        9100,
        2.5,
    )
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(specimen)
    assert result.specimen_id == "000000000123"


@pytest.mark.asyncio
async def test_print_specimen_maps_printer_error_to_502(monkeypatch: pytest.MonkeyPatch) -> None:
    # Simulate an existing specimen and a printer socket failure.
    specimen = SimpleNamespace(
        specimen_id="000000000999",
        order_id=5,
        specimen_type_id=2,
        status="NEW",
        collected_at=None,
        received_at=None,
    )
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    monkeypatch.setattr("hans.orders.services.fetch_specimen", AsyncMock(return_value=specimen))
    monkeypatch.setattr("hans.orders.services.generate_zpl_label", Mock(return_value="^XA^XZ"))
    monkeypatch.setattr(
        "hans.orders.services.asyncio.to_thread",
        AsyncMock(side_effect=OSError("connection refused")),
    )

    with pytest.raises(HTTPException) as exc_ctx:
        await print_specimen(specimen.specimen_id, db)

    assert exc_ctx.value.status_code == 502
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_print_specimen_raises_404_when_specimen_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    # Guard against unknown specimen ids before printer call.
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    monkeypatch.setattr("hans.orders.services.fetch_specimen", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_ctx:
        await print_specimen("unknown", db)

    assert exc_ctx.value.status_code == 404
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_print_specimen_calls_generate_zpl_with_specimen_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Ensure the ZPL payload is built for the exact specimen barcode.
    specimen = SimpleNamespace(
        specimen_id="000000001111",
        order_id=8,
        specimen_type_id=1,
        status="NEW",
        collected_at=None,
        received_at=None,
    )
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    generate_zpl_mock = Mock(return_value="^XA^XZ")
    monkeypatch.setattr("hans.orders.services.fetch_specimen", AsyncMock(return_value=specimen))
    monkeypatch.setattr("hans.orders.services.generate_zpl_label", generate_zpl_mock)
    monkeypatch.setattr("hans.orders.services.send_zpl", Mock())
    monkeypatch.setattr("hans.orders.services.asyncio.to_thread", AsyncMock())

    await print_specimen(specimen.specimen_id, db)

    generate_zpl_mock.assert_called_once_with("000000001111")
