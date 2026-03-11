from pydantic import BaseModel


# --- SCHEMAS ----------------------------------------------------------

class UserCreate(BaseModel):
    username: str
    email: str
    role: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    role: str

    class Config:
        from_attributes = True
