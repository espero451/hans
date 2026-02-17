from hans.core.core import app
from hans.core import auth
from hans.users import router as users_router
from hans.owners import router as owners_router
from hans.patients import router as patients_router
from hans.orders import router as orders_router
from hans.tests import router as tests_router
from hans.services import router as services_router
from hans.specimens import router as specimens_router
from hans.tubes import router as tubes_router
from hans.instruments import router as instruments_router


app.include_router(users_router, tags=["users"])
app.include_router(tests_router, tags=["tests"])
app.include_router(owners_router, tags=["owners"])
app.include_router(orders_router, tags=["orders"])
app.include_router(patients_router, tags=["patients"])
app.include_router(services_router, tags=["services"])
app.include_router(specimens_router, tags=["specimens"])
app.include_router(tubes_router, tags=["tubes"])
app.include_router(instruments_router, tags=["instruments"])


# if without alembic:
# from sqlalchemy import text
# from hans.core.db import engine, Base
# from hans import users, owners, patients, orders, services, tests, specimens, tubes, instruments
# @app.on_event("startup")
# async def startup():
#     async with engine.begin() as conn:
#         await conn.execute(text("CREATE SEQUENCE IF NOT EXISTS specimen_barcode_seq"))
#         await conn.run_sync(Base.metadata.create_all)
