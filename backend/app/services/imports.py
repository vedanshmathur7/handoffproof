import csv
import hashlib
import io
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ApiError
from app.api.schemas import EligibilityInput, ImportRead, RowError, RuleCreate, RuleRead
from app.models import (
    CoverageStatus,
    ImportBatch,
    ImportKind,
    ImportStatus,
    Observation,
    Rule,
)
from app.repositories.imports import (
    find_import,
    find_import_by_checksum,
    lock_workspace,
    next_rule_version,
    rejected_observations,
)

SOURCE_FIELDS = [
    "source_record_id",
    "submitted_at",
    "email",
    "full_name",
    "company",
    "region",
    "transfer_enabled",
]
DESTINATION_FIELDS = [
    "destination_record_id",
    "created_at",
    "email",
    "full_name",
    "company",
    "region",
]
ALLOWED_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
}
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@dataclass(frozen=True)
class ParsedRow:
    row_number: int
    external_record_id: str
    identity_value: str | None
    normalized_data: dict[str, Any]
    original_evidence: dict[str, str]
    eligible: bool
    observed_at: datetime | None
    rejected_reason: str | None = None


def expected_fields(kind: ImportKind) -> list[str]:
    return SOURCE_FIELDS if kind == ImportKind.SOURCE else DESTINATION_FIELDS


