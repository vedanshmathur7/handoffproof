from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ErrorResponse, ImportRead, RuleCreate, RuleRead
from app.config import get_settings
from app.database import get_session
from app.models import CoverageStatus, ImportKind
from app.services.imports import create_import, create_rule, read_import

router = APIRouter(prefix="/api/v1", tags=["imports and rules"])
SessionDependency = Annotated[AsyncSession, Depends(get_session)]

ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse},
    413: {"model": ErrorResponse},
    415: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}


async def upload_csv(
    *,
    kind: ImportKind,
    workspace_id: UUID,
    coverage: CoverageStatus,
    file: UploadFile,
    response: Response,
    session: AsyncSession,
) -> ImportRead:
    settings = get_settings()
    content = await file.read(settings.max_upload_bytes + 1)
    result, created = await create_import(
        session,
        workspace_id=workspace_id,
        kind=kind,
        filename=file.filename or "upload.csv",
        content_type=file.content_type,
        content=content,
        requested_coverage=coverage,
        max_upload_bytes=settings.max_upload_bytes,
    )
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return result


@router.post(
    "/imports/source",
    response_model=ImportRead,
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
)
async def upload_source(
    response: Response,
    session: SessionDependency,
    workspace_id: Annotated[UUID, Form()],
    file: Annotated[UploadFile, File()],
    coverage: Annotated[CoverageStatus, Form()] = CoverageStatus.COMPLETE,
) -> ImportRead:
    return await upload_csv(
        kind=ImportKind.SOURCE,
        workspace_id=workspace_id,
        coverage=coverage,
        file=file,
        response=response,
        session=session,
    )


@router.post(
    "/imports/destination",
    response_model=ImportRead,
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
)
async def upload_destination(
    response: Response,
    session: SessionDependency,
    workspace_id: Annotated[UUID, Form()],
    file: Annotated[UploadFile, File()],
    coverage: Annotated[CoverageStatus, Form()] = CoverageStatus.COMPLETE,
) -> ImportRead:
    return await upload_csv(
        kind=ImportKind.DESTINATION,
        workspace_id=workspace_id,
        coverage=coverage,
        file=file,
        response=response,
        session=session,
    )


@router.get(
    "/imports/{import_id}",
    response_model=ImportRead,
    responses={404: {"model": ErrorResponse}},
)
async def get_import(
    import_id: UUID,
    workspace_id: UUID,
    session: SessionDependency,
) -> ImportRead:
    return await read_import(session, workspace_id, import_id)


@router.post(
    "/rules",
    response_model=RuleRead,
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
)
async def post_rule(data: RuleCreate, session: SessionDependency) -> RuleRead:
    return await create_rule(session, data)
