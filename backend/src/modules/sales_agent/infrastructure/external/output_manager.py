"""Output Manager infrastructure module."""

from __future__ import annotations

import asyncio
import json
import random
import re
from typing import TYPE_CHECKING

import structlog

from src.modules.sales_agent.domain.tuning import (
    CPM_SPEED as _CPM_SPEED,
)
from src.modules.sales_agent.domain.tuning import (
    MAX_TYPING_TIME as _MAX_TYPING_TIME,
)
from src.modules.sales_agent.domain.tuning import (
    MICRO_DELAY_RANGE as _MICRO_DELAY_RANGE,
)
from src.modules.sales_agent.domain.tuning import (
    MIN_TYPING_TIME as _MIN_TYPING_TIME,
)
from src.modules.sales_agent.domain.tuning import (
    TYPING_JITTER,
)
from src.shared.agent_observability.channels.format import get_channel_format
from src.shared.domain.messages import OutgoingMessage

if TYPE_CHECKING:
    from src.shared.infrastructure.channels.base import BaseChannel

logger = structlog.get_logger()


class OutputManager:
    """Manages the "Human Typing Simulation" and "Response Chunking" logic.

    Follows High Ticket sales principles: Triad structure and variable typing speed.
    """

    # Constants for typing simulation (sourced from domain/tuning.py)
    CPM_SPEED = _CPM_SPEED
    JITTER_RANGE = TYPING_JITTER
    MIN_TYPING_TIME = _MIN_TYPING_TIME
    MAX_TYPING_TIME = _MAX_TYPING_TIME
    MICRO_DELAY_RANGE = _MICRO_DELAY_RANGE

    @classmethod
    async def process_response(
        cls,
        user_id: str,
        raw_response: str,
        channel_adapter: BaseChannel,
        channel_type: str = "telegram",
    ) -> None:
        """Parse the raw LLM response and sends it as chunks with human-like delays."""
        chunks = cls._parse_response(raw_response, channel_type=channel_type)

        logger.info(
            "processing_response_chunks",
            user_id=user_id,
            chunks_count=len(chunks),
        )

        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue

            # 1. Calculate Typing Time
            typing_time = cls._calculate_typing_time(chunk)

            # 2. Show Typing Indicator
            # Only if the channel adapter supports it
            if hasattr(channel_adapter, "set_typing_status"):
                await channel_adapter.set_typing_status(user_id)

            logger.debug(
                "simulating_typing",
                user_id=user_id,
                duration=typing_time,
                chunk_preview=chunk[:20],
            )
            await asyncio.sleep(typing_time)

            # 3. Send Message
            outgoing = OutgoingMessage(user_id=user_id, text=chunk)

            try:
                await channel_adapter.send_message(outgoing)
            except Exception as e:
                logger.exception("error_sending_chunk", user_id=user_id, error=str(e))
                # Continue sending other chunks? Or abort?
                # Better to continue in case it's a transient issue, but usually aborts.
                # We'll log and continue.

            # 4. Cognitive Pause (Micro-delay)
            # Don't wait after the last message
            if i < len(chunks) - 1:
                pause = random.uniform(*cls.MICRO_DELAY_RANGE)
                await asyncio.sleep(pause)

    @classmethod
    def _parse_response(
        cls,
        raw_response: str,
        channel_type: str = "telegram",
    ) -> list[str]:
        """Parse the raw LLM response into user-facing chunks.

        Pipeline:
        1. Strip internal blocks ([QUALIFICATION_DATA:...], [SIGNALS:...], [TOOL_REQUEST:...])
        2. Remove markdown code-block wrappers (common LLM artifact)
        3. Try JSON array (backward compat with older prompt format)
        4. Split by paragraph breaks (double newline)
        5. Fallback to single chunk
        6. Cap each chunk to ``ChannelFormat.chunk_size`` when the registry
           declares one for this channel (S5). Channels without ``chunk_size``
           keep the legacy paragraph-only behavior.
        """
        # 1. Strip internal blocks before user sees them
        cleaned = re.sub(
            r"\[(?:QUALIFICATION_DATA|SIGNALS|TOOL_REQUEST):\s*\{.*?\}\]",
            "",
            raw_response,
            flags=re.DOTALL,
        ).strip()

        # 2. Remove markdown code blocks if present
        if cleaned.startswith("```"):
            cleaned = re.sub(
                r"^```(?:json)?\s*|\s*```$",
                "",
                cleaned,
                flags=re.MULTILINE,
            ).strip()

        # 3. Try JSON array first (backward compat)
        chunks: list[str] | None = None
        if cleaned.startswith("["):
            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, list):
                    chunks = [str(item).strip() for item in parsed if item and str(item).strip()]
            except json.JSONDecodeError:
                chunks = None

        # 4. Split by double newline (paragraph breaks)
        if chunks is None:
            paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
            if len(paragraphs) > 1:
                chunks = paragraphs
            elif cleaned:
                # 5. Single chunk fallback
                chunks = [cleaned]
            else:
                chunks = []

        # 6. Cap chunk length when the channel registry declares chunk_size.
        return cls._enforce_chunk_size(chunks, channel_type)

    @classmethod
    def _enforce_chunk_size(cls, chunks: list[str], channel_type: str) -> list[str]:
        """Split chunks longer than ``ChannelFormat.chunk_size`` (S5).

        Strategy: prefer whitespace boundaries (sentence end, then word) so
        we don't chop mid-word. Fall back to hard cut for words longer than
        the cap. ``chunk_size=None`` (chat / email / voice / sms) means no
        enforcement — paragraph chunks pass through as-is.
        """
        fmt = get_channel_format(channel_type)
        cap = fmt.chunk_size
        if cap is None or cap <= 0:
            return chunks

        out: list[str] = []
        for chunk in chunks:
            out.extend(cls._split_by_cap(chunk, cap))
        return out

    @staticmethod
    def _split_by_cap(text: str, cap: int) -> list[str]:
        r"""Split ``text`` so each piece is ≤ ``cap`` chars.

        Boundary preference: sentence end (``. `` / ``! `` / ``? `` / ``…`` /
        ``\n``) → whitespace → hard cut. The boundary character is kept in
        the LEFT piece so chunks read naturally (``"... módulos prácticos."``
        not ``"... módulos prácticos"``).
        """
        if len(text) <= cap:
            return [text]

        pieces: list[str] = []
        remaining = text
        while len(remaining) > cap:
            window = remaining[:cap]
            # Sentence-end markers: index reported by rfind is the start of
            # the substring; piece must end ONE char after the punctuation
            # so the ``.`` / ``!`` / ``?`` stays attached.
            sentence_marker = max((window.rfind(s), len(s)) for s in (". ", "! ", "? ", "…", "\n"))
            sent_idx, sent_len = sentence_marker
            if sent_idx > 0 and sent_idx >= cap // 2:
                split_at = sent_idx + (sent_len - 1) if sent_len > 1 else sent_idx + 1
            else:
                ws = window.rfind(" ")
                split_at = ws if ws > cap // 4 else cap

            piece = remaining[:split_at].rstrip()
            if piece:
                pieces.append(piece)
            remaining = remaining[split_at:].lstrip()

        if remaining:
            pieces.append(remaining)
        return pieces

    @classmethod
    def _calculate_typing_time(cls, text: str) -> float:
        """Calculate typing delay based on CPM and Jitter.

        Formula: (Chars / CPM) * 60 * Jitter
        """
        length = len(text)
        base_seconds = (length / cls.CPM_SPEED) * 60

        # Apply jitter
        jitter = random.uniform(*cls.JITTER_RANGE)
        final_time = base_seconds * jitter

        # Clamp values
        return max(cls.MIN_TYPING_TIME, min(final_time, cls.MAX_TYPING_TIME))
