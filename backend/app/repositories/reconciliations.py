from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Observation,
    ReconciliationResult,
    ReconciliationRun,
    ResultCandidate,
    ResultCategory,
    Review,
    Rule,
)


async def find_rule(
    session: AsyncSession, workspace_id: UUID, rule_id: UUID
) -> Rule | None:
    return cast(
        Rule | None,
        await session.scalar(
            select(Rule).where(Rule.workspace_id == workspace_id, Rule.id == rule_id)
        ),
    )


async def find_run(
    session: AsyncSession, workspace_id: UUID, run_id: UUID
) -> ReconciliationRun | None:
    return cast(
        ReconciliationRun | None,
        await session.scalar(
            select(ReconciliationRun).where(
                ReconciliationRun.workspace_id == workspace_id,
                ReconciliationRun.id == run_id,
            )
        ),
    )


async def find_run_by_idempotency_key(
    session: AsyncSession, workspace_id: UUID, key: str
) -> ReconciliationRun | None:
    return cast(
        ReconciliationRun | None,
        await session.scalar(
            select(ReconciliationRun).where(
                ReconciliationRun.workspace_id == workspace_id,
                ReconciliationRun.idempotency_key == key,
            )
        ),
    )


async def accepted_observations(
    session: AsyncSession, workspace_id: UUID, import_id: UUID
) -> list[Observation]:
    return list(
        (
            await session.scalars(
                select(Observation)
                .where(
                    Observation.workspace_id == workspace_id,
                    Observation.import_id == import_id,
                    Observation.rejected_reason.is_(None),
                )
                .order_by(Observation.external_record_id)
            )
        ).all()
    )


async def query_results(
    session: AsyncSession,
    workspace_id: UUID,
    run_id: UUID,
    category: ResultCategory | None,
    offset: int,
    limit: int,
) -> tuple[list[ReconciliationResult], int]:
    filters = [
        ReconciliationResult.workspace_id == workspace_id,
        ReconciliationResult.run_id == run_id,
    ]
    if category is not None:
        filters.append(ReconciliationResult.category == category)
    total = await session.scalar(
        select(func.count()).select_from(ReconciliationResult).where(*filters)
    )
    results = list(
        (
            await session.scalars(
                select(ReconciliationResult)
                .join(
                    Observation,
                    (Observation.id == ReconciliationResult.source_observation_id)
                    & (Observation.workspace_id == ReconciliationResult.workspace_id),
                )
                .where(*filters)
                .order_by(Observation.external_record_id)
                .offset(offset)
                .limit(limit)
            )
        ).all()
    )
    return results, int(total or 0)


async def find_result(
    session: AsyncSession, workspace_id: UUID, result_id: UUID
) -> ReconciliationResult | None:
    return cast(
        ReconciliationResult | None,
        await session.scalar(
            select(ReconciliationResult).where(
                ReconciliationResult.workspace_id == workspace_id,
                ReconciliationResult.id == result_id,
            )
        ),
    )


async def find_observation(
    session: AsyncSession, workspace_id: UUID, observation_id: UUID
) -> Observation:
    observation = await session.scalar(
        select(Observation).where(
            Observation.workspace_id == workspace_id,
            Observation.id == observation_id,
        )
    )
    assert isinstance(observation, Observation)
    return observation


async def result_candidates(
    session: AsyncSession, workspace_id: UUID, result_id: UUID
) -> list[tuple[ResultCandidate, Observation]]:
    rows = await session.execute(
        select(ResultCandidate, Observation)
        .join(
            Observation,
            (Observation.id == ResultCandidate.destination_observation_id)
            & (Observation.workspace_id == ResultCandidate.workspace_id),
        )
        .where(
            ResultCandidate.workspace_id == workspace_id,
            ResultCandidate.result_id == result_id,
        )
        .order_by(ResultCandidate.rank)
    )
    return list(rows.tuples())


async def result_reviews(
    session: AsyncSession, workspace_id: UUID, result_id: UUID
) -> list[Review]:
    return list(
        (
            await session.scalars(
                select(Review)
                .where(
                    Review.workspace_id == workspace_id,
                    Review.result_id == result_id,
                )
                .order_by(Review.created_at, Review.id)
            )
        ).all()
    )
