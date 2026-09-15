from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ready", "degraded"]
    process: Literal["ready"]
    database: Literal["ready", "unavailable"]


async def check_database() -> bool:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return False
    return True


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
)
async def health(
    response: Response,
    database_ready: Annotated[bool, Depends(check_database)],
) -> HealthResponse:
    if not database_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(
            status="degraded", process="ready", database="unavailable"
        )

    return HealthResponse(status="ready", process="ready", database="ready")
