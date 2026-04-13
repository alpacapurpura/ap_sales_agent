import asyncio
import json
import random
import re

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
from src.shared.domain.messages import OutgoingMessage

logger = structlog.get_logger()


class OutputManager:
    """
    Manages the "Human Typing Simulation" and "Response Chunking" logic.
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
        channel_adapter,
        channel_type: str = "telegram",
    ):
        """
        Parses the raw LLM response and sends it as chunks with human-like delays.
        """
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
                logger.error("error_sending_chunk", user_id=user_id, error=str(e))
                # Continue sending other chunks? Or abort?
                # Better to continue in case it's a transient issue, but usually aborts.
                # We'll log and continue.

            # 4. Cognitive Pause (Micro-delay)
            # Don't wait after the last message
            if i < len(chunks) - 1:
                pause = random.uniform(*cls.MICRO_DELAY_RANGE)  # noqa: S311
                await asyncio.sleep(pause)

    @classmethod
    def _parse_response(
        cls,
        raw_response: str,
        channel_type: str = "telegram",  # noqa: ARG003
    ) -> list[str]:
        """
        Parses the raw LLM response into user-facing chunks.

        Pipeline:
        1. Strip internal blocks ([QUALIFICATION_DATA:...], [SIGNALS:...], [TOOL_REQUEST:...])
        2. Remove markdown code-block wrappers (common LLM artifact)
        3. Try JSON array (backward compat with older prompt format)
        4. Split by paragraph breaks (double newline)
        5. Fallback to single chunk
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
        if cleaned.startswith("["):
            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, list):
                    return [
                        str(item).strip()
                        for item in parsed
                        if item and str(item).strip()
                    ]
            except json.JSONDecodeError:
                pass

        # 4. Split by double newline (paragraph breaks)
        paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
        if len(paragraphs) > 1:
            return paragraphs

        # 5. Single chunk fallback
        return [cleaned] if cleaned else []

    @classmethod
    def _calculate_typing_time(cls, text: str) -> float:
        """
        Calculates typing delay based on CPM and Jitter.
        Formula: (Chars / CPM) * 60 * Jitter
        """
        length = len(text)
        base_seconds = (length / cls.CPM_SPEED) * 60

        # Apply jitter
        jitter = random.uniform(*cls.JITTER_RANGE)  # noqa: S311
        final_time = base_seconds * jitter

        # Clamp values
        return max(cls.MIN_TYPING_TIME, min(final_time, cls.MAX_TYPING_TIME))
