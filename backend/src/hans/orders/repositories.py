from datetime import date
from typing import Optional

from sqlalchemy import case, exists, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from hans.patients.models import Patient
from hans.services import ServiceCatalog
from hans.tests import TestCatalog

from .models import Order, Result, Specimen, TestRun


# --- ORDER QUERIES ----------------------------------------------------

async def fetch_order(order_id: int, db: AsyncSession) -> Optional[Order]:
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.specimens),
            selectinload(Order.test_runs).selectinload(TestRun.results),
            selectinload(Order.service_runs),
        )
    )
    return result.scalar_one_or_none()


async def fetch_order_basic(order_id: int, db: AsyncSession) -> Optional[Order]:
    result = await db.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()


async def fetch_patient_orders(patient_id: int, db: AsyncSession) -> list[Order]:
    result = await db.execute(
        select(Order)
        .where(Order.patient_id == patient_id)
        .options(
            selectinload(Order.specimens),
            selectinload(Order.test_runs).selectinload(TestRun.results),
            selectinload(Order.service_runs),
        )
        .order_by(Order.created_at.desc())
    )
    return result.scalars().unique().all()


def build_orders_query(
    patient_id: int | None,
    owner_id: int | None,
    archived: bool | None,
    resulted: bool | None,
    created_date: date | None,
):
    query = select(Order)
    urgency_order = case(
        (Order.urgency == "STAT", 0),
        (Order.urgency == "URGENT", 1),
        else_=2,
    )

    if patient_id is not None:
        query = query.where(Order.patient_id == patient_id)
    if owner_id is not None:
        query = query.where(Order.patient.has(Patient.owner_id == owner_id))
    if archived is not None:
        query = query.where(Order.archived == archived)
    if created_date is not None:
        # Filter by calendar date regardless of time in created_at.
        query = query.where(func.date(Order.created_at) == created_date)

    if resulted is not None:
        has_results = exists(
            select(Result.id)
            .join(TestRun, Result.test_run_id == TestRun.id)
            .where(TestRun.order_id == Order.id)
        )
        query = query.where(has_results if resulted else ~has_results)

    return query.options(
        selectinload(Order.specimens),
        selectinload(Order.test_runs).selectinload(TestRun.results),
        selectinload(Order.service_runs),
        selectinload(Order.patient),
    ).order_by(
        urgency_order,
        Order.created_at.desc(),
    )


# --- CATALOG QUERIES --------------------------------------------------

async def fetch_test_catalogs(ids: list[int], db: AsyncSession) -> list[TestCatalog]:
    if not ids:
        return []
    result = await db.execute(select(TestCatalog).where(TestCatalog.id.in_(ids)))
    return result.scalars().all()


async def fetch_service_catalogs(ids: list[int], db: AsyncSession) -> list[ServiceCatalog]:
    if not ids:
        return []
    result = await db.execute(select(ServiceCatalog).where(ServiceCatalog.id.in_(ids)))
    return result.scalars().all()


# --- ENTITY QUERIES ---------------------------------------------------

async def fetch_specimen(specimen_id: str, db: AsyncSession) -> Optional[Specimen]:
    result = await db.execute(select(Specimen).where(Specimen.specimen_id == specimen_id))
    return result.scalar_one_or_none()


async def fetch_test_run(test_run_id: int, db: AsyncSession) -> Optional[TestRun]:
    result = await db.execute(select(TestRun).where(TestRun.id == test_run_id))
    return result.scalar_one_or_none()


async def fetch_result(result_id: int, db: AsyncSession) -> Optional[Result]:
    result = await db.execute(select(Result).where(Result.id == result_id))
    return result.scalar_one_or_none()


# --- HELPERS ----------------------------------------------------------

async def next_barcode(db: AsyncSession) -> str:
    result = await db.execute(
        text("select lpad(nextval('specimen_barcode_seq')::text, 12, '0')")
    )
    return result.scalar_one()
