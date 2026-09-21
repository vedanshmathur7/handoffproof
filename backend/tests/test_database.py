from collections.abc import Generator
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, delete, func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    CoverageStatus,
    ImportBatch,
    ImportKind,
    ImportStatus,
    Observation,
    ReconciliationResult,
    ReconciliationRun,
    ResultCandidate,
    ResultCategory,
    Review,
    Rule,
    RunStatus,
    Workspace,
)

engine = create_engine(get_settings().database_url)


@pytest.fixture(autouse=True)
def remove_test_workspaces() -> Generator[None, None, None]:
    yield
    with Session(engine) as session:
        session.execute(delete(Workspace).where(Workspace.name.like("test-%")))
        session.commit()


def make_workspace(session: Session, suffix: str) -> Workspace:
    workspace = Workspace(name=f"test-{suffix}-{uuid4()}")
    session.add(workspace)
    session.flush()
    return workspace


def make_import(
    session: Session,
    workspace: Workspace,
    kind: ImportKind,
    checksum: str,
) -> ImportBatch:
    import_batch = ImportBatch(
        workspace_id=workspace.id,
        kind=kind,
        filename=f"{kind.value}.csv",
        checksum=checksum,
        coverage=CoverageStatus.COMPLETE,
        status=ImportStatus.COMPLETED,
        total_rows=1,
        accepted_rows=1,
        rejected_rows=0,
    )
    session.add(import_batch)
    session.flush()
    return import_batch


def make_rule(session: Session, workspace: Workspace) -> Rule:
    rule = Rule(
        workspace_id=workspace.id,
        version=1,
        name="Email identity",
        identity_field="email",
        required_fields=["company"],
        exclusions=[],
        wait_seconds=300,
    )
    session.add(rule)
    session.flush()
    return rule


def test_migration_created_all_tables_and_timezone_timestamps() -> None:
    expected_tables = {
        "workspaces",
        "imports",
        "observations",
        "rules",
        "reconciliation_runs",
        "reconciliation_results",
        "result_candidates",
        "reviews",
    }
    assert expected_tables <= set(inspect(engine).get_table_names())

    with Session(engine) as session:
        workspace = make_workspace(session, "timestamp")
        session.commit()
        session.refresh(workspace)
        assert workspace.created_at.tzinfo is not None


def test_duplicate_observation_is_rejected() -> None:
    with Session(engine) as session:
        workspace = make_workspace(session, "duplicate")
        import_batch = make_import(
            session, workspace, ImportKind.SOURCE, f"source-{uuid4()}"
        )
        first = Observation(
            workspace_id=workspace.id,
            import_id=import_batch.id,
            external_record_id="SRC-1",
            identity_value="same@example.test",
        )
        session.add(first)
        session.commit()

        session.add(
            Observation(
                workspace_id=workspace.id,
                import_id=import_batch.id,
                external_record_id="SRC-1",
                identity_value="same@example.test",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_cross_workspace_reference_is_rejected() -> None:
    with Session(engine) as session:
        workspace_a = make_workspace(session, "workspace-a")
        workspace_b = make_workspace(session, "workspace-b")
        import_a = make_import(
            session, workspace_a, ImportKind.SOURCE, f"cross-{uuid4()}"
        )
        session.commit()

        session.add(
            Observation(
                workspace_id=workspace_b.id,
                import_id=import_a.id,
                external_record_id="ILLEGAL-CROSS-WORKSPACE",
                identity_value="cross@example.test",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_idempotency_key_is_unique_inside_workspace() -> None:
    with Session(engine) as session:
        workspace = make_workspace(session, "idempotency")
        source_import = make_import(
            session, workspace, ImportKind.SOURCE, f"source-{uuid4()}"
        )
        destination_import = make_import(
            session, workspace, ImportKind.DESTINATION, f"destination-{uuid4()}"
        )
        rule = make_rule(session, workspace)
        first_run = ReconciliationRun(
            workspace_id=workspace.id,
            source_import_id=source_import.id,
            destination_import_id=destination_import.id,
            rule_id=rule.id,
            idempotency_key="same-request",
            status=RunStatus.COMPLETED,
            coverage=CoverageStatus.COMPLETE,
        )
        session.add(first_run)
        session.commit()

        session.add(
            ReconciliationRun(
                workspace_id=workspace.id,
                source_import_id=source_import.id,
                destination_import_id=destination_import.id,
                rule_id=rule.id,
                idempotency_key="same-request",
                status=RunStatus.PENDING,
                coverage=CoverageStatus.COMPLETE,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_deleting_workspace_cascades_through_full_graph() -> None:
    with Session(engine) as session:
        workspace = make_workspace(session, "cascade")
        workspace_id = workspace.id
        source_import = make_import(
            session, workspace, ImportKind.SOURCE, f"source-{uuid4()}"
        )
        destination_import = make_import(
            session, workspace, ImportKind.DESTINATION, f"destination-{uuid4()}"
        )
        source_observation = Observation(
            workspace_id=workspace.id,
            import_id=source_import.id,
            external_record_id="SRC-CASCADE",
            identity_value="cascade@example.test",
        )
        destination_observation = Observation(
            workspace_id=workspace.id,
            import_id=destination_import.id,
            external_record_id="DST-CASCADE",
            identity_value="cascade@example.test",
        )
        session.add_all([source_observation, destination_observation])
        rule = make_rule(session, workspace)
        session.flush()
        run = ReconciliationRun(
            workspace_id=workspace.id,
            source_import_id=source_import.id,
            destination_import_id=destination_import.id,
            rule_id=rule.id,
            idempotency_key=f"cascade-{uuid4()}",
            status=RunStatus.COMPLETED,
            coverage=CoverageStatus.COMPLETE,
        )
        session.add(run)
        session.flush()
        result = ReconciliationResult(
            workspace_id=workspace.id,
            run_id=run.id,
            source_observation_id=source_observation.id,
            category=ResultCategory.MATCHED,
            reason_code="EXACT_MATCH",
        )
        session.add(result)
        session.flush()
        session.add_all(
            [
                ResultCandidate(
                    workspace_id=workspace.id,
                    result_id=result.id,
                    destination_observation_id=destination_observation.id,
                    rank=1,
                ),
                Review(
                    workspace_id=workspace.id,
                    result_id=result.id,
                    reviewer="test@example.test",
                    annotation="Confirmed synthetic match.",
                ),
            ]
        )
        session.commit()

        session.delete(workspace)
        session.commit()

        scoped_models = (
            ImportBatch,
            Observation,
            Rule,
            ReconciliationRun,
            ReconciliationResult,
            ResultCandidate,
            Review,
        )
        for model in scoped_models:
            remaining = session.scalar(
                select(func.count())
                .select_from(model)
                .where(model.workspace_id == workspace_id)
            )
            assert remaining == 0
