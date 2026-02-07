from sqlalchemy import text

from hans.core import app
from hans.db import engine, Base

from hans import owners, patients, orders, services, tests, specimens, auth, instruments


# app.include_router(auth_router, prefix="/auth", tags=["auth"])
# app.include_router(owners_router, prefix="/owners", tags=["owners"])
# app.include_router(patients_router, prefix="/patients", tags=["patients"])
# app.include_router(orders_router, prefix="/orders", tags=["orders"])
# app.include_router(services_router, prefix="/services", tags=["services"])
# app.include_router(tests_router, prefix="/tests", tags=["tests"])
# app.include_router(specimens_router, prefix="/specimens", tags=["specimens"])


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SEQUENCE IF NOT EXISTS specimen_barcode_seq"))
        await conn.run_sync(Base.metadata.create_all)
