import asyncio
import csv
import io
from collections.abc import AsyncIterator, Generator
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.main import app
from app.models import ReconciliationResult, ReconciliationRun, Workspace

FIXTURES = Path(__file__).parent / "fixtures"
engine = create_engine(get_settings().database_url)


@pytest.fixture(autouse=True)
def remove_reconciliation_test_workspaces() -> Generator[None, None, None]:
    yield
    with Session(engine) as session:
        session.execute(delete(Workspace).where(Workspace.name.like("test-recon-%")))
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


async def bootstrap(
    client: AsyncClient, destination_file: str = "destination.csv"
) -> dict[str, str]:
    workspace_response = await client.post(
        "/api/v1/workspaces", json={"name": f"test-recon-{uuid4()}"}
    )
    workspace_id = str(workspace_response.json()["id"])

    async def upload(kind: str, filename: str, coverage: str) -> str:
        response = await client.post(
            f"/api/v1/imports/{kind}",
            data={"workspace_id": workspace_id, "coverage": coverage},
            files={"file": (filename, (FIXTURES / filename).read_bytes(), "text/csv")},
        )
        assert response.status_code == 201, response.text
        return str(response.json()["id"])

    source_id = await upload("source", "source.csv", "complete")
    destination_coverage = (
        "partial" if destination_file == "partial_destination.csv" else "complete"
    )
    destination_id = await upload("destination", destination_file, destination_coverage)
    rule_response = await client.post(
        "/api/v1/rules",
        json={
            "workspace_id": workspace_id,
            "source_import_id": source_id,
            "destination_import_id": destination_id,
            "name": "Fixture email handoff",
            "eligibility": {"field": "transfer_enabled", "equals": "true"},
            "identity_field": "email",
            "required_fields": ["full_name", "company", "region"],
            "wait_seconds": 300,
            "timezone": "UTC",
        },
    )
    assert rule_response.status_code == 201, rule_response.text
    return {
        "workspace_id": workspace_id,
        "source_import_id": source_id,
        "destination_import_id": destination_id,
        "rule_id": str(rule_response.json()["id"]),
    }


def run_payload(ids: dict[str, str], key: str) -> dict[str, str]:
    return {
        **ids,
        "idempotency_key": key,
        "evaluated_at": "2026-09-02T00:00:00Z",
    }


@pytest.mark.anyio
async def test_full_fixture_run_exposes_counts_evidence_filters_and_export(
    client: AsyncClient,
) -> None:
    ids = await bootstrap(client)
    response = await client.post(
        "/api/v1/reconciliations", json=run_payload(ids, "full-fixture")
    )
    assert response.status_code == 201
    summary = cast(dict[str, Any], response.json())
    assert summary["status"] == "completed"
    assert summary["coverage"] == "complete"
    assert summary["result_counts"] == {
        "matched": 1,
        "missing": 2,
        "duplicate": 1,
        "field_mismatch": 1,
        "excluded": 1,
        "unknown": 0,
    }
    run_id = str(summary["id"])

    page = await client.get(
        f"/api/v1/reconciliations/{run_id}/results",
        params={"workspace_id": ids["workspace_id"], "limit": 3},
    )
    assert page.status_code == 200
    assert page.json()["total"] == 6
    assert len(page.json()["items"]) == 3

    duplicate = await client.get(
        f"/api/v1/reconciliations/{run_id}/results",
        params={
            "workspace_id": ids["workspace_id"],
            "category": "duplicate",
        },
    )
    duplicate_item = duplicate.json()["items"][0]
    assert duplicate_item["source_record_id"] == "SRC_DUPLICATE"
    assert duplicate_item["reason_code"] == "MULTIPLE_IDENTITY_MATCHES"
    assert len(duplicate_item["candidates"]) == 2
    assert duplicate_item["rule"]["version"] == 1
    assert duplicate_item["source_evidence"]["email"] == "duplicate@example.test"

    mismatch = await client.get(
        f"/api/v1/reconciliations/{run_id}/results",
        params={
            "workspace_id": ids["workspace_id"],
            "category": "field_mismatch",
        },
    )
    mismatch_item = mismatch.json()["items"][0]
    assert mismatch_item["evidence"]["differences"] == [
        {
            "field": "company",
            "source": "correct company",
            "destination": "wrong company",
        }
    ]

    export = await client.get(
        f"/api/v1/reconciliations/{run_id}/export",
        params={"workspace_id": ids["workspace_id"]},
    )
    rows = list(csv.DictReader(io.StringIO(export.text)))
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("text/csv")
    assert len(rows) == 6
    assert {row["category"] for row in rows} == {
        "matched",
        "missing",
        "duplicate",
        "field_mismatch",
        "excluded",
    }


