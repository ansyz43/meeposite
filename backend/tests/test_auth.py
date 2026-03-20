"""Tests for health endpoint, registration, and login."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    # Register
    resp = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "secret123",
        "name": "Test User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data

    # Duplicate registration
    resp2 = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "secret123",
        "name": "Test User",
    })
    assert resp2.status_code == 400

    # Login
    resp3 = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "secret123",
    })
    assert resp3.status_code == 200
    assert "access_token" in resp3.json()

    # Wrong password
    resp4 = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword",
    })
    assert resp4.status_code == 401


@pytest.mark.asyncio
async def test_profile_requires_auth(client: AsyncClient):
    resp = await client.get("/api/profile")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_register_validation(client: AsyncClient):
    # Too short password
    resp = await client.post("/api/auth/register", json={
        "email": "user@example.com",
        "password": "12345",
        "name": "User",
    })
    assert resp.status_code == 422

    # Invalid email
    resp2 = await client.post("/api/auth/register", json={
        "email": "not-an-email",
        "password": "secret123",
        "name": "User",
    })
    assert resp2.status_code == 422
