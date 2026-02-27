import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import select
from hans.core.db import SessionLocal

# Emit a startup banner for service logs.
print("Hans LIS started...")


# ---------------- FastAPI APP ----------------

app = FastAPI(title="Hans LIS")

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


# ---------------- AUDIT LOG ----------------

def audit_log(user_id: int, action: str) -> None:
    """Write audit log to audit/YYYY-MM-DD.log"""
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    path = "../live/audit"
    os.makedirs(path, exist_ok=True)
    with open(f"{path}/{date_str}.log", "a") as f:
        f.write(f"{datetime.utcnow()} | user_id={user_id} | {action}\n")


# ---------------- SEED ADMIN ----------------

# Moved to tools/seed_admin.py

# @app.on_event("startup")
# async def ensure_admin_user() -> None:
#     # Import auth models lazily to avoid circular imports.
#     from hans.core.auth import User, hash_password

#     # Check admin user
#     async with SessionLocal() as db:
#         result = await db.execute(select(User).where(User.username == "hans"))
#         user = result.scalar_one_or_none()
#         if user:
#             return
#         # Create admin
#         hashed = hash_password("hans")
#         hans = User(
#             username="hans",
#             email="hans@example.com",
#             role="admin",
#             hashed_password=hashed,
#         )
#         db.add(hans)
#         await db.commit()
