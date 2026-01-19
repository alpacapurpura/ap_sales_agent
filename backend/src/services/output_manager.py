import json
import asyncio
import random
import re
import structlog
from typing import List, Union
from src.core.schema import OutgoingMessage

logger = structlog.get_logger()

class OutputManager:
    """
    Manages the "Human Typing Simulation" and "Response Chunking" logic.
    Follows High Ticket sales principles: Triad structure and variable typing speed.
    """
    
    # Constants for typing simulation
    CPM_SPEED = 320  # Characters per minute (High Ticket Standard: 300-350)
    JITTER_RANGE = (0.8, 1.2) # Variability factor
    MIN_TYPING_TIME = 1.5 # Minimum time to show "typing..."
    MAX_TYPING_TIME = 6.0 # Cap to avoid awkward pauses
    MICRO_DELAY_RANGE = (0.4, 0.8) # Pause between sending and next typing (Cognitive pause)
    
    @classmethod
    async def process_response(cls, user_id: str, raw_response: str, channel_adapter):
        """
        Parses the raw LLM response and sends it as chunks with human-like delays.
        """
        chunks = cls._parse_response(raw_response)
        
        logger.info("processing_response_chunks", user_id=user_id, chunks_count=len(chunks))
        
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
                
            # 1. Calculate Typing Time
            typing_time = cls._calculate_typing_time(chunk)
            
            # 2. Show Typing Indicator
            # Only if the channel adapter supports it
            if hasattr(channel_adapter, "set_typing_status"):
                await channel_adapter.set_typing_status(user_id)
            
            logger.debug("simulating_typing", user_id=user_id, duration=typing_time, chunk_preview=chunk[:20])
            await asyncio.sleep(typing_time)
            
            # 3. Send Message
            outgoing = OutgoingMessage(
                user_id=user_id,
                text=chunk
            )
            
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
                pause = random.uniform(*cls.MICRO_DELAY_RANGE)
                await asyncio.sleep(pause)

    @classmethod
    def _parse_response(cls, raw_response: str) -> List[str]:
        """
        Attempts to parse the response as a JSON array.
        Falls back to splitting by newlines or returning raw text if parsing fails.
        """
        cleaned = raw_response.strip()
        
        # Remove markdown code blocks if present (common LLM artifact)
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.MULTILINE)
        
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                # Ensure all elements are strings
                return [str(item) for item in parsed if item]
        except json.JSONDecodeError:
            logger.warning("json_parsing_failed_fallback_text", raw_response=raw_response[:50])
            
        # Fallback: If JSON fails, we return it as a single chunk.
        return [raw_response]

    @classmethod
    def _calculate_typing_time(cls, text: str) -> float:
        """
        Calculates typing delay based on CPM and Jitter.
        Formula: (Chars / CPM) * 60 * Jitter
        """
        length = len(text)
        base_seconds = (length / cls.CPM_SPEED) * 60
        
        # Apply jitter
        jitter = random.uniform(*cls.JITTER_RANGE)
        final_time = base_seconds * jitter
        
        # Clamp values
        return max(cls.MIN_TYPING_TIME, min(final_time, cls.MAX_TYPING_TIME))
