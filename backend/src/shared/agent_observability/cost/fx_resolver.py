"""USD → tenant currency rate resolver.

Source: ``api.frankfurter.dev`` (free, no auth, ECB-backed). Rates are
daily — we cache by (currency_code, ymd) so a single tenant's calls in a
day pay one network round-trip.

If Frankfurter doesn't list the currency (PEN, COP — common LATAM
markets where Nicolify operates) or the network is down, we fall back to
USD passthrough (rate = 1). The source flag (``fx_unsupported`` /
``fx_unavailable``) lands in ``copilot_llm_call.fx_rate_source`` so
reports can flag estimated rows. **Never raise — best-effort.**
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Protocol

import structlog

if TYPE_CHECKING:
    import datetime as dt

logger = structlog.get_logger()

FRANKFURTER_URL = "https://api.frankfurter.dev/v1/latest"


class _HttpClientLike(Protocol):
    """Minimal interface — covers ``httpx.Client`` and the test mock."""

    def get(self, url: str, **kwargs: Any) -> Any: ...  # noqa: ANN401 — duck-typed response


@dataclass
class FXResolver:
    """Resolve USD → ``currency_code`` rate for a given date.

    ``http_client_factory`` returns a fresh client per call. In production
    this is ``lambda: httpx.Client(timeout=10)``; tests pass a mock
    factory. Cache lives on the resolver instance — one resolver per
    process is enough.
    """

    http_client_factory: Callable[[], _HttpClientLike]
    base_url: str = FRANKFURTER_URL
    _cache: dict[tuple[str, str], Decimal] = field(default_factory=dict)

    @classmethod
    def default(cls) -> FXResolver:
        """Production default: ``httpx`` client with 10 s timeout per fetch.

        Encapsulates the ``lambda: httpx.Client(timeout=10)`` boilerplate
        duplicated across orchestrators (PR-2 PI-1.1, 2026-05-01). Tests
        bypass this and instantiate via ``FXResolver(http_client_factory=mock)``
        directly.

        Per ``tessl__graceful-degradation`` Rule 1: explicit timeout on
        every external call. ``_fetch`` already swallows exceptions and
        returns ``None`` → ``resolve()`` falls back to
        ``(Decimal(1), "fx_unavailable")``.
        """
        import httpx  # local import — only needed in this prod path

        return cls(http_client_factory=lambda: httpx.Client(timeout=10))

    def resolve(self, *, currency_code: str, at_ts: dt.datetime) -> tuple[Decimal, str]:
        """Return ``(rate, source)`` — ``Decimal`` rate + provenance string.

        ``source`` values:

        * ``"passthrough"``     — currency_code is USD; no API call.
        * ``"frankfurter"``     — rate fetched from Frankfurter.
        * ``"fx_unsupported"``  — Frankfurter answered without that currency.
        * ``"fx_unavailable"``  — network/parse error; fallback to 1.0.
        """
        currency = currency_code.upper()
        if currency == "USD":
            return Decimal(1), "passthrough"

        ymd = at_ts.date().isoformat()
        cache_key = (currency, ymd)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached, "frankfurter"

        rate = self._fetch(currency=currency, at_ts=at_ts)
        if rate is None:
            return Decimal(1), "fx_unavailable"
        if rate == Decimal(0):
            # Sentinel for "API responded but currency missing from rates".
            return Decimal(1), "fx_unsupported"

        self._cache[cache_key] = rate
        return rate, "frankfurter"

    def _fetch(self, *, currency: str, at_ts: dt.datetime) -> Decimal | None:
        """Network call. Returns rate, ``Decimal(0)`` for unsupported, or ``None`` on error."""
        try:
            client = self.http_client_factory()
            response = client.get(self.base_url, params={"base": "USD", "symbols": currency})
            raise_for_status = getattr(response, "raise_for_status", None)
            if callable(raise_for_status):
                raise_for_status()
            payload = response.json()
        except Exception as exc:  # noqa: BLE001 — best-effort, never break a turn
            logger.warning(
                "fx_resolver_fetch_failed",
                currency=currency,
                at_ts=at_ts.isoformat(),
                error=str(exc),
            )
            return None

        rates = payload.get("rates", {}) if isinstance(payload, dict) else {}
        value = rates.get(currency)
        if value is None:
            logger.info(
                "fx_resolver_currency_unsupported",
                currency=currency,
                at_ts=at_ts.isoformat(),
            )
            return Decimal(0)
        return Decimal(str(value))


__all__ = ["FRANKFURTER_URL", "FXResolver"]
