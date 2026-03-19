from datetime import date, datetime
import asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from hans.core.settings import settings
from hans.interfaces.printers import send_zpl
from hans.tools.barcodes import generate_zpl_label

from .models import Order, Result, ServiceRun, Specimen, TestRun
from .repositories import (
    build_orders_query,
    fetch_order,
    fetch_order_basic,
    fetch_patient_orders,
    fetch_result,
    fetch_service_catalogs,
    fetch_specimen,
    fetch_test_catalogs,
    fetch_test_run,
    next_barcode,
)
from .schemas import (
    OrderArchivedStatusRead,
    OrderCreate,
    OrderRead,
    OrderUpdate,
    ResultCreate,
    ResultRead,
    ResultUpdate,
    SpecimenRead,
)


# --- ORDER FLOWS ------------------------------------------------------

async def create_order(data: OrderCreate, db: AsyncSession, user_id: int) -> OrderRead:
    order = Order(
        patient_id=data.patient_id,
        created_by=user_id,
        comment=data.comment,
        urgency=data.urgency,
    )
    db.add(order)
    await db.flush()

    test_ids = list(set(data.test_catalog_ids)) if data.test_catalog_ids else []
    test_catalogs = await fetch_test_catalogs(test_ids, db)
    if len(test_catalogs) != len(test_ids):
        raise HTTPException(400, "One or more tests not found")

    service_ids = data.service_catalog_ids or []
    service_catalogs = await fetch_service_catalogs(service_ids, db)
    if len(service_catalogs) != len(service_ids):
        raise HTTPException(400, "One or more services not found")

    specimen_map: dict[int, str] = {}
    for test in test_catalogs:
        if test.specimen_type_id in specimen_map:
            continue
        barcode = await next_barcode(db)
        specimen = Specimen(
            specimen_id=barcode,
            order_id=order.id,
            specimen_type_id=test.specimen_type_id,
            status="NEW",
        )
        db.add(specimen)
        specimen_map[test.specimen_type_id] = barcode

    for test in test_catalogs:
        db.add(
            TestRun(
                order_id=order.id,
                test_catalog_id=test.id,
                specimen_id=specimen_map[test.specimen_type_id],
                status="NEW",
                price=float(test.price),
            )
        )

    for service in service_catalogs:
        db.add(
            ServiceRun(
                order_id=order.id,
                service_catalog_id=service.id,
                status="NEW",
                price=float(service.price),
            )
        )

    await db.commit()
    return await load_order(order.id, db)


async def load_order(order_id: int, db: AsyncSession) -> OrderRead:
    order = await fetch_order(order_id, db)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderRead.model_validate(order)


async def get_patient_orders(patient_id: int, db: AsyncSession) -> list[OrderRead]:
    orders = await fetch_patient_orders(patient_id, db)
    return [OrderRead.model_validate(order) for order in orders]


async def get_orders(
    patient_id: int | None,
    owner_id: int | None,
    archived: bool | None,
    resulted: bool | None,
    created_date: date | None,
):
    return build_orders_query(
        patient_id=patient_id,
        owner_id=owner_id,
        archived=archived,
        resulted=resulted,
        created_date=created_date,
    )


async def toggle_order_archive(order_id: int, db: AsyncSession) -> OrderArchivedStatusRead:
    order = await fetch_order_basic(order_id, db)
    if not order:
        raise HTTPException(404, "Order not found")
    # Preserve existing toggle behavior for archive endpoint.
    order.archived = not bool(order.archived)
    await db.commit()
    await db.refresh(order)
    return OrderArchivedStatusRead.model_validate(order)


async def update_order(order_id: int, data: OrderUpdate, db: AsyncSession) -> OrderRead:
    order = await fetch_order_basic(order_id, db)
    if not order:
        raise HTTPException(404, "Order not found")
    # Apply only fields sent by the client.
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(order, key, value)
    await db.commit()
    await db.refresh(order)
    return await load_order(order_id, db)


# --- SPECIMEN FLOWS ---------------------------------------------------

async def collect_specimen(specimen_id: str, db: AsyncSession) -> SpecimenRead:
    specimen = await fetch_specimen(specimen_id, db)
    if not specimen:
        raise HTTPException(404, "Specimen not found")
    if specimen.status == "CANCELED":
        raise HTTPException(400, "Specimen is canceled")
    if specimen.status in ("COLLECTED", "RECEIVED"):
        return SpecimenRead.model_validate(specimen)

    specimen.status = "COLLECTED"
    specimen.collected_at = datetime.utcnow()
    await db.commit()
    await db.refresh(specimen)
    return SpecimenRead.model_validate(specimen)


async def receive_specimen(specimen_id: str, db: AsyncSession) -> SpecimenRead:
    specimen = await fetch_specimen(specimen_id, db)
    if not specimen:
        raise HTTPException(404, "Specimen not found")
    if specimen.status == "CANCELED":
        raise HTTPException(400, "Specimen is canceled")
    if specimen.status == "RECEIVED":
        return SpecimenRead.model_validate(specimen)
    if specimen.status != "COLLECTED":
        raise HTTPException(400, "Specimen must be collected first")

    specimen.status = "RECEIVED"
    specimen.received_at = datetime.utcnow()
    await db.commit()
    await db.refresh(specimen)
    return SpecimenRead.model_validate(specimen)


async def print_specimen(specimen_id: str, db: AsyncSession) -> SpecimenRead:
    specimen = await fetch_specimen(specimen_id, db)
    if not specimen:
        raise HTTPException(404, "Specimen not found")

    # Generate a printer-ready barcode label for the specimen.
    zpl_label = generate_zpl_label(specimen.specimen_id)
    try:
        # Run socket I/O in a worker thread to avoid blocking the event loop.
        await asyncio.to_thread(
            send_zpl,
            zpl_label,
            settings.barcode_printer_ip,
            settings.barcode_printer_port,
            settings.barcode_printer_timeout,
        )
    except OSError as exc:
        raise HTTPException(502, f"Barcode printer is unavailable: {exc}") from exc

    # specimen.printed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(specimen)
    return SpecimenRead.model_validate(specimen)


# --- RESULT FLOWS -----------------------------------------------------

async def create_result(test_run_id: int, data: ResultCreate, db: AsyncSession) -> ResultRead:
    test_run = await fetch_test_run(test_run_id, db)
    if not test_run:
        raise HTTPException(404, "Test run not found")
    result = Result(test_run_id=test_run_id, **data.model_dump())
    db.add(result)
    await db.commit()
    await db.refresh(result)
    return ResultRead.model_validate(result)


async def update_result(result_id: int, data: ResultUpdate, db: AsyncSession) -> ResultRead:
    result = await fetch_result(result_id, db)
    if not result:
        raise HTTPException(404, "Result not found")
    # Apply only fields sent by the client.
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(result, key, value)
    await db.commit()
    await db.refresh(result)
    return ResultRead.model_validate(result)


async def toggle_result_verify(result_id: int, user_id: int, db: AsyncSession) -> ResultRead:
    result = await fetch_result(result_id, db)
    if not result:
        raise HTTPException(404, "Result not found")

    if result.verified:
        result.verified = False
        result.verified_by = None
        result.verified_at = None
    else:
        result.verified = True
        result.verified_by = user_id
        result.verified_at = datetime.utcnow()

    await db.commit()
    await db.refresh(result)
    return ResultRead.model_validate(result)
