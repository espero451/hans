from typing import Optional

from pydantic import BaseModel


# --- SCHEMAS ----------------------------------------------------------

class OwnerCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    comment: Optional[str] = None


class OwnerRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    comment: Optional[str] = None

    class Config:
        from_attributes = True
