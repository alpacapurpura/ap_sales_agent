"""Channel formatter registry — F7.

Replaces F5's tiny ``_CHANNEL_HINTS`` dict in
``application/tools/ask_tenant_data/synthesizer.py`` with a domain-owned,
extension-friendly registry. Consumers:

* ``synthesize_answer`` (F5 hook) — channel-aware system-prompt + truncation.
* ``format_for_channel`` tool (F7) — post-process arbitrary text to a channel
  spec without going through the synthesizer pipeline.
* External providers — ``register_channel(format)`` adds tenant-specific or
  provider-specific channels (e.g. a future Discord adapter).

Specs sourced from April 2026 research on channel limits + LLM output guidance:

* WhatsApp Business — text messages cap at 4096 chars; templates at 1024. We
  keep ``max_chars=1024`` to stay template-safe by default and avoid markdown
  (WhatsApp's *bold*/_italic_/~strike~ subset is not standard markdown — letting
  the LLM emit standard markdown breaks the copy-paste path).
* Email — plain text ranks higher for deliverability than HTML in 2026 cold/
  outreach studies; keeping markdown_allowed=True lets the renderer (or the
  user's email client) decide whether to render it. ``max_chars`` capped at
  5000 to discourage walls of text.
* SMS — GSM-7 single segment is 160 chars; the moment an emoji or accent
  flips the message to UCS-2 the cap drops to 70. We disallow emoji and
  markdown so the LLM stays inside GSM-7 territory.
* Voice — text-to-speech-friendly; no markdown, no emoji, sentence-style
  punctuation that maps to natural pauses.
* Instagram DM — casual short-form; emojis OK but markdown is not rendered.
* Telegram — supports MarkdownV2 + 4096 chars per message; the most
  permissive of the messaging channels.

Registry mutability is intentional but bounded: ``register_channel`` is the
only public mutation entry point and rejects duplicates / empty ids. Tests
restore baseline via ``reset_registry_for_tests``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChannelFormat:
    """Spec for a single output channel.

    All fields are required and immutable. The dataclass is frozen so two
    consumers reading the same registry entry can rely on identity equality.

    Attributes:
        id: Stable lower_snake registry key (``"whatsapp"``, ``"sms"``…).
        label_es: Spanish neutro LatAm label shown in admin and UI selectors.
        max_chars: Hard ceiling enforced by ``format_for_channel`` and the
            synthesizer truncation step. Must be ``> 0``.
        emoji_allowed: When ``False``, the LLM is instructed not to emit emoji
            (SMS GSM-7 / voice). Post-processors may strip emojis if found.
        line_break_style: Newline pattern preferred by the channel. Used by
            the formatter when normalising paragraph breaks.
        markdown_allowed: When ``False``, the LLM is told to emit plain text.
            Post-processors may strip standard markdown markers from output.
        structure_hint: Short Spanish-neutro guidance prepended to the LLM
            system prompt for this channel.
    """

    id: str
    label_es: str
    max_chars: int
    emoji_allowed: bool
    line_break_style: str
    markdown_allowed: bool
    structure_hint: str


# ── Baseline (canonical) channels — F7 ships seven ─────────────────────────

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
    max_chars=1024,
    emoji_allowed=True,
    line_break_style="\n\n",
    markdown_allowed=False,
    structure_hint=(
        "Mensaje listo para copiar y pegar en WhatsApp: hook breve (1 línea), "
        "1 a 3 bullets cortos opcionales con guión, cierre con CTA o pregunta "
        "abierta. Sin markdown; los asteriscos / underscores se ven como "
        "símbolos. Emojis permitidos cuando suman. Mantén el mensaje por "
        "debajo de 1024 caracteres para que no rompa templates."
    ),
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
)


_BASELINE: dict[str, ChannelFormat] = {
    fmt.id: fmt for fmt in (_CHAT, _WHATSAPP, _EMAIL, _SMS, _VOICE, _INSTAGRAM_DM, _TELEGRAM)
}


# Public registry — mutable via ``register_channel`` only. Consumers must
# treat values as immutable (the dataclass enforces it) but the dict itself
# accepts new entries from providers.
CHANNEL_FORMATS: dict[str, ChannelFormat] = dict(_BASELINE)


def _refresh_supported() -> frozenset[str]:
    return frozenset(CHANNEL_FORMATS.keys())


SUPPORTED_CHANNELS: frozenset[str] = _refresh_supported()


def get_channel_format(channel_id: str | None) -> ChannelFormat:
    """Resolve a registry entry, falling back to ``chat`` on miss.

    The fallback keeps the synthesizer / formatter resilient to malformed
    callers — never raises. Callers that want strict lookup should check
    ``channel_id in SUPPORTED_CHANNELS`` before calling.
    """
    if not channel_id:
        return CHANNEL_FORMATS["chat"]
    return CHANNEL_FORMATS.get(channel_id, CHANNEL_FORMATS["chat"])


def register_channel(fmt: ChannelFormat, *, key: str | None = None) -> None:
    """Add a new channel to the registry.

    Providers call this from their package ``__init__`` (or any import-time
    side effect they own) so their channel is available before discovery
    finishes. Registration is idempotent for the *same object* but rejects
    different formats trying to claim an existing id.

    Args:
        fmt: The channel format to register.
        key: Optional explicit registry key. When provided, must equal
            ``fmt.id`` — prevents typos where the wrapper dict and the
            ``ChannelFormat`` value disagree.

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
    """Restore the baseline registry. Tests only.

    Providers register at import time; tests that register custom channels
    must call this in teardown (or via a fixture) to isolate state.
    """
    global SUPPORTED_CHANNELS  # noqa: PLW0603 — see ``register_channel``.

    CHANNEL_FORMATS.clear()
    CHANNEL_FORMATS.update(_BASELINE)
    SUPPORTED_CHANNELS = _refresh_supported()


__all__ = (
    "CHANNEL_FORMATS",
    "SUPPORTED_CHANNELS",
    "ChannelFormat",
    "get_channel_format",
    "register_channel",
    "reset_registry_for_tests",
)
