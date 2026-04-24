"""Offer Section Copilot Tools — per-section draft generators for the Offer Studio.

Each tool is bound to a specific ``section_slug`` and returns draft fields
that the user applies through the normal save flow.  Tools NEVER write to
offer data directly.

Tenant isolation: every port call passes the ``tenant_id`` obtained from the
request-scoped context variable (``get_tenant_id()``).  Every tool returns
an empty draft with ``confidence=0.0`` and a human-readable hint when the
required upstream data is missing.

Architecture rules:
- No cross-module imports: brand, social-proof and scheduling data are read
  through ``shared/links/ports/`` lazy-import shims.
- No SQLAlchemy or FastAPI imports in this file (application layer, not infra).
- PII: no raw email / phone fields are included in any response model.
"""

from __future__ import annotations

import structlog
from langchain_core.tools import tool

from src.core.context import get_tenant_id
from src.core.database import SessionLocal

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _brand_settings(db: object, tenant_id: object) -> object | None:
    """Return BrandSettings for *tenant_id* or None if the brand has not been set up."""
    from src.modules.brand.infrastructure.repositories.brand_repository import (
        BrandRepository,
    )

    repo = BrandRepository(db)  # type: ignore[arg-type]
    settings = repo.get_settings(tenant_id)  # type: ignore[arg-type]
    # get_settings returns a BrandSettings with all-None fields when brand
    # is missing (no row in DB).  Detect that case by checking identity.
    return settings if (settings and settings.identity is not None) else None


def _active_personality(db: object, tenant_id: object) -> object | None:
    """Return the active PersonalityProfileModel for *tenant_id* or None.

    Used to prefer personality.system_instruction over legacy voice_tone string.
    Cross-module access is via lazy import (no direct domain import at module level).
    """
    from src.modules.brand.infrastructure.repositories.personality_repository import (
        PersonalityProfileRepository,
    )

    repo = PersonalityProfileRepository(db)  # type: ignore[arg-type]
    return repo.get_active(tenant_id=tenant_id)  # type: ignore[arg-type]


def _social_proof_bundle(db: object, tenant_id: object) -> dict:
    """Return {testimonials, authority_items, team_members} for *tenant_id*."""
    from src.modules.social_proof.infrastructure.repositories.authority_item_repository import (
        AuthorityItemRepository,
    )
    from src.modules.social_proof.infrastructure.repositories.team_member_repository import (
        TeamMemberRepository,
    )
    from src.modules.social_proof.infrastructure.repositories.testimonial_repository import (
        TestimonialRepository,
    )

    return {
        "testimonials": TestimonialRepository(db).list_by_tenant(tenant_id),  # type: ignore[arg-type]
        "authority_items": AuthorityItemRepository(db).list_by_tenant(tenant_id),  # type: ignore[arg-type]
        "team_members": TeamMemberRepository(db).list_by_tenant(tenant_id),  # type: ignore[arg-type]
    }


def _avatars(db: object, tenant_id: object) -> list:
    """Return Avatar list for *tenant_id*."""
    from src.modules.brand.infrastructure.repositories.avatar_repository import (
        AvatarRepository,
    )

    return AvatarRepository(db).get_by_tenant(tenant_id)  # type: ignore[arg-type]


def _offer_preset_flags(db: object, tenant_id: object, offer_id: str | None) -> list[str]:
    """Return the preset flags (list[str]) for the current offer, or []."""
    if not offer_id:
        return []
    from src.shared.links.ports.offer import get_offer_repository, get_offer_type_preset

    repo = get_offer_repository(db)  # type: ignore[arg-type]
    # OfferRepository.get_all_by_tenant returns list of offer dicts/objects
    offers = repo.get_all_by_tenant(tenant_id)  # type: ignore[arg-type]
    target = next((o for o in offers if str(getattr(o, "id", "")) == str(offer_id)), None)
    if target is None:
        return []
    preset_id = getattr(target, "preset_id", None)
    preset = get_offer_type_preset(preset_id)
    if preset is None:
        return []
    return [f.value for f in getattr(preset, "default_flags", ())]


def _event_types(db: object, tenant_id: object) -> list:
    """Return list[EventType] for *tenant_id* via scheduling EventTypeService."""
    from src.modules.scheduling.application.services.event_type_service import (
        EventTypeService,
    )

    svc = EventTypeService(db=db, tenant_id=tenant_id)  # type: ignore[arg-type]
    return svc.list_event_types()


def _no_data_response(section_slug: str, hint: str) -> str:
    """Return a standard JSON-serialisable string for missing-data cases."""
    import json

    return json.dumps(
        {
            "section_slug": section_slug,
            "draft_fields": {},
            "suggestions": [hint],
            "confidence": 0.0,
            "citations": [],
        }
    )


def _ok_response(
    section_slug: str,
    draft_fields: dict,
    suggestions: list[str],
    confidence: float,
    citations: list[str] | None = None,
) -> str:
    """Return a standard successful response as JSON string."""
    import json

    return json.dumps(
        {
            "section_slug": section_slug,
            "draft_fields": draft_fields,
            "suggestions": suggestions,
            "confidence": confidence,
            "citations": citations or [],
        }
    )


# ---------------------------------------------------------------------------
# Tool 1 — Identity: adapt from brand identity
# ---------------------------------------------------------------------------


