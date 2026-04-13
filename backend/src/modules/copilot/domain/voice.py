"""Voice domain ports for speech-to-text and text-to-speech."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TranscriptionResult:
    """Result of a speech-to-text transcription."""

    text: str
    language: str
    duration_seconds: float


class TranscriptionPort(Protocol):
    """Port for speech-to-text. Implemented by Whisper today, extensible."""

    async def transcribe(self, audio: bytes, mime_type: str) -> TranscriptionResult: ...


class SynthesisPort(Protocol):
    """Port for text-to-speech. Not implemented in Phase 3. Prepared for future TTS."""

    async def synthesize(self, text: str, voice: str) -> bytes: ...
