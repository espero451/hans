from sqlalchemy.ext.asyncio import AsyncSession

from .repositories import fetch_services
from .schemas import ServiceCatalogRead


# --- SERVICE FLOWS ----------------------------------------------------

async def get_services(db: AsyncSession) -> list[ServiceCatalogRead]:
    services = await fetch_services(db)
    return [ServiceCatalogRead.model_validate(service) for service in services]
