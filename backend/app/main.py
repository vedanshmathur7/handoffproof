from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import ApiError, api_error_handler, validation_error_handler
from app.api.health import router as health_router
from app.api.imports import router as imports_router
from app.api.workspaces import router as workspaces_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="HandoffProof API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.include_router(health_router)
app.include_router(workspaces_router)
app.include_router(imports_router)
