from typing import Optional

from pydantic import BaseModel


# --- SCHEMAS ----------------------------------------------------------

class TubeTypeCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None


class TubeTypeRead(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True
