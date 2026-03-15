from typing import Optional

from pydantic import BaseModel

from hans.core.schemas import ORMModel


# --- SCHEMAS ----------------------------------------------------------

class ServiceCatalogRead(ORMModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
