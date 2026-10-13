import asyncio
import time
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

import httpx

from app.connectors.models import ConnectorError

Sleep = Callable[[float], Awaitable[None]]
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
MAX_RETRY_DELAY_SECONDS = 10.0


class ReadOnlyJsonClient:
    """Small HTTP wrapper that exposes GET only and never logs credentials.

    Requests are spaced by ``min_interval_seconds`` to respect provider burst
    limits, and retryable failures wait for ``Retry-After`` (capped) or a short
    exponential backoff before the bounded next attempt.
    """

    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        transport: httpx.AsyncBaseTransport | None = None,
        max_attempts: int = 2,
        min_interval_seconds: float = 0.0,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._transport = transport
        self._max_attempts = max_attempts
        self._min_interval = min_interval_seconds
        self._sleep = sleep
        self._last_request: float | None = None

    def __repr__(self) -> str:
        return f"ReadOnlyJsonClient(base_url={self._base_url!r}, token='***')"

    async def _throttle(self) -> None:
        if self._last_request is not None and self._min_interval > 0:
            wait = self._min_interval - (time.monotonic() - self._last_request)
            if wait > 0:
                await self._sleep(wait)
        self._last_request = time.monotonic()

    async def get_json(
        self, path: str, params: Mapping[str, str | int] | None = None
    ) -> dict[str, Any]:
        for attempt in range(self._max_attempts):
            await self._throttle()
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
                await self._sleep(_backoff(attempt))
                continue

            if response.status_code in RETRYABLE_STATUS:
                if attempt + 1 < self._max_attempts:
                    await self._sleep(_retry_delay(response, attempt))
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


def _backoff(attempt: int) -> float:
    return float(min(2**attempt, MAX_RETRY_DELAY_SECONDS))


def _retry_delay(response: httpx.Response, attempt: int) -> float:
    raw = response.headers.get("Retry-After")
    if raw is not None:
        try:
            return max(0.0, min(float(raw), MAX_RETRY_DELAY_SECONDS))
        except ValueError:
            pass
    return _backoff(attempt)
