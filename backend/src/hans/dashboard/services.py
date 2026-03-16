from sqlalchemy.ext.asyncio import AsyncSession

from .repositories import fetch_dashboard_totals
from .schemas import DashboardStatsRead


# --- SERVICE FLOW -----------------------------------------------------

async def get_dashboard_stats(db: AsyncSession) -> DashboardStatsRead:
    # Map repository totals into API response schema.
    total_orders, total_patients, total_owners = await fetch_dashboard_totals(db)
    return DashboardStatsRead(
        total_orders=total_orders,
        total_patients=total_patients,
        total_owners=total_owners,
    )
