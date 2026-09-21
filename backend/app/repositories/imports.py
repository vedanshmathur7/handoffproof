from typing import cast
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ImportBatch, ImportKind, Observation, Rule, Workspace


def scoped_import_query(
    workspace_id: UUID, import_id: UUID
) -> Select[tuple[ImportBatch]]:
    return select(ImportBatch).where(
        ImportBatch.workspace_id == workspace_id,
        ImportBatch.id == import_id,
    )


async def find_import(
    session: AsyncSession, workspace_id: UUID, import_id: UUID
) -> ImportBatch | None:
    return cast(
        ImportBatch | None,
        await session.scalar(scoped_import_query(workspace_id, import_id)),
    )


async def find_import_by_checksum(
    session: AsyncSession,
    workspace_id: UUID,
    kind: ImportKind,
    checksum: str,
) -> ImportBatch | None:
    return cast(
        ImportBatch | None,
        await session.scalar(
            select(ImportBatch).where(
                ImportBatch.workspace_id == workspace_id,
                ImportBatch.kind == kind,
                ImportBatch.checksum == checksum,
            )
        ),
    )


async def rejected_observations(
    session: AsyncSession, workspace_id: UUID, import_id: UUID
) -> list[Observation]:
    return list(
        (
            await session.scalars(
                select(Observation)
                .where(
                    Observation.workspace_id == workspace_id,
                    Observation.import_id == import_id,
                    Observation.rejected_reason.is_not(None),
                )
                .order_by(Observation.created_at, Observation.id)
            )
        ).all()
    )


async def lock_workspace(session: AsyncSession, workspace_id: UUID) -> Workspace | None:
    return cast(
        Workspace | None,
        await session.scalar(
            select(Workspace).where(Workspace.id == workspace_id).with_for_update()
        ),
    )


async def next_rule_version(session: AsyncSession, workspace_id: UUID) -> int:
    latest = await session.scalar(
        select(Rule.version)
        .where(Rule.workspace_id == workspace_id)
        .order_by(Rule.version.desc())
        .limit(1)
    )
    return (latest or 0) + 1
