from pydantic_settings import BaseSettings, SettingsConfigDict


# --- Settings ---------------------------------------------------------

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 20
    refresh_token_expire_minutes: int = 10080  # 7 days
    barcode_printer_ip: str = "127.0.0.1"
    barcode_printer_port: int = 9100
    barcode_printer_timeout: float = 3.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Load env-backed settings once at import time.
settings = Settings()
