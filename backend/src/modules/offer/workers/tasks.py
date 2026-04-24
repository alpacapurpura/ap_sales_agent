"""ARQ task for async offer extraction with Redis progress tracking.

Phase 1 BE (FLOW-SPEC §3.3): on_progress payload enriched with:
  filled_fields, filled_fields_by_section, sections_touched,
  sections_completed, newly_completed_section, finished_at.

Phase 2 BE (FLOW-SPEC §3.4): on terminal 'completed', publishes
ExtractionSectionCompletedEvent and ExtractionJobCompletedEvent via the
shared EventBus. The copilot module's subscriber (registered at startup)
handles card insertion — no direct offer → copilot import.

Bug fixes (2026-04-24):
- Bug 1: sections were grouped by flat top-level Offer field keys (wrong).
  Now uses fields_to_fe_sections() from extraction_section_map.py to map
  fields to the correct FE section slugs (21 slugs, polymorphic-aware).
- Bug 2: nav pills and summary CTA hard-coded to brand-studio routes.
  Now uses NAV_ROUTE_TEMPLATE + primary_cta_route() from extraction_routes,
  carried through the event payload so the subscriber stays module-agnostic.
"""

import json
import logging
import traceback
from datetime import UTC, datetime
from uuid import UUID

from src.modules.offer.application.extraction_routes import (
    NAV_ROUTE_TEMPLATE,
)
from src.modules.offer.application.extraction_routes import (
    primary_cta_route as build_primary_cta_route,
)
from src.modules.offer.domain.extraction_section_map import (
    BACKEND_WAVE_TO_FE_SLUGS,
    fields_to_fe_sections,
    resolve_details_section,
)

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
    user_id: str | None = None,
    **_extra_kwargs: object,
) -> dict:
    """Run offer extraction.

    Enriched Redis progress payload (FLOW-SPEC §3.3) included.
    Card emission on completion if conversation_id is provided (FLOW-SPEC §3.4).
    user_id is forwarded to the service for future social-proof sync and tracing.
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

    # Accumulated field tracking for the enriched Redis payload.
    # _filled_by_section uses FE section slugs (not backend wave slugs).
    _filled_fields: list[str] = []
    _filled_by_section: dict[str, list[str]] = {}
    _sections_touched: list[str] = []
    _sections_completed: list[str] = []

    # Offer archetype: loaded once after the offer is read, used throughout
    # on_progress to route specific_details.* paths to the correct FE slug.
    # Uses a 1-element list so closures can mutate it without nonlocal.
    _offer_archetype_holder: list = [None]  # holder[0] = OfferArchetype | None

    def _get_fe_slugs_for_backend_wave(backend_slug: str | None) -> list[str]:
        """Return FE slugs to mark completed when a backend wave finishes."""
        if backend_slug is None:
            return []
        if backend_slug == "details":
            slug = resolve_details_section(_offer_archetype_holder[0])
            return [slug] if slug else []
        return list(BACKEND_WAVE_TO_FE_SLUGS.get(backend_slug, ()))

    def on_progress(
        progress_pct: int,
        stage: str,
        *,
        new_fields: list[str] | None = None,
        section_completed: str | None = None,
    ) -> None:
        """Write enriched progress payload to Redis.

        Groups new_fields by FE section slug (not flat field key) using
        fields_to_fe_sections() so the FE completion badges align with the
        actual section editors. The section_completed signal from the
        extraction service carries a backend wave slug (promise/strategy/…);
        we map it to one or more FE slugs via BACKEND_WAVE_TO_FE_SLUGS.
        """
        if new_fields:
            # Strip any backend wave prefix (e.g. "promise.headline_promise" →
            # "headline_promise") if the service emits prefixed paths.
            bare_paths = []
            for fp in new_fields:
                if fp not in _filled_fields:
                    _filled_fields.append(fp)
                # Paths may arrive as "wave_slug.field_name" from _announce_sections.
                # We only care about the top-level Offer field name for grouping.
                bare = fp.split(".", 1)[-1] if "." in fp else fp
                bare_paths.append(bare)

            # Group the bare field paths by FE slug
            new_by_slug = fields_to_fe_sections(
                archetype=_offer_archetype_holder[0],
                filled_paths=bare_paths,
            )
            for slug, paths in new_by_slug.items():
                if slug not in _sections_touched:
                    _sections_touched.append(slug)
                _filled_by_section.setdefault(slug, [])
                for p in paths:
                    if p not in _filled_by_section[slug]:
                        _filled_by_section[slug].append(p)

        # Map the backend wave slug to FE slugs and announce each as completed.
        # A backend wave (e.g. "promise") may populate multiple FE sections
        # (e.g. "identity" + "promise"). We publish a pill for each.
        newly_completed_fe_slugs: list[str] = []
        if section_completed:
            for fe_slug in _get_fe_slugs_for_backend_wave(section_completed):
                if fe_slug not in _sections_completed:
                    _sections_completed.append(fe_slug)
                    newly_completed_fe_slugs.append(fe_slug)

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
                        "newly_completed_section": newly_completed_fe_slugs[0] if newly_completed_fe_slugs else None,
                    },
                ),
            )

        # Per-wave pill: publish one event per FE slug so the copilot
        # subscriber inserts the nav pills into the conversation without waiting
        # for the job to finish. Subscriber is idempotent (Redis guard per
        # job+section) so a later terminal re-publish is a safe no-op.
        if conversation_id:
            for fe_slug in newly_completed_fe_slugs:
                _publish_section_completed_event(
                    tenant_id=tenant_id,
                    job_id=job_id,
                    offer_id=offer_id,
                    conversation_id=conversation_id,
                    section_slug=fe_slug,
                    fields_count=len(_filled_by_section.get(fe_slug, [])),
                )

    try:
        from src.modules.offer.application.offer_extraction_service import (
            OfferExtractionService,
        )
        from src.modules.offer.application.offer_extraction_trace import (
            OfferExtractionTraceCollector,
        )
        from src.modules.offer.infrastructure.repositories.offer_repository import (
            OfferRepository,
        )

        on_progress(5, "Iniciando análisis de oferta...")

        tenant_uuid = UUID(tenant_id)
        offer_uuid = UUID(offer_id)
        user_uuid = UUID(user_id) if user_id else None

        trace = OfferExtractionTraceCollector(
            db,
            tenant_uuid,
            job_id,
            mode=mode,
            url=url,
        )

        service = OfferExtractionService(db, tenant_uuid, offer_uuid)

        # Snapshot pre-extraction state to diff what the worker actually wrote
        # — the offer service doesn't emit per-field progress, so the delta is
        # how we reconstruct the summary without coupling to its internal waves.
        offer_repo = OfferRepository(db)
        before_offer = offer_repo.get_by_id(tenant_uuid, offer_uuid)
        before_dump = before_offer.model_dump(mode="json") if before_offer is not None else {}

        # Capture archetype so on_progress can route specific_details.* paths
        # to the correct FE slug (program_details / service_details / etc.).
        # Mutates _offer_archetype_holder[0] so the closures pick it up.
        if before_offer is not None:
            _offer_archetype_holder[0] = before_offer.archetype

        await service.extract_all(
            url=url,
            text=text,
            mode=mode,
            update_instructions=update_instructions,
            progress_callback=on_progress,
            user_id=user_uuid,
            trace=trace,
        )

        finished_at = datetime.now(UTC).isoformat()

        # Re-read offer and compute what changed — best-effort, tolerate errors.
        # Uses fields_to_fe_sections() to group delta paths by FE slug instead
        # of the raw top-level key grouping that caused Bug 1 (flat field names
        # appearing as section names in the completion badges).
        try:
            after_offer = offer_repo.get_by_id(UUID(tenant_id), UUID(offer_id))
            after_dump = after_offer.model_dump(mode="json") if after_offer is not None else {}

            # Compute which top-level fields actually changed value.
            delta_paths: list[str] = []
            for key, after_val in after_dump.items():
                before_val = before_dump.get(key)
                if after_val != before_val and after_val not in (None, [], {}, ""):
                    delta_paths.append(key)

            # Group delta fields by FE section slug.
            new_by_slug = fields_to_fe_sections(
                archetype=_offer_archetype_holder[0],
                filled_paths=delta_paths,
            )
            for fe_slug, paths in new_by_slug.items():
                if fe_slug not in _sections_touched:
                    _sections_touched.append(fe_slug)
                if fe_slug not in _sections_completed:
                    _sections_completed.append(fe_slug)
                _filled_by_section.setdefault(fe_slug, [])
                for path in paths:
                    if path not in _filled_by_section[fe_slug]:
                        _filled_by_section[fe_slug].append(path)
                for path in delta_paths:
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
            offer_id=offer_id,
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
    offer_id: str,
    conversation_id: str,
    section_slug: str,
    fields_count: int,
) -> None:
    """Publish an ExtractionSectionCompletedEvent per-wave.

    Called from the ``on_progress`` callback the moment a FE section slug
    transitions to completed. Subscriber idempotency guards against duplicate
    emits. Carries entity_id (offer_id) and NAV_ROUTE_TEMPLATE so the
    subscriber can build the correct offer-editor URL without hardcoding routes.
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
                entity_id=offer_id,
                nav_route_template=NAV_ROUTE_TEMPLATE,
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
    offer_id: str,
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

    Carries entity_id (offer_id) and NAV_ROUTE_TEMPLATE + primary_cta_route
    so the subscriber renders correct offer-editor URLs (Bug 2 fix).
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

        cta = build_primary_cta_route(offer_id, sections_completed)

        # Safety-net re-emit for sections surfaced by the post-diff that the
        # per-wave on_progress callback may have missed. Subscriber Redis guard
        # makes duplicates no-ops.
        for section_slug in sections_completed:
            section_fields = filled_by_section.get(section_slug, [])
            _publish_section_completed_event(
                tenant_id=tenant_id,
                job_id=job_id,
                offer_id=offer_id,
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
                primary_cta_route=cta,
                entity_id=offer_id,
                nav_route_template=NAV_ROUTE_TEMPLATE,
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
    # FE section slugs (21 from section-catalog.ts)
    "identity": "Identidad",
    "promise": "Promesa",
    "strategy": "Para quién es",
    "psychology": "Psicología de compra",
    "program_details": "Detalles del programa",
    "service_details": "Detalles del servicio",
    "event_details": "Detalles del evento",
    "product_details": "Detalles del producto",
    "subscription_details": "Detalles de la suscripción",
    "platform_details": "Plataforma",
    "location": "Ubicación",
    "instructors": "Instructores",
    "value_stack": "Value stack",
    "pricing": "Pricing",
    "testimonials": "Testimonios",
    "portfolio": "Portfolio",
    "faq": "FAQ",
    "gallery": "Galería",
    "resources": "Recursos",
    "closing": "Cierre",
    "knowledge": "Conocimiento",
    # Legacy backend wave slugs (kept for backward-compat)
    "details": "Detalles",
    "value-stack": "Stack de Valor",
    "__root__": "Offer Studio",
}


def _section_label(slug: str) -> str:
    """Convert an offer section slug to a human-readable label (Spanish LatAm neutro)."""
    return _OFFER_SECTION_LABELS.get(
        slug,
        slug.replace("-", " ").replace("_", " ").title(),
    )