@tool
def adapt_from_brand_identity() -> str:
    """Adaptar la identidad de marca al campo identidad de la oferta.

    Sección: identity.
    Reads brand identity (brand_name, tagline, voice_tone) and returns
    draft fields for the offer identity section (public_name, internal_sku suggestion).

    Returns:
        JSON string with draft_fields, suggestions, confidence, citations.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return _no_data_response("identity", "No se pudo determinar el tenant.")

    db = SessionLocal()
    try:
        settings = _brand_settings(db, tenant_id)
        if not settings or not settings.identity:
            return _no_data_response(
                "identity",
                "La identidad de marca aún no está configurada. Completa el Brand Studio primero.",
            )

        identity = settings.identity
        brand_name = identity.brand_name or ""
        tagline = identity.tagline or ""
        voice_tone = identity.voice_tone or ""

        # Derive offer public_name suggestion from brand name
        public_name_suggestion = brand_name.strip() if brand_name else None

        draft_fields: dict = {}
        if public_name_suggestion:
            draft_fields["public_name"] = public_name_suggestion
        # internal_sku: sanitize brand name to snake_case prefix
        if brand_name:
            sku_prefix = brand_name.lower().replace(" ", "_")[:12]
            draft_fields["internal_sku"] = f"{sku_prefix}_001"

        suggestions = []
        if tagline:
            suggestions.append(f"Tagline de marca disponible para usar en el titulo: '{tagline}'")

        # Prefer active personality profile's system_instruction over legacy voice_tone (soft migration)
        active_personality = _active_personality(db, tenant_id)
        if active_personality and active_personality.system_instruction:
            suggestions.append(
                "Perfil de personalidad activo: úsalo como referencia del estilo comunicacional "
                "para nombrar y posicionar tu oferta."
            )
        elif voice_tone:
            suggestions.append(f"Tono de voz de marca: {voice_tone}. Úsalo para nombrar tu oferta.")

        if not suggestions:
            suggestions.append("Adapta el nombre de marca como base para tu oferta.")

        logger.info("adapt_from_brand_identity_ok", tenant_id=str(tenant_id))
        return _ok_response("identity", draft_fields, suggestions, 0.8, [f"brand:{brand_name}"])
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 2 — Promise: adapt from brand narrative
# ---------------------------------------------------------------------------


@tool
def adapt_from_brand_narrative() -> str:
    """Generar variantes de promesa basadas en la narrativa StoryBrand de la marca.

    Sección: promise.
    Reads brand narrative (StoryBrand hero, problem, guide, one_liner) and
    returns 3 promise variants aligned with the brand's voice.

    Returns:
        JSON string with draft_fields, suggestions (3 variants), confidence, citations.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return _no_data_response("promise", "No se pudo determinar el tenant.")

    db = SessionLocal()
    try:
        settings = _brand_settings(db, tenant_id)
        if not settings or not settings.narrative:
            return _no_data_response(
                "promise",
                "La narrativa de marca no está configurada. Completa el módulo de narrativa en Brand Studio.",
            )

        narrative = settings.narrative
        one_liner = narrative.one_liner or ""
        hero = narrative.hero
        guide = narrative.guide
        outcome = narrative.outcome

        hero_identity = hero.identity if hero else ""
        hero_desire = hero.desire if hero else ""
        guide_empathy = guide.empathy_statement if guide else ""
        if outcome:
            outcome_result = getattr(outcome, "transformation", None) or getattr(outcome, "before", None) or ""
        else:
            outcome_result = ""

        variants = []
        if one_liner:
            variants.append(f"Variante directa (one-liner): {one_liner}")
        if hero_desire and outcome_result:
            variants.append(
                f"Variante transformación: Ayuda a {hero_identity or 'tu cliente ideal'} "
                f"a pasar de {hero_desire} a {outcome_result}."
            )
        if guide_empathy:
            variants.append(f"Variante empática: {guide_empathy}")

        if not variants:
            return _no_data_response(
                "promise",
                "La narrativa de marca existe pero esta incompleta (sin hero, guide u outcome). "
                "Enriquece el Brand Studio.",
            )

        # Pad to 3 variants if fewer
        while len(variants) < 3:
            variants.append("Edita esta variante basándote en la transformación que ofrece tu programa.")

        draft_fields = {"headline_promise": variants[0]}

        logger.info("adapt_from_brand_narrative_ok", tenant_id=str(tenant_id))
        return _ok_response("promise", draft_fields, variants[:3], 0.75, ["brand:narrative"])
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 3 — Promise: rewrite in 3 tones
# ---------------------------------------------------------------------------


@tool
def rewrite_tones(current_promise: str = "") -> str:
    """Reescribir la promesa actual en 3 registros de voz distintos.

    Sección: promise.
    Given the current promise text, returns 3 rewrites: formal, cercano, entusiasta.

    Args:
        current_promise: El texto actual de la promesa de la oferta.

    Returns:
        JSON string with draft_fields, suggestions (3 rewrites), confidence, citations.

    """
    if not current_promise or not current_promise.strip():
        return _no_data_response(
            "promise",
            "Escribe una promesa inicial antes de pedir reescrituras de tono.",
        )

    p = current_promise.strip()
    suggestions = [
        f"[Formal] {p} — Descubre un camino estructurado hacia tus metas con metodología probada.",
        f"[Cercano] {p} — Te acompaño paso a paso para que logres lo que tanto buscas.",
        f"[Entusiasta] {p} — ¡Es tu momento! Transforma tu vida con este programa diseñado para ti.",
    ]

    return _ok_response("promise", {}, suggestions, 0.7)


# ---------------------------------------------------------------------------
# Tool 4 — Promise: validate preset coherence
# ---------------------------------------------------------------------------


