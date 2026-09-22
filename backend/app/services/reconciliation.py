import csv
import io
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ApiError
from app.api.schemas import (
    CandidateRead,
    ReconciliationCreate,
    ReconciliationSummary,
    ResultPage,
    ResultRead,
    ReviewCreate,
    ReviewRead,
    RuleReference,
)
from app.domain.matching import classify_source
from app.domain.models import ObservationData, RuleData
from app.models import (
    CoverageStatus,
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
)
from app.repositories.imports import find_import, lock_workspace
from app.repositories.reconciliations import (
    accepted_observations,
    find_observation,
    find_result,
    find_rule,
    find_run,
    find_run_by_idempotency_key,
    query_results,
    result_candidates,
    result_reviews,
)


def combined_coverage(
    source: CoverageStatus, destination: CoverageStatus
) -> CoverageStatus:
    if CoverageStatus.FAILED in {source, destination}:
        return CoverageStatus.FAILED
    if CoverageStatus.PARTIAL in {source, destination}:
        return CoverageStatus.PARTIAL
    return CoverageStatus.COMPLETE


def observation_data(observation: Observation) -> ObservationData:
    return ObservationData(
        id=observation.id,
        external_record_id=observation.external_record_id,
        normalized_data=observation.normalized_data,
        original_evidence=observation.original_evidence,
        observed_at=observation.observed_at,
    )


def rule_data(rule: Rule) -> RuleData:
    if not rule.exclusions:
        raise ApiError(
            422, "RULE_ELIGIBILITY_MISSING", "Rule has no eligibility condition."
        )
    eligibility = rule.exclusions[0]
    return RuleData(
        version=rule.version,
        identity_field=rule.identity_field,
        required_fields=tuple(rule.required_fields),
        eligibility_field=str(eligibility["field"]),
        eligibility_value=str(eligibility["value"]),
        wait_seconds=rule.wait_seconds,
        timezone=rule.timezone,
    )


async def run_to_summary(
    session: AsyncSession, run: ReconciliationRun
) -> ReconciliationSummary:
    rule = await find_rule(session, run.workspace_id, run.rule_id)
    assert rule is not None
    return ReconciliationSummary(
        id=run.id,
        workspace_id=run.workspace_id,
        source_import_id=run.source_import_id,
        destination_import_id=run.destination_import_id,
        rule_id=run.rule_id,
        rule_version=rule.version,
        status=run.status,
        coverage=run.coverage,
        result_counts=run.result_counts,
        started_at=run.started_at,
        completed_at=run.completed_at,
        created_at=run.created_at,
    )


async def create_reconciliation(
    session: AsyncSession, data: ReconciliationCreate
) -> tuple[ReconciliationSummary, bool]:
    if await lock_workspace(session, data.workspace_id) is None:
        raise ApiError(404, "WORKSPACE_NOT_FOUND", "Workspace was not found.")
    existing = await find_run_by_idempotency_key(
        session, data.workspace_id, data.idempotency_key
    )
    if existing is not None:
        same_request = (
            existing.source_import_id == data.source_import_id
            and existing.destination_import_id == data.destination_import_id
            and existing.rule_id == data.rule_id
        )
        if not same_request:
            raise ApiError(
                409,
                "IDEMPOTENCY_KEY_REUSED",
                "Idempotency key already belongs to different inputs.",
            )
        return await run_to_summary(session, existing), False

    source_import = await find_import(session, data.workspace_id, data.source_import_id)
    destination_import = await find_import(
        session, data.workspace_id, data.destination_import_id
    )
    rule = await find_rule(session, data.workspace_id, data.rule_id)
    if source_import is None or source_import.kind != ImportKind.SOURCE:
        raise ApiError(
            422, "SOURCE_IMPORT_INVALID", "A completed source import is required."
        )
    if destination_import is None or destination_import.kind != ImportKind.DESTINATION:
        raise ApiError(
            422,
            "DESTINATION_IMPORT_INVALID",
            "A completed destination import is required.",
        )
    if rule is None:
        raise ApiError(422, "RULE_INVALID", "A rule from this workspace is required.")
    if (
        source_import.status != ImportStatus.COMPLETED
        or destination_import.status != ImportStatus.COMPLETED
    ):
        raise ApiError(
            422, "IMPORT_NOT_READY", "Both imports must contain accepted rows."
        )

    evaluated_at = data.evaluated_at or datetime.now(UTC)
    if evaluated_at.tzinfo is None:
        raise ApiError(
            422,
            "EVALUATED_AT_TIMEZONE_REQUIRED",
            "Evaluation time must include a timezone.",
        )
    now = datetime.now(UTC)
    coverage = combined_coverage(source_import.coverage, destination_import.coverage)
    run = ReconciliationRun(
        workspace_id=data.workspace_id,
        source_import_id=source_import.id,
        destination_import_id=destination_import.id,
        rule_id=rule.id,
        idempotency_key=data.idempotency_key,
        status=RunStatus.RUNNING,
        coverage=coverage,
        result_counts={},
        started_at=now,
    )
    session.add(run)
    await session.flush()

    sources = await accepted_observations(session, data.workspace_id, source_import.id)
    destinations = await accepted_observations(
        session, data.workspace_id, destination_import.id
    )
    destination_data = tuple(observation_data(item) for item in destinations)
    configured_rule = rule_data(rule)
    counts = {category.value: 0 for category in ResultCategory}

    for source in sources:
        classification = classify_source(
            observation_data(source),
            destination_data,
            configured_rule,
            coverage,
            evaluated_at,
        )
        result = ReconciliationResult(
            workspace_id=data.workspace_id,
            run_id=run.id,
            source_observation_id=source.id,
            category=classification.category,
            reason_code=classification.reason_code,
            evidence=classification.evidence,
        )
        session.add(result)
        await session.flush()
        session.add_all(
            [
                ResultCandidate(
                    workspace_id=data.workspace_id,
                    result_id=result.id,
                    destination_observation_id=candidate.observation_id,
                    rank=candidate.rank,
                    match_basis=candidate.match_basis,
                )
                for candidate in classification.candidates
            ]
        )
        counts[classification.category.value] += 1

    run.status = RunStatus.COMPLETED
    run.result_counts = counts
    run.completed_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(run)
    return await run_to_summary(session, run), True


