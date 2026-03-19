import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from hans.patients.models import Species
from hans.specimens.models import SpecimenType
from hans.tubes.models import TubeType


# --- Seed Data --------------------------------------------------------

@pytest_asyncio.fixture()
async def species_id(session_factory: async_sessionmaker[AsyncSession]) -> int:
    # Insert one active species used by patient payloads.
    async with session_factory() as session:
        species = Species(code="CAN", name="Canine", latin_name="Canis lupus", active=True)
        session.add(species)
        await session.commit()
        await session.refresh(species)
        return int(species.id)


@pytest_asyncio.fixture()
async def specimen_id(session_factory: async_sessionmaker[AsyncSession]) -> int:
    # Insert tube/specimen records for catalog endpoints.
    async with session_factory() as session:
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


# --- Core Endpoints ---------------------------------------------------

@pytest.mark.asyncio
async def test_owners_crud_flow(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    # Validate owner creation, retrieval, listing and deletion.
    create_response = await client.post(
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
    assert set(owner.keys()) == {"id", "first_name", "last_name", "email", "phone", "comment"}

    get_response = await client.get(f"/owners/{owner['id']}", headers=auth_headers)
    assert get_response.status_code == 200
    owner_data = get_response.json()
    assert owner_data["email"] == "ann@example.com"
    assert set(owner_data.keys()) == {"id", "first_name", "last_name", "email", "phone", "comment"}

    list_response = await client.get("/owners/?limit=10&skip=0", headers=auth_headers)
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert set(list_data.keys()) == {"items", "total"}
    assert list_data["total"] == 1
    assert len(list_data["items"]) == 1

    delete_response = await client.delete(f"/owners/{owner['id']}", headers=auth_headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["ok"] is True


@pytest.mark.asyncio
async def test_patients_create_list_and_get(
    client: AsyncClient,
    auth_headers: dict[str, str],
    species_id: int,
) -> None:
    # Validate patient endpoints with owner/species references.
    owner_response = await client.post(
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

    create_response = await client.post(
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
    assert set(patient.keys()) >= {"id", "name", "owner_id", "sex", "species_id"}

    list_response = await client.get("/patients/?limit=10&skip=0", headers=auth_headers)
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert set(list_data.keys()) == {"items", "total"}
    assert list_data["total"] == 1
    assert list_data["items"][0]["name"] == "Rex"
    assert isinstance(list_data["items"][0]["owner_id"], int)

    get_response = await client.get(f"/patients/{patient['id']}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["owner_id"] == owner_id


@pytest.mark.asyncio
async def test_species_and_dashboard_endpoints(
    client: AsyncClient,
    auth_headers: dict[str, str],
    species_id: int,
) -> None:
    # Validate species list and dashboard counters contract.
    species_response = await client.get("/species/", headers=auth_headers)
    assert species_response.status_code == 200
    species_data = species_response.json()
    assert len(species_data) == 1
    assert species_data[0]["id"] == species_id

    dashboard_response = await client.get("/dashboard/stats", headers=auth_headers)
    assert dashboard_response.status_code == 200
    stats = dashboard_response.json()
    assert stats["total_orders"] == 0
    assert stats["total_patients"] == 0
    assert stats["total_owners"] == 0


@pytest.mark.asyncio
async def test_staff_catalog_endpoints_require_auth_and_return_data(
    client: AsyncClient,
    auth_headers: dict[str, str],
    specimen_id: int,
) -> None:
    # Validate protected catalog endpoints and specimen lookup.
    unauthorized_tubes = await client.get("/tubes/")
    assert unauthorized_tubes.status_code == 401

    tubes_response = await client.get("/tubes/", headers=auth_headers)
    assert tubes_response.status_code == 200
    assert len(tubes_response.json()) == 1

    specimen_response = await client.get(f"/specimens/{specimen_id}", headers=auth_headers)
    assert specimen_response.status_code == 200
    specimen_data = specimen_response.json()
    assert specimen_data["id"] == specimen_id
    assert specimen_data["code"] == "BLOOD"


@pytest.mark.asyncio
async def test_patient_create_rejects_invalid_payload(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    # Ensure schema validation errors are surfaced as 422.
    response = await client.post(
        "/patients/",
        headers=auth_headers,
        json={"name": "Broken"},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list)


@pytest.mark.asyncio
async def test_empty_pages_for_owners_and_patients(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    # Validate empty page contract when no records exist.
    owners_response = await client.get("/owners/?limit=50&skip=0", headers=auth_headers)
    assert owners_response.status_code == 200
    owners_data = owners_response.json()
    assert owners_data["items"] == []
    assert owners_data["total"] == 0

    patients_response = await client.get("/patients/?limit=50&skip=0", headers=auth_headers)
    assert patients_response.status_code == 200
    patients_data = patients_response.json()
    assert patients_data["items"] == []
    assert patients_data["total"] == 0


@pytest.mark.asyncio
async def test_owners_pagination_edges(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    # Validate pagination boundaries and slicing behavior.
    for first_name in ("Ann", "Bob"):
        response = await client.post(
            "/owners/",
            headers=auth_headers,
            json={
                "first_name": first_name,
                "last_name": "User",
                "email": None,
                "phone": None,
                "comment": None,
            },
        )
        assert response.status_code == 200

    page_one = await client.get("/owners/?limit=1&skip=0", headers=auth_headers)
    assert page_one.status_code == 200
    assert page_one.json()["total"] == 2
    assert len(page_one.json()["items"]) == 1

    page_two = await client.get("/owners/?limit=1&skip=1", headers=auth_headers)
    assert page_two.status_code == 200
    assert page_two.json()["total"] == 2
    assert len(page_two.json()["items"]) == 1


@pytest.mark.asyncio
async def test_invalid_pagination_returns_422(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    # Reject out-of-range pagination values defined by query constraints.
    owners_response = await client.get("/owners/?limit=201&skip=0", headers=auth_headers)
    assert owners_response.status_code == 422

    patients_response = await client.get("/patients/?limit=201&skip=0", headers=auth_headers)
    assert patients_response.status_code == 422


@pytest.mark.asyncio
async def test_owner_missing_resource_returns_404(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    # Return explicit not-found errors for missing owner resources.
    get_response = await client.get("/owners/999999", headers=auth_headers)
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Owner not found"

    delete_response = await client.delete("/owners/999999", headers=auth_headers)
    assert delete_response.status_code == 404
    assert delete_response.json()["detail"] == "Owner not found"


@pytest.mark.asyncio
async def test_patient_missing_resource_returns_404(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    # Return explicit not-found errors for missing patient resources.
    get_response = await client.get("/patients/999999", headers=auth_headers)
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Patient not found"

    delete_response = await client.delete("/patients/999999", headers=auth_headers)
    assert delete_response.status_code == 404
    assert delete_response.json()["detail"] == "Patient not found"
