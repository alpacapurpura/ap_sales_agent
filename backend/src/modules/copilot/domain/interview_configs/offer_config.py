"""Offer interview configuration.

Static config (6 blocks) registered for backward compatibility.
Dynamic factory ``get_offer_interview_config(archetype)`` generates a 7-block
config adapted to the offer's archetype (3 universal_first + 1 archetype-specific
+ 3 universal_final), injected between the universal first and final blocks.
"""

from src.modules.copilot.domain.interview_config import (
    InterviewBlock,
    InterviewConfig,
    register_interview_config,
)

# ---------------------------------------------------------------------------
# Universal first blocks -- strategy, promise, psychology (positions 0-2)
# ---------------------------------------------------------------------------

_UNIVERSAL_FIRST: list[InterviewBlock] = [
    InterviewBlock(
        id="identity_strategy",
        label="Identidad y Estrategia",
        campos_objetivo=[
            "public_name",
            "archetype",
            "delivery_model",
            "value_level",
            "format_hint",
        ],
        prompt_context=(
            "Define QUÉ es este offer y DÓNDE encaja en el "
            "ladder de valor. "
            "¿Es un lead magnet, un producto de activación, "
            "o la transformación core? "
            "Identifica el arquetipo (producto digital, "
            "programa, servicio, membresía, experiencia) "
            "y el modelo de entrega "
            "(DIY, Done With You, Done For You). "
            "Asegúrate de que el nombre público sea "
            "memorable, claro y orientado al resultado."
        ),
        coverage_threshold=0.8,
    ),
    InterviewBlock(
        id="promise",
        label="Promesa y Resultado",
        campos_objetivo=[
            "headline_promise",
            "primary_outcome",
            "time_to_value",
            "target_avatar_match",
        ],
        prompt_context=(
            "Construye la PROMESA — el resultado específico "
            "y medible que el cliente obtiene. "
            "headline_promise: MAX 15 palabras. "
            "Resultado específico + tiempo (si aplica). "
            "primary_outcome: Lo que cambia en la vida "
            "del cliente DESPUÉS. "
            "time_to_value: ¿En cuánto tiempo ven "
            "resultados? Sé realista pero motivador. "
            "target_avatar_match: ¿Para quién es perfecto "
            "este offer?"
        ),
        coverage_threshold=0.8,
    ),
    InterviewBlock(
        id="psychology",
        label="Psicología de Venta",
        campos_objetivo=[
            "marketing_pain_points",
            "marketing_desires",
            "objections",
        ],
        prompt_context=(
            "Mapea la psicología de compra: qué dolor "
            "activa la búsqueda, qué deseo motiva "
            "la acción, qué objeciones frenan la decisión. "
            "Para cada objeción, identifica trigger_phrases "
            "(frases textuales del prospecto), "
            "el tipo (precio, tiempo, confianza, pareja, "
            "etc.), la estrategia de rebuttal, "
            "y la respuesta concreta. "
            "Los pain_points deben ser dolores que el "
            "prospecto reconoce y busca activamente "
            "resolver. "
            "Los desires deben conectar con aspiraciones "
            "profundas, no superficiales."
        ),
        coverage_threshold=0.8,
    ),
]

# ---------------------------------------------------------------------------
# Archetype-specific blocks — one per archetype (position 3)
# ---------------------------------------------------------------------------

