"""Voice API — combined upload+transcribe endpoint with rate limiting.

# [COPILOT-VOICE-DUAL-MODE] → docs/domains/copilot/CONTRACT-MULTIMODAL.md §9

Endpoints:
- POST /transcribe — GONE (410). Legacy endpoint deprecated in PI-2 S1 PR-1 (BE side).
  Returns 410 with X-Deprecation-Notice header. FE migration to /upload-and-transcribe
  tracked as follow-up PR (cross-stack, separate scope).
- POST /upload-and-transcribe — canonical combined endpoint (D0.4).
  Atomically stores the audio AND transcribes it. Returns a complete AudioBlock.
  Rate-limited per tenant (copilot-voice scope, PI-2 S1 PR-1).

PI-2 S1 PR-1: rate limit + dynamic media cap applied to /upload-and-transcribe.
"""

from __future__ import annotations

import asyncio
import io
import uuid
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.rate_limit import check_rate_limit
from src.modules.assets.application.assets_service import AssetsService
from src.modules.copilot.api.voice_dto import VoiceUploadAndTranscribeResponse
from src.modules.copilot.application.services.limits_resolver import (
    CopilotLimitsResolver,
    EffectiveLimits,
)
from src.modules.copilot.domain.message_blocks import AudioBlock
from src.modules.copilot.infrastructure.repositories.tenant_limits_repository import (
    SyncCopilotTenantLimitsRepository,
)
from src.modules.copilot.infrastructure.voice.whisper_transcriber import (
    WhisperTranscriber,
)
from src.modules.iam.api.dependencies import get_current_user, get_tenant_context

logger = structlog.get_logger()

router = APIRouter(tags=["Copilot - Voice"])

# Fallback constant (used when DB is unavailable and no env override)
_DEFAULT_MAX_AUDIO_BYTES = 25 * 1024 * 1024


# ── Dependency: resolve effective limits ───────────────────────────────────────


async def _get_voice_limits(
    current_user: Annotated[object, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> EffectiveLimits:
    """DI: resolve effective voice+media limits for tenant (override > env default).

    Uses sync repo + asyncio.to_thread to avoid blocking the event loop.
    Graceful degradation: DB error → env defaults (CopilotLimitsResolver catches).
    """
    tenant_id: UUID = current_user.tenant_id  # type: ignore[attr-defined]
    repo = SyncCopilotTenantLimitsRepository(db)
    resolver = CopilotLimitsResolver(repo)
    return await asyncio.to_thread(resolver.get_effective_sync, tenant_id)


# ── Legacy endpoint (410 Gone — deprecated in PI-2 S1 PR-1 BE side) ─────────

_DEPRECATION_NOTICE = "Migrar a /voice/upload-and-transcribe - endpoint legacy sera eliminado en S2"


@router.post("/transcribe")
async def transcribe_audio(
    file: Annotated[UploadFile, File(...)],
    tenant_id: Annotated[UUID, Depends(get_tenant_context)],
) -> Response:
    """Legacy STT-only endpoint — GONE (410).

    Deprecated in PI-2 S1 PR-1 (BE side). FE migration to /upload-and-transcribe
    tracked as follow-up PR (cross-stack, separate scope).
    Returns 410 Gone with X-Deprecation-Notice header.
    """
    logger.warning(
        "voice_transcribe_legacy_called",
        tenant_id=str(tenant_id),
        deprecation_notice=_DEPRECATION_NOTICE,
    )
    return Response(
        status_code=410,
        headers={"X-Deprecation-Notice": _DEPRECATION_NOTICE},
    )


# ── Combined endpoint (D0.4 — atomic upload + transcribe, rate-limited) ──────


@router.post(
    "/upload-and-transcribe",
    summary="Subir audio y transcribir de forma atómica",
)
async def voice_upload_and_transcribe(
    file: Annotated[UploadFile, File(description="Archivo de audio (webm, mp3, wav, ogg, mp4).")],
    background_tasks: BackgroundTasks,
    current_user: Annotated[object, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limits: Annotated[EffectiveLimits, Depends(_get_voice_limits)],
) -> VoiceUploadAndTranscribeResponse:
    """Subir audio y transcribir en una sola llamada atómica.

    Ejecuta el upload a storage y la transcripción STT en paralelo para minimizar
    la latencia. Retorna un AudioBlock completo con url (reproducción) + transcript
    (accesibilidad).

    Rate limit: por user_id en scope "copilot-voice". Configurable por env o per-tenant.
    Si el STT falla, ``block.transcript`` será una cadena vacía (no null).
    Si el upload falla, retorna 502 y ningún estado parcial es persistido.

    Raises:
        429: Rate limit excedido para este tenant/user.
        413: Archivo excede el tamaño máximo configurado.
        502: Error de storage al subir el archivo.
    """
    tenant_id: UUID = current_user.tenant_id  # type: ignore[attr-defined]
    user_id: str = str(current_user.id)  # type: ignore[attr-defined]

    # ── Rate limit (before reading body to minimize waste) ─────────────────
    try:
        check_rate_limit(
            user_id=user_id,
            scope="copilot-voice",
            max_requests=limits.voice_rpm,
            window_seconds=limits.voice_window_seconds,
        )
    except Exception:
        # Log rate limit hit (Q3: structlog only, no Prometheus in PR-1)
        logger.warning(
            "copilot_voice_rate_limit_hit",
            tenant_id=str(tenant_id),
            user_id=user_id,
            effective_rpm=limits.voice_rpm,
            is_override=limits.voice_rpm_is_override,
        )
        raise

    audio_bytes = await file.read()
    size_bytes = len(audio_bytes)

    max_bytes = limits.media_max_bytes
    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"El audio excede el tamaño máximo de {max_bytes // (1024 * 1024)} MB.",
        )

    mime = file.content_type or "audio/webm"
    filename = file.filename or f"voice-{uuid.uuid4()}.webm"

    logger.info(
        "voice_upload_and_transcribe_start",
        tenant_id=str(tenant_id),
        mime=mime,
        size_bytes=size_bytes,
        filename=filename,
        effective_rpm=limits.voice_rpm,
        effective_max_bytes=max_bytes,
    )

    # Run STT and storage concurrently (§9.2 — one call, two parallel ops)
    transcriber = WhisperTranscriber()
    assets_service = AssetsService(db)

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
