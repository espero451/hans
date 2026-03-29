from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from hans.core.auth import AuthPrincipal, require_admin

from .service import dispatcher_service


# --- Dispatcher API ---------------------------------------------------

router = APIRouter(prefix="/settings/dispatcher")


@router.get("/status")
async def get_dispatcher_status(current_user: AuthPrincipal = Depends(require_admin)) -> dict:
    # Return current dispatcher status for the UI.
    return dispatcher_service.status()


@router.post("/restart")
async def restart_dispatcher(current_user: AuthPrincipal = Depends(require_admin)) -> dict:
    # Restart dispatcher listeners and return status.
    await dispatcher_service.restart()
    return dispatcher_service.status()


@router.get("/trace", response_class=PlainTextResponse)
async def get_dispatcher_trace(current_user: AuthPrincipal = Depends(require_admin)) -> str:
    # Return dispatcher trace output for the UI.
    return dispatcher_service.read_trace()
