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

# ── LATAM national IDs (S1 sales_agent) ─────────────────────────────────
#
# Two-pass strategy:
#  A) Structurally distinctive IDs (CURP, RFC, CUIT/CUIL formatted, CPF
#     formatted) — match without keyword guard. Their alphanumeric shape
#     is unmistakable.
#  B) Bare-digit IDs (DNI AR/PE, CC CO, RUC PE/EC, CUIT bare, CPF bare)
#     — require a LATAM keyword nearby. Otherwise we'd redact every
#     order_id / external_reference / lead score.
#
# Rationale documented in
# ``docs/domains/sales-agent/redesign-2026-04/phases/S1-sales-agent-observability-parity.md``
# section "Hallazgos research → LATAM PII regex 2026".

# Distinctive structural shapes — uppercase only, real CURP/RFC are issued in caps.
_NATIONAL_ID_STRUCTURAL_RES = (
    # CURP MX: 4 letras + 6 dígitos (yymmdd) + H|M + 5 letras (estado2 + consonants3) + alfa1 + dígito1 = 18 chars.
    re.compile(r"\b[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d\b"),
    # RFC MX persona (13 chars) o empresa (12 chars). Iniciales + yymmdd + homoclave3.
    re.compile(r"\b[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}\b"),
    # CUIT/CUIL AR formato dash: 2-8-1.
    re.compile(r"\b\d{2}-\d{8}-\d{1}\b"),
    # CPF BR formato canónico: xxx.xxx.xxx-xx.
    re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
)

# Keyword-guarded bare-digit IDs. Capture group 1 = keyword + spacing,
# group 2 = digits. Replacement preserves the keyword.
_NATIONAL_ID_KEYWORD_RE = re.compile(
    r"(?i)((?:dni|documento|c[eé]dula|\bcc\b|cuit|cuil|ruc|\bcpf\b|nit)\s+)"
    r"(\d{7,11})\b",
)

# Credit card numbers — 16 digits with optional spaces / dashes between
# 4-digit groups. We don't validate Luhn — the shape itself is the
# privacy concern.
_CARD_RE = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")

# CVV / CVC — 3 or 4 digits, keyword-guarded only (3 bare digits = score,
# port, etc — too ambiguous without keyword).
_CVV_KEYWORD_RE = re.compile(
    r"(?i)((?:cvv|cvc|c[oó]digo\s+(?:de\s+)?seguridad)\s+)(\d{3,4})\b",
)

_TOKEN_PLACEHOLDER = "[REDACTED_TOKEN]"
_PHONE_PLACEHOLDER = "[REDACTED_PHONE]"
_NATIONAL_ID_PLACEHOLDER = "[REDACTED_NATIONAL_ID]"
_CARD_PLACEHOLDER = "[REDACTED_CARD]"
_CVV_PLACEHOLDER = "[REDACTED_CVV]"


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
    """Apply every redaction regex in order. Returns a new string.

    Order matters:

    1. Provider tokens (may contain ``@`` look-alikes).
    2. Emails.
    3. Credit-card numbers (4x4 digit groups) — must run *before* phone
       regexes, otherwise ``_PHONE_RES`` would eat the first half.
    4. Keyword-anchored CVV (digits stay short — must run before phone).
    5. Keyword-anchored phones.
    6. Phones with country code / formatted runs.
    7. Structural national IDs (CURP / RFC / CUIT-dash / CPF-formatted).
    8. Keyword-anchored national IDs (DNI / CC / RUC / etc).
    """
    if not value or len(value) < 5:
        return value

    out = value
    # 1-2. Tokens + emails.
    for token_re in _TOKEN_RES:
        out = token_re.sub(_TOKEN_PLACEHOLDER, out)
    out = _EMAIL_RE.sub(_mask_email, out)
    # 3. Card numbers (4x4) before phones — phone regex (3-4 digit groups)
    # would otherwise gobble part of the card.
    out = _CARD_RE.sub(_CARD_PLACEHOLDER, out)
    # 4. CVV keyword-anchored.
    out = _CVV_KEYWORD_RE.sub(rf"\1{_CVV_PLACEHOLDER}", out)
    # 5-6. Phones.
    out = _PHONE_KEYWORD_RE.sub(rf"\1{_PHONE_PLACEHOLDER}", out)
    for phone_re in _PHONE_RES:
        out = phone_re.sub(_is_phone_safe, out)
    # 7. Structural national IDs.
    for nid_re in _NATIONAL_ID_STRUCTURAL_RES:
        out = nid_re.sub(_NATIONAL_ID_PLACEHOLDER, out)
    # 8. Keyword-anchored national IDs.
    out = _NATIONAL_ID_KEYWORD_RE.sub(rf"\1{_NATIONAL_ID_PLACEHOLDER}", out)
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
