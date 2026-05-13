"""ARQ task — daily LiteLLM pricing sync.

Registered in ``backend/src/workers/settings.py`` (cron 03:00 UTC). The
task opens its own session, runs :func:`sync_pricing`, commits and logs.
Best-effort: the copilot does not depend on this task running for any
single turn — pricing is denormalised at write time, so even if pricing
is stale for a day, in-flight calls just record the previous snapshot's
unit cost.

T-2 (PI-12 S1 sales-agent-litellm-canonicalization):
* Auto-locates ``litellm_config.yaml`` at repo root and passes it to
  :func:`sync_pricing` for the yaml↔registry cross-check (warns on models
  not in ``litellm.model_cost``).
* Propagates the new ``config_yaml_warnings`` + ``drift_warnings`` fields
  to the ARQ return dict for downstream observability.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import structlog
from luana_core_observability.pricing.litellm_sync import sync_pricing
from luana_core_platform.core.database import SessionLocal

logger = structlog.get_logger()


def _default_config_yaml_path() -> Path | None:
    """Best-effort locate ``litellm_config.yaml`` at repo root.

    The yaml lives at the repo root (``/home/chris/AISALESHT/litellm_config.yaml``
    in dev, ``/app/litellm_config.yaml`` in container builds depending on COPY).
    Walks ``__file__`` upward looking for the first match. Returns ``None`` if
    not found — callers downgrade gracefully (cross-check skipped silently).
    """
    here = Path(__file__).resolve()
    # Walk up at most 8 levels — covers backend/src/shared/.../workers/ → repo root.
    for parent in [here, *here.parents][:9]:
        candidate = parent / "litellm_config.yaml"
        if candidate.exists():
            return candidate
    return None


async def sync_litellm_pricing(_ctx: dict[str, Any]) -> dict[str, Any]:
    """ARQ task: pull LiteLLM JSON, reconcile against snapshots."""
    session = SessionLocal()
    try:
        with httpx.Client(timeout=30.0) as client:
            result = sync_pricing(
                session,
                http_client=client,
                config_yaml_path=_default_config_yaml_path(),
            )
        session.commit()
    except Exception as exc:
        logger.exception("pricing_sync_task_failed", error=str(exc))
        session.rollback()
        return {"ok": False, "error": str(exc)}
    finally:
        session.close()

    return {
        "ok": True,
        "rows_added": result.rows_added,
        "rows_updated": result.rows_updated,
        "rows_skipped": result.rows_skipped,
        "config_yaml_warnings": result.config_yaml_warnings,
        "drift_warnings": result.drift_warnings,
    }
