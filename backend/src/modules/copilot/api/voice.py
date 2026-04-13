"""Voice API — speech-to-text transcription endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Depends, File, UploadFile

if TYPE_CHECKING:
    from uuid import UUID

from src.modules.copilot.api.voice_dto import TranscriptionResponse
from src.modules.copilot.infrastructure.voice.whisper_transcriber import (
    WhisperTranscriber,
)
from src.modules.iam.api.dependencies import get_tenant_context

logger = structlog.get_logger()

router = APIRouter(tags=["Copilot - Voice"])


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    tenant_id: UUID = Depends(get_tenant_context),
) -> TranscriptionResponse:
    """Receive an audio blob and return transcribed text via Whisper."""
    audio_bytes = await file.read()
    mime_type = file.content_type or "audio/webm"

    logger.info(
        "voice_transcribe_request",
        tenant_id=str(tenant_id),
        file_name=file.filename,
        mime_type=mime_type,
        size_bytes=len(audio_bytes),
    )

    transcriber = WhisperTranscriber()
    result = await transcriber.transcribe(audio_bytes, mime_type)

    return TranscriptionResponse(
        text=result.text,
        language=result.language,
        duration_seconds=result.duration_seconds,
    )