ARCHETYPE_BLOCKS: dict[str, InterviewBlock] = {
    "producto": InterviewBlock(
        id="product_details",
        label="Detalles del Producto Digital",
        campos_objetivo=[
            "specific_details",
            "format_hint",
            "access_duration_text",
            "instructors",
        ],
        prompt_context=(
            "Captura los detalles específicos del PRODUCTO DIGITAL. "
            "Formato: ¿curso, ebook, template, software, físico? "
            "¿Cómo se entrega el acceso? (URL, descarga, envío) "
            "¿Tiene DRM o es descargable libremente? "
            "Tiempo estimado de consumo. "
            "Si tiene componente físico: logística, peso, inventario. "
            "Instructores o autores relevantes si aplica."
        ),
        coverage_threshold=0.7,
    ),
    "programa": InterviewBlock(
        id="program_details",
        label="Detalles del Programa",
        campos_objetivo=[
            "specific_details",
            "has_editions",
            "instructors",
            "access_duration_text",
        ],
        prompt_context=(
            "Captura los detalles del PROGRAMA formativo. "
            "Currículum: módulos, temas por módulo, secuencia pedagógica. "
            "Estructura: ¿cohorts en vivo, asincrónico, híbrido? "
            "Fechas de inicio/fin y límite de cupos. "
            "¿Hay sesiones en vivo? Frecuencia y duración. "
            "¿Incluye certificación, comunidad, tareas? "
            "Instructores o coaches del programa."
        ),
        coverage_threshold=0.7,
    ),
    "servicio": InterviewBlock(
        id="service_details",
        label="Detalles del Servicio",
        campos_objetivo=[
            "specific_details",
            "has_editions",
            "instructors",
            "support_duration_days",
        ],
        prompt_context=(
            "Captura los detalles del SERVICIO profesional. "
            "Categoría: consultoría, agencia, freelance, coaching. "
            "Modo de interacción: síncrono, asíncrono, mixto. "
            "Frecuencia de entregables y rondas de revisión. "
            "Duración del contrato o engagement mínimo. "
            "¿Requiere brief de onboarding o firma de contrato? "
            "Métricas de éxito y SLA si aplica."
        ),
        coverage_threshold=0.7,
    ),
    "membresia": InterviewBlock(
        id="subscription_details",
        label="Detalles de la Membresía",
        campos_objetivo=[
            "specific_details",
            "access_duration_text",
            "instructors",
            "includes_offers",
        ],
        prompt_context=(
            "Captura los detalles de la MEMBRESÍA o suscripción. "
            "Ciclo de facturación: mensual, trimestral, anual. "
            "Nombre del tier y plataforma de acceso. "
            "¿Incluye período de prueba? Duración. "
            "Frecuencia de actualización de contenido. "
            "¿Hay eventos de networking o invitados expertos? "
            "Política de cancelación. "
            "¿Qué otros offers incluye o da acceso como beneficio?"
        ),
        coverage_threshold=0.7,
    ),
    "experiencia": InterviewBlock(
        id="event_details",
        label="Detalles de la Experiencia / Evento",
        campos_objetivo=[
            "specific_details",
            "has_editions",
            "instructors",
            "access_duration_text",
        ],
        prompt_context=(
            "Captura los detalles de la EXPERIENCIA o evento. "
            "Fechas, zona horaria y tipo de locación (virtual/presencial/híbrido). "
            "Si es presencial: venue, ciudad, traslado, alojamiento. "
            "Si es virtual: URL de sala y grabación. "
            "Agenda de highlights — momentos clave del evento. "
            "Ponentes, facilitadores o guests. "
            "Dress code y restricciones dietéticas si aplica."
        ),
        coverage_threshold=0.7,
    ),
}

# ---------------------------------------------------------------------------
# Universal final blocks -- value stack, pricing, closing (positions 4-6)
# ---------------------------------------------------------------------------

# Archetypes that launch by editions and therefore need a "first edition"
# date captured before we close the interview. Matches the catalog flag
# ``ArchetypeCapabilities.supports_editions``; duplicated here as a literal
# set to avoid a runtime import loop (domain → domain).
_EDITION_SUPPORTING_ARCHETYPES: frozenset[str] = frozenset({"programa", "servicio", "experiencia"})

# Appended as the FINAL block for edition-supporting archetypes (Phase 7).
# The field ``first_edition.start_date`` is optional at the interview layer;
# the follow-up procedure either publishes the placeholder edition with the
# captured date (→ UPCOMING + PUBLIC) or leaves it as a DRAFT placeholder.
FIRST_EDITION_DATE_BLOCK = InterviewBlock(
    id="first_edition_date",
    label="Fecha de la primera edición",
    campos_objetivo=[
        "first_edition.start_date",
        "first_edition.end_date",
        "first_edition.location_override",
    ],
    prompt_context=(
        "Antes de cerrar, pregunta por la FECHA DE LA PRIMERA {edition_noun_es}. "
        "Si el usuario ya mencionó una fecha en bloques previos, usala como default. "
        "Ofrecé tres opciones de respuesta: (1) la fecha sugerida por IA, "
        "(2) un date picker, (3) saltar con warning 'La edición quedará privada "
        "y los leads van a waitlist hasta que definas fecha'. "
        "Esta información permite al Sales Agent ofrecer la edición a leads. "
        "Si el usuario decide saltar, guardar null en first_edition.start_date."
    ),
    coverage_threshold=0.3,  # low — skipping is valid, just defaulting to placeholder DRAFT
)


_UNIVERSAL_FINAL: list[InterviewBlock] = [
    InterviewBlock(
        id="value_stack",
        label="Value Stack y Entregables",
        campos_objetivo=[
            "deliverables",
            "includes_offers",
            "access_duration_text",
            "support_duration_days",
        ],
        prompt_context=(
            "Construye el VALUE STACK: qué recibe el "
            "cliente, cuánto vale cada pieza, "
            "cómo anclar el precio. "
            "Cada deliverable necesita: nombre atractivo, "
            "formato, cantidad, y valor percibido "
            "individual. "
            "La suma de valores individuales > precio "
            "total = oferta irresistible. "
            "¿Incluye acceso a otros offers? "
            "¿Por cuánto tiempo tiene acceso? "
            "¿Cuántos días de soporte post-compra?"
        ),
        coverage_threshold=0.7,
    ),
    InterviewBlock(
        id="pricing",
        label="Pricing y Garantía",
        campos_objetivo=[
            "pricing_options",
            "price_pay_in_full",
            "guarantee_type",
            "guarantee_terms",
        ],
        prompt_context=(
            "Diseña la estructura de precio, opciones de pago, y garantía que reduzca "
            "riesgo percibido. "
            "Aplica anclaje: ¿cuál es el valor real de lo que incluye? "
            "Fraccionamiento: ¿cómo hacer cuotas accesibles? "
            "Comparación: vs el costo de NO resolver el problema. "
            "Garantía: condicional (requiere acción) vs incondicional (money-back). "
            "Alinear tipo de garantía con delivery_model y archetype."
        ),
        coverage_threshold=0.7,
    ),
    InterviewBlock(
        id="closing",
        label="Cierre y Acción",
        campos_objetivo=[
            "onboarding_action",
            "prerequisites",
            "requires_application",
            "anti_avatar_keywords",
        ],
        prompt_context=(
            "Define el CIERRE: proceso de onboarding, "
            "calificación, urgencia/escasez legítima. "
            "¿Qué pasa inmediatamente después de comprar? "
            "(email de acceso, llamada kickoff, etc.) "
            "¿Hay prerrequisitos? ¿Se requiere aplicación "
            "o es compra directa? "
            "Anti-avatar: ¿para quién NO es este offer? "
            "Define keywords que descalifican "
            "para que el Sales Agent pueda filtrar "
            "proactivamente."
        ),
        coverage_threshold=0.6,
    ),
]

