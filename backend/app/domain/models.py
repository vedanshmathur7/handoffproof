from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from app.models import CoverageStatus, ImportKind, ResultCategory


@dataclass(frozen=True)
class ObservationData:
    id: UUID
    external_record_id: str
    normalized_data: dict[str, Any]
    original_evidence: dict[str, Any]
    observed_at: datetime | None


@dataclass(frozen=True)
class RuleData:
    version: int
    identity_field: str
    required_fields: tuple[str, ...]
    eligibility_field: str
    eligibility_value: str
    wait_seconds: int
    timezone: str


@dataclass(frozen=True)
class CandidateMatch:
    observation_id: UUID
    external_record_id: str
    rank: int
    match_basis: dict[str, Any]


@dataclass(frozen=True)
class Classification:
    category: ResultCategory
    reason_code: str
    evidence: dict[str, Any]
    candidates: tuple[CandidateMatch, ...] = field(default_factory=tuple)


__all__ = [
    "CandidateMatch",
    "Classification",
    "CoverageStatus",
    "ImportKind",
    "ObservationData",
    "ResultCategory",
    "RuleData",
]
