import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.connectors.http import ReadOnlyJsonClient, Sleep
from app.connectors.models import (
    ConnectorError,
    ConnectorProvider,
    ConnectorRecord,
    ConnectorSnapshot,
)
from app.models import CoverageStatus, ImportKind
from app.services.imports import parse_timestamp

# Typeform documents that responses from roughly the last 30 minutes may not be
# returned yet, so the checkpoint never advances past this boundary.
TYPEFORM_INDEXING_DELAY = timedelta(minutes=30)
# Typeform allows two Responses API requests per second per account.
TYPEFORM_MIN_INTERVAL_SECONDS = 0.5


class TypeformConnector:
    """Read-only Responses API client using the responses:read scope."""

    def __init__(
        self,
        token: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        page_size: int = 1000,
        sleep: Sleep = asyncio.sleep,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        if page_size < 1 or page_size > 1000:
            raise ValueError("Typeform page size must be between 1 and 1000.")
        self._http = ReadOnlyJsonClient(
            base_url="https://api.typeform.com",
            token=token,
            transport=transport,
            min_interval_seconds=TYPEFORM_MIN_INTERVAL_SECONDS,
            sleep=sleep,
        )
        self._page_size = page_size
        self._now = now

    async def read_responses(
        self,
        *,
        form_id: str,
        field_refs: dict[str, str],
        since: datetime | None,
        overlap_seconds: int = 300,
    ) -> ConnectorSnapshot:
        if since is not None and since.tzinfo is None:
            raise ValueError("Typeform checkpoint must be timezone-aware.")
        read_at = self._now()
        params: dict[str, str | int] = {"page_size": self._page_size}
        if since is not None:
            start = since.astimezone(UTC) - timedelta(seconds=overlap_seconds)
            params["since"] = start.strftime("%Y-%m-%dT%H:%M:%S")
        safe_boundary = read_at - TYPEFORM_INDEXING_DELAY
        if since is not None and since > safe_boundary:
            safe_boundary = since

        records: list[ConnectorRecord] = []
        seen: set[str] = set()
        before: str | None = None
        malformed = False
        try:
            while True:
                request_params = dict(params)
                if before is not None:
                    request_params["before"] = before
                payload = await self._http.get_json(
                    f"/forms/{form_id}/responses", request_params
                )
                items = payload.get("items")
                if not isinstance(items, list):
                    raise ConnectorError(
                        "CONNECTOR_RESPONSE_INVALID", "Typeform items are missing."
                    )
                for item in items:
                    record = self._record(item, field_refs)
                    if record is None:
                        malformed = True
                    elif record.external_record_id not in seen:
                        seen.add(record.external_record_id)
                        records.append(record)
                if len(items) < self._page_size:
                    break
                before = _cursor(items[-1])
        except ConnectorError as exc:
            return ConnectorSnapshot(
                provider=ConnectorProvider.TYPEFORM,
                kind=ImportKind.SOURCE,
                records=tuple(records),
                coverage=CoverageStatus.PARTIAL if records else CoverageStatus.FAILED,
                watermark=None,
                continuation=before,
                issues=(exc.code,),
            )
        return ConnectorSnapshot(
            provider=ConnectorProvider.TYPEFORM,
            kind=ImportKind.SOURCE,
            records=tuple(records),
            coverage=(
                CoverageStatus.PARTIAL if malformed else CoverageStatus.COMPLETE
            ),
            watermark=safe_boundary,
            issues=("CONNECTOR_MALFORMED_RECORD",) if malformed else (),
        )

    def _record(
        self, item: object, field_refs: dict[str, str]
    ) -> ConnectorRecord | None:
        if not isinstance(item, dict):
            return None
        response_id = item.get("response_id")
        submitted_at = item.get("submitted_at")
        if not isinstance(response_id, str) or not isinstance(submitted_at, str):
            return None
        answers: dict[str, str] = {}
        raw_answers = item.get("answers", [])
        if isinstance(raw_answers, list):
            for answer in raw_answers:
                if not isinstance(answer, dict):
                    continue
                field = answer.get("field")
                ref = field.get("ref") if isinstance(field, dict) else None
                if isinstance(ref, str):
                    value = _answer_value(answer)
                    if value is not None:
                        answers[ref] = value
        fields = {
            "source_record_id": response_id,
            "submitted_at": submitted_at,
            **{name: answers.get(ref, "") for name, ref in field_refs.items()},
        }
        return ConnectorRecord(
            external_record_id=response_id,
            fields=fields,
            observed_at=parse_timestamp(submitted_at),
            original_evidence={"provider": "typeform", "response": item},
        )


def _cursor(item: object) -> str:
    """Typeform paginates with the response ``token``; response_id is a fallback."""
    if isinstance(item, dict):
        for key in ("token", "response_id"):
            value = item.get(key)
            if isinstance(value, str) and value:
                return value
    raise ConnectorError("CONNECTOR_RESPONSE_INVALID", "Typeform page has no cursor.")


def _answer_value(answer: dict[str, Any]) -> str | None:
    for key in ("email", "text", "boolean", "number", "date", "url"):
        value = answer.get(key)
        if isinstance(value, (str, bool, int, float)):
            return str(value).lower() if isinstance(value, bool) else str(value)
    choice = answer.get("choice")
    if isinstance(choice, dict) and isinstance(choice.get("label"), str):
        label = choice["label"]
        assert isinstance(label, str)
        return label
    return None
