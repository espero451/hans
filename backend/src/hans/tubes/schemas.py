from typing import Optional

from pydantic import BaseModel

from hans.core.schemas import ORMModel


# --- SCHEMAS ----------------------------------------------------------

class TubeTypeCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None


class TubeTypeRead(ORMModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