@pytest.mark.anyio
async def test_review_appends_without_replacing_machine_reason(
    client: AsyncClient,
) -> None:
    ids = await bootstrap(client)
    run = await client.post(
        "/api/v1/reconciliations", json=run_payload(ids, "review-fixture")
    )
    run_id = str(run.json()["id"])
    results = await client.get(
        f"/api/v1/reconciliations/{run_id}/results",
        params={"workspace_id": ids["workspace_id"], "category": "field_mismatch"},
    )
    original = results.json()["items"][0]
    review = await client.post(
        f"/api/v1/results/{original['id']}/reviews",
        json={
            "workspace_id": ids["workspace_id"],
            "reviewer": "reviewer@example.test",
            "annotation": "Confirmed company mismatch.",
        },
    )
    assert review.status_code == 201

    refreshed = await client.get(
        f"/api/v1/reconciliations/{run_id}/results",
        params={"workspace_id": ids["workspace_id"], "category": "field_mismatch"},
    )
    updated = refreshed.json()["items"][0]
    assert updated["reason_code"] == "REQUIRED_FIELD_MISMATCH"
    assert updated["evidence"] == original["evidence"]
    assert updated["reviews"][0]["annotation"] == "Confirmed company mismatch."


@pytest.mark.anyio
async def test_concurrent_same_key_creates_one_run(client: AsyncClient) -> None:
    ids = await bootstrap(client)
    payload = run_payload(ids, "concurrent-fixture")
    first, second = await asyncio.gather(
        client.post("/api/v1/reconciliations", json=payload),
        client.post("/api/v1/reconciliations", json=payload),
    )
    assert sorted([first.status_code, second.status_code]) == [200, 201]
    assert first.json()["id"] == second.json()["id"]

    with Session(engine) as session:
        run_count = session.scalar(
            select(func.count())
            .select_from(ReconciliationRun)
            .where(ReconciliationRun.workspace_id == UUID(ids["workspace_id"]))
        )
        result_count = session.scalar(
            select(func.count())
            .select_from(ReconciliationResult)
            .where(ReconciliationResult.workspace_id == UUID(ids["workspace_id"]))
        )
        assert run_count == 1
        assert result_count == 6


@pytest.mark.anyio
async def test_partial_coverage_is_all_unknown_and_workspace_isolated(
    client: AsyncClient,
) -> None:
    ids = await bootstrap(client, "partial_destination.csv")
    run = await client.post(
        "/api/v1/reconciliations", json=run_payload(ids, "partial-fixture")
    )
    assert run.status_code == 201
    assert run.json()["coverage"] == "partial"
    assert run.json()["result_counts"] == {
        "matched": 0,
        "missing": 0,
        "duplicate": 0,
        "field_mismatch": 0,
        "excluded": 0,
        "unknown": 6,
    }

    other_workspace = await client.post(
        "/api/v1/workspaces", json={"name": f"test-recon-{uuid4()}"}
    )
    hidden = await client.get(
        f"/api/v1/reconciliations/{run.json()['id']}",
        params={"workspace_id": other_workspace.json()["id"]},
    )
    assert hidden.status_code == 404
    assert hidden.json()["code"] == "RECONCILIATION_NOT_FOUND"
