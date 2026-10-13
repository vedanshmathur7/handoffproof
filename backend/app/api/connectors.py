from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    ConnectorCreate,
    ConnectorRead,
    CredentialReplace,
    ErrorResponse,
)
from app.database import get_session
from app.services.connectors import (
    create_connector,
    read_connectors,
    replace_credential,
)

router = APIRouter(prefix="/api/v1/connectors", tags=["connectors"])
SessionDependency = Annotated[AsyncSession, Depends(get_session)]

ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    503: {"model": ErrorResponse},
}


@router.post(
    "",
    response_model=ConnectorRead,
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
)
async def post_connector(
    data: ConnectorCreate, session: SessionDependency
) -> ConnectorRead:
    return await create_connector(session, data)


@router.get("", response_model=list[ConnectorRead])
async def get_connectors(
    workspace_id: UUID, session: SessionDependency
) -> list[ConnectorRead]:
    return await read_connectors(session, workspace_id)


@router.put(
    "/{connector_id}/credential",
    response_model=ConnectorRead,
    responses=ERROR_RESPONSES,
)
async def put_credential(
    connector_id: UUID, data: CredentialReplace, session: SessionDependency
) -> ConnectorRead:
    return await replace_credential(session, connector_id, data)
