from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import (
    CoverageStatus,
    ImportKind,
    ImportStatus,
    ResultCategory,
    RunStatus,
)


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


class ReconciliationCreate(BaseModel):
    workspace_id: UUID
    source_import_id: UUID
    destination_import_id: UUID
    rule_id: UUID
    idempotency_key: str = Field(min_length=1, max_length=255)
    evaluated_at: datetime | None = None


class ReconciliationSummary(BaseModel):
    id: UUID
    workspace_id: UUID
    source_import_id: UUID
    destination_import_id: UUID
    rule_id: UUID
    rule_version: int
    status: RunStatus
    coverage: CoverageStatus
    result_counts: dict[str, int]
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class RuleReference(BaseModel):
    id: UUID
    version: int
    name: str
    identity_field: str
    required_fields: list[str]
    wait_seconds: int
    timezone: str


class CandidateRead(BaseModel):
    destination_observation_id: UUID
    external_record_id: str
    rank: int
    match_basis: dict[str, Any]
    original_evidence: dict[str, Any]


class ReviewCreate(BaseModel):
    workspace_id: UUID
    reviewer: str = Field(min_length=1, max_length=200)
    annotation: str = Field(min_length=1, max_length=4000)


class ReviewRead(BaseModel):
    id: UUID
    reviewer: str
    annotation: str
    created_at: datetime


class ResultRead(BaseModel):
    id: UUID
    run_id: UUID
    source_observation_id: UUID
    source_record_id: str
    category: ResultCategory
    reason_code: str
    evidence: dict[str, Any]
    source_evidence: dict[str, Any]
    candidates: list[CandidateRead]
    reviews: list[ReviewRead]
    rule: RuleReference
    created_at: datetime


class ResultPage(BaseModel):
    items: list[ResultRead]
    total: int
    offset: int
    limit: int
