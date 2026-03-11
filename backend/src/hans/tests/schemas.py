from typing import Optional

from pydantic import BaseModel


# --- SCHEMAS ----------------------------------------------------------

class TestCatalogCreate(BaseModel):
    code: str
    description: Optional[str] = None
    price: float
    specimen_type_id: int


class TestCatalogRead(BaseModel):
    id: int
    code: str
    description: Optional[str] = None
    price: float
    specimen_type_id: int

    class Config:
        from_attributes = True
