"""ARQ task for async brand extraction with Redis progress tracking.

Phase 1 BE (FLOW-SPEC §3.3): on_progress payload enriched with:
  filled_fields, filled_fields_by_section, sections_touched,
  sections_completed, newly_completed_section, finished_at.

Phase 2 BE (FLOW-SPEC §3.4): on terminal 'completed', publishes
ExtractionSectionCompletedEvent and ExtractionJobCompletedEvent via the
shared EventBus. The copilot module's subscriber (registered at startup)
handles card insertion — no direct brand → copilot import.
"""

import json
import logging
import traceback
from datetime import UTC, datetime
from uuid import UUID

from src.modules.brand.application.extraction_routes import (
    NAV_ROUTE_TEMPLATE,
)
from src.modules.brand.application.extraction_routes import (
    primary_cta_route as build_brand_primary_cta_route,
)

logger = logging.getLogger(__name__)


def _fail_progress(redis: object, progress_key: str, error_msg: str, log_detail: str) -> None:
    """Write a user-friendly failure to Redis and log the full detail for debugging."""
    logger.error("Brand extraction task error: %s", log_detail)
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
                },
            ),
        )


async def run_brand_extraction(
    ctx: dict,
    job_id: str,
    tenant_id: str,
    url: str | None,
    text: str | None,
    mode: str,
    update_instructions: str | None,
    include_visuals: bool = False,
    include_assets: bool = False,
    dry_run: bool = False,
    conversation_id: str | None = None,
    user_id: str | None = None,
    **_extra_kwargs: object,
) -> dict[str, str]:
    """Execute brand extraction as a background job.

    Writes enriched progress to Redis at each extraction wave so the frontend
    can poll for real-time updates (FLOW-SPEC §3.3).

    On completion, inserts an extraction_summary card + per-section navigation
    pills into the conversation if conversation_id is provided (FLOW-SPEC §3.4).

    The **_extra_kwargs catch-all prevents TypeError crashes when the API
    sends new parameters that this worker version doesn't know about yet
    (e.g. after a deploy where the API reloaded but the worker didn't).
    """
    redis = ctx.get("redis_cache")
    progress_key = f"brand_extract:{tenant_id}:{job_id}"

    if _extra_kwargs:
        logger.warning(
            "Brand extraction received unexpected kwargs (API/worker version mismatch?): %s",
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
            "Error interno al conectar con la base de datos. Intenta de nuevo.",
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
        """Write enriched progress payload to Redis.

        Args:
            progress_pct: 0-100 completion percentage.
            stage: Human-readable stage description.
            new_fields: Field paths populated in this wave (cumulative-adds).
            section_completed: If a section just finished, its slug.
        """
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
                module="brand",
                section_slug=newly_completed,
                fields_count=len(_filled_by_section.get(newly_completed, [])),
            )

    # Create trace collector for this job
    trace = None
    try:
        from src.modules.brand.application.extraction_trace import (
            ExtractionTraceCollector,
        )

        trace = ExtractionTraceCollector(
            db=db,
            tenant_id=UUID(tenant_id),
            job_id=job_id,
            mode=mode,
            profile_name="safe",  # will be overridden by service profile
            url=url,
            include_visuals=include_visuals,
            include_assets=include_assets,
        )
    except Exception as exc:  # noqa: BLE001 — worker task error boundary
        logger.warning("Could not create trace collector: %s", exc)

    try:
        from src.modules.brand.application.extraction_service import (
            BrandExtractionService,
        )
        from src.modules.brand.infrastructure.repositories.brand_repository import (
            BrandRepository,
        )
        from src.shared.application.field_diff import (
            diff_filled_by_section,
        )

        on_progress(5, "Iniciando análisis...")

        service = BrandExtractionService(db, UUID(tenant_id))

        # Update trace with actual profile name from service
        if trace:
            trace._profile_name = service.profile.name

        # Snapshot pre-extraction state so we can diff what the worker actually
        # wrote. The extraction service only reports progress_pct + stage, not
        # per-field progress; the diff is how we reconstruct a meaningful
        # summary without coupling to the service's internal waves.
        brand_repo = BrandRepository(db)
        before_dump = brand_repo.get_settings(UUID(tenant_id)).model_dump(mode="json")

        await service.extract_all(
            url=url,
            text=text,
            mode=mode,
            update_instructions=update_instructions,
            dry_run=dry_run,
            include_visuals=include_visuals,
            include_assets=include_assets,
            progress_callback=on_progress,
            trace=trace,
            user_id=UUID(user_id) if user_id else None,
        )

        finished_at = datetime.now(UTC).isoformat()

        # Re-read settings and compute what changed. Tolerate failures —
        # summary card can still emit with empty deltas.
        try:
            after_dump = brand_repo.get_settings(UUID(tenant_id)).model_dump(mode="json")
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
                "Brand extraction post-diff failed (summary will be empty)",
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
                        "stage": "¡Análisis completado!",
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
        # (no direct brand → copilot import — EventBus decouples the modules)
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
            "Brand extraction completed for tenant=%s job=%s",
            tenant_id,
            job_id,
        )

    except Exception as exc:  # noqa: BLE001 — worker task error boundary
        # Save trace even on failure
        if trace:
            try:
                trace.finish(status="failed", error_message=str(exc))
            except Exception:  # noqa: BLE001 — worker task error boundary
                logger.warning("Could not save failure trace", exc_info=True)

        _fail_progress(
            redis,
            progress_key,
            "Ocurrió un error durante el análisis. Intenta de nuevo.",
            f"Brand extraction failed for tenant={tenant_id} job={job_id}: {exc}\n{traceback.format_exc()}",
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
    module: str,
    section_slug: str,
    fields_count: int,
) -> None:
    """Publish an ExtractionSectionCompletedEvent per-wave.

    Called from the ``on_progress`` callback the moment a section transitions
    to completed (subscriber then inserts the nav pill into the conversation).
    Swallows exceptions so an event-bus hiccup never aborts the extraction.
    Carries entity_id=None and NAV_ROUTE_TEMPLATE so the copilot subscriber
    can build the brand-studio URL without module-specific logic.
    """
    try:
        from src.shared.domain.events import ExtractionSectionCompletedEvent
        from src.shared.domain_events.outbox.application.event_bus_adapter import (
            adapter_bus as EventBus,  # noqa: N812
        )

        EventBus.publish(
            ExtractionSectionCompletedEvent.create(
                tenant_id=UUID(tenant_id),
                job_id=job_id,
                conversation_id=conversation_id,
                module=module,
                section_slug=section_slug,
                section_label=_section_label(section_slug, module),
                fields_count=fields_count,
                entity_id=None,
                nav_route_template=NAV_ROUTE_TEMPLATE,
            ),
            session=None,
        )
    except Exception:  # noqa: BLE001 — card emission must not fail the job
        logger.warning(
            "Brand extraction per-wave section event failed",
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
    wave completes. This function now only publishes the final summary card.
    A safety net re-publishes any section the diff picked up that the progress
    callback missed — subscriber is idempotent so duplicates are no-ops.
    """
    if not conversation_id:
        return
    try:
        from src.shared.domain.events import ExtractionJobCompletedEvent
        from src.shared.domain_events.outbox.application.event_bus_adapter import (
            adapter_bus as EventBus,  # noqa: N812
        )

        source_ref = url or "documento"
        started_dt = datetime.fromisoformat(started_at)
        finished_dt = datetime.fromisoformat(finished_at)
        duration_s = int((finished_dt - started_dt).total_seconds())

        # Safety net: post-diff may surface sections the progress callback never
        # announced (e.g. the service didn't invoke ``_announce_sections`` for
        # that slug). Subscriber's Redis idempotency key makes the re-emit a
        # no-op for sections already pilled per-wave.
        for section_slug in sections_completed:
            section_fields = filled_by_section.get(section_slug, [])
            _publish_section_completed_event(
                tenant_id=tenant_id,
                job_id=job_id,
                conversation_id=conversation_id,
                module="brand",
                section_slug=section_slug,
                fields_count=len(section_fields),
            )

        cta = build_brand_primary_cta_route(sections_completed)

        EventBus.publish(
            ExtractionJobCompletedEvent.create(
                tenant_id=UUID(tenant_id),
                job_id=job_id,
                conversation_id=conversation_id,
                module="brand",
                source_ref=source_ref,
                duration_seconds=duration_s,
                filled_fields=list(filled_fields),
                filled_fields_by_section=dict(filled_by_section),
                sections_completed=list(sections_completed),
                primary_cta_route=cta,
                entity_id=None,
                nav_route_template=NAV_ROUTE_TEMPLATE,
            ),
            session=None,
        )
    except Exception:  # noqa: BLE001 — card emission must not fail the job
        logger.warning(
            "Brand extraction event publication failed",
            exc_info=True,
            job_id=job_id,
            conversation_id=conversation_id,
        )


_BRAND_SECTION_LABELS: dict[str, str] = {
    "identity": "Identidad",
    "strategy": "Estrategia",
    "positioning": "Posicionamiento",
    "narrative": "Narrativa",
    "audience": "Audiencia",
    "visuals": "Visuales",
    "communication-assets": "Activos de Comunicación",
    "communication_assets": "Activos de Comunicación",
    "authority": "Autoridad",
    "story": "Historia",
    "people-contact": "Equipo y Contacto",
    "people_contact": "Equipo y Contacto",
    "__root__": "Brand Studio",
}

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


def _section_label(slug: str, module: str) -> str:
    """Convert a section slug to a human-readable label (Spanish LatAm neutro)."""
    labels = _BRAND_SECTION_LABELS if module == "brand" else _OFFER_SECTION_LABELS
    return labels.get(slug, slug.replace("-", " ").replace("_", " ").title())
