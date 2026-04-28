"""Channel format dataclass + cross-agent registry (S5).

Migrado desde ``src/modules/copilot/domain/output_channels.py`` con tres
extensiones para sales_agent:

* ``chunk_size: int | None`` — máximo por chunk en
  ``OutputManager._parse_response``. None → no enforce (paragraph-only split).
* ``typing_simulation_cpm: int | None`` — chars-per-minute realismo del
  ``OutputManager`` typing indicator. None → fallback a ``CPM_SPEED`` global.
* ``parse_mode: str | None`` — hint para channel adapter (ej: Telegram
  ``"MarkdownV2"``). El registry no lo aplica auto; el adapter consume.

Specs sourced de research April 2026 (ver
``phases/S5-channel-registry.md::Hallazgos research``):

* WhatsApp Business — 4096 session text, 1024 templates. Markdown subset
  propio (no estándar). chunk_size=1024 para copy-paste safe + Evolution
  API v2 wrapper compatible.
* Telegram — 4096 chars, parse_mode MarkdownV2 escape (lista oficial en
  ``escape_markdown_v2``). chunk_size=4096 (no split).
* Instagram DM — 1000 chars, plain text only.
* SMS — GSM-7 single segment 160 chars; tildes/emoji disparan UCS-2 (70).
* Voice / Email / Chat — sin chunk_size (el adapter decide).

# [SALES-AGENT-CHANNEL-REGISTRY-S5] -> docs/domains/sales-agent/redesign-2026-04/phases/S5-channel-registry.md
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChannelFormat:
    """Spec for a single output channel.

    Attributes:
        id: Stable lower_snake registry key (``"whatsapp"``, ``"sms"``…).
        label_es: Spanish neutro LatAm label shown in admin and UI selectors.
        max_chars: Hard ceiling enforced by ``format_for_channel`` and the
            synthesizer truncation step. Must be ``> 0``.
        emoji_allowed: When ``False``, the LLM is instructed not to emit
            emoji and post-processors strip them.
        line_break_style: Newline pattern preferred by the channel.
        markdown_allowed: When ``False``, the LLM is told to emit plain text
            and post-processors strip standard markdown markers.
        structure_hint: Spanish-neutro guidance prepended to the LLM system
            prompt for this channel.
        chunk_size: Optional sales-only field. ``OutputManager._parse_response``
            splits paragraphs longer than this. ``None`` keeps legacy
            paragraph-only behavior.
        typing_simulation_cpm: Optional sales-only field. ``OutputManager``
            uses it to scale typing-simulation latency. ``None`` falls back
            to the global ``CPM_SPEED`` constant.
        parse_mode: Optional adapter hint (``"MarkdownV2"`` for Telegram).
            The registry does not apply it; channel adapters consume it.
    """

    id: str
    label_es: str
    max_chars: int
    emoji_allowed: bool
    line_break_style: str
    markdown_allowed: bool
    structure_hint: str
    chunk_size: int | None = None
    typing_simulation_cpm: int | None = None
    parse_mode: str | None = None


# ── Baseline (canonical) channels — S5 ships seven ────────────────────────

_CHAT = ChannelFormat(
    id="chat",
    label_es="Chat (Copilot)",
    max_chars=4000,
    emoji_allowed=True,
    line_break_style="\n\n",
    markdown_allowed=True,
    structure_hint=(
        "Respuesta directa para el chat del Copilot. Markdown ligero permitido "
        "(negritas, listas, links). 1 a 3 párrafos cortos; usa listas si hay "
        "múltiples ítems. No menciones que estás en un canal específico."
    ),
)

_WHATSAPP = ChannelFormat(
    id="whatsapp",
    label_es="WhatsApp",
    max_chars=4096,  # session-message ceiling per WhatsApp Business API 2026
    emoji_allowed=True,
    line_break_style="\n\n",
    markdown_allowed=False,  # WA usa subset propio (*bold*/_italic_/~strike~), no markdown estándar.
    structure_hint=(
        "Mensaje listo para copiar y pegar en WhatsApp: hook breve (1 línea), "
        "1 a 3 bullets cortos opcionales con guión, cierre con CTA o pregunta "
        "abierta. Sin markdown estándar; los asteriscos / underscores se ven "
        "como símbolos. Emojis permitidos cuando suman. Mantén el mensaje "
        "por debajo de 1024 caracteres para que no rompa templates."
    ),
    chunk_size=1024,  # WA template-safe ceiling for copy-paste
)

_EMAIL = ChannelFormat(
    id="email",
    label_es="Email",
    max_chars=5000,
    emoji_allowed=True,
    line_break_style="\n\n",
    markdown_allowed=True,
    structure_hint=(
        "Email en texto plano (mejor entregabilidad que HTML). Estructura: "
        "asunto en la primera línea precedido de 'Asunto:', luego saludo "
        "personal, 2 a 4 párrafos cortos, CTA claro, firma. Evita imágenes y "
        "links excesivos para no caer en spam."
    ),
)

_SMS = ChannelFormat(
    id="sms",
    label_es="SMS",
    max_chars=160,
    emoji_allowed=False,
    line_break_style=" — ",
    markdown_allowed=False,
    structure_hint=(
        "Un único SMS GSM-7 de máximo 160 caracteres. Sin emoji y sin tildes "
        "(fuerzan codificación UCS-2 que reduce el cupo a 70 caracteres). Una "
        "sola idea + CTA o link corto. Sin markdown ni saltos de línea."
    ),
)

_VOICE = ChannelFormat(
    id="voice",
    label_es="Voz (audio)",
    max_chars=800,
    emoji_allowed=False,
    line_break_style=". ",
    markdown_allowed=False,
    structure_hint=(
        "Texto pensado para que se lea en audio (TTS). Oraciones cortas, "
        "puntuación clara para marcar pausas naturales. Sin markdown, sin "
        "emojis, sin links largos. Tono conversacional."
    ),
)

_INSTAGRAM_DM = ChannelFormat(
    id="instagram_dm",
    label_es="Instagram DM",
    max_chars=1000,
    emoji_allowed=True,
    line_break_style="\n\n",
    markdown_allowed=False,
    structure_hint=(
        "Mensaje directo de Instagram en tono casual. 1 o 2 párrafos breves, "
        "emojis permitidos cuando suman, cierre con pregunta abierta o CTA "
        "suave. Sin markdown — los DMs no lo renderizan."
    ),
    chunk_size=900,  # leave headroom for emojis (count as ≥2 chars)
)

_TELEGRAM = ChannelFormat(
    id="telegram",
    label_es="Telegram",
    max_chars=4096,
    emoji_allowed=True,
    line_break_style="\n\n",
    markdown_allowed=True,
    structure_hint=(
        "Mensaje de Telegram. Markdown permitido (Telegram soporta MarkdownV2 "
        "con negritas, cursivas, código y links). Hasta 4096 caracteres por "
        "mensaje. Estructura clara: hook, cuerpo con bullets si aplica, CTA."
    ),
    parse_mode="MarkdownV2",
)


_BASELINE: dict[str, ChannelFormat] = {
    fmt.id: fmt for fmt in (_CHAT, _WHATSAPP, _EMAIL, _SMS, _VOICE, _INSTAGRAM_DM, _TELEGRAM)
}


# Aliases — sales_agent ChannelResolver uses ``instagram`` (no ``_dm`` suffix).
# Single SSoT pero permite ambos spellings sin duplicar entrada.
_CHANNEL_ID_ALIASES: dict[str, str] = {
    "instagram": "instagram_dm",
}


# Public registry — mutable via ``register_channel`` only.
CHANNEL_FORMATS: dict[str, ChannelFormat] = dict(_BASELINE)


def _refresh_supported() -> frozenset[str]:
    return frozenset(CHANNEL_FORMATS.keys())


SUPPORTED_CHANNELS: frozenset[str] = _refresh_supported()


def get_channel_format(channel_id: str | None) -> ChannelFormat:
    """Resolve a registry entry, falling back to ``chat`` on miss.

    Aliases (``instagram`` → ``instagram_dm``) are resolved transparently.
    Never raises — malformed callers get the safe ``chat`` baseline.
    """
    if not channel_id:
        return CHANNEL_FORMATS["chat"]
    canonical = _CHANNEL_ID_ALIASES.get(channel_id, channel_id)
    return CHANNEL_FORMATS.get(canonical, CHANNEL_FORMATS["chat"])


def register_channel(fmt: ChannelFormat, *, key: str | None = None) -> None:
    """Add a new channel to the registry.

    Idempotent for the *same object* but rejects different formats trying
    to claim an existing id.

    Raises:
        ValueError: If ``fmt.id`` is empty, the key/id mismatch, or the id
            is already taken by a different ``ChannelFormat``.
    """
    global SUPPORTED_CHANNELS  # noqa: PLW0603 — registry mutation is the entire purpose.

    if not fmt.id:
        msg = "ChannelFormat requires a non-empty id"
        raise ValueError(msg)
    if key is not None and key != fmt.id:
        msg = f"register_channel id mismatch: key={key!r} fmt.id={fmt.id!r}"
        raise ValueError(msg)

    existing = CHANNEL_FORMATS.get(fmt.id)
    if existing is not None and existing != fmt:
        msg = f"channel {fmt.id!r} already registered with different spec"
        raise ValueError(msg)

    CHANNEL_FORMATS[fmt.id] = fmt
    SUPPORTED_CHANNELS = _refresh_supported()


def reset_registry_for_tests() -> None:
    """Restore the baseline registry. Tests only."""
    global SUPPORTED_CHANNELS  # noqa: PLW0603 — registry mutation is the entire purpose.

    CHANNEL_FORMATS.clear()
    CHANNEL_FORMATS.update(_BASELINE)
    SUPPORTED_CHANNELS = _refresh_supported()


# ── Telegram MarkdownV2 escape utility ────────────────────────────────────

# Per https://core.telegram.org/bots/api#markdownv2-style — chars that MUST be
# escaped with a preceding ``\`` in MarkdownV2 mode (outside pre/code blocks
# and link href context, which have their own subset).
_MARKDOWN_V2_SPECIAL_CHARS = "_*[]()~`>#+-=|{}.!"
_MARKDOWN_V2_RE = re.compile(rf"([{re.escape(_MARKDOWN_V2_SPECIAL_CHARS)}\\])")


def escape_markdown_v2(text: str) -> str:
    """Escape Telegram MarkdownV2 special characters.

    Use when emitting raw user text via Telegram's ``parse_mode=MarkdownV2``
    so a stray ``.`` / ``-`` / ``!`` does not break parsing. Channel adapters
    apply this; the system prompt formatter does not auto-apply (would break
    intentional markdown).
    """
    return _MARKDOWN_V2_RE.sub(r"\\\1", text)


__all__ = (
    "CHANNEL_FORMATS",
    "SUPPORTED_CHANNELS",
    "ChannelFormat",
    "escape_markdown_v2",
    "get_channel_format",
    "register_channel",
    "reset_registry_for_tests",
)
