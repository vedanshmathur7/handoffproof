import asyncio
from datetime import datetime

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

HUBSPOT_PROPERTIES = "email,firstname,lastname,company,region"
# Private apps on Free/Starter get 100 requests per 10 seconds per app.
HUBSPOT_MIN_INTERVAL_SECONDS = 0.1


class HubSpotConnector:
    """Read-only CRM contacts client; it has no write-capable method."""

    def __init__(
        self,
        token: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        self._http = ReadOnlyJsonClient(
            base_url="https://api.hubapi.com",
            token=token,
            transport=transport,
            min_interval_seconds=HUBSPOT_MIN_INTERVAL_SECONDS,
            sleep=sleep,
        )

    async def read_contacts(self) -> ConnectorSnapshot:
        records: list[ConnectorRecord] = []
        seen: set[str] = set()
        latest: datetime | None = None
        after: str | None = None
        malformed = False
        try:
            while True:
                params: dict[str, str | int] = {
                    "limit": 100,
                    "properties": HUBSPOT_PROPERTIES,
                }
                if after is not None:
                    params["after"] = after
                payload = await self._http.get_json("/crm/v3/objects/contacts", params)
                items = payload.get("results")
                if not isinstance(items, list):
                    raise ConnectorError(
                        "CONNECTOR_RESPONSE_INVALID", "HubSpot results are missing."
                    )
                for item in items:
                    record = self._record(item)
                    if record is None:
                        malformed = True
                    elif record.external_record_id not in seen:
                        seen.add(record.external_record_id)
                        records.append(record)
                        if record.observed_at is not None and (
                            latest is None or record.observed_at > latest
                        ):
                            latest = record.observed_at
                paging = payload.get("paging")
                next_page = paging.get("next") if isinstance(paging, dict) else None
                after = next_page.get("after") if isinstance(next_page, dict) else None
                if not isinstance(after, str):
                    break
        except ConnectorError as exc:
            return ConnectorSnapshot(
                provider=ConnectorProvider.HUBSPOT,
                kind=ImportKind.DESTINATION,
                records=tuple(records),
                coverage=CoverageStatus.PARTIAL if records else CoverageStatus.FAILED,
                watermark=latest,
                continuation=after,
                issues=(exc.code,),
            )
        return ConnectorSnapshot(
            provider=ConnectorProvider.HUBSPOT,
            kind=ImportKind.DESTINATION,
            records=tuple(records),
            coverage=(
                CoverageStatus.PARTIAL if malformed else CoverageStatus.COMPLETE
            ),
            watermark=latest,
            issues=("CONNECTOR_MALFORMED_RECORD",) if malformed else (),
        )

    def _record(self, item: object) -> ConnectorRecord | None:
        if not isinstance(item, dict):
            return None
        contact_id = item.get("id")
        created_at = item.get("createdAt")
        properties = item.get("properties")
        if not isinstance(contact_id, str) or not isinstance(created_at, str):
            return None
        if not isinstance(properties, dict):
            properties = {}
        first_name = _text(properties.get("firstname"))
        last_name = _text(properties.get("lastname"))
        fields = {
            "destination_record_id": contact_id,
            "created_at": created_at,
            "email": _text(properties.get("email")),
            "full_name": " ".join(part for part in (first_name, last_name) if part),
            "company": _text(properties.get("company")),
            "region": _text(properties.get("region")),
        }
        return ConnectorRecord(
            external_record_id=contact_id,
            fields=fields,
            observed_at=parse_timestamp(created_at),
            original_evidence={"provider": "hubspot", "contact": item},
        )


def _text(value: object) -> str:
    return value if isinstance(value, str) else ""
