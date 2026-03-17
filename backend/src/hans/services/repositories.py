from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ServiceCatalog


# --- SERVICE QUERIES --------------------------------------------------

async def fetch_services(db: AsyncSession) -> list[ServiceCatalog]:
    result = await db.execute(select(ServiceCatalog).order_by(ServiceCatalog.name))
    return result.scalars().all()