@tool
def validate_preset_coherence(current_promise: str = "", offer_id: str = "") -> str:
    """Validar coherencia entre la promesa y los flags del preset seleccionado.

    Sección: promise.
    Checks the promise against preset flags (HIGH_TICKET, LEAD_MAGNET,
    RECURRING_BILLING, etc.) and returns a list of coherence issues.

    Args:
        current_promise: El texto actual de la promesa.
        offer_id: UUID de la oferta en edición.

    Returns:
        JSON string with draft_fields (empty), suggestions (issues list), confidence.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return _no_data_response("promise", "No se pudo determinar el tenant.")

    db = SessionLocal()
    try:
        flags = _offer_preset_flags(db, tenant_id, offer_id or None)
        issues: list[str] = []

        if not current_promise.strip():
            issues.append("La promesa está vacía — define una antes de validar coherencia.")
        else:
            p_lower = current_promise.lower()
            if "high_ticket" in flags and not any(
                w in p_lower for w in ["transformacion", "resultado", "premium", "exclusivo", "inversion"]
            ):
                issues.append(
                    "El preset es HIGH_TICKET pero la promesa no comunica valor premium. "
                    'Incluye palabras como "transformación", "resultado" o "exclusivo".'
                )
            if "is_lead_magnet" in flags and any(w in p_lower for w in ["pago", "inversión", "precio"]):
                issues.append(
                    "El preset es LEAD_MAGNET (gratuito) pero la promesa menciona pago o inversión. "
                    "Reformula para reflejar el valor gratuito."
                )
            if "recurring_billing" in flags and "mes" not in p_lower and "acceso" not in p_lower:
                issues.append(
                    'El preset tiene RECURRING_BILLING. Considera incluir "acceso mensual" o "comunidad" en la promesa.'
                )

        if not issues:
            issues.append("La promesa parece coherente con los flags del preset seleccionado.")

        logger.info("validate_preset_coherence_ok", tenant_id=str(tenant_id), flags=flags)
        return _ok_response("promise", {}, issues, 0.65 if len(issues) > 1 else 0.9)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 5 — Audience / Strategy: reuse brand buyer personas
# ---------------------------------------------------------------------------


@tool
def reuse_brand_buyer_personas() -> str:
    """Listar buyer personas de la marca para reutilizar en la sección de audiencia.

    Sección: audience / strategy.
    Lists tenant's brand avatars/buyer personas with primary persona flagged.
    Use these as the starting point for the offer's target audience section.

    Returns:
        JSON string with draft_fields, suggestions (persona list), confidence.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return _no_data_response("audience", "No se pudo determinar el tenant.")

    db = SessionLocal()
    try:
        avatars = _avatars(db, tenant_id)
        if not avatars:
            return _no_data_response(
                "audience",
                "No hay buyer personas configuradas en el Brand Studio. "
                "Crea al menos un perfil de cliente ideal antes de reutilizarlos en la oferta.",
            )

        suggestions = []
        primary = None
        for av in avatars:
            is_default = getattr(av, "is_default", False)
            name = getattr(av, "name", "Sin nombre")
            icp = getattr(av, "icp_description", "") or ""
            label = f"{'★ Principal — ' if is_default else ''}{name}"
            if icp:
                label += f": {icp[:120]}"
            suggestions.append(label)
            if is_default:
                primary = av

        draft_fields: dict = {}
        if primary:
            draft_fields["target_audience_name"] = getattr(primary, "name", "")
            icp = getattr(primary, "icp_description", "") or ""
            if icp:
                draft_fields["target_audience_description"] = icp

        logger.info("reuse_brand_buyer_personas_ok", tenant_id=str(tenant_id), count=len(avatars))
        return _ok_response("audience", draft_fields, suggestions, 0.8)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 6 — Methodology: inherit brand methodology
# ---------------------------------------------------------------------------


@tool
def inherit_brand_methodology() -> str:
    """Heredar la metodología de marca como base para la metodología de la oferta.

    Sección: methodology.
    Reads brand strategy pillars and methodology name, returns them as draft
    defaults for the offer methodology section.

    Returns:
        JSON string with draft_fields (methodology_name, pillars), suggestions.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return _no_data_response("methodology", "No se pudo determinar el tenant.")

    db = SessionLocal()
    try:
        settings = _brand_settings(db, tenant_id)
        if not settings or not settings.strategy:
            return _no_data_response(
                "methodology",
                "La estrategia de marca no está configurada. Define la metodología en Brand Studio → Estrategia.",
            )

        strategy = settings.strategy
        name = strategy.methodology_name or ""
        description = strategy.methodology_description or ""
        pillars = getattr(strategy, "methodology_pillars", []) or []

        if not name and not pillars:
            return _no_data_response(
                "methodology",
                "La estrategia de marca existe pero sin metodología ni pilares. Enriquece el Brand Studio.",
            )

        draft_fields: dict = {}
        if name:
            draft_fields["methodology_name"] = name
        if description:
            draft_fields["methodology_description"] = description
        if pillars:
            draft_fields["methodology_pillars"] = [
                {"name": getattr(p, "name", str(p)), "description": getattr(p, "description", "")} for p in pillars
            ]

        suggestions = [f"Metodología de marca: {name}" if name else "Metodología sin nombre definido"]
        if pillars:
            suggestions.append(f"{len(pillars)} pilar(es) disponibles para adaptar a esta oferta.")

        logger.info("inherit_brand_methodology_ok", tenant_id=str(tenant_id))
        return _ok_response("methodology", draft_fields, suggestions, 0.8, ["brand:strategy"])
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 7 — Pricing: high-ticket tiering template
# ---------------------------------------------------------------------------


@tool
def high_ticket_tiering_template(offer_id: str = "") -> str:
    """Sugerir plantilla de 3 niveles para ofertas HIGH_TICKET.

    Sección: pricing.
    Trigger: preset flag HIGH_TICKET present.
    Returns a 3-tier template (Básico / Premium / Enterprise) with suggested
    price anchors and feature highlights.

    Args:
        offer_id: UUID de la oferta (para verificar el flag HIGH_TICKET).

    Returns:
        JSON string with draft_fields (pricing tiers), suggestions.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return _no_data_response("pricing", "No se pudo determinar el tenant.")

    db = SessionLocal()
    try:
        flags = _offer_preset_flags(db, tenant_id, offer_id or None)

        if offer_id and "high_ticket" not in flags:
            return _no_data_response(
                "pricing",
                "Este preset no tiene el flag HIGH_TICKET. "
                "La plantilla de 3 niveles aplica solo a ofertas de alto valor.",
            )

        template = [
            {
                "tier": "Básico",
                "price_anchor": "Desde $997",
                "description": "Acceso al programa principal + materiales",
                "features": ["Acceso vitalicio al contenido", "Comunidad privada", "Soporte por email"],
            },
            {
                "tier": "Premium",
                "price_anchor": "Desde $2,497",
                "description": "Programa + 4 sesiones de mentoría grupal",
                "features": [
                    "Todo lo de Básico",
                    "4 sesiones grupales mensuales",
                    "Revisión de ejercicios",
                    "Acceso prioritario a soporte",
                ],
            },
            {
                "tier": "Enterprise / VIP",
                "price_anchor": "Desde $5,997",
                "description": "Acompañamiento 1:1 personalizado",
                "features": [
                    "Todo lo de Premium",
                    "8 sesiones individuales",
                    "Canal directo con mentor",
                    "Garantía de resultados",
                ],
            },
        ]

        draft_fields = {"pricing_tiers": template}
        suggestions = [
            "Los precios son referencias — ajústalos al mercado y moneda de tu audiencia.",
            "Ancla psicológica: el nivel Premium debe costar ~60% del Enterprise.",
            "Incluye garantía de devolución en el nivel Básico para reducir fricción de entrada.",
        ]

        logger.info("high_ticket_tiering_template_ok", tenant_id=str(tenant_id))
        return _ok_response("pricing", draft_fields, suggestions, 0.85)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 8 — Pricing: recurring billing setup
