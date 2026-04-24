"""Offer editable-field catalog — single source of truth for the copilot.

# [COPILOT-EDITABLE-FIELDS-SSOT] → docs/domains/copilot/editable-fields.md
#
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  IMPORTANTE PARA AGENTES / DEVS                                      ║
# ║                                                                      ║
# ║  Esta es la fuente de verdad de los campos de offer que el copilot  ║
# ║  puede proponer editar vía `propose_field_updates`.                  ║
# ║                                                                      ║
# ║  Cuando AGREGUES, ELIMINES, RENOMBRES o MUEVAS un campo en:          ║
# ║  - frontend/src/features/offer-studio/schemas/*.schema.ts            ║
# ║  - el modelo Pydantic en backend/src/modules/offer/domain/offer.py   ║
# ║  - backend/src/modules/copilot/domain/offer_fields.py                ║
# ║    (PERSISTABLE_FIELDS — la lista mínima que valida el interview)    ║
# ║                                                                      ║
# ║  TAMBIÉN ACTUALIZA ESTE ARCHIVO. Sin esta actualización el LLM       ║
# ║  alucinará ``field_id``s obsoletos o ignorará campos nuevos.         ║
# ╚══════════════════════════════════════════════════════════════════════╝

La Offer es polimórfica: según ``archetype`` el FE renderiza secciones
específicas (``program_details`` / ``service_details`` / ``event_details`` /
``product_details`` / ``subscription_details`` / ``platform_details``).
Los paths de esas secciones usan ``specific_details.<field>`` porque en
la entidad ``Offer`` viven bajo el atributo ``specific_details``.
"""

from __future__ import annotations

from src.shared.links.ports.editable_fields import FieldSpec, register_catalog

# ── identity ─────────────────────────────────────────────────────────────
# Form-runtime: offer.identity
_IDENTITY = (
    FieldSpec(
        "public_name", "Nombre público", "identity", "Nombre que verá el cliente en la landing y en el sales agent."
    ),
    FieldSpec(
        "headline_promise", "Promesa principal", "identity", "La gran promesa de la oferta — qué gana el cliente."
    ),
    FieldSpec("primary_outcome", "Resultado principal", "identity"),
    FieldSpec(
        "time_to_value", "Tiempo para ver valor", "identity", "Cuánto tarda el cliente en ver el primer resultado."
    ),
)

# ── strategy ─────────────────────────────────────────────────────────────
# Form-runtime: offer.strategy
_STRATEGY = (
    FieldSpec("target_avatar_match", "Avatares objetivo", "strategy"),
    FieldSpec("marketing_pain_points", "Pain points de marketing", "strategy"),
    FieldSpec("marketing_desires", "Deseos de marketing", "strategy"),
    FieldSpec("anti_avatar_keywords", "Anti-avatar (palabras clave)", "strategy"),
)

# ── promise narrative ─────────────────────────────────────────────────────
# Form-runtime: offer.promise
_PROMISE_NARRATIVE = (
    FieldSpec(
        "before_state",
        "Situación previa del cliente",
        "promise",
        "Cómo vive el cliente ANTES de la oferta. Dolor concreto y situación cotidiana específica.",
    ),
    FieldSpec(
        "after_state",
        "Situación objetivo del cliente",
        "promise",
        "Cómo vive el cliente DESPUÉS de completar la oferta. Evidencia concreta, no abstracta.",
    ),
    FieldSpec(
        "why_now",
        "Por qué ahora",
        "promise",
        "Razón por la que postergar tiene costo concreto. Conecta con el costo real de inacción.",
    ),
    FieldSpec(
        "measurable_outcomes",
        "Resultados medibles",
        "promise",
        "Lista de resultados medibles concretos, uno por ítem. Idealmente con números.",
    ),
)

