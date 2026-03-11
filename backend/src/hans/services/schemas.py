from typing import Optional

from pydantic import BaseModel


# --- SCHEMAS ----------------------------------------------------------

class ServiceCatalogCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float


class ServiceCatalogRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float

    class Config:
        from_attributes = True