# ---------------------------------------------------------------------------


@tool
def recurring_billing_setup(offer_id: str = "") -> str:
    """Sugerir configuración de facturación recurrente para ofertas RECURRING_BILLING.

    Sección: pricing.
    Trigger: preset flag RECURRING_BILLING.
    Returns suggested billing cycle, trial period, and proration fields.

    Args:
        offer_id: UUID de la oferta (para verificar el flag RECURRING_BILLING).

    Returns:
        JSON string with draft_fields (billing config), suggestions.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return _no_data_response("pricing", "No se pudo determinar el tenant.")

    db = SessionLocal()
    try:
        flags = _offer_preset_flags(db, tenant_id, offer_id or None)

        if offer_id and "recurring_billing" not in flags:
            return _no_data_response(
                "pricing",
                "Este preset no tiene el flag RECURRING_BILLING. "
                "La configuración de suscripción solo aplica a membresías o programas continuos.",
            )

        draft_fields = {
            "billing_frequency": "monthly",
            "trial_period_days": 7,
            "proration_enabled": True,
            "cancel_anytime": True,
            "grace_period_days_on_failed_payment": 3,
        }
        suggestions = [
            "Ciclo recomendado: mensual (menor fricción para nuevos suscriptores).",
            "Período de prueba de 7 días reduce la barrera de entrada sin sacrificar conversión.",
            "Activa prorrateo para que los cambios de plan sean justos y automáticos.",
            "Añade política de cancelación clara — reduce chargebacks y mejora confianza.",
        ]

        logger.info("recurring_billing_setup_ok", tenant_id=str(tenant_id))
        return _ok_response("pricing", draft_fields, suggestions, 0.8)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 9 — Pricing: detect currency mismatch
# ---------------------------------------------------------------------------


@tool
def detect_currency_mismatch(offer_id: str = "") -> str:
    """Detectar discrepancias entre la moneda de la oferta y la del tenant.

    Sección: pricing.
    Checks current offer currency vs tenant locale currency.
    Returns a mismatch report if currencies differ.

    Args:
        offer_id: UUID de la oferta a revisar.

    Returns:
        JSON string with draft_fields (empty), suggestions (mismatch list).

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return _no_data_response("pricing", "No se pudo determinar el tenant.")

    db = SessionLocal()
    try:
        # Get tenant currency from IAM tenant model
        from sqlalchemy import select

        from src.modules.iam.infrastructure.models.tenant_model import TenantModel

        stmt = select(TenantModel).where(TenantModel.id == tenant_id)
        tenant_row = db.execute(stmt).scalars().first()  # type: ignore[attr-defined]
        tenant_currency = getattr(tenant_row, "default_currency", None) if tenant_row else None

        # Get offer currency if offer_id provided
        offer_currency = None
        if offer_id:
            from src.shared.links.ports.offer import get_offer_repository

            repo = get_offer_repository(db)  # type: ignore[arg-type]
            offers = repo.get_all_by_tenant(tenant_id)  # type: ignore[arg-type]
            target = next((o for o in offers if str(getattr(o, "id", "")) == str(offer_id)), None)
            offer_currency = getattr(target, "currency", None) if target else None

        issues: list[str] = []
        if not tenant_currency:
            issues.append(
                "La moneda del tenant no está configurada. Define la moneda predeterminada en Configuración → Perfil."
            )
        if offer_currency and tenant_currency and offer_currency != tenant_currency:
            issues.append(
                f"La oferta usa {offer_currency} pero el tenant tiene {tenant_currency} como moneda principal. "
                f"Verifica que esta diferencia sea intencional (ej: oferta en USD para mercado internacional)."
            )
        if not issues:
            currency_display = offer_currency or tenant_currency or "sin moneda definida"
            issues.append(f"No hay discrepancias de moneda detectadas. Moneda activa: {currency_display}.")

        confidence = 0.5 if not tenant_currency else (0.6 if len(issues) > 1 else 0.95)
        logger.info("detect_currency_mismatch_ok", tenant_id=str(tenant_id))
        return _ok_response("pricing", {}, issues, confidence)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 10 — Schedule: import scheduling event type
# ---------------------------------------------------------------------------


