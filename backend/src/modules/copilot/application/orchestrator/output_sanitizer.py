"""Last-line-of-defense sanitizer for assistant text blocks.

Three safety nets, applied in order, before SSE ``block_end``:

1. **JSON strip** — the system prompt forbids JSON in chat. When the LLM
   ignores it we drop fenced code blocks + bare top-level objects so the
   user only sees prose.
2. **Voseo autocorrect (TP6)** — even with the explicit "español neutro
   sin voseo" rule in the system prompt, Kimi K2.6 (thinking-disabled)
   lapses into voseo (``podés`` / ``Querés`` / ``mirá``) intermittently.
   The sanitizer rewrites those forms to neutro tuteo so the regla 11
   invariant holds at the channel boundary.
3. **Channel format enforcement (TP6)** — when the user message asks for
   output for a non-chat channel and the AGENT ignores the channel-aware
   ``format_for_channel`` tool result, we re-apply ``format_for_channel_impl``
   deterministically. Idempotent: when the AGENT already obeyed the tool's
   ``content`` field, the second pass is a no-op.

Rationale:
  - Tool payloads travel via ``ui_action`` cards — not assistant text.
  - Users should never see raw JSON; they see interactive cards instead.
  - SMS / WhatsApp / etc. limits are channel-specific; the LLM's
    instruction-following is unreliable at 100% so we enforce here.
"""

from __future__ import annotations

import re

# ── 1. JSON strip ────────────────────────────────────────────────────────────

# ``` ```json {...} ``` `` or ``` ``` {...} ``` `` blocks with any whitespace/newlines.
_CODE_FENCE_JSON = re.compile(
    r"```(?:json|JSON)?\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*```",
    re.MULTILINE,
)

# Bare ``` {...} ``` without a fence close (streamed/truncated leftover).
_BARE_BALANCED_OBJECT = re.compile(
    r"(?<![A-Za-z0-9_])\{[\s\S]{40,}?\}(?![A-Za-z0-9_])",
)


# ── 2. Voseo autocorrect ─────────────────────────────────────────────────────

# Map curated from `.claude/rules/spanish-text.md` glosario. Includes the
# top forms emitted by AGENT during TP6 matrix (``podés / querés / tenés
# / sabés / mirá``). Keys are lowercased; the case of the original token
# is restored in `_voseo_replace`.
_VOSEO_TO_NEUTRO: dict[str, str] = {
    # Pronouns + 2nd-person singular voseo conjugations.
    "vos": "tú",
    "sos": "eres",
    "tenés": "tienes",
    "querés": "quieres",
    "podés": "puedes",
    "sabés": "sabes",
    "hacés": "haces",
    "venís": "vienes",
    "decís": "dices",
    "ofrecés": "ofreces",
    "cobrás": "cobras",
    "ejecutás": "ejecutas",
    "acompañás": "acompañas",
    "activás": "activas",
    "desactivás": "desactivas",
    "atendés": "atiendes",
    "integrás": "integras",
    "referís": "te refieres",
    # Imperatives -á (1st conjugation).
    "mirá": "mira",
    "dejá": "deja",
    "poné": "pon",
    "usá": "usa",
    "hacé": "haz",
    "seleccioná": "selecciona",
    "empezá": "empieza",
    "arrancá": "empieza",
    "agregá": "agrega",
    "configurá": "configura",
    "revisá": "revisa",
    "guardá": "guarda",
    "cambiá": "cambia",
    "linkeá": "enlaza",
    "reactivá": "reactiva",
    "validá": "valida",
    "considerá": "considera",
    "marcá": "marca",
    "listá": "lista",
    "probá": "prueba",
    "mostrá": "muestra",
    "contá": "cuenta",
    "explicá": "explica",
    "tomá": "toma",
    "esperá": "espera",
    "andá": "ve",
    "llevá": "lleva",
    "terminá": "termina",
    "aceptá": "acepta",
    # Imperatives -é (2nd conjugation).
    "crecé": "crece",
    "leé": "lee",
    "aprendé": "aprende",
    "vendé": "vende",
    # Imperatives -í (3rd conjugation).
    "escribí": "escribe",
    "subí": "sube",
    "abrí": "abre",
    "volvé": "vuelve",
    "elegí": "elige",
    "seguí": "sigue",
    "salí": "sal",
    "vení": "ven",
    "compartí": "comparte",
    # Pronominal forms.
    "decime": "dime",
    "contame": "cuéntame",
    "fijate": "ten en cuenta",
    "acordate": "recuerda",
    "despublicala": "despublícala",
    "cancelala": "cancélala",
    "formulala": "formúlala",
    # Casual markers (rare in copilot output but cheap to include).
    "dale": "ok",
}


