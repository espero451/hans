import asyncio
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from hans.patients.models import Species
from hans.specimens.models import SpecimenType
from hans.tubes.models import TubeType


# --- Helpers ----------------------------------------------------------

def _run(coro: Any) -> Any:
    # Execute async seed helpers from sync tests.
    return asyncio.run(coro)


# --- Seed Data --------------------------------------------------------

def _seed_species(setup_session_factory: async_sessionmaker[AsyncSession]) -> int:
    # Insert one active species used by patient payloads.
    async def _seed() -> int:
        async with setup_session_factory() as session:
            species = Species(code="CAN", name="Canine", latin_name="Canis lupus", active=True)
            session.add(species)
            await session.commit()
            await session.refresh(species)
            return int(species.id)

    return _run(_seed())


def _seed_catalogs(setup_session_factory: async_sessionmaker[AsyncSession]) -> int:
    # Insert tube/specimen records for catalog endpoints.
    async def _seed() -> int:
        async with setup_session_factory() as session:
            tube = TubeType(code="SER", name="Serum", description="Serum tube")
            session.add(tube)
            await session.flush()
            specimen = SpecimenType(
                code="BLOOD",
                name="Whole Blood",
                type="blood",
                tube_type_id=int(tube.id),
                description="Whole blood specimen",
            )
            session.add(specimen)
            await session.commit()
            await session.refresh(specimen)
            return int(specimen.id)

    return _run(_seed())


# --- Core Endpoints ---------------------------------------------------

def test_owners_crud_flow(client: TestClient, auth_headers: dict[str, str]) -> None:
    # Validate owner creation, retrieval, listing and deletion.
    create_response = client.post(
        "/owners/",
        headers=auth_headers,
        json={
            "first_name": "Ann",
            "last_name": "Owner",
            "email": "ann@example.com",
            "phone": "+1000000000",
            "comment": "vip",
        },
    )
    assert create_response.status_code == 200
    owner = create_response.json()

    get_response = client.get(f"/owners/{owner['id']}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["email"] == "ann@example.com"

    list_response = client.get("/owners/?limit=10&skip=0", headers=auth_headers)
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["total"] == 1
    assert len(list_data["items"]) == 1

    delete_response = client.delete(f"/owners/{owner['id']}", headers=auth_headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["ok"] is True


def test_patients_create_list_and_get(
    client: TestClient,
    auth_headers: dict[str, str],
    setup_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    # Validate patient endpoints with owner/species references.
    species_id = _seed_species(setup_session_factory)

    owner_response = client.post(
        "/owners/",
        headers=auth_headers,
        json={
            "first_name": "Bob",
            "last_name": "Human",
            "email": "bob@example.com",
            "phone": "+1000000001",
            "comment": None,
        },
    )
    assert owner_response.status_code == 200
    owner_id = owner_response.json()["id"]

    create_response = client.post(
        "/patients/",
        headers=auth_headers,
        json={
            "name": "Rex",
            "species": "Canine",
            "species_id": species_id,
            "owner_id": owner_id,
            "breed": "Labrador",
            "birth_date": "2022-01-01",
            "comment": "friendly",
            "sex": "male",
            "weight": 22.5,
            "microchip_number": "MC-100",
        },
    )
    assert create_response.status_code == 200
    patient = create_response.json()

    list_response = client.get("/patients/?limit=10&skip=0", headers=auth_headers)
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["total"] == 1
    assert list_data["items"][0]["name"] == "Rex"

    get_response = client.get(f"/patients/{patient['id']}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["owner_id"] == owner_id


def test_species_and_dashboard_endpoints(
    client: TestClient,
    auth_headers: dict[str, str],
    setup_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    # Validate species list and dashboard counters contract.
    _seed_species(setup_session_factory)

    species_response = client.get("/species/", headers=auth_headers)
    assert species_response.status_code == 200
    assert len(species_response.json()) == 1

    dashboard_response = client.get("/dashboard/stats", headers=auth_headers)
    assert dashboard_response.status_code == 200
    stats = dashboard_response.json()
    assert stats["total_orders"] == 0
    assert stats["total_patients"] == 0
    assert stats["total_owners"] == 0


def test_staff_catalog_endpoints_require_auth_and_return_data(
    client: TestClient,
    auth_headers: dict[str, str],
    setup_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    # Validate protected catalog endpoints and specimen lookup.
    specimen_id = _seed_catalogs(setup_session_factory)

    unauthorized_tubes = client.get("/tubes/")
    assert unauthorized_tubes.status_code == 401

    tubes_response = client.get("/tubes/", headers=auth_headers)
    assert tubes_response.status_code == 200
    assert len(tubes_response.json()) == 1

    specimen_response = client.get(f"/specimens/{specimen_id}", headers=auth_headers)
    assert specimen_response.status_code == 200
    assert specimen_response.json()["code"] == "BLOOD"


def test_patient_create_rejects_invalid_payload(client: TestClient, auth_headers: dict[str, str]) -> None:
    # Ensure schema validation errors are surfaced as 422.
    response = client.post(
        "/patients/",
        headers=auth_headers,
        json={"name": "Broken"},
    )

    assert response.status_code == 422
