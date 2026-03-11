from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel


# --- SCHEMAS ----------------------------------------------------------

class PatientCreate(BaseModel):
    # Core patient identification fields.
    name: str
    species: str
    owner_id: int
    breed: Optional[str] = None
    birth_date: Optional[date] = None
    comment: Optional[str] = None
    sex: Literal["male", "female", "unknown"]
    weight: Optional[float] = None
    microchip_number: Optional[str] = None
    species_id: int


# Partial update schema
class PatientUpdate(BaseModel):
    # Optional identity updates.
    name: Optional[str] = None
    species: Optional[str] = None
    owner_id: Optional[int] = None
    breed: Optional[str] = None
    birth_date: Optional[date] = None
    comment: Optional[str] = None
    sex: Optional[Literal["male", "female", "unknown"]] = None
    weight: Optional[float] = None
    microchip_number: Optional[str] = None
    species_id: Optional[int] = None


class PatientRead(BaseModel):
    id: int
    name: str
    species: str
    owner_id: int
    breed: Optional[str] = None
    birth_date: Optional[date] = None
    created_at: datetime
    comment: Optional[str] = None
    sex: Literal["male", "female", "unknown"]
    weight: Optional[float] = None
    microchip_number: Optional[str] = None
    species_id: int

    class Config:
        from_attributes = True


class SpeciesRead(BaseModel):
    # Species data for UI dropdowns.
    id: int
    code: str
    name: str
    latin_name: Optional[str] = None
    active: bool

    class Config:
        from_attributes = True
