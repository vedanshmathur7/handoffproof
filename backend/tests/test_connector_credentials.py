import logging
from collections.abc import AsyncIterator, Generator
from typing import Any
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.main import app
from app.models import Connector, Workspace
from app.services.credentials import decrypt_credential

engine = create_engine(get_settings().database_url)
TOKEN = "tfp_fake-token-for-tests-0123456789"
FIELD_REFS = {
    name: f"ref_{name}"
    for name in ("email", "full_name", "company", "region", "transfer_enabled")
}


@pytest.fixture(autouse=True)
def encryption_key(monkeypatch: pytest.MonkeyPatch) -> Generator[str, None, None]:
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("CONNECTOR_ENCRYPTION_KEYS", key)
    get_settings.cache_clear()
    yield key
    get_settings.cache_clear()
    with Session(engine) as session:
        session.execute(delete(Workspace).where(Workspace.name.like("test-cred-%")))
        session.commit()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as test_client:
        yield test_client


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def workspace(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/workspaces", json={"name": f"test-cred-{uuid4()}"}
    )
    return str(response.json()["id"])


def typeform_body(workspace_id: str, **overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "workspace_id": workspace_id,
        "provider": "typeform",
        "name": "Lead form",
        "token": TOKEN,
        "typeform": {"form_id": "abc123XY", "field_refs": FIELD_REFS},
    }
    body.update(overrides)
    return body


def stored_connector(connector_id: str) -> Connector:
    with Session(engine) as session:
        connector = session.scalar(
            select(Connector).where(Connector.id == connector_id)
        )
        assert connector is not None
        session.expunge(connector)
        return connector


@pytest.mark.anyio
async def test_credentials_are_encrypted_and_never_returned_or_logged(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    workspace_id = await workspace(client)

    created = await client.post("/api/v1/connectors", json=typeform_body(workspace_id))
    listed = await client.get(
        "/api/v1/connectors", params={"workspace_id": workspace_id}
    )

    assert created.status_code == 201, created.text
    body = created.json()
    assert body["kind"] == "source"
    assert body["credential_configured"] is True
    assert body["config"] == {"form_id": "abc123XY", "field_refs": FIELD_REFS}
    assert "token" not in body
    assert TOKEN not in created.text
    assert TOKEN not in listed.text
    assert [item["id"] for item in listed.json()] == [body["id"]]

    stored = stored_connector(body["id"])
    assert TOKEN.encode() not in stored.encrypted_credential
    assert "redacted" in repr(stored)
    assert decrypt_credential(stored.encrypted_credential) == TOKEN
    assert TOKEN not in caplog.text


@pytest.mark.anyio
async def test_validation_errors_do_not_echo_tokens(client: AsyncClient) -> None:
    workspace_id = await workspace(client)

    hubspot_with_form = await client.post(
        "/api/v1/connectors",
        json=typeform_body(workspace_id, provider="hubspot"),
    )
    bad_refs = await client.post(
        "/api/v1/connectors",
        json=typeform_body(
            workspace_id,
            typeform={"form_id": "abc123XY", "field_refs": {"email": "e"}},
        ),
    )
    schema_error = await client.post(
        "/api/v1/connectors", json=typeform_body(workspace_id, name="")
    )

    assert hubspot_with_form.json()["code"] == "CONNECTOR_CONFIG_INVALID"
    assert bad_refs.json()["code"] == "CONNECTOR_CONFIG_INVALID"
    assert "company" in bad_refs.json()["details"]["missing"]
    assert schema_error.json()["code"] == "REQUEST_VALIDATION_ERROR"
    for response in (hubspot_with_form, bad_refs, schema_error):
        assert response.status_code == 422
        assert TOKEN not in response.text


@pytest.mark.anyio
async def test_connectors_are_workspace_scoped(client: AsyncClient) -> None:
    owner = await workspace(client)
    other = await workspace(client)
    created = await client.post(
        "/api/v1/connectors",
        json={
            "workspace_id": owner,
            "provider": "hubspot",
            "name": "CRM",
            "token": TOKEN,
        },
    )
    connector_id = created.json()["id"]

    other_list = await client.get("/api/v1/connectors", params={"workspace_id": other})
    cross_replace = await client.put(
        f"/api/v1/connectors/{connector_id}/credential",
        json={"workspace_id": other, "token": "pat-another-fake-token"},
    )
    duplicate = await client.post(
        "/api/v1/connectors",
        json={
            "workspace_id": owner,
            "provider": "hubspot",
            "name": "CRM",
            "token": TOKEN,
        },
    )

    assert created.json()["kind"] == "destination"
    assert other_list.json() == []
    assert cross_replace.status_code == 404
    assert cross_replace.json()["code"] == "CONNECTOR_NOT_FOUND"
    assert duplicate.status_code == 409
    assert (
        decrypt_credential(stored_connector(connector_id).encrypted_credential) == TOKEN
    )


@pytest.mark.anyio
async def test_credentials_rotate_with_keys_and_require_configuration(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, encryption_key: str
) -> None:
    workspace_id = await workspace(client)
    created = await client.post(
        "/api/v1/connectors",
        json={
            "workspace_id": workspace_id,
            "provider": "hubspot",
            "name": "CRM",
            "token": TOKEN,
        },
    )
    connector_id = created.json()["id"]

    monkeypatch.setenv(
        "CONNECTOR_ENCRYPTION_KEYS",
        f"{Fernet.generate_key().decode()},{encryption_key}",
    )
    get_settings.cache_clear()
    assert (
        decrypt_credential(stored_connector(connector_id).encrypted_credential) == TOKEN
    )
    replaced = await client.put(
        f"/api/v1/connectors/{connector_id}/credential",
        json={"workspace_id": workspace_id, "token": "pat-rotated-fake-token"},
    )
    assert replaced.status_code == 200
    assert "pat-rotated-fake-token" not in replaced.text

    monkeypatch.setenv("CONNECTOR_ENCRYPTION_KEYS", "")
    get_settings.cache_clear()
    missing_key = await client.post(
        "/api/v1/connectors",
        json={
            "workspace_id": workspace_id,
            "provider": "hubspot",
            "name": "CRM 2",
            "token": TOKEN,
        },
    )
    assert missing_key.status_code == 503
    assert missing_key.json()["code"] == "CONNECTOR_ENCRYPTION_NOT_CONFIGURED"
    other = await client.get(
        "/api/v1/connectors", params={"workspace_id": workspace_id}
    )
    assert [item["name"] for item in other.json()] == ["CRM"]
