"""LiteLLM CustomLogger that captures ``kwargs['response_cost']`` per call.

PI-12 Sprint S1 · sales-agent-litellm-canonicalization · T-1.

LiteLLM computes the USD cost of every completion natively and surfaces it
in ``kwargs["response_cost"]`` on every callback hook. This module wires a
process-wide :class:`CostRecorderCustomLogger` into ``litellm.callbacks`` at
boot (FastAPI + ARQ workers + scheduler) so the value is stashed in a
thread-safe TTL cache keyed by ``litellm_call_id``. The LangChain
:class:`~src.shared.agent_observability.recording.base_callback_handler.BaseAgentCallbackHandler.on_llm_end`
hook then consumes the cost via :func:`pop_cost` and persists it to
``copilot_llm_call`` / ``sales_agent_llm_call`` — bridging the two callback
systems with a single source of truth for cost.

Why a NEW class (anti-duplication audit, see ``03-arch-be.md`` §10):

* LiteLLM ``CustomLogger`` is conceptually distinct from LangChain
  ``BaseCallbackHandler`` — they sit on different surfaces (proxy-side vs
  runtime-side) and are invoked at different lifecycle points.
* Both coexist by design: the LangChain handler captures the LangChain
  span (provider/model/tokens), the LiteLLM CustomLogger captures
  ``kwargs["response_cost"]``. They are bridged via ``litellm_call_id``.
* This is NOT a mirror of the existing :class:`BaseAgentCallbackHandler`
  shared abstraction; it is a NEW abstraction at a NEW boundary.

Key invariants:

* Best-effort: every cache mutation is wrapped in ``try/except`` +
  ``structlog.warning``. The callback **never** blocks the LLM turn.
* Single-use: :func:`pop_cost` drains the entry. Repeat calls return
  ``None``.
* TTL purge: entries older than 60 s are removed lazily on every cache
  operation; a structlog warning identifies the orphan call_id (for
  observability — typically signals a slow LangChain consumer or a
  non-LiteLLM call that fired the LiteLLM callback by mistake).
* Process-wide: the cache is module-global. The
  :class:`BaseAgentCallbackHandler` carries the tenant context — this
  module is intentionally tenant-agnostic so it can be registered once
  at boot without per-request setup.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from threading import Lock
from time import monotonic
from typing import Any

import structlog

logger = structlog.get_logger()

# TTL cache: litellm_call_id → (cost_usd, expires_at_monotonic).
# ``cost_usd`` is ``Decimal | None``: ``None`` distinguishes
# "we know there's no cost" (e.g. unknown model, LiteLLM did not compute
# one) from "valid Decimal('0')" (a zero-cost call that completed).
_CACHE_TTL_S: float = 60.0
_cache: dict[str, tuple[Decimal | None, float]] = {}
_lock = Lock()


def _purge_expired() -> None:
    """Drop expired entries (TTL exceeded). Caller must hold ``_lock``."""
    now = monotonic()
    expired_ids = [cid for cid, (_, exp) in _cache.items() if exp < now]
    for cid in expired_ids:
        cost, _ = _cache.pop(cid)
        logger.warning(
            "cost_recorder.orphan_entry_purged",
            call_id=cid,
            cost_usd=str(cost) if cost is not None else None,
            ttl_s=_CACHE_TTL_S,
        )


def _coerce_decimal(value: Any) -> Decimal | None:  # noqa: ANN401 — payload is foreign
    """Return a ``Decimal`` for numeric inputs, ``None`` otherwise.

    LiteLLM populates ``kwargs["response_cost"]`` as a Python ``float``;
    we round-trip through ``str`` to preserve the literal value (avoiding
    binary-float artefacts) and reject any other shape silently — the
    callback is best-effort and a malformed payload should NEVER raise.
    """
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int | float | str):
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
    return None


def _resolve_call_id(kwargs: dict[str, Any], response_obj: Any) -> str | None:  # noqa: ANN401
    """Resolve a stable ``call_id`` LangChain can echo back via response metadata.

    LiteLLM populates ``litellm_call_id`` in ``kwargs`` for every successful
    request; provider-specific responses also bubble it up via the
    ``response_metadata`` dict that LangChain serialises on the message.

    Returns ``None`` when no usable id is present — the caller logs and
    skips stashing rather than fabricating a key.
    """
    call_id = kwargs.get("litellm_call_id")
    if call_id:
        return str(call_id)
    response_id = getattr(response_obj, "id", None)
    if response_id:
        return str(response_id)
    return None


def _stash(call_id: str, cost: Decimal | None) -> None:
    """Insert ``(cost, expiry)`` under ``call_id`` and purge expired neighbours."""
    with _lock:
        _purge_expired()
        _cache[call_id] = (cost, monotonic() + _CACHE_TTL_S)


def pop_cost(call_id: str) -> Decimal | None:
    """Retrieve and remove the cost recorded for ``call_id``.

    Returns ``None`` on miss (no recorder fired, expired, or the recorder
    fired without a numeric ``response_cost``). Callers MUST treat ``None``
    as "cost unknown" and persist ``cost_usd = NULL`` on the audit row;
    they MUST NOT default to ``Decimal('0')`` (which would mask cost-tracking
    drift).
    """
    with _lock:
        _purge_expired()
        entry = _cache.pop(call_id, None)
        return entry[0] if entry is not None else None


def register_cost_recorder() -> None:
    """Idempotently install :class:`CostRecorderCustomLogger` into ``litellm.callbacks``.

    Safe to call from FastAPI startup, ARQ ``WorkerSettings.on_startup``, and
    ``SchedulerSettings.on_startup``. Subsequent invocations are no-ops — the
    module is process-singleton and ``litellm.callbacks`` is also process-wide.
    """
    try:
        import litellm
    except ImportError:
        logger.warning(
            "cost_recorder.litellm_unavailable_skipping_registration",
            hint="`litellm` SDK not installed; cost capture disabled",
        )
        return

    callbacks = getattr(litellm, "callbacks", None)
    if callbacks is None:
        litellm.callbacks = []
        callbacks = litellm.callbacks

    for cb in callbacks:
        if isinstance(cb, CostRecorderCustomLogger):
            return
    callbacks.append(CostRecorderCustomLogger())
    logger.info("cost_recorder.registered", callback_count=len(callbacks))


def _custom_logger_base() -> type:
    """Return the LiteLLM ``CustomLogger`` base, or a stub if SDK unavailable.

    Lazy import so the module is importable in test contexts without the
    LiteLLM SDK installed (CI smoke + linting). The bootstrap function
    :func:`register_cost_recorder` performs the same defensive import.
    """
    try:
        from litellm.integrations.custom_logger import CustomLogger
    except ImportError:

        class _Stub:
            """Fallback when LiteLLM is not installed; never invoked at runtime."""

        return _Stub
    return CustomLogger


_BaseCustomLogger = _custom_logger_base()


class CostRecorderCustomLogger(_BaseCustomLogger):  # type: ignore[misc, valid-type]
    """LiteLLM ``CustomLogger`` that stashes ``kwargs['response_cost']``.

    Only the success hooks are overridden — failures don't carry a cost,
    so we let the base no-ops handle them. Both sync and async hooks are
    implemented because LiteLLM dispatches whichever matches the calling
    context (sync ``litellm.completion`` vs. async
    ``litellm.acompletion``).
    """

    def log_success_event(
        self,
        kwargs: dict[str, Any],
        response_obj: Any,  # noqa: ANN401 — provider-specific shape
        start_time: float,
        end_time: float,
    ) -> None:
        """Sync hook — best-effort; never raises."""
        del start_time, end_time
        try:
            self._record(kwargs, response_obj)
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning("cost_recorder.log_success_failed", error=str(exc))

    async def async_log_success_event(
        self,
        kwargs: dict[str, Any],
        response_obj: Any,  # noqa: ANN401 — provider-specific shape
        start_time: float,
        end_time: float,
    ) -> None:
        """Async hook — best-effort; never raises."""
        del start_time, end_time
        try:
            self._record(kwargs, response_obj)
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning("cost_recorder.async_log_success_failed", error=str(exc))

    @staticmethod
    def _record(kwargs: dict[str, Any], response_obj: Any) -> None:  # noqa: ANN401
        """Common stash logic shared by sync + async success hooks."""
        call_id = _resolve_call_id(kwargs, response_obj)
        if call_id is None:
            logger.warning(
                "cost_recorder.missing_call_id",
                model=kwargs.get("model"),
                hint="LiteLLM did not provide litellm_call_id; cost will not bridge to LangChain",
            )
            return
        cost = _coerce_decimal(kwargs.get("response_cost"))
        _stash(call_id, cost)


__all__ = [
    "CostRecorderCustomLogger",
    "pop_cost",
    "register_cost_recorder",
]
