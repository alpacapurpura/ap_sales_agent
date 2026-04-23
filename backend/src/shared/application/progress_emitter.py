"""Backwards-compatible progress callback emission.

Extraction orchestrators historically call a 2-arg progress callback
``callback(pct, stage)`` to report high-level progress to the REST layer.
For copilot-driven extractions the worker needs richer per-wave data
(which sections completed and which field paths were populated) so the
frontend can render live progress on the ToolCallChip + NavRail badges.

To keep the orchestrator decoupled from any particular callback shape,
this module introspects the callback's signature and emits the
appropriate call style:

- If the callback accepts ``new_fields`` and ``section_completed`` as
  keyword arguments (or a catch-all ``**kwargs``) → pass the rich payload.
- Otherwise → call the legacy 2-arg form.

Callers NEVER have to care which style their callback is. The helper
shields them.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable  # noqa: TC003 — runtime type: lru_cache parameter + public signature
from functools import lru_cache
from typing import Any

__all__ = ["emit_progress", "fields_from_model", "supports_rich_progress"]


@lru_cache(maxsize=128)
def _callback_accepts_rich_kwargs(callback: Callable) -> bool:
    """Return True when the callback signature accepts the enriched kwargs.

    Cached per-callback so we don't introspect on every wave tick.
    """
    try:
        sig = inspect.signature(callback)
    except (TypeError, ValueError):
        return False

    has_new_fields = False
    has_section_completed = False
    has_var_kw = False

    for param in sig.parameters.values():
        if param.kind is inspect.Parameter.VAR_KEYWORD:
            has_var_kw = True
        elif param.name == "new_fields":
            has_new_fields = True
        elif param.name == "section_completed":
            has_section_completed = True

    return has_var_kw or (has_new_fields and has_section_completed)


def supports_rich_progress(callback: Callable[..., None] | None) -> bool:
    """Expose ``_callback_accepts_rich_kwargs`` for orchestrators.

    Orchestrators use this to decide whether to emit per-section events
    (rich) or a single aggregate event per wave (legacy). Safe with None.
    """
    if callback is None:
        return False
    return _callback_accepts_rich_kwargs(callback)


def emit_progress(
    callback: Callable[..., None] | None,
    pct: int,
    stage: str,
    *,
    new_fields: list[str] | None = None,
    section_completed: str | None = None,
) -> None:
    """Dispatch a progress update to ``callback`` using whichever signature it supports.

    Safe to call with ``callback=None`` (no-op).
    Exceptions raised inside the callback are swallowed so extraction can't
    be aborted by an observability bug.
    """
    if callback is None:
        return
    try:
        if _callback_accepts_rich_kwargs(callback):
            callback(pct, stage, new_fields=new_fields, section_completed=section_completed)
        else:
            callback(pct, stage)
    except Exception:  # noqa: BLE001 — progress is best-effort; never abort extraction
        import structlog

        structlog.get_logger(__name__).warning(
            "progress_callback raised; swallowed to keep extraction alive",
            exc_info=True,
        )


def fields_from_model(section_slug: str, model: Any) -> list[str]:  # noqa: ANN401 — Pydantic model or dict
    """Return dotted paths of filled leaves in ``model`` under ``section_slug``.

    Delegates to ``field_diff.filled_fields_by_section`` so the definition
    of "filled" is shared across workers and orchestrator emission.

    Accepts either a Pydantic BaseModel (uses ``model_dump``), a raw dict,
    or a list (treated as a single-item section). Returns ``[]`` for None
    or empty payloads.
    """
    from src.shared.application.field_diff import filled_fields_by_section

    if model is None:
        return []

    dump: dict[str, Any]
    if hasattr(model, "model_dump"):
        section_data = model.model_dump(mode="json")
        if isinstance(section_data, dict):
            dump = {section_slug: section_data}
        else:
            dump = {section_slug: section_data} if section_data else {}
    elif isinstance(model, (dict, list)):
        dump = {section_slug: model}
    else:
        return []

    by_section = filled_fields_by_section(dump)
    return by_section.get(section_slug, [])
