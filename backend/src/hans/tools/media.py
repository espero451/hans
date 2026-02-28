import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException

DATA_ROOT = Path("/app/live/data")
PATIENTS_DIR = DATA_ROOT / "patients"

# BASE_DIR = Path(__file__).resolve().parents[3]
# PATIENTS_DIR = BASE_DIR.parent / "live" / "data" / "patients"

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE = 5 * 1024 * 1024  # 5MB


class MediaService:

    async def save_patient_photo(
        self,
        patient_id: int,
        file: UploadFile,
    ) -> str:

        # 1. MIME validation
        if file.content_type not in ALLOWED_TYPES:
            raise HTTPException(400, "Unsupported file type")

        # 2. Size validation
        # Read into memory once to validate size and write to disk.
        contents = await file.read()
        if len(contents) > MAX_SIZE:
            raise HTTPException(400, "File too large")

        # 3. Create patient folder and deterministic filename.
        patient_dir = PATIENTS_DIR / str(patient_id) / "photos"
        patient_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{patient_id}.jpg"

        # 4. Save file atomically
        file_path = patient_dir / filename
        with open(file_path, "wb") as f:
            f.write(contents)

        # 5. Return relative path
        return f"data/patients/{patient_id}/photos/{filename}"

    def patient_photo_path(self, patient_id: int) -> Path:
        # Deterministic patient photo path.
        return PATIENTS_DIR / str(patient_id) / "photos" / f"{patient_id}.jpg"


    def delete_file(self, relative_path: str):
        full_path = (DATA_ROOT / relative_path.removeprefix("data/")).resolve()

        if not str(full_path).startswith(str(DATA_ROOT.resolve())):
            raise ValueError("Unsafe path")

        if full_path.exists():
            full_path.unlink()

    def _extension_from_mime(self, mime: str) -> str:
        return {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
        }[mime]
