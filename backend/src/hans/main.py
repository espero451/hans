from hans.core.core import create_app

from hans.core.auth import router as auth_router
from hans.owners.routers import router as owners_router
from hans.patients.routers import router as patients_router, species_router
from hans.orders.routers import router as orders_router
from hans.tests.routers import router as tests_router
from hans.services.routers import router as services_router
from hans.specimens.routers import router as specimens_router
from hans.tubes.routers import router as tubes_router
from hans.instruments import router as instruments_router
from hans.dashboard.routers import router as dashboard_router
from hans.interfaces.dispatcher.api import router as dispatcher_router
from fastapi_pagination import add_pagination

from hans.admin import build_admin
from hans.runtime import register_runtime


app = create_app()

app.include_router(auth_router)
app.include_router(owners_router)
app.include_router(patients_router)
app.include_router(orders_router)
app.include_router(tests_router)
app.include_router(services_router)
app.include_router(species_router)
app.include_router(specimens_router)
app.include_router(tubes_router)
app.include_router(dashboard_router)
app.include_router(instruments_router, tags=["instruments"])
app.include_router(dispatcher_router, tags=["dispatcher"])
add_pagination(app)

# Register SQLAdmin UI and auth.
build_admin(app)

# Start background services tied to app lifecycle.
register_runtime(app)