# ── psychology ───────────────────────────────────────────────────────────
# Form-runtime: offer.psychology
_PSYCHOLOGY = (
    FieldSpec("objections", "Objeciones", "psychology"),
    FieldSpec(
        "cultural_trust_barriers",
        "Barreras culturales de confianza",
        "psychology",
        "Barreras culturales Latam que no son objeciones clásicas. Uno por ítem.",
    ),
    FieldSpec(
        "emotional_triggers",
        "Disparadores emocionales",
        "psychology",
        "Miedos, deseos y aspiraciones que mueven la decisión de compra. Uno por ítem.",
    ),
    FieldSpec(
        "status_drivers",
        "Motores de estatus",
        "psychology",
        "Qué cambia en la percepción social del cliente cuando compra y tiene éxito. Uno por ítem.",
    ),
    FieldSpec(
        "regret_scenarios",
        "Escenarios de arrepentimiento",
        "psychology",
        "Situaciones futuras concretas donde el lead se va a arrepentir de no haber comprado hoy. Uno por ítem.",
    ),
)

# ── value-stack ──────────────────────────────────────────────────────────
# Form-runtime: offer.value_stack
_VALUE_STACK = (
    FieldSpec("deliverables", "Entregables", "value_stack"),
    FieldSpec("includes_offers", "Ofertas incluidas", "value_stack"),
)

# ── pricing ──────────────────────────────────────────────────────────────
# Form-runtime: offer.pricing
_PRICING = (
    FieldSpec("pricing_options", "Opciones de precio", "pricing"),
    FieldSpec("price_pay_in_full", "Precio pago único", "pricing"),
    FieldSpec("currency", "Moneda", "pricing"),
)

# ── closing ──────────────────────────────────────────────────────────────
# Form-runtime: offer.closing
_CLOSING = (
    FieldSpec("guarantee_type", "Tipo de garantía", "closing"),
    FieldSpec("guarantee_terms", "Términos de la garantía", "closing"),
    FieldSpec("support_duration_days", "Duración del soporte (días)", "closing"),
    FieldSpec(
        "refund_process_description",
        "Proceso de devolución",
        "closing",
        "Cómo se devuelve el dinero, desglosado por método de pago. Combate la desconfianza Latam.",
    ),
    FieldSpec(
        "urgency_drivers",
        "Razones de urgencia honestas",
        "closing",
        "Razones HONESTAS para comprar ahora. Uno por ítem. Urgencia falsa pierde confianza.",
    ),
    FieldSpec(
        "scarcity_reason_honest",
        "Motivo de escasez real",
        "closing",
        "Razón honesta de los cupos limitados — logística real, tiempo del experto, calidad de atención.",
    ),
    FieldSpec(
        "bonus_if_act_now",
        "Bonus por decidir ahora",
        "closing",
        "Bonus condicional a actuar en una ventana de acción definida (48h, 7 días).",
    ),
    FieldSpec(
        "final_push_copy",
        "Frase de cierre",
        "closing",
        "Frase de cierre emocional para cuando el lead está a un paso de decidir.",
    ),
)

# ── onboarding / prerequisites ───────────────────────────────────────────
_ONBOARDING = (
    FieldSpec("onboarding_action", "Acción de onboarding", "onboarding"),
    FieldSpec("access_duration_text", "Duración del acceso", "onboarding"),
    FieldSpec("prerequisites", "Prerequisitos", "onboarding"),
    FieldSpec("requires_application", "Requiere aplicación", "onboarding"),
)

# ── classification (archetype / value level / format) ────────────────────
# Rarely edited inline, but the LLM may propose them during offer creation.
_CLASSIFICATION = (
    FieldSpec("archetype", "Archetype de la oferta", "classification"),
    FieldSpec("format_hint", "Formato (hint)", "classification"),
    FieldSpec("value_level", "Nivel de valor", "classification"),
    FieldSpec("delivery_model", "Modelo de entrega", "classification"),
)


OFFER_EDITABLE_FIELDS: tuple[FieldSpec, ...] = (
    *_IDENTITY,
    *_PROMISE_NARRATIVE,
    *_STRATEGY,
    *_PSYCHOLOGY,
    *_VALUE_STACK,
    *_PRICING,
    *_CLOSING,
    *_ONBOARDING,
    *_CLASSIFICATION,
)


# Register at import time so the copilot sees the catalog via the port.
register_catalog("offer", OFFER_EDITABLE_FIELDS)


__all__ = ["OFFER_EDITABLE_FIELDS"]
