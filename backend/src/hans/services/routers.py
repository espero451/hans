from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from hans.core.auth import require_staff_or_admin
from hans.core.db import get_db
from hans.users import User

from .schemas import ServiceCatalogRead
from .services import get_services as get_services_service


# --- ROUTES -----------------------------------------------------------

router = APIRouter(prefix="/services", tags=["services"])


@router.get("/", response_model=list[ServiceCatalogRead])
async def get_services(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
) -> list[ServiceCatalogRead]:
    return await get_services_service(db)
