"""F7 — ``format_for_channel`` transversal tool.

Deterministic post-processor that adapts arbitrary text to a channel's
spec. No LLM call: the purpose is "I have this draft, give it to me clean
for WhatsApp / SMS / email". For prose generation use the synthesizer of
``ask_tenant_data`` (which already reads the same registry).

The tool is a thin wrapper around the registry — adding a new channel via
``register_channel`` makes it available here automatically.

# [COPILOT-CHANNEL-FORMATTER-F7] -> docs/domains/copilot/redesign-2026-04/phases/F7-channel-formatter.md
"""

from __future__ import annotations

import json
import re

import structlog
from langchain_core.tools import tool

from src.modules.copilot.domain.output_channels import (
    ChannelFormat,
    get_channel_format,
)

logger = structlog.get_logger()


# Standard markdown markers we strip when ``markdown_allowed=False``. The
# patterns are ordered: link → fenced code → inline code → bold → italic →
# heading → blockquote → list-bullet. Replacement keeps inner text + URLs
# (so a link "[click](https://x.com)" becomes "click https://x.com") so the
# message remains useful when pasted in plain channels.
_MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_MD_FENCED = re.compile(r"```[a-zA-Z0-9_-]*\n?(.*?)```", re.DOTALL)
_MD_INLINE_CODE = re.compile(r"`([^`]+)`")
_MD_BOLD = re.compile(r"\*\*([^*]+)\*\*|__([^_]+)__")
_MD_ITALIC = re.compile(r"(?<!\*)\*(?!\*)([^*\n]+)\*(?!\*)|(?<!_)_([^_\n]+)_(?!_)")
_MD_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+", re.MULTILINE)
_MD_BLOCKQUOTE = re.compile(r"^\s{0,3}>\s?", re.MULTILINE)
_MD_LIST_BULLET = re.compile(r"^\s{0,3}[-*+]\s+", re.MULTILINE)


# Emoji ranges per Unicode 15.1 (April 2026 baseline). Covers the bulk of
# pictographs without depending on the ``emoji`` package — keeps the tool
# import-light. False negatives on rare glyphs are acceptable; the goal is
# to keep SMS GSM-7-clean, not to be a strict moderation filter.
_EMOJI_RE = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # symbols & pictographs
    "\U0001f680-\U0001f6ff"  # transport & map
    "\U0001f1e0-\U0001f1ff"  # flags
    "\U00002500-\U00002bef"  # geometric / arrows
    "\U00002702-\U000027b0"  # dingbats
    "\U000024c2-\U0001f251"
    "\U0001f900-\U0001f9ff"  # supplemental symbols & pictographs
    "\U0001fa70-\U0001faff"  # symbols & pictographs extended-A
    "\U00002600-\U000026ff"  # misc symbols
    "]",
    flags=re.UNICODE,
)


def _strip_markdown(text: str) -> str:
    """Remove standard markdown markers, preserving inner content + URLs."""
    out = text
    out = _MD_LINK.sub(r"\1 \2", out)
    out = _MD_FENCED.sub(r"\1", out)
    out = _MD_INLINE_CODE.sub(r"\1", out)
    out = _MD_BOLD.sub(lambda m: m.group(1) or m.group(2) or "", out)
    out = _MD_ITALIC.sub(lambda m: m.group(1) or m.group(2) or "", out)
    out = _MD_HEADING.sub("", out)
    out = _MD_BLOCKQUOTE.sub("", out)
    out = _MD_LIST_BULLET.sub("- ", out)
    return out


def _strip_emoji(text: str) -> str:
    return _EMOJI_RE.sub("", text)


def _truncate(text: str, limit: int) -> str:
    """Hard truncate to ``limit`` characters, marking the cut with `…`."""
    if len(text) <= limit:
        return text
    if limit <= 1:
        return text[:limit]
    return text[: limit - 1].rstrip() + "…"


def format_for_channel_impl(*, content: str, channel_id: str) -> dict[str, object]:
    """Apply a channel's spec to raw text and report what changed.

    Args:
        content: Raw text to format.
        channel_id: Target channel id (must be in ``CHANNEL_FORMATS``; falls
            back to ``chat`` when unknown).

    Returns:
        A dict with::

            {
                "channel": str,        # resolved channel id
                "label": str,          # human label (Spanish neutro)
                "content": str,        # adjusted text
                "warnings": list[str], # ordered: markdown_stripped /
                                       #          emoji_stripped /
                                       #          truncated
                "char_count": int,     # len(content)
            }
    """
    fmt: ChannelFormat = get_channel_format(channel_id)
    out = content
    warnings: list[str] = []

    if not fmt.markdown_allowed and out:
        stripped = _strip_markdown(out)
        if stripped != out:
            warnings.append("markdown_stripped")
            out = stripped

    if not fmt.emoji_allowed and out:
        stripped = _strip_emoji(out)
        if stripped != out:
            warnings.append("emoji_stripped")
            out = stripped

    if len(out) > fmt.max_chars:
        out = _truncate(out, fmt.max_chars)
        warnings.append("truncated")

    return {
        "channel": fmt.id,
        "label": fmt.label_es,
        "content": out,
        "warnings": warnings,
        "char_count": len(out),
    }


@tool
async def format_for_channel(content: str, channel_id: str) -> str:
    """Adapta un texto al canal de salida indicado (whatsapp, email, sms…).

    Cuándo usarla:
    - El usuario dice "dame esto listo para WhatsApp / email / SMS".
    - Después de generar prosa larga, querés validar que cumpla con el cap
      de chars y limpiar markdown que el canal destino no renderiza.
    - Antes de copiar al portapapeles algo que el usuario va a enviar
      manualmente desde otro canal.

    Args:
        content: Texto crudo que querés adaptar.
        channel_id: Id del canal destino (``chat``, ``whatsapp``, ``email``,
            ``sms``, ``voice``, ``instagram_dm``, ``telegram``). Si no se
            reconoce, se usa ``chat``.

    Returns:
        JSON con ``channel``, ``label``, ``content`` adaptado,
        ``warnings`` (lista con ``markdown_stripped`` / ``emoji_stripped`` /
        ``truncated`` si aplica) y ``char_count``.
    """
    payload = format_for_channel_impl(content=content, channel_id=channel_id)
    logger.info(
        "format_for_channel_done",
        channel=payload["channel"],
        warnings=payload["warnings"],
        char_count=payload["char_count"],
    )
    return json.dumps(payload, ensure_ascii=False)


__all__ = ("format_for_channel", "format_for_channel_impl")
