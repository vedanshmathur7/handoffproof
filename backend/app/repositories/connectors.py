from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Connector


async def find_connector(
    session: AsyncSession, workspace_id: UUID, connector_id: UUID
) -> Connector | None:
    return cast(
        Connector | None,
        await session.scalar(
            select(Connector).where(
                Connector.workspace_id == workspace_id,
                Connector.id == connector_id,
            )
        ),
    )


async def find_connector_by_name(
    session: AsyncSession, workspace_id: UUID, name: str
) -> Connector | None:
    return cast(
        Connector | None,
        await session.scalar(
            select(Connector).where(
                Connector.workspace_id == workspace_id, Connector.name == name
            )
        ),
    )


async def list_connectors(session: AsyncSession, workspace_id: UUID) -> list[Connector]:
    rows = await session.scalars(
        select(Connector)
        .where(Connector.workspace_id == workspace_id)
        .order_by(Connector.created_at, Connector.id)
    )
    return list(rows)