@tool
def import_scheduling_event_type(event_type_id: str = "") -> str:
    """Importar un tipo de evento de la agenda al campo de programación de la oferta.

    Sección: schedule.
    Loads scheduling event type data (duration, capacity, slug) and returns
    the fields for the offer schedule section.

    Args:
        event_type_id: ID del tipo de evento en la agenda del tenant.

    Returns:
        JSON string with draft_fields (duration, capacity, slug), suggestions.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return _no_data_response("schedule", "No se pudo determinar el tenant.")

    db = SessionLocal()
    try:
        event_types = _event_types(db, tenant_id)
        if not event_types:
            return _no_data_response(
                "schedule",
                "No hay tipos de evento configurados en la Agenda. "
                "Crea al menos uno en Conexiones → Google Calendar antes de importar.",
            )

        target = None
        if event_type_id:
            target = next(
                (et for et in event_types if str(getattr(et, "id", "")) == str(event_type_id)),
                None,
            )
            if not target:
                return _no_data_response(
                    "schedule",
                    f"No se encontró el tipo de evento {event_type_id}. "
                    "Verifica el ID o selecciona uno de los disponibles.",
                )
        else:
            # Default to first non-hidden event type
            target = next((et for et in event_types if not getattr(et, "is_hidden", False)), event_types[0])

        duration = getattr(target, "duration", 30)
        slug = getattr(target, "slug", "")
        title = getattr(target, "title", "")
        booking_config = getattr(target, "booking_config", None)
        max_per_day = getattr(booking_config, "max_per_day", None) if booking_config else None

        draft_fields: dict = {
            "scheduling_event_type_id": str(getattr(target, "id", "")),
            "session_duration_minutes": duration,
        }
        if max_per_day:
            draft_fields["capacity"] = max_per_day
        if slug:
            draft_fields["booking_slug"] = slug

        suggestions = [
            f'Tipo de evento importado: "{title}" ({duration} min).',
        ]
        if max_per_day:
            suggestions.append(f"Capacidad máxima por día: {max_per_day} sesiones.")
        available_names = [getattr(et, "title", "") for et in event_types if not getattr(et, "is_hidden", False)]
        if len(available_names) > 1:
            suggestions.append(f"Otros tipos disponibles: {', '.join(available_names[1:3])}.")

        logger.info(
            "import_scheduling_event_type_ok", tenant_id=str(tenant_id), event_type_id=str(getattr(target, "id", ""))
        )
        return _ok_response("schedule", draft_fields, suggestions, 0.9)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 11 — Location: detect hybrid split
# ---------------------------------------------------------------------------


@tool
def detect_hybrid_split(location_data: str = "") -> str:
    """Detectar modalidad híbrida en la sección de ubicación y sugerir división.

    Sección: location.
    For modality offers, detects if location data indicates hybrid and suggests
    a location_override split (presencial + online percentages or dates).

    Args:
        location_data: Texto libre con la información de ubicación actual.

    Returns:
        JSON string with draft_fields (location_override), suggestions.

    """
    if not location_data.strip():
        return _no_data_response(
            "location",
            "Proporciona los datos de ubicación actuales para detectar si hay modalidad híbrida.",
        )

    data_lower = location_data.lower()
    hybrid_keywords = ["híbrido", "hibrido", "online y presencial", "virtual y presencial", "remoto y presencial"]
    is_hybrid = any(kw in data_lower for kw in hybrid_keywords)

    if not is_hybrid:
        return _ok_response(
            "location",
            {},
            ["No se detectó modalidad híbrida en los datos de ubicación proporcionados."],
            0.8,
        )

    draft_fields = {
        "modality": "hybrid",
        "location_override": {
            "online_percentage": 70,
            "presencial_percentage": 30,
            "online_platform": "Zoom / Meet (por confirmar)",
            "presencial_address": "Por definir",
        },
    }
    suggestions = [
        "Se detectó modalidad híbrida. Ajusta los porcentajes online/presencial según tu programa.",
        "Define la plataforma online (Zoom, Teams, Meet) y la dirección física.",
        "Comunica claramente a los participantes cuáles sesiones son presenciales y cuáles virtuales.",
    ]

    return _ok_response("location", draft_fields, suggestions, 0.75)


# ---------------------------------------------------------------------------
# Tool 12 — Testimonials: import from brand vault
# ---------------------------------------------------------------------------


@tool
def import_from_brand_vault() -> str:
    """Importar testimonios del vault de la marca para la sección de testimonios.

    Sección: testimonials.
    Lists tenant's brand testimonials (from social_proof module) reusable
    for this offer's testimonials section.

    Returns:
        JSON string with draft_fields, suggestions (testimonial list), confidence.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return _no_data_response("testimonials", "No se pudo determinar el tenant.")

    db = SessionLocal()
    try:
        bundle = _social_proof_bundle(db, tenant_id)
        testimonials = bundle.get("testimonials", [])

        if not testimonials:
            return _no_data_response(
                "testimonials",
                "No hay testimonios en el vault de la marca. "
                "Agrega testimonios en Brand Studio → Prueba Social antes de importarlos aquí.",
            )

        items = []
        for t in testimonials[:10]:  # cap at 10
            author = getattr(t, "author_name", "") or ""
            role = getattr(t, "author_role", "") or ""
            content = getattr(t, "content", "") or getattr(t, "quote", "") or ""
            rating = getattr(t, "rating", None)
            stars = "★" * (rating or 5)
            label = f"{stars} {author}"
            if role:
                label += f" ({role})"
            if content:
                label += f": {content[:100]}..."
            items.append(label)

        draft_fields = {
            "testimonials": [
                {
                    "author_name": getattr(t, "author_name", ""),
                    "author_role": getattr(t, "author_role", ""),
                    "content": getattr(t, "content", "") or getattr(t, "quote", "") or "",
                    "rating": getattr(t, "rating", 5),
                    "source": "brand_vault",
                }
                for t in testimonials[:5]
            ]
        }

        suggestions = items
        logger.info("import_from_brand_vault_ok", tenant_id=str(tenant_id), count=len(testimonials))
        return _ok_response("testimonials", draft_fields, suggestions, 0.9, ["social_proof:testimonials"])
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 13 — Testimonials: suggest missing objections
# ---------------------------------------------------------------------------


