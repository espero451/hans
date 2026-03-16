from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from hans.orders import Order
from hans.owners import Owner
from hans.patients import Patient


# --- REPOSITORY -------------------------------------------------------

async def fetch_dashboard_totals(db: AsyncSession) -> tuple[int, int, int]:
    # Collect summary counters for dashboard cards.
    total_orders = await db.scalar(select(func.count()).select_from(Order))
    total_patients = await db.scalar(select(func.count()).select_from(Patient))
    total_owners = await db.scalar(select(func.count()).select_from(Owner))
    return int(total_orders or 0), int(total_patients or 0), int(total_owners or 0)
