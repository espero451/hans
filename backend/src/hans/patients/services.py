from pathlib import Path

from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from hans.tools.media import MediaService

from .models import Patient
from .repositories import fetch_patient, fetch_patients, fetch_species, count_patients
from .schemas import PatientCreate, PatientRead, PatientUpdate, SpeciesRead


# --- SERVICE STATE ----------------------------------------------------

media_service = MediaService()


# --- SPECIES FLOWS ----------------------------------------------------

async def get_species(db: AsyncSession) -> list[SpeciesRead]:
    species = await fetch_species(db)
    return [SpeciesRead.model_validate(item) for item in species]


# --- PATIENT FLOWS ----------------------------------------------------

# async def get_patients(skip: int, limit: int, db: AsyncSession) -> list[PatientRead]:
    # patients = await fetch_patients(skip, limit, db)
    # return [PatientRead.model_validate(item) for item in patients]


async def get_patients(
    skip: int,
    limit: int,
    q: str | None,
    species_id: int | None,
    owner_id: int | None,
    db: AsyncSession,
) -> tuple[list[PatientRead], int]:
    patients = await fetch_patients(skip, limit, q, species_id, owner_id, db)
    total = await count_patients(q, species_id, owner_id, db)
    items = [PatientRead.model_validate(p) for p in patients]
    return items, total


async def get_patient(patient_id: int, db: AsyncSession) -> PatientRead:
    patient = await fetch_patient_or_404(patient_id, db)
    return PatientRead.model_validate(patient)


async def create_patient(data: PatientCreate, db: AsyncSession) -> PatientRead:
    patient = Patient(**data.dict())
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return PatientRead.model_validate(patient)


async def update_patient(patient_id: int, data: PatientCreate, db: AsyncSession) -> PatientRead:
    patient = await fetch_patient_or_404(patient_id, db)
    # Replace patient fields with provided payload values.
    for key, value in data.dict().items():
        setattr(patient, key, value)
    await db.commit()
    await db.refresh(patient)
    return PatientRead.model_validate(patient)


async def patch_patient(patient_id: int, data: PatientUpdate, db: AsyncSession) -> PatientRead:
    patient = await fetch_patient_or_404(patient_id, db)
    # Apply only fields provided by the partial payload.
    for key, value in data.dict(exclude_unset=True).items():
        setattr(patient, key, value)
    await db.commit()
    await db.refresh(patient)
    return PatientRead.model_validate(patient)


async def delete_patient(patient_id: int, db: AsyncSession) -> None:
    patient = await fetch_patient_or_404(patient_id, db)
    await db.delete(patient)
    await db.commit()


# --- PATIENT MEDIA ----------------------------------------------------

async def upload_patient_photo(patient_id: int, file: UploadFile, db: AsyncSession) -> str:
    await fetch_patient_or_404(patient_id, db)
    return await media_service.save_patient_photo(patient_id, file)


async def get_patient_photo(patient_id: int, db: AsyncSession) -> FileResponse:
    await fetch_patient_or_404(patient_id, db)
    photo_path = media_service.patient_photo_path(patient_id)
    if not photo_path.exists():
        raise HTTPException(404, "Patient photo not found")
    return FileResponse(str(photo_path), media_type="image/jpeg")


# --- HELPERS ----------------------------------------------------------

async def fetch_patient_or_404(patient_id: int, db: AsyncSession) -> Patient:
    patient = await fetch_patient(patient_id, db)
    if not patient:
        raise HTTPException(404, "Patient not found")
    return patient
