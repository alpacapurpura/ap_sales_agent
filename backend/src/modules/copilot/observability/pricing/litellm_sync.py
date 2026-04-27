"""LiteLLM pricing sync — daily worker that mirrors upstream pricing.

Pulls the canonical pricing JSON from
``raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json``
and reconciles it against ``model_pricing_snapshot``:

* New (provider, model) → insert active row.
* Changed cost values    → close the active row (set ``valid_to=NOW()``)
  and insert a new active row.
* Unchanged              → leave alone.

Skips:

* The ``sample_spec`` template entry.
* Non-chat modes (``image_generation``, ``audio_*``) — Phase 1 cost
  pipeline only handles chat tokens.
* Entries missing ``input_cost_per_token`` / ``output_cost_per_token``.

ETag short-circuit avoids re-parsing on no-change days.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Protocol

import structlog

from src.modules.copilot.observability.persistence.pricing_snapshot_repository import (
    PricingSnapshotRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()

LITELLM_JSON_URL = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
SUPPORTED_MODES = {"chat", "completion"}

# ``model_pricing_snapshot.source_etag`` is varchar(64). GitHub raw
# returns weak ETags shaped like ``W/"<sha256-hex>"`` (≈71 chars), so we
# strip the weak indicator + surrounding quotes and clip to the column
# width. The value is only used as a fingerprint for the next If-None-Match
# round-trip — exact byte preservation isn't required.
_ETAG_MAX_LENGTH = 64


def _normalise_etag(raw: str | None) -> str | None:
    """Return a column-safe ETag, or ``None`` if there isn't one."""
    if not raw:
        return None
    cleaned = raw.removeprefix("W/").strip('"').strip()
    return cleaned[:_ETAG_MAX_LENGTH] if cleaned else None


class _HttpClient(Protocol):
    """Minimal interface — covers httpx.Client and our test mocks."""

    def get(self, url: str, **kwargs: Any) -> Any: ...  # noqa: ANN401 — duck-typed response


@dataclass(slots=True)
class SyncResult:
    """Summary of a single sync run, useful for worker logs + admin dashboards."""

    rows_added: int = 0
    rows_updated: int = 0
    rows_skipped: int = 0
    etag: str | None = None


def sync_pricing(
    db: Session,
    *,
    http_client: _HttpClient,
    url: str = LITELLM_JSON_URL,
    if_none_match: str | None = None,
) -> SyncResult:
    """Run one pricing sync cycle. Returns a :class:`SyncResult`.

    Caller controls commit. ARQ task wraps with a session per run.
    """
    headers: dict[str, str] = {}
    if if_none_match:
        headers["If-None-Match"] = if_none_match

    response = http_client.get(url, headers=headers)
    if getattr(response, "status_code", 200) == 304:
        # Nothing changed since the last sync.
        logger.info("litellm_sync_not_modified", url=url, etag=if_none_match)
        return SyncResult(etag=if_none_match)

    # Raise on real HTTP errors — the worker will retry (ARQ max_tries).
    raise_for_status = getattr(response, "raise_for_status", None)
    if callable(raise_for_status):
        raise_for_status()

    payload = response.json()
    raw_etag = response.headers.get("ETag") if hasattr(response, "headers") else None
    etag = _normalise_etag(raw_etag)

    repo = PricingSnapshotRepository(db)
    now = dt.datetime.now(tz=dt.UTC)
    result = SyncResult(etag=etag)

    for model_name, entry in payload.items():
        _reconcile_entry(repo, model_name, entry, etag=etag, now=now, result=result)

    logger.info(
        "litellm_sync_complete",
        rows_added=result.rows_added,
        rows_updated=result.rows_updated,
        rows_skipped=result.rows_skipped,
        etag=etag,
    )
    return result


def _parse_entry(model_name: str, entry: object) -> dict[str, Any] | None:
    """Return the parsed cost fields for a chat/completion entry, or ``None``.

    ``None`` means "skip this entry" — sample template, wrong mode, or
    missing required cost fields. The caller bumps ``rows_skipped``.
    """
    if model_name == "sample_spec" or not isinstance(entry, dict):
        return None
    if entry.get("mode") not in SUPPORTED_MODES:
        return None
    provider = entry.get("litellm_provider")
    input_cost = entry.get("input_cost_per_token")
    output_cost = entry.get("output_cost_per_token")
    if provider is None or input_cost is None or output_cost is None:
        return None
    batch_input = entry.get("batch_input_cost_per_token")
    return {
        "provider": provider,
        "input_cost_per_token": Decimal(str(input_cost)),
        "output_cost_per_token": Decimal(str(output_cost)),
        "cache_read_cost_per_token": Decimal(str(entry.get("cache_read_input_token_cost") or 0)),
        "cache_write_cost_per_token": Decimal(str(entry.get("cache_creation_input_token_cost") or 0)),
        "batch_input_cost_per_token": Decimal(str(batch_input)) if batch_input is not None else None,
        "raw_payload": entry,
    }


def _reconcile_entry(
    repo: PricingSnapshotRepository,
    model_name: str,
    entry: object,
    *,
    etag: str | None,
    now: dt.datetime,
    result: SyncResult,
) -> None:
    """Insert / close-and-replace / no-op for a single LiteLLM entry."""
    parsed = _parse_entry(model_name, entry)
    if parsed is None:
        result.rows_skipped += 1
        return

    provider = parsed["provider"]
    active = repo.find_active(provider=provider, model=model_name)
    if active is None:
        repo.add(
            provider=provider,
            model=model_name,
            input_cost_per_token=parsed["input_cost_per_token"],
            output_cost_per_token=parsed["output_cost_per_token"],
            cache_read_cost_per_token=parsed["cache_read_cost_per_token"],
            cache_write_cost_per_token=parsed["cache_write_cost_per_token"],
            batch_input_cost_per_token=parsed["batch_input_cost_per_token"],
            source="litellm",
            source_etag=etag,
            valid_from=now,
            valid_to=None,
            raw_payload=parsed["raw_payload"],
        )
        result.rows_added += 1
        return

    unchanged = (
        active.input_cost_per_token == parsed["input_cost_per_token"]
        and active.output_cost_per_token == parsed["output_cost_per_token"]
        and (active.cache_read_cost_per_token or Decimal(0)) == parsed["cache_read_cost_per_token"]
        and (active.cache_write_cost_per_token or Decimal(0)) == parsed["cache_write_cost_per_token"]
    )
    if unchanged:
        return

    repo.close_active(provider=provider, model=model_name, at_ts=now)
    repo.add(
        provider=provider,
        model=model_name,
        input_cost_per_token=parsed["input_cost_per_token"],
        output_cost_per_token=parsed["output_cost_per_token"],
        cache_read_cost_per_token=parsed["cache_read_cost_per_token"],
        cache_write_cost_per_token=parsed["cache_write_cost_per_token"],
        batch_input_cost_per_token=parsed["batch_input_cost_per_token"],
        source="litellm",
        source_etag=etag,
        valid_from=now,
        valid_to=None,
        raw_payload=parsed["raw_payload"],
    )
    result.rows_added += 1
    result.rows_updated += 1


__all__ = [
    "LITELLM_JSON_URL",
    "SUPPORTED_MODES",
    "SyncResult",
    "sync_pricing",
]
