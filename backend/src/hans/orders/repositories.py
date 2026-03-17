from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