def parse_timestamp(raw: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def rejected_row(row_number: int, original: dict[str, str], reason: str) -> ParsedRow:
    return ParsedRow(
        row_number=row_number,
        external_record_id=f"__rejected_row_{row_number}__",
        identity_value=None,
        normalized_data={"_row_number": row_number},
        original_evidence=original,
        eligible=False,
        observed_at=None,
        rejected_reason=reason,
    )


def parse_row(
    kind: ImportKind,
    row_number: int,
    row: dict[str, str],
    seen_ids: set[str],
) -> tuple[ParsedRow, bool]:
    original = {key: value or "" for key, value in row.items()}
    normalized: dict[str, Any] = {
        key: normalize_text(value or "") for key, value in row.items()
    }
    id_field = (
        "source_record_id" if kind == ImportKind.SOURCE else "destination_record_id"
    )
    time_field = "submitted_at" if kind == ImportKind.SOURCE else "created_at"
    prefix = "SOURCE" if kind == ImportKind.SOURCE else "DESTINATION"
    external_id = normalized[id_field]

    if not external_id:
        return rejected_row(row_number, original, f"MISSING_{prefix}_RECORD_ID"), False
    if external_id in seen_ids:
        return rejected_row(row_number, original, f"DUPLICATE_{prefix}_RECORD_ID"), True
    seen_ids.add(external_id)

    observed_at = parse_timestamp(normalized[time_field])
    if observed_at is None:
        return rejected_row(
            row_number, original, f"INVALID_{time_field.upper()}"
        ), False

    email = normalized["email"].casefold()
    if not EMAIL_PATTERN.fullmatch(email):
        return rejected_row(row_number, original, "INVALID_EMAIL"), False
    normalized["email"] = email

    eligible = True
    if kind == ImportKind.SOURCE:
        raw_eligible = normalized["transfer_enabled"].casefold()
        if raw_eligible not in {"true", "false"}:
            return rejected_row(row_number, original, "INVALID_TRANSFER_ENABLED"), False
        eligible = raw_eligible == "true"
        normalized["transfer_enabled"] = eligible

    return (
        ParsedRow(
            row_number=row_number,
            external_record_id=external_id,
            identity_value=email,
            normalized_data=normalized,
            original_evidence=original,
            eligible=eligible,
            observed_at=observed_at,
        ),
        False,
    )


def parse_csv(
    kind: ImportKind, content: bytes
) -> tuple[list[ParsedRow], list[str], int]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ApiError(
            422, "CSV_ENCODING_INVALID", "CSV must use UTF-8 encoding."
        ) from exc
    if "\x00" in text:
        raise ApiError(422, "CSV_CONTENT_INVALID", "CSV contains invalid null bytes.")

    reader = csv.DictReader(io.StringIO(text, newline=""))
    fields = reader.fieldnames or []
    required = expected_fields(kind)
    missing = [field for field in required if field not in fields]
    if missing:
        raise ApiError(
            422,
            "CSV_MISSING_HEADERS",
            "CSV is missing required headers.",
            {"missing": missing, "expected": required},
        )
    unexpected = [field for field in fields if field not in required]
    if unexpected:
        raise ApiError(
            422,
            "CSV_UNEXPECTED_HEADERS",
            "CSV contains headers outside the fixed contract.",
            {"unexpected": unexpected, "expected": required},
        )

    parsed: list[ParsedRow] = []
    seen_ids: set[str] = set()
    duplicate_rows = 0
    for row_number, row in enumerate(reader, start=2):
        item, duplicate = parse_row(kind, row_number, row, seen_ids)
        parsed.append(item)
        duplicate_rows += int(duplicate)
    if not parsed:
        raise ApiError(422, "CSV_EMPTY", "CSV must contain at least one data row.")
    return parsed, list(fields), duplicate_rows


def resolved_coverage(
    requested: CoverageStatus, accepted: int, rejected: int
) -> CoverageStatus:
    if requested == CoverageStatus.FAILED or accepted == 0:
        return CoverageStatus.FAILED
    if requested == CoverageStatus.PARTIAL or rejected > 0:
        return CoverageStatus.PARTIAL
    return CoverageStatus.COMPLETE


async def import_to_read(session: AsyncSession, batch: ImportBatch) -> ImportRead:
    rejected = await rejected_observations(session, batch.workspace_id, batch.id)
    rejected.sort(key=lambda item: int(item.normalized_data.get("_row_number", 0)))
    errors = [
        RowError(
            row_number=int(item.normalized_data.get("_row_number", 0)),
            code=item.rejected_reason or "UNKNOWN_ROW_ERROR",
        )
        for item in rejected
    ]
    return ImportRead(
        id=batch.id,
        workspace_id=batch.workspace_id,
        kind=batch.kind,
        filename=batch.filename,
        checksum=batch.checksum,
        coverage=batch.coverage,
        status=batch.status,
        total_rows=batch.total_rows,
        accepted_rows=batch.accepted_rows,
        rejected_rows=batch.rejected_rows,
        duplicate_rows=batch.duplicate_rows,
        schema_fields=batch.schema_fields,
        row_errors=errors,
        created_at=batch.created_at,
    )


async def create_import(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    kind: ImportKind,
    filename: str,
    content_type: str | None,
    content: bytes,
    requested_coverage: CoverageStatus,
    max_upload_bytes: int,
) -> tuple[ImportRead, bool]:
    if content_type not in ALLOWED_CONTENT_TYPES or not filename.casefold().endswith(
        ".csv"
    ):
        raise ApiError(
            415,
            "CSV_FILE_TYPE_INVALID",
            "Upload a .csv file with a CSV content type.",
        )
    if len(content) > max_upload_bytes:
        raise ApiError(
            413,
            "CSV_FILE_TOO_LARGE",
            f"CSV exceeds the {max_upload_bytes}-byte limit.",
        )
    if await lock_workspace(session, workspace_id) is None:
        raise ApiError(404, "WORKSPACE_NOT_FOUND", "Workspace was not found.")

    checksum = hashlib.sha256(content).hexdigest()
    existing = await find_import_by_checksum(session, workspace_id, kind, checksum)
    if existing is not None:
        return await import_to_read(session, existing), False

    rows, fields, duplicate_rows = parse_csv(kind, content)
    accepted = sum(row.rejected_reason is None for row in rows)
    rejected = len(rows) - accepted
    coverage = resolved_coverage(requested_coverage, accepted, rejected)
    batch = ImportBatch(
        workspace_id=workspace_id,
        kind=kind,
        filename=Path(filename).name,
        checksum=checksum,
        coverage=coverage,
        status=ImportStatus.FAILED if accepted == 0 else ImportStatus.COMPLETED,
        total_rows=len(rows),
        accepted_rows=accepted,
        rejected_rows=rejected,
        duplicate_rows=duplicate_rows,
        schema_fields=fields,
    )
    session.add(batch)
    await session.flush()
    session.add_all(
        [
            Observation(
                workspace_id=workspace_id,
                import_id=batch.id,
                external_record_id=row.external_record_id,
                identity_value=row.identity_value,
                normalized_data=row.normalized_data,
                original_evidence=row.original_evidence,
                eligible=row.eligible,
                rejected_reason=row.rejected_reason,
                observed_at=row.observed_at,
            )
            for row in rows
        ]
    )
    await session.commit()
    await session.refresh(batch)
    return await import_to_read(session, batch), True


async def read_import(
    session: AsyncSession, workspace_id: UUID, import_id: UUID
) -> ImportRead:
    batch = await find_import(session, workspace_id, import_id)
    if batch is None:
        raise ApiError(
            404, "IMPORT_NOT_FOUND", "Import was not found in this workspace."
        )
    return await import_to_read(session, batch)


async def create_rule(session: AsyncSession, data: RuleCreate) -> RuleRead:
    workspace = await lock_workspace(session, data.workspace_id)
    if workspace is None:
        raise ApiError(404, "WORKSPACE_NOT_FOUND", "Workspace was not found.")
    source = await find_import(session, data.workspace_id, data.source_import_id)
    destination = await find_import(
        session, data.workspace_id, data.destination_import_id
    )
    if source is None or source.kind != ImportKind.SOURCE:
        raise ApiError(
            422,
            "SOURCE_IMPORT_INVALID",
            "A source import from this workspace is required.",
        )
    if destination is None or destination.kind != ImportKind.DESTINATION:
        raise ApiError(
            422,
            "DESTINATION_IMPORT_INVALID",
            "A destination import from this workspace is required.",
        )
    if (
        source.status != ImportStatus.COMPLETED
        or destination.status != ImportStatus.COMPLETED
    ):
        raise ApiError(
            422, "IMPORT_NOT_READY", "Both imports must contain accepted rows."
        )

    common_fields = set(source.schema_fields) & set(destination.schema_fields)
    if data.identity_field not in common_fields:
        raise ApiError(
            422,
            "RULE_IDENTITY_FIELD_INVALID",
            "Identity field must exist in both imported schemas.",
            {"available": sorted(common_fields)},
        )
    invalid_required = sorted(set(data.required_fields) - common_fields)
    if invalid_required:
        raise ApiError(
            422,
            "RULE_REQUIRED_FIELDS_INVALID",
            "Every required field must exist in both imported schemas.",
            {"invalid": invalid_required, "available": sorted(common_fields)},
        )
    if len(set(data.required_fields)) != len(data.required_fields):
        raise ApiError(
            422,
            "RULE_REQUIRED_FIELDS_DUPLICATE",
            "Required fields must be unique.",
        )
    if data.eligibility.field not in source.schema_fields:
        raise ApiError(
            422,
            "RULE_ELIGIBILITY_FIELD_INVALID",
            "Eligibility field must exist in the source schema.",
            {"available": source.schema_fields},
        )
    try:
        ZoneInfo(data.timezone)
    except ZoneInfoNotFoundError as exc:
        raise ApiError(
            422, "RULE_TIMEZONE_INVALID", "Timezone must be a valid IANA name."
        ) from exc

    rule = Rule(
        workspace_id=data.workspace_id,
        version=await next_rule_version(session, data.workspace_id),
        name=data.name.strip(),
        identity_field=data.identity_field,
        required_fields=data.required_fields,
        exclusions=[
            {
                "field": data.eligibility.field,
                "operator": "not_equals",
                "value": data.eligibility.equals,
            }
        ],
        wait_seconds=data.wait_seconds,
        timezone=data.timezone,
    )
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule_to_read(rule)


def rule_to_read(rule: Rule) -> RuleRead:
    exclusion = rule.exclusions[0]
    return RuleRead(
        id=rule.id,
        workspace_id=rule.workspace_id,
        version=rule.version,
        name=rule.name,
        eligibility=EligibilityInput(
            field=str(exclusion["field"]), equals=str(exclusion["value"])
        ),
        identity_field=rule.identity_field,
        required_fields=rule.required_fields,
        wait_seconds=rule.wait_seconds,
        timezone=rule.timezone,
        created_at=rule.created_at,
    )
