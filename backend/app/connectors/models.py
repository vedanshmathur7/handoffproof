from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from app.models import CoverageStatus, ImportKind


class ConnectorProvider(StrEnum):
    TYPEFORM = "typeform"
    HUBSPOT = "hubspot"


@dataclass(frozen=True)
class ConnectorRecord:
    external_record_id: str
    fields: dict[str, str]
    observed_at: datetime | None
    original_evidence: dict[str, Any]


@dataclass(frozen=True)
class ConnectorSnapshot:
    provider: ConnectorProvider
    kind: ImportKind
    records: tuple[ConnectorRecord, ...]
    coverage: CoverageStatus
    watermark: datetime | None
    continuation: str | None = None
    issues: tuple[str, ...] = field(default_factory=tuple)


class ConnectorError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)
