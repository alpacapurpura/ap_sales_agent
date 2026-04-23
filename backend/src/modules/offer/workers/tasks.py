"""ARQ task for async offer extraction with Redis progress tracking.

Phase 1 BE (FLOW-SPEC §3.3): on_progress payload enriched with:
  filled_fields, filled_fields_by_section, sections_touched,
  sections_completed, newly_completed_section, finished_at.

Phase 2 BE (FLOW-SPEC §3.4): on terminal 'completed', publishes
ExtractionSectionCompletedEvent and ExtractionJobCompletedEvent via the
shared EventBus. The copilot module's subscriber (registered at startup)
handles card insertion — no direct offer → copilot import.
"""

import json
import logging
import traceback
from datetime import UTC, datetime
from uuid import UUID

logger = logging.getLogger(__name__)


def _fail_progress(redis: object, progress_key: str, error_msg: str, log_detail: str) -> None:
    logger.error("Offer extraction task error: %s", log_detail)
    if redis:
        redis.setex(
            progress_key,
            3600,
            json.dumps(
                {
                    "status": "failed",
                    "progress": 0,
                    "error": error_msg,
                    "filled_fields": [],
                    "filled_fields_by_section": {},
                    "sections_touched": [],
                    "sections_completed": [],
                    "newly_completed_section": None,
                    "finished_at": datetime.now(UTC).isoformat(),
                }
            ),
        )


