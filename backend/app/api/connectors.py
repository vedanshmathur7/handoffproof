from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    ConnectorCreate,
    ConnectorRead,
    ConnectorSyncRead,
    CredentialReplace,
    ErrorResponse,
    ShadowSyncCreate,
    ShadowSyncRead,
)
from app.database import get_session
from app.services.connectors import (
    create_connector,
    read_connectors,
    replace_credential,
)
from app.services.shadow_sync import (
    ConnectorClients,
    get_connector_clients,
    read_syncs,
    run_shadow_sync,
)

router = APIRouter(prefix="/api/v1", tags=["connectors"])
SessionDependency = Annotated[AsyncSession, Depends(get_session)]
ClientsDependency = Annotated[ConnectorClients, Depends(get_connector_clients)]

ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    503: {"model": ErrorResponse},
}


@router.post(
    "/connectors",
    response_model=ConnectorRead,
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
)
async def post_connector(
    data: ConnectorCreate, session: SessionDependency
) -> ConnectorRead:
    return await create_connector(session, data)


@router.get("/connectors", response_model=list[ConnectorRead])
async def get_connectors(
    workspace_id: UUID, session: SessionDependency
) -> list[ConnectorRead]:
    return await read_connectors(session, workspace_id)


@router.put(
    "/connectors/{connector_id}/credential",
    response_model=ConnectorRead,
    responses=ERROR_RESPONSES,
)
async def put_credential(
    connector_id: UUID, data: CredentialReplace, session: SessionDependency
) -> ConnectorRead:
    return await replace_credential(session, connector_id, data)


@router.get(
    "/connectors/{connector_id}/syncs",
    response_model=list[ConnectorSyncRead],
    responses={404: {"model": ErrorResponse}},
)
async def get_syncs(
    connector_id: UUID, workspace_id: UUID, session: SessionDependency
) -> list[ConnectorSyncRead]:
    return await read_syncs(session, workspace_id, connector_id)


@router.post(
    "/shadow-syncs",
    response_model=ShadowSyncRead,
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
)
async def post_shadow_sync(
    data: ShadowSyncCreate, session: SessionDependency, clients: ClientsDependency
) -> ShadowSyncRead:
    """Manually read Typeform then HubSpot (GET only) into coverage-aware imports."""
    return await run_shadow_sync(session, data, clients=clients)
