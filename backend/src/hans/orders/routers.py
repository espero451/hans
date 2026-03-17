from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from hans.core.auth import get_current_user
from hans.core.core import audit_log
from hans.core.db import get_db
from hans.users import User

from .schemas import (
    OrderArchivedStatusRead,
    OrderCreate,
    OrderRead,
    OrderUpdate,
    ResultCreate,
    ResultRead,
    ResultUpdate,
    SpecimenRead,
)
from .services import (
    create_order as create_order_service,
    collect_specimen as collect_specimen_service,
    receive_specimen as receive_specimen_service,
    print_specimen as print_specimen_service,
    create_result as create_result_service,
    get_patient_orders as get_patient_orders_service,
    load_order,
    toggle_order_archive,
    toggle_result_verify,
    update_order as update_order_service,
    update_result as update_result_service,
)


# --- ROUTES -----------------------------------------------------------

router = APIRouter(tags=["orders"])


@router.post("/orders", response_model=OrderRead)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderRead:
    order = await create_order_service(data, db, user.id)
    audit_log(user.id, f"Created order {order.id} for patient {data.patient_id}")
    return order


@router.get("/orders/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderRead:
    return await load_order(order_id, db)


@router.patch("/orders/{order_id}", response_model=OrderRead)
async def update_order(
    order_id: int,
    data: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderRead:
    order = await update_order_service(order_id, data, db)
    audit_log(user.id, f"Updated order {order_id}")
    return order


@router.patch("/orders/{order_id}/archive", response_model=OrderArchivedStatusRead)
async def archive_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderArchivedStatusRead:
    order = await toggle_order_archive(order_id, db)
    audit_log(user.id, f"Order {order_id} archived")
    return order


@router.get("/patients/{patient_id}/orders", response_model=list[OrderRead])
async def get_patient_orders(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[OrderRead]:
    return await get_patient_orders_service(patient_id, db)


# Mark specimen as collected
@router.patch("/orders/barcode/{specimen_id}/collect", response_model=SpecimenRead)
async def collect_specimen(
    specimen_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SpecimenRead:
    specimen = await collect_specimen_service(specimen_id, db)
    audit_log(user.id, f"Specimen collected {specimen_id}")
    return specimen


@router.patch("/orders/barcode/{specimen_id}/receive", response_model=SpecimenRead)
async def receive_specimen(
    specimen_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SpecimenRead:
    specimen = await receive_specimen_service(specimen_id, db)
    audit_log(user.id, f"Specimen received {specimen_id}")
    return specimen


@router.patch("/orders/barcode/{specimen_id}/print", response_model=SpecimenRead)
async def print_specimen(
    specimen_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SpecimenRead:
    specimen = await print_specimen_service(specimen_id, db)
    audit_log(user.id, f"Specimen {specimen_id} barcode printed")
    return specimen


@router.post("/test-runs/{test_run_id}/results", response_model=ResultRead)
async def create_result(
    test_run_id: int,
    data: ResultCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResultRead:
    result = await create_result_service(test_run_id, data, db)
    audit_log(user.id, f"Created result {result.id} for test_run {test_run_id}")
    return result


@router.patch("/results/{result_id}", response_model=ResultRead)
async def update_result(
    result_id: int,
    data: ResultUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResultRead:
    result = await update_result_service(result_id, data, db)
    audit_log(user.id, f"Updated result {result_id}")
    return result


@router.post("/results/{result_id}/verify", response_model=ResultRead)
async def verify_result(
    result_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResultRead:
    result = await toggle_result_verify(result_id, user.id, db)
    action = "verified" if result.verified else "unverified"
    audit_log(user.id, f"Result {result_id} {action}")
    return result