async def run_offer_extraction(
    ctx: dict,
    job_id: str,
    tenant_id: str,
    offer_id: str,
    url: str | None,
    text: str | None,
    mode: str,
    update_instructions: str | None = None,
    conversation_id: str | None = None,
    **_extra_kwargs: object,
) -> dict:
    """Run offer extraction.

    Enriched Redis progress payload (FLOW-SPEC §3.3) included.
    Card emission on completion if conversation_id is provided (FLOW-SPEC §3.4).
    """
    redis = ctx.get("redis_cache")
    progress_key = f"offer_extract:{tenant_id}:{job_id}"

    if _extra_kwargs:
        logger.warning(
            "Offer extraction received unexpected kwargs: %s",
            list(_extra_kwargs.keys()),
        )

    db = None
    try:
        db_factory = ctx["db_factory"]
        db = db_factory()
    except Exception as exc:  # noqa: BLE001 — worker task error boundary
        _fail_progress(
            redis,
            progress_key,
            "Error interno al conectar con la base de datos.",
            f"DB factory failed for tenant={tenant_id} job={job_id}: {exc}\n{traceback.format_exc()}",
        )
        return {"status": "failed", "tenant_id": tenant_id, "error": str(exc)}

    started_at = datetime.now(UTC).isoformat()

    # Accumulated field tracking for the enriched Redis payload
    _filled_fields: list[str] = []
    _filled_by_section: dict[str, list[str]] = {}
    _sections_touched: list[str] = []
    _sections_completed: list[str] = []

    def on_progress(
        progress_pct: int,
        stage: str,
        *,
        new_fields: list[str] | None = None,
        section_completed: str | None = None,
    ) -> None:
        """Write enriched progress payload to Redis."""
        if new_fields:
            for fp in new_fields:
                if fp not in _filled_fields:
                    _filled_fields.append(fp)
                parts = fp.split(".", 1)
                sec = parts[0] if len(parts) > 1 else "__root__"
                if sec not in _sections_touched:
                    _sections_touched.append(sec)
                _filled_by_section.setdefault(sec, [])
                if fp not in _filled_by_section[sec]:
                    _filled_by_section[sec].append(fp)

        newly_completed: str | None = None
        if section_completed and section_completed not in _sections_completed:
            _sections_completed.append(section_completed)
            newly_completed = section_completed

        if redis:
            redis.setex(
                progress_key,
                3600,
                json.dumps(
                    {
                        "status": "processing",
                        "progress": progress_pct,
                        "stage": stage,
                        "started_at": started_at,
                        "finished_at": None,
                        "filled_fields": list(_filled_fields),
                        "filled_fields_by_section": dict(_filled_by_section),
                        "sections_touched": list(_sections_touched),
                        "sections_completed": list(_sections_completed),
                        "newly_completed_section": newly_completed,
                    },
                ),
            )

        # Per-wave pill: publish the section event immediately so the copilot
        # subscriber inserts the nav pill into the conversation without waiting
        # for the job to finish. Subscriber is idempotent (Redis guard per
        # job+section) so a later terminal re-publish is a safe no-op.
        if newly_completed and conversation_id:
            _publish_section_completed_event(
                tenant_id=tenant_id,
                job_id=job_id,
                conversation_id=conversation_id,
                section_slug=newly_completed,
                fields_count=len(_filled_by_section.get(newly_completed, [])),
            )

    try:
        from src.modules.offer.application.offer_extraction_service import (
            OfferExtractionService,
        )
        from src.modules.offer.infrastructure.repositories.offer_repository import (
            OfferRepository,
        )
        from src.shared.application.field_diff import diff_filled_by_section

        on_progress(5, "Iniciando análisis de oferta...")

        service = OfferExtractionService(db, UUID(tenant_id), UUID(offer_id))

        # Snapshot pre-extraction state to diff what the worker actually wrote
        # — the offer service doesn't emit per-field progress, so the delta is
        # how we reconstruct the summary without coupling to its internal waves.
        offer_repo = OfferRepository(db)
        before_offer = offer_repo.get_by_id(UUID(tenant_id), UUID(offer_id))
        before_dump = before_offer.model_dump(mode="json") if before_offer is not None else {}

        await service.extract_all(
            url=url,
            text=text,
            mode=mode,
            update_instructions=update_instructions,
            progress_callback=on_progress,
        )

        finished_at = datetime.now(UTC).isoformat()

        # Re-read offer and compute what changed — best-effort, tolerate errors.
        try:
            after_offer = offer_repo.get_by_id(UUID(tenant_id), UUID(offer_id))
            after_dump = after_offer.model_dump(mode="json") if after_offer is not None else {}
            new_by_section = diff_filled_by_section(before_dump, after_dump)
            for slug, paths in new_by_section.items():
                if slug not in _sections_touched:
                    _sections_touched.append(slug)
                if slug not in _sections_completed:
                    _sections_completed.append(slug)
                _filled_by_section.setdefault(slug, []).extend(paths)
                for path in paths:
                    if path not in _filled_fields:
                        _filled_fields.append(path)
        except Exception:  # noqa: BLE001 — observability is best-effort
            logger.warning(
                "Offer extraction post-diff failed (summary will be empty)",
                exc_info=True,
                job_id=job_id,
            )

        if redis:
            redis.setex(
                progress_key,
                3600,
                json.dumps(
                    {
                        "status": "completed",
                        "progress": 100,
                        "stage": "¡Análisis de oferta completado!",
                        "started_at": started_at,
                        "finished_at": finished_at,
                        "filled_fields": list(_filled_fields),
                        "filled_fields_by_section": dict(_filled_by_section),
                        "sections_touched": list(_sections_touched),
                        "sections_completed": list(_sections_completed),
                        "newly_completed_section": None,
                    },
                ),
            )

        # Phase 2: publish domain events so copilot subscriber emits cards
        # (no direct offer → copilot import — EventBus decouples the modules)
        _publish_completion_events(
            tenant_id=tenant_id,
            job_id=job_id,
            conversation_id=conversation_id,
            url=url,
            started_at=started_at,
            finished_at=finished_at,
            filled_fields=_filled_fields,
            filled_by_section=_filled_by_section,
            sections_completed=_sections_completed,
        )

        logger.info(
            "Offer extraction completed for tenant=%s job=%s",
            tenant_id,
            job_id,
        )

    except Exception as exc:  # noqa: BLE001 — worker task error boundary
        _fail_progress(
            redis,
            progress_key,
            "Ocurrió un error durante el análisis. Intenta de nuevo.",
            f"Offer extraction failed for tenant={tenant_id} job={job_id}: {exc}\n{traceback.format_exc()}",
        )
        return {"status": "failed", "tenant_id": tenant_id, "error": str(exc)}

    else:
        return {"status": "success", "tenant_id": tenant_id, "job_id": job_id}
    finally:
        if db:
            db.close()


