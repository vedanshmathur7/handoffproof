"""Manual, read-only shadow sync: provider reads -> imports -> checkpoints.

Connectors never classify results. A sync only reads, normalizes through the CSV
import contract, and records which checkpoint the read proved.
"""

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ApiError
from app.api.schemas import ConnectorSyncRead, ShadowSyncCreate, ShadowSyncRead
from app.config import get_settings
from app.connectors.hubspot import HubSpotConnector
from app.connectors.models import ConnectorSnapshot
from app.connectors.typeform import TypeformConnector
from app.models import Connector, ConnectorProvider, ConnectorSync, CoverageStatus
from app.repositories.connectors import find_connector, latest_checkpoint, list_syncs
from app.services.credentials import decrypt_credential
from app.services.imports import create_connector_import
from app.services.reconciliation import combined_coverage


@dataclass(frozen=True)
class ConnectorClients:
    typeform: Callable[[str], TypeformConnector] = TypeformConnector
    hubspot: Callable[[str], HubSpotConnector] = HubSpotConnector


def get_connector_clients() -> ConnectorClients:
    return ConnectorClients()


def utc_now() -> datetime:
    return datetime.now(UTC)


def sync_to_read(sync: ConnectorSync, provider: ConnectorProvider) -> ConnectorSyncRead:
    return ConnectorSyncRead(
        id=sync.id,
        workspace_id=sync.workspace_id,
        connector_id=sync.connector_id,
        provider=provider,
        import_id=sync.import_id,
        coverage=sync.coverage,
        record_count=sync.record_count,
        issues=sync.issues,
        checkpoint_before=sync.checkpoint_before,
        checkpoint_after=sync.checkpoint_after,
        started_at=sync.started_at,
        completed_at=sync.completed_at,
    )


async def scoped_connector(
    session: AsyncSession,
    workspace_id: UUID,
    connector_id: UUID,
    provider: ConnectorProvider,
) -> Connector:
    connector = await find_connector(session, workspace_id, connector_id)
    if connector is None:
        raise ApiError(
            404, "CONNECTOR_NOT_FOUND", "Connector was not found in this workspace."
        )
    if connector.provider != provider:
        raise ApiError(
            422,
            "CONNECTOR_ROLE_INVALID",
            f"This shadow sync needs a {provider.value} connector here.",
        )
    return connector


async def sync_connector(
    session: AsyncSession,
    connector: Connector,
    *,
    clients: ConnectorClients,
    full_resync: bool,
    now: Callable[[], datetime],
) -> ConnectorSyncRead:
    started_at = now()
    checkpoint: datetime | None = None
    extra_issues: tuple[str, ...] = ()
    token = decrypt_credential(connector.encrypted_credential)
    snapshot: ConnectorSnapshot
    if connector.provider == ConnectorProvider.TYPEFORM:
        if not full_resync:
            checkpoint = await latest_checkpoint(
                session, connector.workspace_id, connector.id
            )
        max_age = timedelta(hours=get_settings().connector_checkpoint_max_age_hours)
        if checkpoint is not None and (
            checkpoint > started_at or started_at - checkpoint > max_age
        ):
            extra_issues = ("CONNECTOR_WATERMARK_STALE",)
        snapshot = await clients.typeform(token).read_responses(
            form_id=str(connector.config["form_id"]),
            field_refs=dict(connector.config["field_refs"]),
            since=checkpoint,
        )
    else:
        snapshot = await clients.hubspot(token).read_contacts()
    del token

    coverage = snapshot.coverage
    if extra_issues and coverage == CoverageStatus.COMPLETE:
        coverage = CoverageStatus.PARTIAL
    snapshot = replace(
        snapshot, coverage=coverage, issues=snapshot.issues + extra_issues
    )

    import_id: UUID | None = None
    if snapshot.records:
        imported, _created = await create_connector_import(
            session,
            workspace_id=connector.workspace_id,
            snapshot=snapshot,
            filename=f"{connector.provider.value}-{connector.id}.json",
        )
        import_id = imported.id
        coverage = imported.coverage  # rejected provider rows downgrade coverage

    checkpoint_after: datetime | None = None
    if coverage == CoverageStatus.COMPLETE and snapshot.watermark is not None:
        checkpoint_after = (
            max(checkpoint, snapshot.watermark)
            if checkpoint is not None
            else snapshot.watermark
        )

    sync = ConnectorSync(
        workspace_id=connector.workspace_id,
        connector_id=connector.id,
        import_id=import_id,
        coverage=coverage,
        record_count=len(snapshot.records),
        issues=list(snapshot.issues),
        checkpoint_before=checkpoint,
        checkpoint_after=checkpoint_after,
        started_at=started_at,
        completed_at=now(),
    )
    session.add(sync)
    await session.commit()
    await session.refresh(sync)
    return sync_to_read(sync, connector.provider)


async def run_shadow_sync(
    session: AsyncSession,
    data: ShadowSyncCreate,
    *,
    clients: ConnectorClients,
    now: Callable[[], datetime] = utc_now,
) -> ShadowSyncRead:
    source = await scoped_connector(
        session,
        data.workspace_id,
        data.source_connector_id,
        ConnectorProvider.TYPEFORM,
    )
    destination = await scoped_connector(
        session,
        data.workspace_id,
        data.destination_connector_id,
        ConnectorProvider.HUBSPOT,
    )
    # Source first, then destination: the destination snapshot is never older
    # than any source record it is compared against.
    source_sync = await sync_connector(
        session, source, clients=clients, full_resync=data.full_resync, now=now
    )
    destination_sync = await sync_connector(
        session, destination, clients=clients, full_resync=data.full_resync, now=now
    )
    coverage = combined_coverage(source_sync.coverage, destination_sync.coverage)
    if destination_sync.import_id is None:
        coverage = CoverageStatus.FAILED  # no destination evidence at all
    return ShadowSyncRead(
        source=source_sync,
        destination=destination_sync,
        coverage=coverage,
        evaluated_at=destination_sync.started_at,
    )


async def read_syncs(
    session: AsyncSession, workspace_id: UUID, connector_id: UUID
) -> list[ConnectorSyncRead]:
    connector = await find_connector(session, workspace_id, connector_id)
    if connector is None:
        raise ApiError(
            404, "CONNECTOR_NOT_FOUND", "Connector was not found in this workspace."
        )
    return [
        sync_to_read(sync, connector.provider)
        for sync in await list_syncs(session, workspace_id, connector_id)
    ]
