from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Any | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


def error_body(code: str, message: str, details: Any | None = None) -> dict[str, Any]:
    return {"code": code, "message": message, "details": details}


async def api_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ApiError)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(exc.code, exc.message, exc.details),
    )


async def validation_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    return JSONResponse(
        status_code=422,
        content=error_body(
            "REQUEST_VALIDATION_ERROR",
            "The request did not match the API contract.",
            [
                {key: value for key, value in error.items() if key != "input"}
                for error in exc.errors()
            ],
        ),
    )
