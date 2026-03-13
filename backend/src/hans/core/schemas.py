from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    # Enable ORM object parsing for response schemas.
    model_config = ConfigDict(from_attributes=True)
