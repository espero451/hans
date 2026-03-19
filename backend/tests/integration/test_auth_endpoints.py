import pytest
from httpx import AsyncClient


# --- Auth Endpoints ---------------------------------------------------

@pytest.mark.asyncio
async def test_login_and_me_success(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    # Confirm that /auth/me accepts a valid access token.
    response = await client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_login_rejects_invalid_password(client: AsyncClient, admin_user: object) -> None:
    # Reject invalid credentials and keep response contract stable.
    response = await client.post(
        "/auth/token",
        data={"username": "admin", "password": "wrong-pass"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_refresh_rotates_tokens(client: AsyncClient, admin_user: object) -> None:
    # Verify refresh returns a new token pair and token type.
    login_response = await client.post(
        "/auth/token",
        data={"username": "admin", "password": "adminpass"},
    )
    assert login_response.status_code == 200

    refresh_response = await client.post(
        "/auth/refresh",
        json={"refresh_token": login_response.json()["refresh_token"]},
    )

    assert refresh_response.status_code == 200
    payload = refresh_response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["refresh_token"]


@pytest.mark.asyncio
async def test_me_requires_token(client: AsyncClient) -> None:
    # Block unauthenticated access to protected endpoint.
    response = await client.get("/auth/me")

    assert response.status_code == 401