@tool
def suggest_missing_objections(offer_id: str = "", existing_objections: str = "") -> str:
    """Sugerir objeciones comunes que faltan en la sección de testimonios.

    Sección: testimonials.
    Given the offer's preset flags + existing testimonials, suggests missing
    objection themes that should be covered by testimonials.

    Args:
        offer_id: UUID de la oferta.
        existing_objections: Texto con las objeciones ya cubiertas.

    Returns:
        JSON string with draft_fields (empty), suggestions (missing themes).

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return _no_data_response("testimonials", "No se pudo determinar el tenant.")

    db = SessionLocal()
    try:
        flags = _offer_preset_flags(db, tenant_id, offer_id or None)
        covered = existing_objections.lower()

        all_objections = [
            ("tiempo", "¿Vale la pena el tiempo que requiere?"),
            ("precio", "¿El precio es justo para los resultados que promete?"),
            ("experiencia_previa", "¿Funciona aunque sea principiante?"),
            ("resultados_reales", "¿Hay resultados reales y verificables?"),
            ("soporte", "¿Qué pasa si tengo dudas o problemas durante el programa?"),
        ]

        # Add flag-specific objections
        if "high_ticket" in flags:
            all_objections.append(("inversion_alta", "¿Cómo sé que vale la inversión de alto valor?"))
        if "recurring_billing" in flags:
            all_objections.append(("compromiso_mensual", "¿Puedo cancelar cuando quiera?"))
        if "is_lead_magnet" in flags:
            all_objections.append(("valor_gratuito", "¿Qué tan bueno puede ser si es gratis?"))

        missing = [
            text
            for key, text in all_objections
            if key not in covered and not any(word in covered for word in key.split("_"))
        ]

        if not missing:
            return _ok_response(
                "testimonials",
                {},
                ["Todas las objeciones principales parecen estar cubiertas. ¡Excelente trabajo!"],
                0.85,
            )

        suggestions = ["Objeciones aún sin testimonio que las responda:", *missing]
        logger.info("suggest_missing_objections_ok", tenant_id=str(tenant_id), missing_count=len(missing))
        return _ok_response("testimonials", {}, suggestions, 0.8)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 14 — FAQ: generate from preset flags
# ---------------------------------------------------------------------------


@tool
def generate_from_preset_flags(offer_id: str = "") -> str:
    """Generar FAQs basadas en los flags del preset de la oferta.

    Sección: faq.
    Given the preset flags, returns 5-8 FAQ templates relevant to those flags.

    Args:
        offer_id: UUID de la oferta.

    Returns:
        JSON string with draft_fields (faq list), suggestions.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return _no_data_response("faq", "No se pudo determinar el tenant.")

    db = SessionLocal()
    try:
        flags = _offer_preset_flags(db, tenant_id, offer_id or None)

        base_faqs = [
            {"q": "¿Para quién es este programa?", "a": "Es ideal para [describe tu perfil de cliente ideal]."},
            {"q": "¿Qué resultados puedo esperar?", "a": "Al completar el programa, lograrás [resultado principal]."},
            {
                "q": "¿Cuánto tiempo requiere por semana?",
                "a": "Recomendamos dedicar [X horas] semanales para aprovechar al máximo.",
            },
            {
                "q": "¿Tengo acceso vitalicio al contenido?",
                "a": "Sí, una vez inscrito tienes acceso de por vida a los materiales.",
            },
            {
                "q": "¿Qué pasa si tengo dudas?",
                "a": "Tenemos [soporte por email / comunidad / sesiones de preguntas] para acompañarte.",
            },
        ]

        flag_faqs: list[dict] = []
        if "high_ticket" in flags:
            flag_faqs.append(
                {
                    "q": "¿Por qué tiene este precio?",
                    "a": "La inversión refleja el acompañamiento personalizado y los resultados garantizados.",
                }
            )
            flag_faqs.append(
                {
                    "q": "¿Hay opciones de pago a plazos?",
                    "a": "Sí, ofrecemos planes de pago en [X cuotas] para facilitar tu acceso.",
                }
            )
        if "recurring_billing" in flags:
            flag_faqs.append(
                {
                    "q": "¿Puedo cancelar mi suscripción en cualquier momento?",
                    "a": "Sí, puedes cancelar antes de tu próximo ciclo de facturación sin penalización.",
                }
            )
        if "is_lead_magnet" in flags:
            flag_faqs.append(
                {"q": "¿Es realmente gratuito?", "a": "Sí, completamente. Solo necesitas registrarte con tu correo."}
            )
        if "requires_start_date" in flags:
            flag_faqs.append(
                {
                    "q": "¿Cuándo comienza el programa?",
                    "a": "La próxima cohorte inicia el [fecha]. Inscríbete antes para asegurar tu lugar.",
                }
            )

        all_faqs = base_faqs + flag_faqs
        draft_fields = {"faqs": all_faqs[:8]}

        suggestions = [f"Se generaron {len(all_faqs[:8])} FAQs basadas en el preset y sus flags."]
        if flags:
            suggestions.append(f"Flags activos: {', '.join(flags)}.")

        logger.info("generate_from_preset_flags_ok", tenant_id=str(tenant_id), faq_count=len(all_faqs[:8]))
        return _ok_response("faq", draft_fields, suggestions, 0.8)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 15 — FAQ: pull sales agent common questions
# ---------------------------------------------------------------------------


