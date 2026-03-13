from pydantic import BaseModel

from hans.core.schemas import ORMModel


# --- SCHEMAS ----------------------------------------------------------

class UserCreate(BaseModel):
    username: str
    email: str
    role: str
    password: str


class UserRead(ORMModel):
    id: int
    username: str
    email: str
    role: str
