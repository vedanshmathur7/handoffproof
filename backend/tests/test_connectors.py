from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

from app.api.schemas import EligibilityInput, ReconciliationCreate, RuleCreate
from app.connectors.hubspot import HubSpotConnector
from app.connectors.models import ConnectorProvider, ConnectorRecord, ConnectorSnapshot
from app.connectors.typeform import TypeformConnector
from app.database import async_session_factory
from app.models import CoverageStatus, ImportKind
from app.services.imports import create_connector_import, create_rule
from app.services.reconciliation import create_reconciliation


async def no_sleep(_seconds: float) -> None:
    return None


def typeform_response(response_id: str, submitted_at: str) -> dict[str, Any]:
    return {
        "response_id": response_id,
        "token": f"token-{response_id}",
        "submitted_at": submitted_at,
        "answers": [
            {"field": {"ref": "email"}, "email": f"{response_id}@example.test"},
            {"field": {"ref": "full_name"}, "text": "Ada Lovelace"},
            {"field": {"ref": "company"}, "text": "Analytical Engines"},
            {"field": {"ref": "region"}, "text": "IN"},
            {"field": {"ref": "transfer_enabled"}, "boolean": True},
        ],
    }


@pytest.mark.anyio
async def test_typeform_uses_read_only_pagination_overlap_and_deduplication() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(
                200,
                json={
                    "items": [
                        typeform_response("tf-1", "2026-09-01T12:00:00Z"),
                        typeform_response("tf-2", "2026-09-01T12:01:00Z"),
                    ]
                },
            )
        return httpx.Response(
            200,
            json={
                "items": [
                    typeform_response("tf-2", "2026-09-01T12:01:00Z"),
                ]
            },
        )

    snapshot = await TypeformConnector(
        "not-a-real-token",
        transport=httpx.MockTransport(handler),
        page_size=2,
        sleep=no_sleep,
        now=lambda: datetime(2026, 9, 1, 13, 0, tzinfo=UTC),
    ).read_responses(
        form_id="form-1",
        field_refs={
            "email": "email",
            "full_name": "full_name",
            "company": "company",
            "region": "region",
            "transfer_enabled": "transfer_enabled",
        },
        since=datetime(2026, 9, 1, 12, 0, tzinfo=UTC),
    )

    assert snapshot.coverage == CoverageStatus.COMPLETE
    assert [record.external_record_id for record in snapshot.records] == [
        "tf-1",
        "tf-2",
    ]
    assert snapshot.records[0].fields["transfer_enabled"] == "true"
    assert all(request.method == "GET" for request in requests)
    assert requests[0].url.params["page_size"] == "2"
    assert requests[0].url.params["since"] == "2026-09-01T11:55:00"
    assert requests[1].url.params["before"] == "token-tf-2"
    # The checkpoint stops 30 minutes before the read to cover indexing delay.
    assert snapshot.watermark == datetime(2026, 9, 1, 12, 30, tzinfo=UTC)


@pytest.mark.anyio
async def test_hubspot_later_throttling_becomes_partial_coverage() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "id": "hs-1",
                            "createdAt": "2026-09-01T12:00:00Z",
                            "properties": {
                                "email": "ada@example.test",
                                "firstname": "Ada",
                                "lastname": "Lovelace",
                                "company": "Analytical Engines",
                                "region": "IN",
                            },
                        }
                    ],
                    "paging": {"next": {"after": "cursor-1"}},
                },
            )
        return httpx.Response(429, json={"message": "slow down"})

    delays: list[float] = []

    async def record_sleep(seconds: float) -> None:
        delays.append(seconds)

    snapshot = await HubSpotConnector(
        "not-a-real-token", transport=httpx.MockTransport(handler), sleep=record_sleep
    ).read_contacts()

    assert snapshot.coverage == CoverageStatus.PARTIAL
    assert snapshot.issues == ("CONNECTOR_THROTTLED",)
    assert snapshot.continuation == "cursor-1"
    assert snapshot.records[0].fields["full_name"] == "Ada Lovelace"
    assert len(requests) == 3  # one page plus bounded retry attempts
    assert all(request.method == "GET" for request in requests)
    assert requests[1].url.params["after"] == "cursor-1"
    assert 1.0 in delays  # retry waited for backoff instead of hammering


