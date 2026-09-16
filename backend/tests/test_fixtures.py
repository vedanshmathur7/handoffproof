import csv
import json
from pathlib import Path
from typing import Any

from app.models import ResultCategory

FIXTURES = Path(__file__).parent / "fixtures"
SOURCE_HEADERS = [
    "source_record_id",
    "submitted_at",
    "email",
    "full_name",
    "company",
    "region",
    "transfer_enabled",
]
DESTINATION_HEADERS = [
    "destination_record_id",
    "created_at",
    "email",
    "full_name",
    "company",
    "region",
]


def read_csv(name: str) -> tuple[list[str], list[dict[str, str]]]:
    with (FIXTURES / name).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def test_csv_headers_and_manifest_are_frozen() -> None:
    source_headers, source_rows = read_csv("source.csv")
    destination_headers, _ = read_csv("destination.csv")
    manifest: dict[str, Any] = json.loads(
        (FIXTURES / "fixture_manifest.json").read_text(encoding="utf-8")
    )

    assert source_headers == SOURCE_HEADERS
    assert destination_headers == DESTINATION_HEADERS
    assert {row["source_record_id"] for row in source_rows} == {
        case["source_record_id"] for case in manifest["cases"]
    }
    assert {case["category"] for case in manifest["cases"]} == {
        category.value for category in ResultCategory
    }
    assert all(case["reason_code"] for case in manifest["cases"])


def test_duplicate_and_mismatch_evidence_is_present() -> None:
    _, destination_rows = read_csv("destination.csv")
    duplicate_rows = [
        row
        for row in destination_rows
        if row["email"] == "duplicate@example.test"
    ]
    mismatch_row = next(
        row
        for row in destination_rows
        if row["email"] == "mismatch@example.test"
    )

    assert len(duplicate_rows) == 2
    assert mismatch_row["company"] == "Wrong Company"


def test_partial_and_malformed_scenarios_are_explicit() -> None:
    _, partial_rows = read_csv("partial_destination.csv")
    _, malformed_rows = read_csv("malformed_source.csv")
    manifest: dict[str, Any] = json.loads(
        (FIXTURES / "fixture_manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["partial_inputs"]["destination_coverage"] == "partial"
    assert len(partial_rows) == 1
    assert len(malformed_rows) == manifest["malformed_source"][
        "expected_rejected_rows"
    ]
    assert len(manifest["malformed_source"]["reason_codes"]) == len(
        malformed_rows
    )
