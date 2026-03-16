from pydantic import BaseModel, ConfigDict
from typing import Generic, TypeVar, List

class ORMModel(BaseModel):
    # Enable ORM object parsing for response schemas.
    model_config = ConfigDict(from_attributes=True)


# --- Pagination ------------------------------------------------------

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int