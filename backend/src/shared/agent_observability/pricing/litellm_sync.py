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

T-2 extensions (PI-12 S1 sales-agent-litellm-canonicalization):

* ``config_yaml_path`` — when supplied, parse ``litellm_config.yaml`` ``model_list``
  and warn (``pricing_sync.config_yaml_model_unknown_to_litellm``) if any model
  declared in the yaml is missing from ``litellm.model_cost`` (the in-memory
  registry that LiteLLM uses to compute ``response_cost`` natively). This is an
  opt-in best-effort cross-check; missing yaml is logged + skipped silently.

* Upstream drift detection — when an active snapshot row diverges from the
  upstream JSON entry by more than ``UPSTREAM_DRIFT_THRESHOLD_USD`` per token
  on either ``input_cost_per_token`` or ``output_cost_per_token``, structlog
  emits ``pricing_sync.upstream_drift_detected`` with the delta. The reconciler
  still closes the old row + inserts a new one — drift detection is an audit
  signal, not a correction.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Protocol

import structlog

from src.shared.agent_observability.persistence.pricing_snapshot_repository import (
    PricingSnapshotRepository,
)

if TYPE_CHECKING:
    from pathlib import Path

    from sqlalchemy.orm import Session

logger = structlog.get_logger()

LITELLM_JSON_URL = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
SUPPORTED_MODES = {"chat", "completion"}

# Drift threshold per token (USD). Anything above this delta on input or output
# cost between an existing active snapshot row and the upstream entry triggers
# ``pricing_sync.upstream_drift_detected``. 0.0001 USD/token is wider than any
# realistic single-day price move (typical: 1e-9 .. 1e-5 per token); use as
# "step change happened" indicator.
UPSTREAM_DRIFT_THRESHOLD_USD = Decimal("0.0001")

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
    # T-2 — number of yaml model entries declared in ``litellm_config.yaml``
    # ``model_list`` that are NOT in the LiteLLM in-memory ``model_cost`` registry.
    # Each unknown model emits a structlog warn at sync time.
    config_yaml_warnings: int = 0
    # T-2 — number of active snapshot rows that diverged from upstream JSON
    # by more than ``UPSTREAM_DRIFT_THRESHOLD_USD`` per token on input or output cost.
    # Drift triggers a structlog warn but the reconciler still closes + re-adds
    # the row through the normal change path.
    drift_warnings: int = 0
    # Detail of unknown-to-litellm yaml models for downstream ops queries.
    unknown_yaml_models: list[str] = field(default_factory=list)