def _publish_section_completed_event(
    *,
    tenant_id: str,
    job_id: str,
    conversation_id: str,
    section_slug: str,
    fields_count: int,
) -> None:
    """Publish an ExtractionSectionCompletedEvent per-wave.

    Called from the ``on_progress`` callback the moment a section transitions
    to completed. Subscriber idempotency guards against duplicate emits.
    """
    try:
        from src.shared.domain.events import (
            EventBus,
            ExtractionSectionCompletedEvent,
        )

        EventBus.publish(
            ExtractionSectionCompletedEvent.create(
                tenant_id=UUID(tenant_id),
                job_id=job_id,
                conversation_id=conversation_id,
                module="offer",
                section_slug=section_slug,
                section_label=_section_label(section_slug),
                fields_count=fields_count,
            ),
            session=None,
        )
    except Exception:  # noqa: BLE001 — card emission must not fail the job
        logger.warning(
            "Offer extraction per-wave section event failed",
            exc_info=True,
            job_id=job_id,
            section_slug=section_slug,
            conversation_id=conversation_id,
        )


def _publish_completion_events(
    *,
    tenant_id: str,
    job_id: str,
    conversation_id: str | None,
    url: str | None,
    started_at: str,
    finished_at: str,
    filled_fields: list[str],
    filled_by_section: dict[str, list[str]],
    sections_completed: list[str],
) -> None:
    """Publish the terminal job event (summary card).

    Per-wave section events are already published by ``on_progress`` as each
    wave completes. This function emits only the final summary card, plus a
    safety-net re-emission of section events for slugs the progress callback
    missed (post-diff picks them up). Subscriber idempotency makes re-emits
    no-ops for sections already pilled per-wave.
    """
    if not conversation_id:
        return
    try:
        from src.shared.domain.events import (
            EventBus,
            ExtractionJobCompletedEvent,
        )

        source_ref = url or "documento"
        started_dt = datetime.fromisoformat(started_at)
        finished_dt = datetime.fromisoformat(finished_at)
        duration_s = int((finished_dt - started_dt).total_seconds())

        for section_slug in sections_completed:
            section_fields = filled_by_section.get(section_slug, [])
            _publish_section_completed_event(
                tenant_id=tenant_id,
                job_id=job_id,
                conversation_id=conversation_id,
                section_slug=section_slug,
                fields_count=len(section_fields),
            )

        EventBus.publish(
            ExtractionJobCompletedEvent.create(
                tenant_id=UUID(tenant_id),
                job_id=job_id,
                conversation_id=conversation_id,
                module="offer",
                source_ref=source_ref,
                duration_seconds=duration_s,
                filled_fields=list(filled_fields),
                filled_fields_by_section=dict(filled_by_section),
                sections_completed=list(sections_completed),
            ),
            session=None,
        )
    except Exception:  # noqa: BLE001 — card emission must not fail the job
        logger.warning(
            "Offer extraction event publication failed",
            exc_info=True,
            job_id=job_id,
            conversation_id=conversation_id,
        )


_OFFER_SECTION_LABELS: dict[str, str] = {
    "promise": "Promesa",
    "details": "Detalles",
    "strategy": "Estrategia",
    "psychology": "Psicología",
    "value-stack": "Stack de Valor",
    "value_stack": "Stack de Valor",
    "closing": "Cierre",
    "__root__": "Offer Studio",
}


def _section_label(slug: str) -> str:
    """Convert an offer section slug to a human-readable label (Spanish LatAm neutro)."""
    return _OFFER_SECTION_LABELS.get(
        slug,
        slug.replace("-", " ").replace("_", " ").title(),
    )
