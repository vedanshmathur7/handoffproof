from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ApiError
from app.api.schemas import (
    TYPEFORM_REQUIRED_FIELDS,
    ConnectorCreate,
    ConnectorRead,
    CredentialReplace,
)
from app.models import Connector, ConnectorProvider, ImportKind
from app.repositories.connectors import (
    find_connector,
    find_connector_by_name,
    list_connectors,
)
from app.repositories.imports import lock_workspace
from app.services.credentials import encrypt_credential

PROVIDER_KIND = {
    ConnectorProvider.TYPEFORM: ImportKind.SOURCE,
    ConnectorProvider.HUBSPOT: ImportKind.DESTINATION,
}


def connector_to_read(connector: Connector) -> ConnectorRead:
    return ConnectorRead(
        id=connector.id,
        workspace_id=connector.workspace_id,
        provider=connector.provider,
        kind=PROVIDER_KIND[connector.provider],
        name=connector.name,
        config=connector.config,
        credential_configured=bool(connector.encrypted_credential),
        credential_updated_at=connector.credential_updated_at,
        created_at=connector.created_at,
    )


def validated_config(data: ConnectorCreate) -> dict[str, object]:
    if data.provider == ConnectorProvider.HUBSPOT:
        if data.typeform is not None:
            raise ApiError(
                422,
                "CONNECTOR_CONFIG_INVALID",
                "HubSpot connectors do not accept Typeform configuration.",
            )
        return {}
    if data.typeform is None:
        raise ApiError(
            422,
            "CONNECTOR_CONFIG_INVALID",
            "Typeform connectors require a form ID and field refs.",
        )
    missing = [
        name
        for name in TYPEFORM_REQUIRED_FIELDS
        if not data.typeform.field_refs.get(name)
    ]
    unexpected = sorted(set(data.typeform.field_refs) - set(TYPEFORM_REQUIRED_FIELDS))
    if missing or unexpected:
        raise ApiError(
            422,
            "CONNECTOR_CONFIG_INVALID",
            "Typeform field refs must map exactly the normalized source fields.",
            {"missing": missing, "unexpected": unexpected},
        )
    return data.typeform.model_dump()


async def create_connector(
    session: AsyncSession, data: ConnectorCreate
) -> ConnectorRead:
    if await lock_workspace(session, data.workspace_id) is None:
        raise ApiError(404, "WORKSPACE_NOT_FOUND", "Workspace was not found.")
    name = data.name.strip()
    if await find_connector_by_name(session, data.workspace_id, name) is not None:
        raise ApiError(
            409, "CONNECTOR_NAME_TAKEN", "A connector with this name already exists."
        )
    connector = Connector(
        workspace_id=data.workspace_id,
        provider=data.provider,
        name=name,
        config=validated_config(data),
        encrypted_credential=encrypt_credential(data.token.get_secret_value()),
    )
    session.add(connector)
    await session.commit()
    await session.refresh(connector)
    return connector_to_read(connector)


async def replace_credential(
    session: AsyncSession, connector_id: UUID, data: CredentialReplace
) -> ConnectorRead:
    connector = await find_connector(session, data.workspace_id, connector_id)
    if connector is None:
        raise ApiError(
            404, "CONNECTOR_NOT_FOUND", "Connector was not found in this workspace."
        )
    connector.encrypted_credential = encrypt_credential(data.token.get_secret_value())
    connector.credential_updated_at = func.now()
    await session.commit()
    await session.refresh(connector)
    return connector_to_read(connector)


async def read_connectors(
    session: AsyncSession, workspace_id: UUID
) -> list[ConnectorRead]:
    return [
        connector_to_read(item) for item in await list_connectors(session, workspace_id)
    ]
