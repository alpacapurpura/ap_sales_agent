"""Payload sanitisation for trace rows.

Phase 1 keeps it cheap: truncate every string to ``MAX_PAYLOAD_CHARS``.
PII redaction (Presidio + regex) is added in Phase 3 — this is the seam
those passes drop into without the rest of the pipeline learning a new
shape.
"""

from __future__ import annotations

from typing import Any

MAX_PAYLOAD_CHARS: int = 4_000


def truncate(value: Any, limit: int = MAX_PAYLOAD_CHARS) -> Any:  # noqa: ANN401 — polymorphic
    """Trim long strings; pass everything else through."""
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + " [truncated]"
    return value


def sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Shallow-trim every string value in ``payload``."""
    if not payload:
        return {}
    return {k: truncate(v) for k, v in payload.items()}


__all__ = ["MAX_PAYLOAD_CHARS", "sanitize_payload", "truncate"]