@pytest.mark.anyio
async def test_bad_or_expired_typeform_reads_cannot_be_healthy() -> None:
    malformed = await TypeformConnector(
        "not-a-real-token",
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(200, json={"items": [{"bad": "row"}]})
        ),
        sleep=no_sleep,
    ).read_responses(form_id="form-1", field_refs={}, since=None)
    expired = await TypeformConnector(
        "not-a-real-token",
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(401, json={"message": "expired"})
        ),
        sleep=no_sleep,
    ).read_responses(form_id="form-1", field_refs={}, since=None)

    assert malformed.coverage == CoverageStatus.PARTIAL
    assert malformed.issues == ("CONNECTOR_MALFORMED_RECORD",)
    assert expired.coverage == CoverageStatus.FAILED
    assert expired.issues == ("CONNECTOR_AUTH_FAILED",)
    assert expired.watermark is None


@pytest.mark.anyio
async def test_connector_snapshots_reuse_the_csv_reconciliation_contract() -> None:
    from uuid import uuid4

    from sqlalchemy import delete

    from app.models import Workspace

    workspace_id = uuid4()
    source_snapshot = ConnectorSnapshot(
        provider=ConnectorProvider.TYPEFORM,
        kind=ImportKind.SOURCE,
        coverage=CoverageStatus.COMPLETE,
        watermark=datetime(2026, 9, 1, 12, 0, tzinfo=UTC),
        records=(
            ConnectorRecord(
                external_record_id="tf-1",
                fields={
                    "source_record_id": "tf-1",
                    "submitted_at": "2026-09-01T12:00:00Z",
                    "email": "ada@example.test",
                    "full_name": "Ada Lovelace",
                    "company": "Analytical Engines",
                    "region": "IN",
                    "transfer_enabled": "true",
                },
                observed_at=datetime(2026, 9, 1, 12, 0, tzinfo=UTC),
                original_evidence={"provider": "typeform", "response": {"id": "tf-1"}},
            ),
        ),
    )
    destination_snapshot = ConnectorSnapshot(
        provider=ConnectorProvider.HUBSPOT,
        kind=ImportKind.DESTINATION,
        coverage=CoverageStatus.COMPLETE,
        watermark=datetime(2026, 9, 1, 12, 1, tzinfo=UTC),
        records=(
            ConnectorRecord(
                external_record_id="hs-1",
                fields={
                    "destination_record_id": "hs-1",
                    "created_at": "2026-09-01T12:01:00Z",
                    "email": "ada@example.test",
                    "full_name": "Ada Lovelace",
                    "company": "Analytical Engines",
                    "region": "IN",
                },
                observed_at=datetime(2026, 9, 1, 12, 1, tzinfo=UTC),
                original_evidence={"provider": "hubspot", "contact": {"id": "hs-1"}},
            ),
        ),
    )
    async with async_session_factory() as session:
        session.add(Workspace(id=workspace_id, name=f"test-connectors-{workspace_id}"))
        await session.commit()
        source, _ = await create_connector_import(
            session,
            workspace_id=workspace_id,
            snapshot=source_snapshot,
            filename="typeform-form-1.json",
        )
        destination, _ = await create_connector_import(
            session,
            workspace_id=workspace_id,
            snapshot=destination_snapshot,
            filename="hubspot-contacts.json",
        )
        rule = await create_rule(
            session,
            RuleCreate(
                workspace_id=workspace_id,
                source_import_id=source.id,
                destination_import_id=destination.id,
                name="Connector handoff",
                eligibility=EligibilityInput(field="transfer_enabled", equals="true"),
                identity_field="email",
                required_fields=["full_name", "company", "region"],
                wait_seconds=0,
                timezone="UTC",
            ),
        )
        run, _ = await create_reconciliation(
            session,
            ReconciliationCreate(
                workspace_id=workspace_id,
                source_import_id=source.id,
                destination_import_id=destination.id,
                rule_id=rule.id,
                idempotency_key="connector-contract",
                evaluated_at=datetime(2026, 9, 1, 12, 2, tzinfo=UTC),
            ),
        )
        assert run.coverage == CoverageStatus.COMPLETE
        assert run.result_counts["matched"] == 1
        await session.execute(delete(Workspace).where(Workspace.id == workspace_id))
        await session.commit()
