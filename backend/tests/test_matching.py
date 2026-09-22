import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

import pytest

from app.domain.matching import classify_source, normalize_scalar
from app.domain.models import CoverageStatus, ObservationData, RuleData

FIXTURES = Path(__file__).parent / "fixtures"
MANIFEST = cast(
    dict[str, Any], json.loads((FIXTURES / "fixture_manifest.json").read_text())
)


def load_observations(
    filename: str, id_field: str, time_field: str
) -> list[ObservationData]:
    with (FIXTURES / filename).open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [
        ObservationData(
            id=uuid5(NAMESPACE_URL, row[id_field]),
            external_record_id=row[id_field],
            normalized_data={
                **row,
                "email": row["email"].casefold(),
                **(
                    {"transfer_enabled": row["transfer_enabled"] == "true"}
                    if "transfer_enabled" in row
                    else {}
                ),
            },
            original_evidence=row,
            observed_at=datetime.fromisoformat(row[time_field].replace("Z", "+00:00")),
        )
        for row in rows
    ]


SOURCES = load_observations("source.csv", "source_record_id", "submitted_at")
DESTINATIONS = load_observations(
    "destination.csv", "destination_record_id", "created_at"
)
RULE = RuleData(
    version=1,
    identity_field=cast(str, MANIFEST["identity_field"]),
    required_fields=tuple(cast(list[str], MANIFEST["required_fields"])),
    eligibility_field="transfer_enabled",
    eligibility_value="true",
    wait_seconds=300,
    timezone="UTC",
)
EVALUATED_AT = datetime.fromisoformat("2026-09-02T00:00:00+00:00")


@pytest.mark.parametrize("case", MANIFEST["cases"])
def test_manifest_classifications(case: dict[str, str]) -> None:
    source = next(
        item for item in SOURCES if item.external_record_id == case["source_record_id"]
    )
    coverage = (
        CoverageStatus.PARTIAL
        if case.get("input_set") == "partial_inputs"
        else CoverageStatus.COMPLETE
    )
    result = classify_source(source, tuple(DESTINATIONS), RULE, coverage, EVALUATED_AT)

    assert result.category.value == case["category"]
    assert result.reason_code == case["reason_code"]


def test_partial_coverage_never_returns_a_healthy_result() -> None:
    results = [
        classify_source(
            source,
            tuple(DESTINATIONS),
            RULE,
            CoverageStatus.PARTIAL,
            EVALUATED_AT,
        )
        for source in SOURCES
    ]
    assert len(results) == len(SOURCES)
    assert {result.category.value for result in results} == {"unknown"}
    assert {result.reason_code for result in results} == {
        "DESTINATION_COVERAGE_PARTIAL"
    }


def test_normalization_is_typed_and_deterministic() -> None:
    assert normalize_scalar("  Mira   SHAH ") == "mira shah"
    assert normalize_scalar(True) == "true"
    assert normalize_scalar(False) == "false"
    assert normalize_scalar({"ambiguous": "value"}) is None