def _restore_case(template: str, replacement: str) -> str:
    """Match the casing of ``template`` onto ``replacement`` (first letter)."""
    if not template or not replacement:
        return replacement
    if template[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


_VOSEO_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in sorted(_VOSEO_TO_NEUTRO, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def correct_voseo_in_text(text: str) -> str:
    """Rewrite voseo forms to neutro LatAm tuteo, preserving capitalization."""
    if not text:
        return text

    def _sub(match: re.Match[str]) -> str:
        token = match.group(1)
        replacement = _VOSEO_TO_NEUTRO.get(token.lower())
        if replacement is None:
            return token
        return _restore_case(token, replacement)

    return _VOSEO_RE.sub(_sub, text)


# ── 3. Channel format enforcement ────────────────────────────────────────────

# Detects channel keywords in the *user* message so the sanitizer knows
# whether to apply ``format_for_channel_impl``. Matches ``"SMS"``,
# ``"para WhatsApp"``, ``"un email"``, ``"Telegram"``, ``"Instagram DM"``,
# ``"audio"`` / ``"voz"``. Order matters in the alternation — the more
# specific patterns (``instagram_dm``) come before the generic ones.
_CHANNEL_KEYWORD_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\binstagram[ _-]?dm\b|\bIG[ _-]?DM\b", re.IGNORECASE), "instagram_dm"),
    (re.compile(r"\bwhats[ _-]?app\b|\bWA\b", re.IGNORECASE), "whatsapp"),
    (re.compile(r"\btelegram\b", re.IGNORECASE), "telegram"),
    (re.compile(r"\bsms\b|\bmensaje de texto\b", re.IGNORECASE), "sms"),
    (re.compile(r"\bemail\b|\bcorreo electr[oó]nico\b|\bcorreo\b", re.IGNORECASE), "email"),
    (re.compile(r"\b(audio|voz|voice|tts)\b", re.IGNORECASE), "voice"),
]


def detect_channel_in_user_msg(user_msg: str | None) -> str | None:
    """Return the canonical channel id mentioned in the user message, if any."""
    if not user_msg:
        return None
    for pattern, channel_id in _CHANNEL_KEYWORD_PATTERNS:
        if pattern.search(user_msg):
            return channel_id
    return None


def enforce_channel_format_if_needed(text: str, user_msg: str | None) -> str:
    """Apply ``format_for_channel_impl`` when the user asked for a specific channel.

    Idempotent: when the AGENT already returned the canonical channel
    output (e.g. it copied the tool's ``content`` field verbatim), the
    sanitizer's pass is a no-op. When the AGENT ignored the tool result
    and emitted a longer / unsanitised draft, this function enforces.

    Returns the original ``text`` when no channel keyword is present in
    ``user_msg`` or the resolved channel is ``"chat"``.
    """
    if not text:
        return text
    channel_id = detect_channel_in_user_msg(user_msg)
    if channel_id is None or channel_id == "chat":
        return text

    # Lazy import — keeps module load cheap and avoids any import cycle
    # with the tools layer (output_sanitizer is imported by chat.py at
    # module load).
    from src.modules.copilot.application.tools.format_for_channel import (
        format_for_channel_impl,
    )

    payload = format_for_channel_impl(content=text, channel_id=channel_id)
    return str(payload.get("content") or text)


# ── Composition ──────────────────────────────────────────────────────────────


def sanitize_assistant_text(text: str, *, user_msg: str | None = None) -> str:
    """Run all 3 safety nets in order: JSON strip → voseo → channel format.

    Conservative on the JSON strip: only drops fenced code blocks whose
    content parses as a JSON object/array, plus bare top-level ``{…}``
    blobs over ~40 chars. Inline short ``{x}`` templates pass through.

    ``user_msg`` is optional — when omitted, the channel enforcement step
    is skipped (default for legacy callers).
    """
    if not text:
        return text

    cleaned = _CODE_FENCE_JSON.sub("", text)
    cleaned = _BARE_BALANCED_OBJECT.sub("", cleaned)
    # Collapse 3+ consecutive blank lines left by the substitutions.
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = cleaned.strip()

    cleaned = correct_voseo_in_text(cleaned)
    cleaned = enforce_channel_format_if_needed(cleaned, user_msg)
    return cleaned


__all__ = [
    "correct_voseo_in_text",
    "detect_channel_in_user_msg",
    "enforce_channel_format_if_needed",
    "sanitize_assistant_text",
]
