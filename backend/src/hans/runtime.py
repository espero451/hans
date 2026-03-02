from fastapi import FastAPI

from hans.interfaces.dispatcher.service import dispatcher_service


# --- Runtime ----------------------------------------------------------

def register_runtime(app: FastAPI) -> None:
    # Register lifecycle hooks for background services.
    @app.on_event("startup")
    async def _start_dispatcher() -> None:
        # Start dispatcher listeners on app startup.
        await dispatcher_service.start()

    @app.on_event("shutdown")
    async def _stop_dispatcher() -> None:
        # Stop dispatcher listeners on app shutdown.
        await dispatcher_service.stop()
