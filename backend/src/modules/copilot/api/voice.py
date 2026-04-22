"""Voice API — speech-to-text transcription and combined upload+transcribe endpoints.

# [COPILOT-VOICE-DUAL-MODE] → docs/domains/copilot/CONTRACT-MULTIMODAL.md §9

Two endpoints:
- POST /transcribe — legacy endpoint (STT only). Kept for backward-compat.
- POST /upload-and-transcribe — new combined endpoint (D0.4 of the contract).
  Atomically stores the audio AND transcribes it. Returns a complete AudioBlock.
  Both operations run concurrently (asyncio.gather) to minimize latency.
"""

import asyncio
import io
import uuid
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.assets.application.assets_service import AssetsService
from src.modules.copilot.api.voice_dto import (
    TranscriptionResponse,
    VoiceUploadAndTranscribeResponse,
)
from src.modules.copilot.domain.message_blocks import AudioBlock
from src.modules.copilot.infrastructure.voice.whisper_transcriber import (
    WhisperTranscriber,
)
from src.modules.iam.api.dependencies import get_current_user, get_tenant_context

logger = structlog.get_logger()

router = APIRouter(tags=["Copilot - Voice"])

# Max audio file size for combined endpoint: 25 MB
_MAX_AUDIO_BYTES = 25 * 1024 * 1024


# ── Legacy endpoint (backward-compat) ─────────────────────────────────────────


@router.post("/transcribe")
async def transcribe_audio(
    file: Annotated[UploadFile, File(...)],
    tenant_id: Annotated[UUID, Depends(get_tenant_context)],
) -> TranscriptionResponse:
    """Receive an audio blob and return transcribed text via Whisper.

    Legacy endpoint kept for backward-compat. New code should use
    /upload-and-transcribe for the full AudioBlock (url + transcript).
    """
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


# ── Combined endpoint (D0.4 — atomic upload + transcribe) ─────────────────────


@router.post(
    "/upload-and-transcribe",
    summary="Subir audio y transcribir de forma atómica",
)
async def voice_upload_and_transcribe(
    file: Annotated[UploadFile, File(description="Archivo de audio (webm, mp3, wav, ogg, mp4).")],
    background_tasks: BackgroundTasks,
    current_user: Annotated[object, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> VoiceUploadAndTranscribeResponse:
    """Subir audio y transcribir en una sola llamada atómica.

    Ejecuta el upload a storage y la transcripción STT en paralelo para minimizar
    la latencia. Retorna un AudioBlock completo con url (reproducción) + transcript
    (accesibilidad).

    Si el STT falla, ``block.transcript`` será una cadena vacía (no null).
    Si el upload falla, retorna 502 y ningún estado parcial es persistido.

    Raises:
        413: Archivo excede 25 MB.
        502: Error de storage al subir el archivo.
    """
    tenant_id: UUID = current_user.tenant_id  # type: ignore[attr-defined]

    audio_bytes = await file.read()
    size_bytes = len(audio_bytes)

    if size_bytes > _MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"El audio excede el tamaño máximo de {_MAX_AUDIO_BYTES // (1024 * 1024)} MB.",
        )

    mime = file.content_type or "audio/webm"
    filename = file.filename or f"voice-{uuid.uuid4()}.webm"

    logger.info(
        "voice_upload_and_transcribe_start",
        tenant_id=str(tenant_id),
        mime=mime,
        size_bytes=size_bytes,
        filename=filename,
    )

    # Run STT and storage concurrently (§9.2 — one call, two parallel ops)
    transcriber = WhisperTranscriber()
    assets_service = AssetsService(db)

    # We need bytes for STT and a file-like object for storage
    transcribe_task = asyncio.create_task(transcriber.transcribe(audio_bytes, mime))

    # Upload to storage
    try:
        file_obj = io.BytesIO(audio_bytes)
        asset = assets_service.upload_asset(
            tenant_id=tenant_id,
            file_obj=file_obj,
            filename=filename,
            mime_type=mime,
            background_tasks=background_tasks,
        )
    except Exception as upload_err:
        logger.exception(
            "voice_upload_storage_error",
            tenant_id=str(tenant_id),
        )
        raise HTTPException(
            status_code=502,
            detail="Error al almacenar el audio. Intenta de nuevo.",
        ) from upload_err

    # Await transcription — on failure, use empty transcript (§9.6)
    transcript = ""
    transcript_language: str | None = None
    duration_ms: int | None = None

    try:
        transcription = await transcribe_task
        transcript = transcription.text
        transcript_language = transcription.language or None
        if transcription.duration_seconds:
            duration_ms = int(transcription.duration_seconds * 1000)
    except Exception:
        logger.exception(
            "voice_transcription_error",
            tenant_id=str(tenant_id),
            filename=filename,
        )
        # transcript remains "" — AudioBlock invariant: transcript never null

    block = AudioBlock(
        id=uuid.uuid4(),
        asset_id=asset.id,
        url=asset.public_url,  # type: ignore[arg-type]
        mime=mime,
        duration_ms=duration_ms,
        transcript=transcript,
        transcript_language=transcript_language,
    )

    logger.info(
        "voice_upload_and_transcribe_done",
        tenant_id=str(tenant_id),
        asset_id=str(asset.id),
        transcript_length=len(transcript),
        duration_ms=duration_ms,
    )

    return VoiceUploadAndTranscribeResponse(block=block)
