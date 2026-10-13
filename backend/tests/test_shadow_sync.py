from collections.abc import AsyncIterator, Callable, Generator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from app.config import get_settings
from app.connectors.hubspot import HubSpotConnector
from app.connectors.typeform import TypeformConnector
from app.main import app
from app.models import ConnectorSync, CoverageStatus, Workspace
from app.services.shadow_sync import ConnectorClients, get_connector_clients

engine = create_engine(get_settings().database_url)
TYPEFORM_TOKEN = "tfp_fake-typeform-token-0001"
HUBSPOT_TOKEN = "pat-fake-hubspot-token-0001"
FIELDS = ("email", "full_name", "company", "region", "transfer_enabled")
Handler = Callable[[httpx.Request], httpx.Response]


async def no_sleep(_seconds: float) -> None:
    return None


def typeform_item(
    response_id: str, email: str, submitted_at: datetime
) -> dict[str, Any]:
    return {
        "response_id": response_id,
        "token": response_id,
        "submitted_at": submitted_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "answers": [
            {"field": {"ref": "ref_email"}, "email": email},
            {"field": {"ref": "ref_full_name"}, "text": "Ada Lovelace"},
            {"field": {"ref": "ref_company"}, "text": "Analytical Engines"},
            {"field": {"ref": "ref_region"}, "text": "IN"},
            {"field": {"ref": "ref_transfer_enabled"}, "boolean": True},
        ],
    }


def hubspot_contact(
    contact_id: str, email: str, created_at: datetime
) -> dict[str, Any]:
    return {
        "id": contact_id,
        "createdAt": created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "properties": {
            "email": email,
            "firstname": "Ada",
            "lastname": "Lovelace",
            "company": "Analytical Engines",
            "region": "IN",
        },
    }