def sync_pricing(
    db: Session,
    *,
    http_client: _HttpClient,
    url: str = LITELLM_JSON_URL,
    if_none_match: str | None = None,
    config_yaml_path: Path | None = None,
) -> SyncResult:
    """Run one pricing sync cycle. Returns a :class:`SyncResult`.

    Caller controls commit. ARQ task wraps with a session per run.

    Args:
        db: SQLAlchemy session bound to the snapshot DB. Caller commits.
        http_client: Duck-typed httpx-like client (real or test mock).
        url: Upstream JSON endpoint. Override only for tests.
        if_none_match: Last sync ETag (enables 304 short-circuit).
        config_yaml_path: Optional path to ``litellm_config.yaml``. When supplied,
            cross-checks each ``model_list`` entry against ``litellm.model_cost`` and
            warns on unknown models (T-2 A3). Missing path is logged + skipped
            silently — best-effort by design.
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

    # T-2 — yaml cross-check (best-effort, opt-in via config_yaml_path).
    if config_yaml_path is not None:
        _validate_yaml_against_litellm_registry(config_yaml_path, result)

    for model_name, entry in payload.items():
        _reconcile_entry(repo, model_name, entry, etag=etag, now=now, result=result)

    logger.info(
        "litellm_sync_complete",
        rows_added=result.rows_added,
        rows_updated=result.rows_updated,
        rows_skipped=result.rows_skipped,
        config_yaml_warnings=result.config_yaml_warnings,
        drift_warnings=result.drift_warnings,
        etag=etag,
    )
    return result


def _validate_yaml_against_litellm_registry(yaml_path: Path, result: SyncResult) -> None:
    """Cross-check ``litellm_config.yaml`` model_list vs ``litellm.model_cost`` (T-2 A3).

    Parses the yaml, walks ``model_list`` entries, and emits one
    ``pricing_sync.config_yaml_model_unknown_to_litellm`` structlog warn per model
    that is missing from the LiteLLM in-memory pricing registry.

    Best-effort: yaml missing → info log + return; yaml malformed → warn + return.
    Sync proceeds either way (the upstream HTTP fetch is the canonical source).
    """
    if not yaml_path.exists():
        logger.info("pricing_sync.config_yaml_skipped", reason="not_found", path=str(yaml_path))
        return

    try:
        import yaml  # PyYAML — transitively installed via langchain-core.

        raw = yaml_path.read_text(encoding="utf-8")
        config = yaml.safe_load(raw) or {}
    except Exception as exc:  # noqa: BLE001 — best-effort
        logger.warning(
            "pricing_sync.config_yaml_parse_failed",
            path=str(yaml_path),
            error=str(exc),
        )
        return

    model_list = config.get("model_list") or []
    if not isinstance(model_list, list):
        return

    # Lazy-import litellm — registry lookup is not on the hot path.
    try:
        import litellm  # type: ignore[import-untyped]

        registry: dict[str, Any] = litellm.model_cost  # type: ignore[attr-defined]
    except Exception as exc:  # noqa: BLE001 — best-effort, never block sync
        logger.warning("pricing_sync.litellm_registry_unavailable", error=str(exc))
        return

    for entry in model_list:
        if not isinstance(entry, dict):
            continue
        params = entry.get("litellm_params") or {}
        # The "model" field inside litellm_params is what LiteLLM resolves; the
        # outer "model_name" is the alias the application uses.
        model_field = params.get("model") if isinstance(params, dict) else None
        if not isinstance(model_field, str):
            continue
        if model_field in registry:
            continue
        # Some entries in registry are stored without provider prefix (e.g.
        # "gpt-4o-mini"). Try the bare name as fallback.
        bare = model_field.split("/", 1)[-1]
        if bare in registry:
            continue
        result.config_yaml_warnings += 1
        result.unknown_yaml_models.append(model_field)
        logger.warning(
            "pricing_sync.config_yaml_model_unknown_to_litellm",
            model=model_field,
            yaml_path=str(yaml_path),
        )


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

    # T-2 A4 — emit upstream drift audit signal when active row diverges from
    # upstream by more than the threshold on either input or output token cost.
    # The reconciler still proceeds with the close-and-replace below; this is
    # informational, useful for billing reconciliation alarms.
    delta_input = abs((active.input_cost_per_token or Decimal(0)) - parsed["input_cost_per_token"])
    delta_output = abs((active.output_cost_per_token or Decimal(0)) - parsed["output_cost_per_token"])
    if delta_input > UPSTREAM_DRIFT_THRESHOLD_USD or delta_output > UPSTREAM_DRIFT_THRESHOLD_USD:
        result.drift_warnings += 1
        logger.warning(
            "pricing_sync.upstream_drift_detected",
            provider=provider,
            model=model_name,
            delta_input_usd=str(delta_input),
            delta_output_usd=str(delta_output),
            threshold_usd=str(UPSTREAM_DRIFT_THRESHOLD_USD),
            old_input=str(active.input_cost_per_token),
            new_input=str(parsed["input_cost_per_token"]),
            old_output=str(active.output_cost_per_token),
            new_output=str(parsed["output_cost_per_token"]),
        )

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
    "UPSTREAM_DRIFT_THRESHOLD_USD",
    "SyncResult",
    "sync_pricing",
]
