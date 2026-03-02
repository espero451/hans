import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from hans.core.db import SessionLocal

print("Hans LIS started...")


# --- FastAPI APP -----------------------------------------------------

# app = FastAPI(title="Hans LIS")

def create_app() -> FastAPI:
    app = FastAPI(
        title="Hans LIMS",
        version="1.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        # Local dev origins (Vite + Docker)
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app

# app.add_middleware(
#     CORSMiddleware,
#     # Local dev origins (Vite + Docker)
#     allow_origins=[
#         "http://localhost:5173",
#         "http://127.0.0.1:5173",
#         "http://localhost:8080",
#         "http://127.0.0.1:8080",
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# --- AUDIT LOG -------------------------------------------------------

def audit_log(user_id: int, action: str) -> None:
    """Write audit log to audit/YYYY-MM-DD.log"""
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    path = "../live/audit"
    os.makedirs(path, exist_ok=True)
    with open(f"{path}/{date_str}.log", "a") as f:
        f.write(f"{datetime.utcnow()} | user_id={user_id} | {action}\n")
