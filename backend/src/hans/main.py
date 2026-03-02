from hans.core.core import create_app

from hans.core.auth import router as auth_router
# from hans.users import router as users_router
from hans.owners import router as owners_router
from hans.patients import router as patients_router, species_router
from hans.orders import router as orders_router
from hans.tests import router as tests_router
from hans.services import router as services_router
# from hans.specimens import router as specimens_router
from hans.tubes import router as tubes_router
from hans.instruments import router as instruments_router
from hans.interfaces.dispatcher.api import router as dispatcher_router

from hans.admin import build_admin
from hans.runtime import register_runtime


app = create_app()

app.include_router(auth_router)
# app.include_router(users_router, tags=["users"])
app.include_router(owners_router, tags=["owners"])
app.include_router(patients_router, tags=["patients"])
app.include_router(orders_router, tags=["orders"])
app.include_router(tests_router, tags=["tests"])
app.include_router(services_router, tags=["services"])
app.include_router(species_router, tags=["species"])
# app.include_router(specimens_router, tags=["specimens"])
app.include_router(tubes_router, tags=["tubes"])
app.include_router(instruments_router, tags=["instruments"])
app.include_router(dispatcher_router, tags=["dispatcher"])

# Register SQLAdmin UI and auth.
build_admin(app)

# Start background services tied to app lifecycle.
register_runtime(app)
