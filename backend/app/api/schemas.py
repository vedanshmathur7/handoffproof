from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import CoverageStatus, ImportKind, ImportStatus


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200, examples=["Demo workspace"])


class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    created_at: datetime


class RowError(BaseModel):
    row_number: int
    code: str


class ImportRead(BaseModel):
    id: UUID
    workspace_id: UUID
    kind: ImportKind
    filename: str
    checksum: str
    coverage: CoverageStatus
    status: ImportStatus
    total_rows: int
    accepted_rows: int
    rejected_rows: int
    duplicate_rows: int
    schema_fields: list[str]
    row_errors: list[RowError]
    created_at: datetime


class EligibilityInput(BaseModel):
    field: str = Field(examples=["transfer_enabled"])
    equals: str = Field(examples=["true"])


class RuleCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "workspace_id": "00000000-0000-0000-0000-000000000001",
                    "source_import_id": "00000000-0000-0000-0000-000000000002",
                    "destination_import_id": "00000000-0000-0000-0000-000000000003",
                    "name": "Email handoff",
                    "eligibility": {
                        "field": "transfer_enabled",
                        "equals": "true",
                    },
                    "identity_field": "email",
                    "required_fields": ["full_name", "company", "region"],
                    "wait_seconds": 300,
                    "timezone": "UTC",
                }
            ]
        }
    )

    workspace_id: UUID
    source_import_id: UUID
    destination_import_id: UUID
    name: str = Field(min_length=1, max_length=200)
    eligibility: EligibilityInput
    identity_field: str
    required_fields: list[str]
    wait_seconds: int = Field(ge=0, le=2_592_000)
    timezone: str = "UTC"


class RuleRead(BaseModel):
    id: UUID
    workspace_id: UUID
    version: int
    name: str
    eligibility: EligibilityInput
    identity_field: str
    required_fields: list[str]
    wait_seconds: int
    timezone: str
    created_at: datetime


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Any | None = None
