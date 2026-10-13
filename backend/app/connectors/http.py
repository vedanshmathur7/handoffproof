import asyncio
from collections.abc import Mapping
from typing import Any

import httpx

from app.connectors.models import ConnectorError


class ReadOnlyJsonClient:
    """Small HTTP wrapper that exposes GET only and never logs credentials."""

    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        transport: httpx.AsyncBaseTransport | None = None,
        max_attempts: int = 2,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._transport = transport
        self._max_attempts = max_attempts

    async def get_json(
        self, path: str, params: Mapping[str, str | int] | None = None
    ) -> dict[str, Any]:
        for attempt in range(self._max_attempts):
            try:
                async with httpx.AsyncClient(
                    base_url=self._base_url,
                    headers={"Authorization": f"Bearer {self._token}"},
                    timeout=httpx.Timeout(10.0),
                    transport=self._transport,
                ) as client:
                    response = await client.get(path, params=params)
            except httpx.HTTPError as exc:
                if attempt + 1 == self._max_attempts:
                    raise ConnectorError(
                        "CONNECTOR_NETWORK_ERROR", "Provider read failed."
                    ) from exc
                await asyncio.sleep(0)
                continue

            if response.status_code in {429, 500, 502, 503, 504}:
                if attempt + 1 < self._max_attempts:
                    await asyncio.sleep(0)
                    continue
                raise ConnectorError(
                    "CONNECTOR_THROTTLED"
                    if response.status_code == 429
                    else "CONNECTOR_UPSTREAM_ERROR",
                    "Provider read did not complete.",
                )
            if response.status_code >= 400:
                raise ConnectorError(
                    "CONNECTOR_AUTH_FAILED"
                    if response.status_code in {401, 403}
                    else "CONNECTOR_HTTP_ERROR",
                    "Provider rejected the read request.",
                )
            try:
                payload = response.json()
            except ValueError as exc:
                raise ConnectorError(
                    "CONNECTOR_RESPONSE_INVALID", "Provider returned invalid JSON."
                ) from exc
            if not isinstance(payload, dict):
                raise ConnectorError(
                    "CONNECTOR_RESPONSE_INVALID",
                    "Provider returned an invalid response.",
                )
            return payload
        raise AssertionError("retry loop must return or raise")