@tool
def pull_sales_agent_common_questions() -> str:
    """Extraer las preguntas más frecuentes de los leads del agente de ventas.

    Sección: faq.
    Reads sales_agent conversation data via SQL to extract top 5 common
    lead questions and return them as FAQ candidates.

    Returns:
        JSON string with draft_fields (faq candidates), suggestions.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return _no_data_response("faq", "No se pudo determinar el tenant.")

    db = SessionLocal()
    try:
        from sqlalchemy import text

        # Query conversation summaries from leads — look for stored question patterns
        rows = (
            db.execute(  # type: ignore[attr-defined]
                text(
                    "SELECT conversation_summary FROM leads "
                    "WHERE tenant_id = :tid "
                    "AND conversation_summary IS NOT NULL "
                    "AND conversation_summary != '' "
                    "ORDER BY updated_at DESC LIMIT 50"
                ),
                {"tid": str(tenant_id)},
            )
            .mappings()
            .all()
        )

        if not rows:
            return _no_data_response(
                "faq",
                "El agente de ventas no tiene conversaciones con resumen disponibles aún. "
                "Las preguntas frecuentes se extraen automáticamente después de las primeras interacciones.",
            )

        # Extract question-like sentences from summaries
        common_themes: list[str] = []
        for row in rows:
            summary = row.get("conversation_summary", "") or ""
            # Simple heuristic: extract sentences containing question words
            sentences = summary.split(".")
            for sentence in sentences:
                s = sentence.strip()
                if any(q in s.lower() for q in ["precio", "costo", "duración", "cuándo", "cómo funciona", "garantía"]):
                    if s not in common_themes and len(s) > 10:
                        common_themes.append(s[:120])
                    if len(common_themes) >= 5:
                        break
            if len(common_themes) >= 5:
                break

        if not common_themes:
            return _no_data_response(
                "faq",
                "Se encontraron conversaciones pero sin patrones de preguntas claros. "
                'Usa "Generar desde flags de preset" como alternativa.',
            )

        faq_candidates = [
            {"q": f"Pregunta frecuente detectada: {theme}", "a": "[Añade tu respuesta aquí]"}
            for theme in common_themes[:5]
        ]
        draft_fields = {"faq_candidates": faq_candidates}
        suggestions = [
            f"Se detectaron {len(faq_candidates)} temas frecuentes en conversaciones del agente.",
            "Edita las preguntas para hacerlas más claras y añade respuestas completas.",
        ]

        logger.info("pull_sales_agent_common_questions_ok", tenant_id=str(tenant_id), themes=len(common_themes))
        return _ok_response("faq", draft_fields, suggestions, 0.65)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 16 — Value Stack: assemble from brand authority
# ---------------------------------------------------------------------------


@tool
def assemble_from_brand_authority() -> str:
    """Ensamblar value stack desde los activos de autoridad de la marca.

    Sección: value_stack.
    Reads brand authority signals (certifications, media mentions, client logos)
    and packages them as value stack items.

    Returns:
        JSON string with draft_fields (value_stack items), suggestions.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return _no_data_response("value_stack", "No se pudo determinar el tenant.")

    db = SessionLocal()
    try:
        bundle = _social_proof_bundle(db, tenant_id)
        authority_items = bundle.get("authority_items", [])

        if not authority_items:
            return _no_data_response(
                "value_stack",
                "No hay activos de autoridad configurados en el Brand Studio. "
                "Agrega certificaciones, menciones en medios o logos de clientes en Brand Studio → Prueba Social.",
            )

        value_stack_items = []
        for item in authority_items[:8]:
            entity_name = getattr(item, "entity_name", "") or getattr(item, "title", "") or ""
            item_type = getattr(item, "type", "") or ""
            context = getattr(item, "context", "") or ""

            label = entity_name or "Autoridad sin nombre"
            type_map = {
                "certification": "Certificación",
                "media": "Mención en medios",
                "award": "Premio / Reconocimiento",
                "client_logo": "Cliente destacado",
                "partnership": "Alianza estratégica",
            }
            type_label = type_map.get(item_type.lower(), item_type or "Autoridad")
            value_stack_items.append(
                {
                    "title": label,
                    "type": type_label,
                    "description": context[:200] if context else f"{type_label}: {label}",
                    "source": "brand_authority_vault",
                }
            )

        draft_fields = {"value_stack": value_stack_items}
        suggestions = [
            f"{len(value_stack_items)} activo(s) de autoridad importados desde el vault de la marca.",
            "Reordena los ítems según su impacto percibido (el más fuerte, primero).",
            "Añade logos o imágenes de respaldo para aumentar la credibilidad visual.",
        ]

        logger.info("assemble_from_brand_authority_ok", tenant_id=str(tenant_id), count=len(value_stack_items))
        return _ok_response("value_stack", draft_fields, suggestions, 0.85, ["social_proof:authority_items"])
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 17 — Instructors: reuse brand team
# ---------------------------------------------------------------------------


