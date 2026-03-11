from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from .models import OrderUrgency


# --- SCHEMAS ----------------------------------------------------------

class OrderCreate(BaseModel):
    patient_id: int
    test_catalog_ids: List[int] = []
    service_catalog_ids: List[int] = []
    comment: Optional[str] = None
    urgency: OrderUrgency = OrderUrgency.ROUTINE


class OrderUpdate(BaseModel):
    # Payload for order edits.
    comment: Optional[str] = None
    urgency: Optional[OrderUrgency] = None


class ResultRead(BaseModel):
    id: int
    test_run_id: int
    value: Optional[str] = None
    units: Optional[str] = None
    flags: Optional[str] = None
    reference_range: Optional[str] = None
    abnormal_flag: Optional[str] = None
    verified_by: Optional[int] = None
    verified_at: Optional[datetime] = None
    comment: Optional[str] = None
    completed_at: Optional[datetime] = None
    verified: bool

    class Config:
        from_attributes = True


class ResultCreate(BaseModel):
    # Payload for manual result creation.
    value: Optional[str] = None
    units: Optional[str] = None
    flags: Optional[str] = None
    reference_range: Optional[str] = None
    abnormal_flag: Optional[str] = None
    comment: Optional[str] = None
    completed_at: Optional[datetime] = None


class ResultUpdate(BaseModel):
    # Payload for manual result updates.
    value: Optional[str] = None
    units: Optional[str] = None
    flags: Optional[str] = None
    reference_range: Optional[str] = None
    abnormal_flag: Optional[str] = None
    comment: Optional[str] = None
    completed_at: Optional[datetime] = None


class SpecimenRead(BaseModel):
    specimen_id: str
    order_id: int
    specimen_type_id: int
    status: str
    collected_at: Optional[datetime] = None
    received_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestRunRead(BaseModel):
    id: int
    order_id: int
    test_catalog_id: int
    specimen_id: str
    workstation_id: Optional[int] = None
    instrument_id: Optional[int] = None
    status: str
    price: float
    results: List[ResultRead] = []

    class Config:
        from_attributes = True


class ServiceRunRead(BaseModel):
    id: int
    order_id: int
    service_catalog_id: int
    status: str
    price: float
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderRead(BaseModel):
    id: int
    patient_id: int
    created_by: Optional[int] = None
    created_at: datetime
    archived: bool
    urgency: OrderUrgency
    comment: Optional[str] = None
    specimens: List[SpecimenRead] = []
    test_runs: List[TestRunRead] = []
    service_runs: List[ServiceRunRead] = []

    class Config:
        from_attributes = True


class OrderArchivedStatusRead(BaseModel):
    id: int
    archived: bool

    class Config:
        from_attributes = True
