from datetime import datetime, timedelta
from typing import Any

from app.domain.models import (
    CandidateMatch,
    Classification,
    CoverageStatus,
    ObservationData,
    ResultCategory,
    RuleData,
)


def normalize_scalar(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list, tuple, set)):
        return None
    normalized = " ".join(str(value).strip().split()).casefold()
    return normalized or None


def classify_source(
    source: ObservationData,
    destinations: tuple[ObservationData, ...],
    rule: RuleData,
    coverage: CoverageStatus,
    evaluated_at: datetime,
) -> Classification:
    common_evidence: dict[str, Any] = {
        "source_record_id": source.external_record_id,
        "rule_version": rule.version,
        "evaluated_at": evaluated_at.isoformat(),
        "coverage": coverage.value,
    }

    if coverage != CoverageStatus.COMPLETE:
        reason = (
            "DESTINATION_COVERAGE_FAILED"
            if coverage == CoverageStatus.FAILED
            else "DESTINATION_COVERAGE_PARTIAL"
        )
        return Classification(ResultCategory.UNKNOWN, reason, common_evidence)

    eligibility = normalize_scalar(source.normalized_data.get(rule.eligibility_field))
    if eligibility != normalize_scalar(rule.eligibility_value):
        return Classification(
            ResultCategory.EXCLUDED,
            "RULE_EXCLUDED",
            {
                **common_evidence,
                "eligibility": {
                    "field": rule.eligibility_field,
                    "actual": eligibility,
                    "expected": normalize_scalar(rule.eligibility_value),
                },
            },
        )

    if source.observed_at is None:
        return Classification(
            ResultCategory.UNKNOWN,
            "SOURCE_TIME_MISSING",
            common_evidence,
        )
    wait_until = source.observed_at + timedelta(seconds=rule.wait_seconds)
    if evaluated_at < wait_until:
        return Classification(
            ResultCategory.UNKNOWN,
            "WAIT_WINDOW_OPEN",
            {**common_evidence, "wait_until": wait_until.isoformat()},
        )

    raw_identity = source.normalized_data.get(rule.identity_field)
    identity = normalize_scalar(raw_identity)
    if identity is None:
        reason = (
            "IDENTITY_AMBIGUOUS"
            if isinstance(raw_identity, (dict, list, tuple, set))
            else "IDENTITY_MISSING"
        )
        return Classification(ResultCategory.UNKNOWN, reason, common_evidence)

    matched_destinations = tuple(
        destination
        for destination in destinations
        if normalize_scalar(destination.normalized_data.get(rule.identity_field))
        == identity
    )
    candidates = tuple(
        CandidateMatch(
            observation_id=destination.id,
            external_record_id=destination.external_record_id,
            rank=rank,
            match_basis={"field": rule.identity_field, "value": identity},
        )
        for rank, destination in enumerate(matched_destinations, start=1)
    )
    evidence = {
        **common_evidence,
        "identity": {"field": rule.identity_field, "normalized_value": identity},
        "candidate_count": len(candidates),
    }

    if not candidates:
        return Classification(
            ResultCategory.MISSING,
            "NO_CANDIDATE_AFTER_WAIT",
            evidence,
        )
    if len(candidates) > 1:
        return Classification(
            ResultCategory.DUPLICATE,
            "MULTIPLE_IDENTITY_MATCHES",
            evidence,
            candidates,
        )

    destination = matched_destinations[0]
    differences = []
    for field_name in rule.required_fields:
        source_value = normalize_scalar(source.normalized_data.get(field_name))
        destination_value = normalize_scalar(
            destination.normalized_data.get(field_name)
        )
        if source_value != destination_value:
            differences.append(
                {
                    "field": field_name,
                    "source": source_value,
                    "destination": destination_value,
                }
            )
    evidence["differences"] = differences
    if differences:
        return Classification(
            ResultCategory.FIELD_MISMATCH,
            "REQUIRED_FIELD_MISMATCH",
            evidence,
            candidates,
        )
    return Classification(
        ResultCategory.MATCHED,
        "EXACT_MATCH",
        evidence,
        candidates,
    )
