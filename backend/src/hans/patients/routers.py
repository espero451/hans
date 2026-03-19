from fastapi import APIRouter, Depends, File, UploadFile, Query
from sqlalchemy.ext.asyncio import AsyncSession

from hans.core.auth import get_current_principal, get_current_user
from hans.core.core import audit_log
from hans.core.db import get_db
from hans.users import User
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

from .schemas import PatientCreate, PatientRead, PatientUpdate, SpeciesRead
from .services import (
    create_patient as create_patient_service,
    delete_patient as delete_patient_service,
    get_patient as get_patient_service,
    get_patient_photo as get_patient_photo_service,
    get_patients as get_patients_service,
    get_species as get_species_service,
    patch_patient as patch_patient_service,
    update_patient as update_patient_service,
    upload_patient_photo as upload_patient_photo_service,
)


# --- ROUTES -----------------------------------------------------------

router = APIRouter(prefix="/patients", tags=["patients"])
species_router = APIRouter(prefix="/species", tags=["species"])


@species_router.get("/", response_model=list[SpeciesRead])
async def get_species(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_principal),
) -> list[SpeciesRead]:
    return await get_species_service(db)


# @router.get("/", response_model=list[PatientRead])
# async def get_patients(
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user),
#     skip: int = 0,
#     limit: int = 100,
# ) -> list[PatientRead]:
#     return await get_patients_service(skip, limit, db)

@router.get("/", response_model=Page[PatientRead])
async def get_patients(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    params: Params = Depends(),
    q: str | None = Query(None, min_length=1),
    species_id: int | None = Query(None, ge=1),
    owner_id: int | None = Query(None, ge=1),
) -> Page[PatientRead]:
    query = await get_patients_service(q, species_id, owner_id)
    return await paginate(db, query, params=params)


@router.post("/", response_model=PatientRead)
async def create_patient(
    data: PatientCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PatientRead:
    patient = await create_patient_service(data, db)
    audit_log(user.id, f"Created patient {patient.id}")
    return patient


@router.put("/{patient_id}", response_model=PatientRead)
async def update_patient(
    patient_id: int,
    data: PatientCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PatientRead:
    patient = await update_patient_service(patient_id, data, db)
    audit_log(user.id, f"Updated patient {patient_id}")
    return patient


@router.patch("/{patient_id}", response_model=PatientRead)
async def patch_patient(
    patient_id: int,
    data: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PatientRead:
    patient = await patch_patient_service(patient_id, data, db)
    audit_log(user.id, f"Patched patient {patient_id}")
    return patient


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, bool]:
    await delete_patient_service(patient_id, db)
    audit_log(user.id, f"Deleted patient {patient_id}")
    return {"ok": True}


@router.get("/{patient_id}", response_model=PatientRead)
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PatientRead:
    return await get_patient_service(patient_id, db)


@router.post("/{patient_id}/photo")
async def upload_patient_photo(
    patient_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    relative_path = await upload_patient_photo_service(patient_id, file, db)
    audit_log(user.id, f"Uploaded photo for patient {patient_id}")
    return {"path": relative_path}


@router.get("/{patient_id}/photo")
async def get_patient_photo(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_patient_photo_service(patient_id, db)