@tool
def reuse_brand_team() -> str:
    """Reutilizar el equipo de la marca como instructores de la oferta.

    Sección: instructors.
    Lists brand team members (from social_proof TeamMember repository)
    for reuse as offer instructors.

    Returns:
        JSON string with draft_fields (instructors list), suggestions.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return _no_data_response("instructors", "No se pudo determinar el tenant.")

    db = SessionLocal()
    try:
        bundle = _social_proof_bundle(db, tenant_id)
        team_members = bundle.get("team_members", [])

        # Also check brand settings team (KeyFigure) as fallback
        brand_team: list[dict] = []
        settings = _brand_settings(db, tenant_id)
        if settings and settings.team:
            for member in settings.team:
                brand_team.append(
                    {
                        "id": str(getattr(member, "id", "")),
                        "name": getattr(member, "name", ""),
                        "role": getattr(member, "role", ""),
                        "bio": getattr(member, "bio", "") or "",
                        "headshot_url": getattr(member, "headshot_url", None),
                        "source": "brand_studio_team",
                    }
                )

        sp_team = []
        for m in team_members:
            sp_team.append(
                {
                    "id": str(getattr(m, "id", "")),
                    "name": getattr(m, "name", "") or getattr(m, "display_name", ""),
                    "role": getattr(m, "role", "") or getattr(m, "job_title", ""),
                    "bio": getattr(m, "bio", "") or "",
                    "headshot_url": getattr(m, "avatar_url", None) or getattr(m, "headshot_url", None),
                    "source": "social_proof_team",
                }
            )

        combined = sp_team or brand_team
        if not combined:
            return _no_data_response(
                "instructors",
                "No hay miembros del equipo configurados. "
                "Agrega el equipo en Brand Studio → Equipo o en el módulo de Prueba Social.",
            )

        draft_fields = {"instructors": combined[:6]}
        suggestions = [
            f"{len(combined)} miembro(s) del equipo disponibles como instructores.",
        ]
        if len(combined) > 6:
            suggestions.append(f"Mostrando los primeros 6. Tienes {len(combined)} en total.")
        suggestions.append("Selecciona solo los instructores relevantes para esta oferta específica.")

        logger.info("reuse_brand_team_ok", tenant_id=str(tenant_id), count=len(combined))
        return _ok_response("instructors", draft_fields, suggestions, 0.9, ["social_proof:team_members", "brand:team"])
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 18 — Psychology: structure objections from raw text (paste-AI)
# ---------------------------------------------------------------------------


@tool
def structure_objections(raw_text: str) -> str:
    """Estructurar objeciones pegadas en texto libre a formato tipado.

    Seccion: psychology.
    El usuario pega texto (un email con dudas de prospectos, notas de
    ventas, resumen de call) y devuelve objections[] estructuradas
    con type/rebuttal/strategy/trigger_phrases listas para aplicar en el
    aggregate Offer.

    Args:
        raw_text: Texto libre con las objeciones del prospecto. Obligatorio.

    Returns:
        JSON string con draft_fields.objections lista para aplicar.

    """
    import json

    from pydantic import BaseModel, Field

    from src.shared.application.ai_action_service import (
        AIActionPolicy,
        AIActionService,
        AIModelPolicy,
    )

    tenant_id = get_tenant_id()
    if not tenant_id:
        return _no_data_response("psychology", "No se pudo determinar el tenant.")

    if not raw_text or not raw_text.strip():
        return _no_data_response(
            "psychology",
            "Necesito el texto con las objeciones pegadas. Pega el contenido y vuelve a intentarlo.",
        )

    # Local schema for LLM structured output (not exported — tool-private)
    class _ObjectionItemOut(BaseModel):
        type: str = Field(description="Categoria de la objecion. Valores: price, time, trust, partner, fit, custom.")
        rebuttal: str = Field(
            description=(
                "Guion de respuesta del agente de ventas."
                " Tuteo latinoamericano neutro (tu/tienes/puedes), sin voseo."
                " Tono consultivo, 3-5 oraciones."
            )
        )
        strategy: str = Field(
            description=(
                "Nombre corto de la estrategia de rebuttal."
                " Ej: 'ROI Reframing', 'Risk Reversal', 'Decision Facilitator'."
            )
        )
        trigger_phrases: list[str] = Field(
            default_factory=list,
            description=("Frases textuales que el prospecto diria. 2-4 frases como habla una persona real."),
        )

    class _StructureObjectionsOutput(BaseModel):
        objections: list[_ObjectionItemOut] = Field(default_factory=list)

    system_prompt = (
        "Eres un experto en ventas consultivas para el mercado latinoamericano."
        " Tu tarea: leer el texto con objeciones de prospectos y estructurarlas"
        " en objections[] tipadas con type, rebuttal, strategy y trigger_phrases."
        " Cada rebuttal debe estar en espanol latinoamericano neutro, tuteo (tu/tienes),"
        " sin voseo (vos/tenes/podes). Tono consultivo, no manipulativo."
        " Responde SOLO con JSON valido que cumpla el schema _StructureObjectionsOutput."
        " Sin markdown, sin code blocks, sin texto adicional."
        f"\n\nSCHEMA:\n{json.dumps(_StructureObjectionsOutput.model_json_schema(), indent=2)}"
    )

    try:
        ai_svc = AIActionService()
        policy = AIActionPolicy(
            retries=2,
            retry_delay_seconds=2.0,
            model=AIModelPolicy(
                model_type="reasoning",
                temperature=0,
                max_output_tokens=2000,
            ),
        )
        result: _StructureObjectionsOutput = ai_svc.run_structured_action(
            action_name="structure_objections",
            tenant_id=tenant_id,
            system_prompt=system_prompt,
            user_prompt=f"Objeciones a estructurar:\n\n{raw_text[:4000]}",
            response_model=_StructureObjectionsOutput,
            policy=policy,
            metadata={"section": "psychology", "tool": "structure_objections"},
        )
    except Exception:
        logger.exception("structure_objections_llm_failed", tenant_id=str(tenant_id))
        return _no_data_response(
            "psychology",
            "No se pudo estructurar las objeciones. Intenta de nuevo o hazlo manualmente.",
        )

    if not result.objections:
        return _no_data_response(
            "psychology",
            "No encontre objeciones claras en el texto. Asegurate de pegar texto con dudas o frases de prospectos.",
        )

    # Map _ObjectionItemOut → dict compatible with ObjectionItem domain shape
    objections_payload = [
        {
            "type": o.type,
            "rebuttal": o.rebuttal,
            "strategy": o.strategy,
            "trigger_phrases": o.trigger_phrases,
        }
        for o in result.objections
    ]

    suggestions = [
        f"Se estructuraron {len(result.objections)} objeciones desde el texto pegado.",
        "Revisa los rebuttals — ajusta el tono si el agente necesita mas o menos formalidad.",
        "Agrega trigger_phrases adicionales que escuches en tus llamadas reales.",
    ]

    logger.info(
        "structure_objections_ok",
        tenant_id=str(tenant_id),
        objections_count=len(result.objections),
        types=[o.type for o in result.objections],
    )
    return _ok_response(
        "psychology",
        {"objections": objections_payload},
        suggestions,
        0.8,
        ["copilot:llm:structure_objections"],
    )


# ---------------------------------------------------------------------------
# Exported group
# ---------------------------------------------------------------------------

OFFER_SECTION_TOOLS = [
    adapt_from_brand_identity,
    adapt_from_brand_narrative,
    rewrite_tones,
    validate_preset_coherence,
    reuse_brand_buyer_personas,
    inherit_brand_methodology,
    high_ticket_tiering_template,
    recurring_billing_setup,
    detect_currency_mismatch,
    import_scheduling_event_type,
    detect_hybrid_split,
    import_from_brand_vault,
    suggest_missing_objections,
    generate_from_preset_flags,
    pull_sales_agent_common_questions,
    assemble_from_brand_authority,
    reuse_brand_team,
    structure_objections,
]
