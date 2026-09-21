from collections.abc import AsyncIterator, Generator
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.main import app
from app.models import Observation, Rule, Workspace

FIXTURES = Path(__file__).parent / "fixtures"
engine = create_engine(get_settings().database_url)


@pytest.fixture(autouse=True)
def remove_api_test_workspaces() -> Generator[None, None, None]:
    yield
    with Session(engine) as session:
        session.execute(delete(Workspace).where(Workspace.name.like("test-api-%")))
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


async def create_workspace(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/workspaces", json={"name": f"test-api-{uuid4()}"}
    )
    assert response.status_code == 201
    return str(response.json()["id"])


async def upload_fixture(
    client: AsyncClient,
    workspace_id: str,
    kind: str,
    filename: str,
    coverage: str = "complete",
) -> dict[str, Any]:
    content = (FIXTURES / filename).read_bytes()
    response = await client.post(
        f"/api/v1/imports/{kind}",
        data={"workspace_id": workspace_id, "coverage": coverage},
        files={"file": (filename, content, "text/csv")},
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


@pytest.mark.anyio
async def test_valid_fixtures_import_with_exact_counts_and_evidence(
    client: AsyncClient,
) -> None:
    workspace_id = await create_workspace(client)
    source = await upload_fixture(client, workspace_id, "source", "source.csv")
    destination = await upload_fixture(
        client, workspace_id, "destination", "destination.csv"
    )

    assert (source["total_rows"], source["accepted_rows"], source["rejected_rows"]) == (
        6,
        6,
        0,
    )
    assert source["coverage"] == "complete"
    assert destination["total_rows"] == 4
    assert destination["accepted_rows"] == 4

    with Session(engine) as session:
        observation = session.scalar(
            select(Observation).where(
                Observation.workspace_id == UUID(workspace_id),
                Observation.external_record_id == "SRC_MATCH",
            )
        )
        assert observation is not None
        assert observation.original_evidence["email"] == "match@example.test"
        assert observation.normalized_data["email"] == "match@example.test"
        assert observation.observed_at is not None


@pytest.mark.anyio
async def test_malformed_rows_are_preserved_with_stable_errors(
    client: AsyncClient,
) -> None:
    workspace_id = await create_workspace(client)
    result = await upload_fixture(
        client, workspace_id, "source", "malformed_source.csv"
    )

    assert result["status"] == "failed"
    assert result["coverage"] == "failed"
    assert result["accepted_rows"] == 0
    assert result["rejected_rows"] == 4
    assert [error["code"] for error in result["row_errors"]] == [
        "MISSING_SOURCE_RECORD_ID",
        "INVALID_SUBMITTED_AT",
        "INVALID_EMAIL",
        "INVALID_TRANSFER_ENABLED",
    ]


@pytest.mark.anyio
async def test_partial_coverage_and_duplicate_rows_are_reported(
    client: AsyncClient,
) -> None:
    workspace_id = await create_workspace(client)
    partial = await upload_fixture(
        client,
        workspace_id,
        "destination",
        "partial_destination.csv",
        coverage="partial",
    )
    assert partial["coverage"] == "partial"

    duplicate_csv = (FIXTURES / "source.csv").read_text().splitlines()
    content = "\n".join([duplicate_csv[0], duplicate_csv[1], duplicate_csv[1]])
    response = await client.post(
        "/api/v1/imports/source",
        data={"workspace_id": workspace_id},
        files={"file": ("duplicates.csv", content, "text/csv")},
    )
    assert response.status_code == 201
    assert response.json()["duplicate_rows"] == 1
    assert response.json()["coverage"] == "partial"


@pytest.mark.anyio
async def test_file_contract_errors_have_stable_codes(client: AsyncClient) -> None:
    workspace_id = await create_workspace(client)
    wrong_type = await client.post(
        "/api/v1/imports/source",
        data={"workspace_id": workspace_id},
        files={"file": ("source.txt", b"hello", "text/plain")},
    )
    assert wrong_type.status_code == 415
    assert wrong_type.json()["code"] == "CSV_FILE_TYPE_INVALID"

    missing_headers = await client.post(
        "/api/v1/imports/source",
        data={"workspace_id": workspace_id},
        files={"file": ("source.csv", b"email\na@example.test\n", "text/csv")},
    )
    assert missing_headers.status_code == 422
    assert missing_headers.json()["code"] == "CSV_MISSING_HEADERS"

    oversized = await client.post(
        "/api/v1/imports/source",
        data={"workspace_id": workspace_id},
        files={"file": ("source.csv", b"x" * 1_000_001, "text/csv")},
    )
    assert oversized.status_code == 413
    assert oversized.json()["code"] == "CSV_FILE_TOO_LARGE"


@pytest.mark.anyio
async def test_import_is_idempotent_and_workspace_scoped(client: AsyncClient) -> None:
    workspace_id = await create_workspace(client)
    other_workspace_id = await create_workspace(client)
    content = (FIXTURES / "source.csv").read_bytes()
    first = await client.post(
        "/api/v1/imports/source",
        data={"workspace_id": workspace_id},
        files={"file": ("source.csv", content, "text/csv")},
    )
    second = await client.post(
        "/api/v1/imports/source",
        data={"workspace_id": workspace_id},
        files={"file": ("source.csv", content, "text/csv")},
    )
    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]

    hidden = await client.get(
        f"/api/v1/imports/{first.json()['id']}",
        params={"workspace_id": other_workspace_id},
    )
    assert hidden.status_code == 404
    assert hidden.json()["code"] == "IMPORT_NOT_FOUND"


@pytest.mark.anyio
async def test_rules_validate_fields_and_create_immutable_versions(
    client: AsyncClient,
) -> None:
    workspace_id = await create_workspace(client)
    source = await upload_fixture(client, workspace_id, "source", "source.csv")
    destination = await upload_fixture(
        client, workspace_id, "destination", "destination.csv"
    )
    payload = {
        "workspace_id": workspace_id,
        "source_import_id": source["id"],
        "destination_import_id": destination["id"],
        "name": "Email handoff",
        "eligibility": {"field": "transfer_enabled", "equals": "true"},
        "identity_field": "email",
        "required_fields": ["full_name", "company", "region"],
        "wait_seconds": 300,
        "timezone": "Asia/Kolkata",
    }
    first = await client.post("/api/v1/rules", json=payload)
    second = await client.post(
        "/api/v1/rules", json={**payload, "name": "Email handoff v2"}
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["version"] == 1
    assert second.json()["version"] == 2
    assert first.json()["id"] != second.json()["id"]

    invalid = await client.post(
        "/api/v1/rules", json={**payload, "identity_field": "phone"}
    )
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "RULE_IDENTITY_FIELD_INVALID"

    with Session(engine) as session:
        stored = session.scalars(
            select(Rule)
            .where(Rule.workspace_id == UUID(workspace_id))
            .order_by(Rule.version)
        ).all()
        assert [(rule.version, rule.name) for rule in stored] == [
            (1, "Email handoff"),
            (2, "Email handoff v2"),
        ]
