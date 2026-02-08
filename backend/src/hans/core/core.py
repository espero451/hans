import os
from datetime import datetime
from fastapi import FastAPI
from pydantic_settings import BaseSettings
from fastapi.middleware.cors import CORSMiddleware


# ---------------- CONFIG ----------------

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440 # 24 hours

    class Config:
        env_file = ".env"

settings = Settings()

print("Hans LIS started...")


# ---------------- FastAPI APP ----------------

app = FastAPI(title="Hans LIS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- AUDIT LOG ----------------

def audit_log(user_id: int, action: str):
    """Write audit log to audit/YYYY-MM-DD.log"""
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    path = "../prod/audit"
    os.makedirs(path, exist_ok=True)
    with open(f"{path}/{date_str}.log", "a") as f:
        f.write(f"{datetime.utcnow()} | user_id={user_id} | {action}\n")
