from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from hans.core.auth import AuthPrincipal, require_staff_or_admin
from hans.core.db import get_db

from .schemas import DashboardStatsRead
from .services import get_dashboard_stats as get_dashboard_stats_service


# --- ROUTES -----------------------------------------------------------

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsRead)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: AuthPrincipal = Depends(require_staff_or_admin),
) -> DashboardStatsRead:
    return await get_dashboard_stats_service(db)