class FakeProviders:
    def __init__(self) -> None:
        submitted = datetime.now(UTC) - timedelta(hours=3)
        self.typeform_items = [
            typeform_item("tf-1", "ada@example.test", submitted),
            typeform_item("tf-2", "grace@example.test", submitted),
        ]
        self.hubspot_pages: list[dict[str, Any] | int] = [
            {"results": [hubspot_contact("hs-1", "ada@example.test", submitted)]}
        ]
        self.typeform_status = 200
        self.requests: list[httpx.Request] = []

    def typeform(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.typeform_status != 200:
            return httpx.Response(self.typeform_status, json={"message": "no"})
        return httpx.Response(200, json={"items": self.typeform_items})

    def hubspot(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        index = sum(r.url.host == "api.hubapi.com" for r in self.requests) - 1
        page = self.hubspot_pages[min(index, len(self.hubspot_pages) - 1)]
        if isinstance(page, int):
            return httpx.Response(page, json={"message": "slow down"})
        return httpx.Response(200, json=page)

    def clients(self) -> ConnectorClients:
        return ConnectorClients(
            typeform=lambda token: TypeformConnector(
                token, transport=httpx.MockTransport(self.typeform), sleep=no_sleep
            ),
            hubspot=lambda token: HubSpotConnector(
                token, transport=httpx.MockTransport(self.hubspot), sleep=no_sleep
            ),
        )


@pytest.fixture(autouse=True)
def environment(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    monkeypatch.setenv("CONNECTOR_ENCRYPTION_KEYS", Fernet.generate_key().decode())
    get_settings.cache_clear()
    yield
    app.dependency_overrides.pop(get_connector_clients, None)
    get_settings.cache_clear()
    with Session(engine) as session:
        session.execute(delete(Workspace).where(Workspace.name.like("test-shadow-%")))
        session.commit()


@pytest.fixture
def providers() -> FakeProviders:
    fake = FakeProviders()
    app.dependency_overrides[get_connector_clients] = fake.clients
    return fake


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as test_client:
        yield test_client


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def setup_connectors(client: AsyncClient) -> dict[str, str]:
    workspace = await client.post(
        "/api/v1/workspaces", json={"name": f"test-shadow-{uuid4()}"}
    )
    workspace_id = str(workspace.json()["id"])
    source = await client.post(
        "/api/v1/connectors",
        json={
            "workspace_id": workspace_id,
            "provider": "typeform",
            "name": "Lead form",
            "token": TYPEFORM_TOKEN,
            "typeform": {
                "form_id": "abc123XY",
                "field_refs": {name: f"ref_{name}" for name in FIELDS},
            },
        },
    )
    destination = await client.post(
        "/api/v1/connectors",
        json={
            "workspace_id": workspace_id,
            "provider": "hubspot",
            "name": "CRM",
            "token": HUBSPOT_TOKEN,
        },
    )
    assert source.status_code == destination.status_code == 201
    return {
        "workspace_id": workspace_id,
        "source_connector_id": str(source.json()["id"]),
        "destination_connector_id": str(destination.json()["id"]),
    }


async def shadow_sync(
    client: AsyncClient, ids: dict[str, str], **extra: Any
) -> httpx.Response:
    return await client.post("/api/v1/shadow-syncs", json={**ids, **extra})


@pytest.mark.anyio
async def test_shadow_sync_reads_only_and_feeds_the_same_engine(
    client: AsyncClient, providers: FakeProviders
) -> None:
    ids = await setup_connectors(client)

    response = await shadow_sync(client, ids)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["coverage"] == "complete"
    assert body["source"]["record_count"] == 2
    assert body["destination"]["record_count"] == 1
    assert body["source"]["checkpoint_before"] is None
    assert body["source"]["checkpoint_after"] is not None
    assert body["evaluated_at"] == body["destination"]["started_at"]
    assert all(request.method == "GET" for request in providers.requests)
    auth = {r.url.host: r.headers["Authorization"] for r in providers.requests}
    assert auth == {
        "api.typeform.com": f"Bearer {TYPEFORM_TOKEN}",
        "api.hubapi.com": f"Bearer {HUBSPOT_TOKEN}",
    }
    assert TYPEFORM_TOKEN not in response.text and HUBSPOT_TOKEN not in response.text
    # Typeform is read before HubSpot so the destination is never the older snapshot.
    assert providers.requests[0].url.host == "api.typeform.com"

    workspace_id = ids["workspace_id"]
    rule = await client.post(
        "/api/v1/rules",
        json={
            "workspace_id": workspace_id,
            "source_import_id": body["source"]["import_id"],
            "destination_import_id": body["destination"]["import_id"],
            "name": "Live shadow handoff",
            "eligibility": {"field": "transfer_enabled", "equals": "true"},
            "identity_field": "email",
            "required_fields": ["full_name", "company", "region"],
            "wait_seconds": 300,
            "timezone": "UTC",
        },
    )
    run = await client.post(
        "/api/v1/reconciliations",
        json={
            "workspace_id": workspace_id,
            "source_import_id": body["source"]["import_id"],
            "destination_import_id": body["destination"]["import_id"],
            "rule_id": rule.json()["id"],
            "idempotency_key": "shadow-1",
            "evaluated_at": body["evaluated_at"],
        },
    )
    assert run.status_code == 201, run.text
    counts = run.json()["result_counts"]
    assert counts["matched"] == 1
    assert counts["missing"] == 1
    assert counts["unknown"] == 0


@pytest.mark.anyio
async def test_checkpoint_persists_and_only_advances_after_complete_reads(
    client: AsyncClient, providers: FakeProviders
) -> None:
    ids = await setup_connectors(client)
    first = (await shadow_sync(client, ids)).json()
    checkpoint = datetime.fromisoformat(first["source"]["checkpoint_after"])

    providers.requests.clear()
    second = (await shadow_sync(client, ids)).json()
    since = providers.requests[0].url.params["since"]
    assert since == (checkpoint - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S")
    assert second["source"]["checkpoint_before"] == first["source"]["checkpoint_after"]
    assert datetime.fromisoformat(second["source"]["checkpoint_after"]) >= checkpoint

    providers.typeform_status = 401
    failed = (await shadow_sync(client, ids)).json()
    assert failed["source"]["coverage"] == "failed"
    assert failed["source"]["issues"] == ["CONNECTOR_AUTH_FAILED"]
    assert failed["source"]["checkpoint_after"] is None
    assert failed["coverage"] == "failed"

    history = await client.get(
        f"/api/v1/connectors/{ids['source_connector_id']}/syncs",
        params={"workspace_id": ids["workspace_id"]},
    )
    assert [item["coverage"] for item in history.json()] == [
        "failed",
        "complete",
        "complete",
    ]


@pytest.mark.anyio
async def test_destination_throttling_makes_every_result_unknown(
    client: AsyncClient, providers: FakeProviders
) -> None:
    submitted = datetime.now(UTC) - timedelta(hours=3)
    providers.hubspot_pages = [
        {
            "results": [hubspot_contact("hs-1", "ada@example.test", submitted)],
            "paging": {"next": {"after": "cursor-1"}},
        },
        429,
    ]
    ids = await setup_connectors(client)

    body = (await shadow_sync(client, ids)).json()

    assert body["destination"]["coverage"] == "partial"
    assert body["destination"]["issues"] == ["CONNECTOR_THROTTLED"]
    assert body["destination"]["checkpoint_after"] is None
    assert body["coverage"] == "partial"
    rule = await client.post(
        "/api/v1/rules",
        json={
            "workspace_id": ids["workspace_id"],
            "source_import_id": body["source"]["import_id"],
            "destination_import_id": body["destination"]["import_id"],
            "name": "Throttled",
            "eligibility": {"field": "transfer_enabled", "equals": "true"},
            "identity_field": "email",
            "required_fields": ["full_name"],
            "wait_seconds": 0,
            "timezone": "UTC",
        },
    )
    run = await client.post(
        "/api/v1/reconciliations",
        json={
            "workspace_id": ids["workspace_id"],
            "source_import_id": body["source"]["import_id"],
            "destination_import_id": body["destination"]["import_id"],
            "rule_id": rule.json()["id"],
            "idempotency_key": "shadow-throttled",
            "evaluated_at": body["evaluated_at"],
        },
    )
    counts = run.json()["result_counts"]
    assert counts["unknown"] == 2
    assert counts["matched"] == counts["missing"] == 0


@pytest.mark.anyio
async def test_stale_watermark_is_partial_until_full_resync(
    client: AsyncClient, providers: FakeProviders
) -> None:
    ids = await setup_connectors(client)
    stale = datetime.now(UTC) - timedelta(days=8)
    with Session(engine) as session:
        session.add(
            ConnectorSync(
                workspace_id=UUID(ids["workspace_id"]),
                connector_id=UUID(ids["source_connector_id"]),
                coverage=CoverageStatus.COMPLETE,
                record_count=0,
                issues=[],
                checkpoint_after=stale,
                started_at=stale,
                completed_at=stale,
            )
        )
        session.commit()

    stale_read = (await shadow_sync(client, ids)).json()
    providers.requests.clear()
    resync = (await shadow_sync(client, ids, full_resync=True)).json()

    assert stale_read["source"]["coverage"] == "partial"
    assert stale_read["source"]["issues"] == ["CONNECTOR_WATERMARK_STALE"]
    assert stale_read["source"]["checkpoint_after"] is None
    assert stale_read["coverage"] == "partial"
    assert "since" not in providers.requests[0].url.params
    assert resync["source"]["coverage"] == "complete"
    assert resync["source"]["checkpoint_before"] is None
    assert datetime.fromisoformat(resync["source"]["checkpoint_after"]) > stale


@pytest.mark.anyio
async def test_shadow_sync_is_workspace_scoped_and_role_checked(
    client: AsyncClient, providers: FakeProviders
) -> None:
    ids = await setup_connectors(client)
    other = await setup_connectors(client)

    cross = await shadow_sync(
        client, {**ids, "destination_connector_id": other["destination_connector_id"]}
    )
    swapped = await shadow_sync(
        client,
        {
            **ids,
            "source_connector_id": ids["destination_connector_id"],
            "destination_connector_id": ids["source_connector_id"],
        },
    )
    history = await client.get(
        f"/api/v1/connectors/{ids['source_connector_id']}/syncs",
        params={"workspace_id": other["workspace_id"]},
    )

    assert cross.status_code == 404
    assert cross.json()["code"] == "CONNECTOR_NOT_FOUND"
    assert swapped.status_code == 422
    assert swapped.json()["code"] == "CONNECTOR_ROLE_INVALID"
    assert history.status_code == 404
    assert providers.requests == []
