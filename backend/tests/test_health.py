import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ping(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/ping")
    assert response.status_code == 200
    assert response.json()["pong"] is True


@pytest.mark.asyncio
async def test_health_check_structure(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "components" in data
    assert "database" in data["components"]
    assert "redis" in data["components"]


@pytest.mark.asyncio
async def test_health_db_component(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    data = response.json()
    db = data["components"]["database"]
    assert isinstance(db["ok"], bool)
    assert "latency_ms" in db
