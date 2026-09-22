from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    ErrorResponse,
    ReconciliationCreate,
    ReconciliationSummary,
    ResultPage,
    ReviewCreate,
    ReviewRead,
)
from app.database import get_session
from app.models import ResultCategory
from app.services.reconciliation import (
    add_review,
    create_reconciliation,
    export_results,
    read_reconciliation,
    read_results,
)

router = APIRouter(prefix="/api/v1", tags=["reconciliations"])
SessionDependency = Annotated[AsyncSession, Depends(get_session)]
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}


@router.post(
    "/reconciliations",
    response_model=ReconciliationSummary,
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
)
async def post_reconciliation(
    data: ReconciliationCreate,
    response: Response,
    session: SessionDependency,
) -> ReconciliationSummary:
    result, created = await create_reconciliation(session, data)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return result


@router.get(
    "/reconciliations/{run_id}",
    response_model=ReconciliationSummary,
    responses={404: {"model": ErrorResponse}},
)
async def get_reconciliation(
    run_id: UUID,
    workspace_id: UUID,
    session: SessionDependency,
) -> ReconciliationSummary:
    return await read_reconciliation(session, workspace_id, run_id)


@router.get(
    "/reconciliations/{run_id}/results",
    response_model=ResultPage,
    responses={404: {"model": ErrorResponse}},
)
async def get_results(
    run_id: UUID,
    workspace_id: UUID,
    session: SessionDependency,
    category: ResultCategory | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ResultPage:
    return await read_results(session, workspace_id, run_id, category, offset, limit)


@router.post(
    "/results/{result_id}/reviews",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}},
)
async def post_review(
    result_id: UUID,
    data: ReviewCreate,
    session: SessionDependency,
) -> ReviewRead:
    return await add_review(session, result_id, data)


@router.get(
    "/reconciliations/{run_id}/export",
    response_class=StreamingResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_export(
    run_id: UUID,
    workspace_id: UUID,
    session: SessionDependency,
) -> StreamingResponse:
    content = await export_results(session, workspace_id, run_id)
    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="reconciliation-{run_id}.csv"'
        },
    )
