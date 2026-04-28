"""Payload sanitisation for trace rows.

Two passes:

1. **Truncate** every long string to :data:`MAX_PAYLOAD_CHARS` so JSONB
   storage stays bounded.
2. **Redact PII** with regex matchers for emails, LATAM phone numbers,
   and provider API tokens. Synchronous and fast (<0.5ms for typical
   trace payloads) so it lives inside the callback handler hot path.

Microsoft Presidio + spaCy NER is **not** wired here — see Phase 3
deferred-debt for the async post-write worker that runs Presidio on
unstructured prompt text. Regex covers ~90% of the realistic PII surface
in our payloads (emails + phones + API tokens).

The functions are pure; callers decide where they hook in:

* :func:`sanitize_payload` is the existing top-level helper used by
  ``LlmCallRepository`` / ``trace_event_repository`` for shallow dicts
  (truncate + redact each value).
* :func:`redact_value` walks nested dict/list structures (used by tool
  call args).
"""

from __future__ import annotations

import re
from typing import Any

MAX_PAYLOAD_CHARS: int = 4_000

# ── Regex catalogue ─────────────────────────────────────────────────────

_EMAIL_RE = re.compile(
    r"\b([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b",
)

# Provider API tokens (OpenAI, Anthropic, Cohere, Mistral, etc).
# The pattern matches conservatively: the well-known prefixes plus a
# minimum body length so we don't false-positive `sk-foo` strings.
_TOKEN_RES = (
    re.compile(r"\bsk-ant-api\d{2}-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bxai-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bgsk_[A-Za-z0-9_-]{20,}\b"),  # Groq
)

# LATAM phone numbers — three shapes, all requiring some structure to
# avoid eating decimal / numeric IDs:
#  1. ``+<country 1-3>`` followed by 7-14 digits (optionally separated).
#  2. Two or three digit groups joined by space/dash (e.g. "55-1234-5678").
#  3. Bare 8-12 digit run preceded by a LATAM phone keyword
#     (``num/numero/cel/celular/tel/teléfono/whatsapp/wsp/llámame/contacto``)
#     so plain decimal runs in cost/token fields don't false-positive.
#     Implemented via a capture-group + custom replacement so the keyword
#     stays in place and only the digits are masked.
_PHONE_KEYWORD_RE = re.compile(
    r"(?i)((?:n[uú]m(?:ero)?|cel(?:ular)?|tel(?:[eé]fono)?|"
    r"whatsapp|wsp|ll[aá]mame|ll[aá]mar|llame|contacto)\s+)(\d{8,12})\b",
)
_PHONE_RES = (
    re.compile(r"\+\d{1,3}[\s-]?\d[\d\s-]{6,14}\d"),
    re.compile(r"\b\d{2,4}[-\s]\d{3,4}[-\s]\d{3,4}\b"),
)

_TOKEN_PLACEHOLDER = "[REDACTED_TOKEN]"
_PHONE_PLACEHOLDER = "[REDACTED_PHONE]"


def _mask_email(match: re.Match[str]) -> str:
    first, domain = match.group(1), match.group(2)
    return f"{first}***@{domain}"


def _is_phone_safe(match: re.Match[str]) -> str:
    """Replace match with placeholder, preserving leading + and country prefix when possible."""
    raw = match.group(0)
    if raw.startswith("+"):
        # Keep the +<country> prefix and replace the rest.
        country_match = re.match(r"\+\d{1,3}", raw)
        prefix = country_match.group(0) if country_match else "+"
        return f"{prefix} {_PHONE_PLACEHOLDER}"
    return _PHONE_PLACEHOLDER


# ── Public API ──────────────────────────────────────────────────────────


def truncate(value: Any, limit: int = MAX_PAYLOAD_CHARS) -> Any:  # noqa: ANN401 — polymorphic
    """Trim long strings; pass everything else through."""
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + " [truncated]"
    return value


def redact_string(value: str) -> str:
    """Apply every redaction regex in order. Returns a new string."""
    if not value or len(value) < 5:
        return value

    out = value
    # Tokens first — they may contain @-like characters.
    for token_re in _TOKEN_RES:
        out = token_re.sub(_TOKEN_PLACEHOLDER, out)
    out = _EMAIL_RE.sub(_mask_email, out)
    # Keyword-anchored phones: keep the keyword, replace the digits only.
    out = _PHONE_KEYWORD_RE.sub(rf"\1{_PHONE_PLACEHOLDER}", out)
    for phone_re in _PHONE_RES:
        out = phone_re.sub(_is_phone_safe, out)
    return out


def redact_value(value: Any) -> Any:  # noqa: ANN401 — polymorphic
    """Walk dict/list structures redacting every string leaf."""
    if isinstance(value, str):
        return redact_string(value)
    if isinstance(value, dict):
        return {k: redact_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item) for item in value)
    return value


def sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Trim every string then redact PII. Single shallow pass for the trace store."""
    if not payload:
        return {}
    out: dict[str, Any] = {}
    for key, raw in payload.items():
        trimmed = truncate(raw)
        out[key] = redact_value(trimmed)
    return out


__all__ = [
    "MAX_PAYLOAD_CHARS",
    "redact_string",
    "redact_value",
    "sanitize_payload",
    "truncate",
]
