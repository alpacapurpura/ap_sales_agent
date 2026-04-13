"""Offer interview configuration — 6 thematic blocks for irresistible offer design."""

from src.modules.copilot.domain.interview_config import (
    InterviewBlock,
    InterviewConfig,
    register_interview_config,
)

OFFER_BLOCKS = [
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
            "Define QUÉ es este offer y DÓNDE encaja en el ladder de valor. "
            "¿Es un lead magnet, un producto de activación, o la transformación core? "
            "Identifica el arquetipo (producto digital, programa, servicio, membresía, experiencia) "
            "y el modelo de entrega (DIY, Done With You, Done For You). "
            "Asegúrate de que el nombre público sea memorable, claro y orientado al resultado."
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
            "Construye la PROMESA — el resultado específico y medible que el cliente obtiene. "
            "headline_promise: MAX 15 palabras. Resultado específico + tiempo (si aplica). "
            "primary_outcome: Lo que cambia en la vida del cliente DESPUÉS. "
            "time_to_value: ¿En cuánto tiempo ven resultados? Sé realista pero motivador. "
            "target_avatar_match: ¿Para quién es perfecto este offer?"
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
            "Mapea la psicología de compra: qué dolor activa la búsqueda, qué deseo motiva "
            "la acción, qué objeciones frenan la decisión. "
            "Para cada objeción, identifica trigger_phrases (frases textuales del prospecto), "
            "el tipo (precio, tiempo, confianza, pareja, etc.), la estrategia de rebuttal, "
            "y la respuesta concreta. "
            "Los pain_points deben ser dolores que el prospecto reconoce y busca activamente resolver. "
            "Los desires deben conectar con aspiraciones profundas, no superficiales."
        ),
        coverage_threshold=0.8,
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
        id="value_stack",
        label="Value Stack y Entregables",
        campos_objetivo=[
            "deliverables",
            "includes_offers",
            "access_duration_text",
            "support_duration_days",
        ],
        prompt_context=(
            "Construye el VALUE STACK: qué recibe el cliente, cuánto vale cada pieza, "
            "cómo anclar el precio. "
            "Cada deliverable necesita: nombre atractivo, formato, cantidad, y valor percibido individual. "
            "La suma de valores individuales > precio total = oferta irresistible. "
            "¿Incluye acceso a otros offers? ¿Por cuánto tiempo tiene acceso? "
            "¿Cuántos días de soporte post-compra?"
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
            "Define el CIERRE: proceso de onboarding, calificación, urgencia/escasez legítima. "
            "¿Qué pasa inmediatamente después de comprar? (email de acceso, llamada kickoff, etc.) "
            "¿Hay prerrequisitos? ¿Se requiere aplicación o es compra directa? "
            "Anti-avatar: ¿para quién NO es este offer? Define keywords que descalifican "
            "para que el Sales Agent pueda filtrar proactivamente."
        ),
        coverage_threshold=0.6,
    ),
]

OFFER_INTERVIEW_CONFIG = InterviewConfig(
    domain="offer",
    objetivo=(
        "Diseñar un offer irresistible, diferenciado, y alineado "
        "con el ladder de valor del negocio"
    ),
    bloques=OFFER_BLOCKS,
    output_schema_path="modules.offer.domain.offer.Offer",
    datos_previos_fields=[
        "public_name",
        "archetype",
        "pricing_options",
        "headline_promise",
    ],
    tono=(
        "Eres un estratega de producto con experiencia en info-productos, "
        "SaaS, y servicios premium."
    ),
    expertise_template="offer_expertise",
    document_extraction_template="offer_doc_extraction",
    rag_collection=None,
    initial_research_enabled=True,
    context_loader="offer_context",
)

register_interview_config("offer", OFFER_INTERVIEW_CONFIG)
