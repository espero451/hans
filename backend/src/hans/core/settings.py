# --- Imports ----------------------------------------------------------
from pydantic_settings import BaseSettings


# --- Settings ---------------------------------------------------------
class Settings(BaseSettings):
    database_url: str
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    class Config:
        env_file = ".env"


# Load env-backed settings once at import time.
settings = Settings()
