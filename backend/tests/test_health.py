import pytest
from httpx import ASGITransport, AsyncClient

from app.api.health import check_database
from app.main import app


async def database_is_ready() -> bool:
    return True


async def database_is_unavailable() -> bool:
    return False


@pytest.mark.anyio
async def test_health_reports_ready_process_and_database() -> None:
    app.dependency_overrides[check_database] = database_is_ready
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "process": "ready",
        "database": "ready",
    }


@pytest.mark.anyio
async def test_health_reports_degraded_when_database_is_unavailable() -> None:
    app.dependency_overrides[check_database] = database_is_unavailable
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "status": "degraded",
        "process": "ready",
        "database": "unavailable",
    }


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
