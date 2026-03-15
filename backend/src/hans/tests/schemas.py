from typing import Optional

from pydantic import BaseModel

from hans.core.schemas import ORMModel


# --- SCHEMAS ----------------------------------------------------------

class TestCatalogRead(ORMModel):
    id: int
    code: str
    description: Optional[str] = None
    price: float
    specimen_type_id: int