# ---------------------------------------------------------------------------
# Static config — 6 blocks, kept for backward compatibility
# Original order: identity_strategy, promise, psychology, pricing, value_stack, closing
# ---------------------------------------------------------------------------

_PRICING_BLOCK = _UNIVERSAL_FINAL[1]  # pricing
_VALUE_STACK_BLOCK = _UNIVERSAL_FINAL[0]  # value_stack
_CLOSING_BLOCK = _UNIVERSAL_FINAL[2]  # closing

OFFER_BLOCKS: list[InterviewBlock] = [
    *_UNIVERSAL_FIRST,
    _PRICING_BLOCK,
    _VALUE_STACK_BLOCK,
    _CLOSING_BLOCK,
]

OFFER_INTERVIEW_CONFIG = InterviewConfig(
    domain="offer",
    objetivo=("Diseñar un offer irresistible, diferenciado, y alineado con el ladder de valor del negocio"),
    bloques=OFFER_BLOCKS,
    output_schema_path="modules.offer.domain.offer.Offer",
    datos_previos_fields=[
        "public_name",
        "archetype",
        "pricing_options",
        "headline_promise",
    ],
    tono=("Eres un estratega de producto con experiencia en info-productos, SaaS, y servicios premium."),
    expertise_template="offer_expertise",
    document_extraction_template="offer_doc_extraction",
    rag_collection=None,
    initial_research_enabled=True,
    context_loader="offer_context",
)

register_interview_config("offer", OFFER_INTERVIEW_CONFIG)


# ---------------------------------------------------------------------------
# Dynamic factory — 7 blocks, archetype-aware
# ---------------------------------------------------------------------------


def get_offer_interview_config(archetype: str) -> InterviewConfig:
    """Return a dynamic 7-block InterviewConfig adapted to the offer's archetype.

    Block layout:
      0. identity_strategy  ── universal first
      1. promise             ── universal first
      2. psychology          ── universal first
      3. <archetype_block>   ── archetype-specific (position 3)
      4. value_stack         ── universal final
      5. pricing             ── universal final
      6. closing             ── universal final

    For unknown archetypes falls back to the static OFFER_INTERVIEW_CONFIG.
    """
    archetype_block = ARCHETYPE_BLOCKS.get(archetype)
    if archetype_block is None:
        return OFFER_INTERVIEW_CONFIG

    dynamic_bloques: list[InterviewBlock] = [
        *_UNIVERSAL_FIRST,
        archetype_block,
        *_UNIVERSAL_FINAL,
    ]
    # Phase 7: edition-supporting archetypes get one extra final block so the
    # interview ends with a concrete date the Sales Agent can promise (or an
    # explicit "skip" that keeps the placeholder edition DRAFT + PRIVATE).
    if archetype in _EDITION_SUPPORTING_ARCHETYPES:
        dynamic_bloques.append(FIRST_EDITION_DATE_BLOCK)

    return InterviewConfig(
        domain=OFFER_INTERVIEW_CONFIG.domain,
        objetivo=OFFER_INTERVIEW_CONFIG.objetivo,
        bloques=dynamic_bloques,
        output_schema_path=OFFER_INTERVIEW_CONFIG.output_schema_path,
        datos_previos_fields=OFFER_INTERVIEW_CONFIG.datos_previos_fields,
        tono=OFFER_INTERVIEW_CONFIG.tono,
        expertise_template=OFFER_INTERVIEW_CONFIG.expertise_template,
        document_extraction_template=OFFER_INTERVIEW_CONFIG.document_extraction_template,
        rag_collection=OFFER_INTERVIEW_CONFIG.rag_collection,
        initial_research_enabled=OFFER_INTERVIEW_CONFIG.initial_research_enabled,
        context_loader=OFFER_INTERVIEW_CONFIG.context_loader,
        max_mensajes=OFFER_INTERVIEW_CONFIG.max_mensajes,
        supported_file_types=OFFER_INTERVIEW_CONFIG.supported_file_types,
    )
