from typing import Optional

from pydantic import BaseModel

from hans.core.schemas import ORMModel


# --- SCHEMAS ----------------------------------------------------------

class SpecimenTypeCreate(BaseModel):
    code: str
    name: str
    type: str
    tube_type_id: int
    description: Optional[str] = None


class SpecimenTypeRead(ORMModel):
    id: int
    code: str
    name: str
    type: Optional[str] = None
    tube_type_id: int
    description: Optional[str] = None