async def read_reconciliation(
    session: AsyncSession, workspace_id: UUID, run_id: UUID
) -> ReconciliationSummary:
    run = await find_run(session, workspace_id, run_id)
    if run is None:
        raise ApiError(
            404,
            "RECONCILIATION_NOT_FOUND",
            "Reconciliation was not found in this workspace.",
        )
    return await run_to_summary(session, run)


def rule_reference(rule: Rule) -> RuleReference:
    return RuleReference(
        id=rule.id,
        version=rule.version,
        name=rule.name,
        identity_field=rule.identity_field,
        required_fields=rule.required_fields,
        wait_seconds=rule.wait_seconds,
        timezone=rule.timezone,
    )


async def result_to_read(
    session: AsyncSession,
    result: ReconciliationResult,
    rule: Rule,
) -> ResultRead:
    source = await find_observation(
        session, result.workspace_id, result.source_observation_id
    )
    candidate_rows = await result_candidates(session, result.workspace_id, result.id)
    reviews = await result_reviews(session, result.workspace_id, result.id)
    return ResultRead(
        id=result.id,
        run_id=result.run_id,
        source_observation_id=result.source_observation_id,
        source_record_id=source.external_record_id,
        category=result.category,
        reason_code=result.reason_code,
        evidence=result.evidence,
        source_evidence=source.original_evidence,
        candidates=[
            CandidateRead(
                destination_observation_id=candidate.destination_observation_id,
                external_record_id=destination.external_record_id,
                rank=candidate.rank,
                match_basis=candidate.match_basis,
                original_evidence=destination.original_evidence,
            )
            for candidate, destination in candidate_rows
        ],
        reviews=[
            ReviewRead(
                id=review.id,
                reviewer=review.reviewer,
                annotation=review.annotation,
                created_at=review.created_at,
            )
            for review in reviews
        ],
        rule=rule_reference(rule),
        created_at=result.created_at,
    )


async def read_results(
    session: AsyncSession,
    workspace_id: UUID,
    run_id: UUID,
    category: ResultCategory | None,
    offset: int,
    limit: int,
) -> ResultPage:
    run = await find_run(session, workspace_id, run_id)
    if run is None:
        raise ApiError(
            404,
            "RECONCILIATION_NOT_FOUND",
            "Reconciliation was not found in this workspace.",
        )
    rule = await find_rule(session, workspace_id, run.rule_id)
    assert rule is not None
    results, total = await query_results(
        session, workspace_id, run_id, category, offset, limit
    )
    return ResultPage(
        items=[await result_to_read(session, result, rule) for result in results],
        total=total,
        offset=offset,
        limit=limit,
    )


async def add_review(
    session: AsyncSession, result_id: UUID, data: ReviewCreate
) -> ReviewRead:
    result = await find_result(session, data.workspace_id, result_id)
    if result is None:
        raise ApiError(
            404, "RESULT_NOT_FOUND", "Result was not found in this workspace."
        )
    review = Review(
        workspace_id=data.workspace_id,
        result_id=result.id,
        reviewer=data.reviewer.strip(),
        annotation=data.annotation.strip(),
    )
    session.add(review)
    await session.commit()
    await session.refresh(review)
    return ReviewRead(
        id=review.id,
        reviewer=review.reviewer,
        annotation=review.annotation,
        created_at=review.created_at,
    )


def safe_csv_cell(value: Any) -> str:
    rendered = value if isinstance(value, str) else json.dumps(value, sort_keys=True)
    return f"'{rendered}" if rendered.startswith(("=", "+", "-", "@")) else rendered


async def export_results(
    session: AsyncSession, workspace_id: UUID, run_id: UUID
) -> str:
    page = await read_results(
        session,
        workspace_id,
        run_id,
        category=None,
        offset=0,
        limit=1_000_000,
    )
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "source_record_id",
            "category",
            "reason_code",
            "candidate_record_ids",
            "differences",
            "rule_version",
        ],
    )
    writer.writeheader()
    for item in page.items:
        row: dict[str, Any] = {
            "source_record_id": item.source_record_id,
            "category": item.category.value,
            "reason_code": item.reason_code,
            "candidate_record_ids": [
                candidate.external_record_id for candidate in item.candidates
            ],
            "differences": item.evidence.get("differences", []),
            "rule_version": item.rule.version,
        }
        writer.writerow({key: safe_csv_cell(value) for key, value in row.items()})
    return output.getvalue()
