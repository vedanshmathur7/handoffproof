from datetime import datetime
from enum import Enum, StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ImportKind(StrEnum):
    SOURCE = "source"
    DESTINATION = "destination"


class CoverageStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


class ImportStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ResultCategory(StrEnum):
    MATCHED = "matched"
    MISSING = "missing"
    DUPLICATE = "duplicate"
    FIELD_MISMATCH = "field_mismatch"
    EXCLUDED = "excluded"
    UNKNOWN = "unknown"


class ConnectorProvider(StrEnum):
    TYPEFORM = "typeform"
    HUBSPOT = "hubspot"


def enum_values(enum_type: type[Enum]) -> list[str]:
    return [str(item.value) for item in enum_type]


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)


class ImportBatch(Base, TimestampMixin):
    __tablename__ = "imports"
    __table_args__ = (
        UniqueConstraint("workspace_id", "id", name="uq_imports_workspace_id_id"),
        UniqueConstraint(
            "workspace_id",
            "kind",
            "checksum",
            name="uq_imports_workspace_kind_checksum",
        ),
        CheckConstraint(
            "total_rows >= 0 AND accepted_rows >= 0 AND rejected_rows >= 0",
            name="nonnegative_row_counts",
        ),
        CheckConstraint(
            "accepted_rows + rejected_rows = total_rows",
            name="row_counts_balance",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[ImportKind] = mapped_column(
        SqlEnum(
            ImportKind,
            name="import_kind",
            values_callable=enum_values,
        ),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    coverage: Mapped[CoverageStatus] = mapped_column(
        SqlEnum(
            CoverageStatus,
            name="coverage_status",
            values_callable=enum_values,
        ),
        nullable=False,
    )
    status: Mapped[ImportStatus] = mapped_column(
        SqlEnum(
            ImportStatus,
            name="import_status",
            values_callable=enum_values,
        ),
        nullable=False,
        default=ImportStatus.PENDING,
    )
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    accepted_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    schema_fields: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )


class Observation(Base, TimestampMixin):
    __tablename__ = "observations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "import_id"],
            ["imports.workspace_id", "imports.id"],
            name="fk_observations_workspace_import",
            ondelete="CASCADE",
        ),
        UniqueConstraint("workspace_id", "id", name="uq_observations_workspace_id_id"),
        UniqueConstraint(
            "workspace_id",
            "import_id",
            "external_record_id",
            name="uq_observations_import_external_record",
        ),
        Index("ix_observations_workspace_identity", "workspace_id", "identity_value"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    import_id: Mapped[UUID] = mapped_column(nullable=False)
    external_record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    identity_value: Mapped[str | None] = mapped_column(String(320))
    normalized_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    original_evidence: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rejected_reason: Mapped[str | None] = mapped_column(String(100))
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Rule(Base, TimestampMixin):
    __tablename__ = "rules"
    __table_args__ = (
        UniqueConstraint("workspace_id", "id", name="uq_rules_workspace_id_id"),
        UniqueConstraint("workspace_id", "version", name="uq_rules_workspace_version"),
        CheckConstraint("version > 0", name="positive_version"),
        CheckConstraint("wait_seconds >= 0", name="nonnegative_wait_seconds"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    identity_field: Mapped[str] = mapped_column(String(100), nullable=False)
    required_fields: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    exclusions: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    wait_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    timezone: Mapped[str] = mapped_column(String(100), nullable=False, default="UTC")


class ReconciliationRun(Base, TimestampMixin):
    __tablename__ = "reconciliation_runs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "source_import_id"],
            ["imports.workspace_id", "imports.id"],
            name="fk_runs_workspace_source_import",
        ),
        ForeignKeyConstraint(
            ["workspace_id", "destination_import_id"],
            ["imports.workspace_id", "imports.id"],
            name="fk_runs_workspace_destination_import",
        ),
        ForeignKeyConstraint(
            ["workspace_id", "rule_id"],
            ["rules.workspace_id", "rules.id"],
            name="fk_runs_workspace_rule",
        ),
        UniqueConstraint(
            "workspace_id", "id", name="uq_reconciliation_runs_workspace_id_id"
        ),
        UniqueConstraint(
            "workspace_id",
            "idempotency_key",
            name="uq_reconciliation_runs_workspace_idempotency_key",
        ),
        CheckConstraint(
            "source_import_id <> destination_import_id",
            name="distinct_imports",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    source_import_id: Mapped[UUID] = mapped_column(nullable=False)
    destination_import_id: Mapped[UUID] = mapped_column(nullable=False)
    rule_id: Mapped[UUID] = mapped_column(nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[RunStatus] = mapped_column(
        SqlEnum(
            RunStatus,
            name="run_status",
            values_callable=enum_values,
        ),
        nullable=False,
        default=RunStatus.PENDING,
    )
    coverage: Mapped[CoverageStatus] = mapped_column(
        SqlEnum(
            CoverageStatus,
            name="coverage_status",
            values_callable=enum_values,
            create_type=False,
        ),
        nullable=False,
    )
    result_counts: Mapped[dict[str, int]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ReconciliationResult(Base, TimestampMixin):
    __tablename__ = "reconciliation_results"
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "run_id"],
            ["reconciliation_runs.workspace_id", "reconciliation_runs.id"],
            name="fk_results_workspace_run",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["workspace_id", "source_observation_id"],
            ["observations.workspace_id", "observations.id"],
            name="fk_results_workspace_source_observation",
        ),
        UniqueConstraint(
            "workspace_id", "id", name="uq_reconciliation_results_workspace_id_id"
        ),
        UniqueConstraint(
            "workspace_id",
            "run_id",
            "source_observation_id",
            name="uq_reconciliation_results_run_source",
        ),
        Index("ix_results_workspace_category", "workspace_id", "category"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    run_id: Mapped[UUID] = mapped_column(nullable=False)
    source_observation_id: Mapped[UUID] = mapped_column(nullable=False)
    category: Mapped[ResultCategory] = mapped_column(
        SqlEnum(
            ResultCategory,
            name="result_category",
            values_callable=enum_values,
        ),
        nullable=False,
    )
    reason_code: Mapped[str] = mapped_column(String(100), nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )


class ResultCandidate(Base, TimestampMixin):
    __tablename__ = "result_candidates"
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "result_id"],
            ["reconciliation_results.workspace_id", "reconciliation_results.id"],
            name="fk_candidates_workspace_result",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["workspace_id", "destination_observation_id"],
            ["observations.workspace_id", "observations.id"],
            name="fk_candidates_workspace_destination_observation",
        ),
        UniqueConstraint(
            "workspace_id", "id", name="uq_result_candidates_workspace_id_id"
        ),
        UniqueConstraint(
            "workspace_id",
            "result_id",
            "destination_observation_id",
            name="uq_result_candidates_result_destination",
        ),
        CheckConstraint("rank > 0", name="positive_rank"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    result_id: Mapped[UUID] = mapped_column(nullable=False)
    destination_observation_id: Mapped[UUID] = mapped_column(nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    match_basis: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )


class Review(Base, TimestampMixin):
    __tablename__ = "reviews"
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "result_id"],
            ["reconciliation_results.workspace_id", "reconciliation_results.id"],
            name="fk_reviews_workspace_result",
            ondelete="CASCADE",
        ),
        UniqueConstraint("workspace_id", "id", name="uq_reviews_workspace_id_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    result_id: Mapped[UUID] = mapped_column(nullable=False)
    reviewer: Mapped[str] = mapped_column(String(200), nullable=False)
    annotation: Mapped[str] = mapped_column(Text, nullable=False)


class Connector(Base, TimestampMixin):
    """Read-only provider configuration with an encrypted credential."""

    __tablename__ = "connectors"
    __table_args__ = (
        UniqueConstraint("workspace_id", "id", name="uq_connectors_workspace_id_id"),
        UniqueConstraint("workspace_id", "name", name="uq_connectors_workspace_name"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[ConnectorProvider] = mapped_column(
        SqlEnum(
            ConnectorProvider,
            name="connector_provider",
            values_callable=enum_values,
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    encrypted_credential: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    credential_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"Connector(id={self.id!r}, provider={self.provider!r}, "
            "encrypted_credential=<redacted>)"
        )


class ConnectorSync(Base, TimestampMixin):
    """One manual read of a connector and the checkpoint it proved."""

    __tablename__ = "connector_syncs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "connector_id"],
            ["connectors.workspace_id", "connectors.id"],
            name="fk_connector_syncs_workspace_connector",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["workspace_id", "import_id"],
            ["imports.workspace_id", "imports.id"],
            name="fk_connector_syncs_workspace_import",
        ),
        UniqueConstraint(
            "workspace_id", "id", name="uq_connector_syncs_workspace_id_id"
        ),
        CheckConstraint("record_count >= 0", name="nonnegative_record_count"),
        CheckConstraint(
            "checkpoint_after IS NULL OR coverage = 'complete'",
            name="checkpoint_requires_complete_coverage",
        ),
        Index(
            "ix_connector_syncs_workspace_connector",
            "workspace_id",
            "connector_id",
            "started_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    connector_id: Mapped[UUID] = mapped_column(nullable=False)
    import_id: Mapped[UUID | None] = mapped_column()
    coverage: Mapped[CoverageStatus] = mapped_column(
        SqlEnum(
            CoverageStatus,
            name="coverage_status",
            values_callable=enum_values,
            create_type=False,
        ),
        nullable=False,
    )
    record_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    issues: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    checkpoint_before: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    checkpoint_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
