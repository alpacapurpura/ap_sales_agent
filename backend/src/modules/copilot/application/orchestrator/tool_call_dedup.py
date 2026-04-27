"""Parent-agent tool-call dedup guard.

Background — 2026-04-27 incident (conversation ``fbc79125-…``): Kimi K2.6
emitted ``get_module_data(module='offer', section='X')`` repeatedly with
rotating section names. Nothing capped it; the deep-agent graph hit
``GraphRecursionError`` after 25 nodes, the SSE stream broke, and the
conversation persisted as empty.

This module installs a deterministic, in-memory guard ABOVE the LLM
decision loop:

* :class:`ToolCallDedupTracker` keeps a per-turn count of identical
  ``(tool_name, args)`` pairs.
* At ``threshold`` repeats it returns ``WARN`` so the orchestrator can
  inject an anti-loop directive into the ``ToolMessage`` the LLM will
  see next.
* At ``hard_limit`` repeats it raises :class:`ToolCallLoopError` so
  the orchestrator ends the turn gracefully — better a cooperative
  abort with partial state than letting LangGraph run to its recursion
  limit and lose everything.

The guard is intentionally minimal:

* No persistence; the tracker lives for one turn only.
* No knowledge of which tools are "loop-prone" — every tool counts the
  same. Tool-specific suppression is out of scope (and a future foot-gun).
* No LangGraph coupling. The guard observes whatever events the
  orchestrator hands it.

Configurable via env:

* ``COPILOT_TOOL_CALL_DEDUP_THRESHOLD`` (default 3) — repeats before
  WARN.
* ``COPILOT_TOOL_CALL_DEDUP_HARD_LIMIT`` (default 5) — repeats before
  ABORT. Must be ≥ threshold.
"""

from __future__ import annotations

import enum
import hashlib
import json
import os
from dataclasses import dataclass, field

__all__ = [
    "DEFAULT_DEDUP_HARD_LIMIT",
    "DEFAULT_DEDUP_THRESHOLD",
    "DedupVerdict",
    "ToolCallDedupTracker",
    "ToolCallLoopError",
    "augment_tool_message_for_warn",
    "hash_tool_args",
]


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


DEFAULT_DEDUP_THRESHOLD: int = _env_int("COPILOT_TOOL_CALL_DEDUP_THRESHOLD", 3)
DEFAULT_DEDUP_HARD_LIMIT: int = _env_int("COPILOT_TOOL_CALL_DEDUP_HARD_LIMIT", 5)


class DedupVerdict(enum.Enum):
    """Outcome of one observation.

    OK    — first or second hit; let the call through unchanged.
    WARN  — threshold reached; augment ToolMessage so the LLM sees a
            directive to stop repeating.
    """

    OK = "ok"
    WARN = "warn"


class ToolCallLoopError(RuntimeError):
    """Raised when an identical call exceeds ``hard_limit`` repeats.

    Carries enough metadata to tag the trace event without re-querying
    the tracker.
    """

    def __init__(
        self,
        *,
        tool_name: str,
        repeat_count: int,
        args_hash: str,
    ) -> None:
        """Build the loop-abort error with metadata.

        The fields are copied to attributes so trace recorders can tag
        the row without re-deriving state from the tracker.
        """
        super().__init__(
            f"Tool {tool_name!r} called {repeat_count} times with identical "
            f"args (hash {args_hash}); aborting turn to prevent burn.",
        )
        self.tool_name = tool_name
        self.repeat_count = repeat_count
        self.args_hash = args_hash


def hash_tool_args(args: object) -> str:
    """Return a stable short hash for ``args``.

    Dicts are normalised by sorting keys so payload ordering does not
    create false negatives. Strings (LangChain occasionally stringifies
    inputs) hash directly. ``None`` and empty dict collapse into the
    same bucket so missing-arg invocations count as repeats too.

    The hash is short (16 hex chars of sha256) — collision risk is
    immaterial for a per-turn counter that resets every turn.
    """
    if args is None or args == {}:
        normalised = ""
    elif isinstance(args, str):
        normalised = args
    elif isinstance(args, dict):
        try:
            normalised = json.dumps(args, sort_keys=True, default=str)
        except TypeError:
            normalised = repr(sorted(args.items()))
    else:
        normalised = repr(args)
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()[:16]


@dataclass
class ToolCallDedupTracker:
    """Per-turn tracker. Construct one per ``stream_chat`` invocation.

    The tracker is intentionally not async-safe: each turn is single-
    threaded inside its SSE generator and the orchestrator owns its own
    instance, so contention is impossible.
    """

    threshold: int = DEFAULT_DEDUP_THRESHOLD
    hard_limit: int = DEFAULT_DEDUP_HARD_LIMIT
    counts: dict[tuple[str, str], int] = field(default_factory=dict)

    def observe(self, tool_name: str, tool_args: object) -> DedupVerdict:
        """Increment count for ``(tool_name, args)`` and return verdict.

        Raises ``ToolCallLoopError`` once ``hard_limit`` is reached.
        Callers handle that exception in the stream loop's exception
        block, same path as ``TimeoutError`` / ``GraphRecursionError``.
        """
        args_hash = hash_tool_args(tool_args)
        key = (tool_name, args_hash)
        n = self.counts.get(key, 0) + 1
        self.counts[key] = n
        if n >= self.hard_limit:
            raise ToolCallLoopError(
                tool_name=tool_name,
                repeat_count=n,
                args_hash=args_hash,
            )
        if n >= self.threshold:
            return DedupVerdict.WARN
        return DedupVerdict.OK


# ── ToolMessage content augmentation ─────────────────────────────────


_LOOP_DIRECTIVE_TEMPLATE = (
    "[GUARD ANTI-LOOP — {tool_name}]\n"
    "Ya llamaste {tool_name} con estos args: {args_summary}.\n"
    "La data de abajo es la misma que recibiste en el intento previo. "
    "NO repitas esta tool con esos args. Próxima respuesta debe ser:\n"
    "  1) texto al usuario explicando lo que ya tienes, o\n"
    "  2) una tool DISTINTA (con args distintos) que avance el plan, o\n"
    "  3) una propuesta vía propose_field_updates si ya tienes lo que falta.\n"
    "[/GUARD]\n\n"
    "{original_content}"
)


def augment_tool_message_for_warn(
    *,
    tool_name: str,
    tool_args: object,
    original_content: str | None,
) -> str:
    """Wrap the original ToolMessage content with an anti-loop directive.

    The directive is in Spanish neutro (tuteo) so the agent's own outputs
    stay aligned with the brand voice rule. The original content is
    preserved verbatim — the LLM still needs the data; we only add a
    rail above it.
    """
    safe_content = original_content if original_content is not None else ""
    args_summary = _summarise_args(tool_args)
    return _LOOP_DIRECTIVE_TEMPLATE.format(
        tool_name=tool_name,
        args_summary=args_summary,
        original_content=safe_content,
    )


def _summarise_args(args: object) -> str:
    if args is None:
        return "(sin args)"
    if isinstance(args, dict):
        if not args:
            return "(sin args)"
        try:
            return json.dumps(args, sort_keys=True, default=str, ensure_ascii=False)[:200]
        except TypeError:
            return str(sorted(args.items()))[:200]
    return str(args)[:200]
