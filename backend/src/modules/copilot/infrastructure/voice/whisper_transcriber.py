"""WhisperTranscriber — Speech-to-text via OpenAI Whisper API."""

from __future__ import annotations

import io

import structlog
from openai import AsyncOpenAI

from src.core.config import settings
from src.modules.copilot.domain.voice import TranscriptionResult

logger = structlog.get_logger()

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

MIME_TO_EXT: dict[str, str] = {
    "audio/webm": "webm",
    "audio/mp4": "mp4",
    "audio/wav": "wav",
    "audio/mpeg": "mp3",
    "audio/m4a": "m4a",
}


class WhisperTranscriber:
    """Speech-to-text via OpenAI Whisper API.

    Implements ``TranscriptionPort`` structurally (duck typing / Protocol).
    """

    async def transcribe(self, audio: bytes, mime_type: str) -> TranscriptionResult:
        ext = MIME_TO_EXT.get(mime_type, "webm")
        audio_file = io.BytesIO(audio)
        audio_file.name = f"recording.{ext}"

        logger.info(
            "whisper_transcribe_start", size_bytes=len(audio), mime_type=mime_type
        )

        response = await openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="es",
            response_format="verbose_json",
        )

        result = TranscriptionResult(
            text=response.text,
            language=response.language or "es",
            duration_seconds=response.duration or 0.0,
        )

        logger.info(
            "whisper_transcribe_done",
            text_length=len(result.text),
            language=result.language,
            duration=result.duration_seconds,
        )
        return result
