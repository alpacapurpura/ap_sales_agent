"""BuyerPersona interview configuration — 5 thematic blocks."""

from src.modules.copilot.domain.interview_config import (
    InterviewBlock,
    InterviewConfig,
    register_interview_config,
)

BUYER_PERSONA_BLOCKS = [
    InterviewBlock(
        id="demographics",
        label="Demografía y Contexto",
        campos_objetivo=[
            "demographics.age_range",
            "demographics.location",
            "demographics.occupation",
            "demographics.income_range",
            "demographics.education",
            "demographics.family_status",
        ],
        prompt_context=(
            "Comienza entendiendo QUIEN es esta persona. No hagas preguntas "
            "de encuesta — pregunta por historias. ¿Quienes son tus mejores clientes? "
            "¿Donde viven? ¿A que se dedican? ¿Que nivel de ingreso tienen? "
            "Busca patrones, no datos sueltos."
        ),
        coverage_threshold=0.8,
    ),
    InterviewBlock(
        id="psychographics",
        label="Psicografía y Personalidad",
        campos_objetivo=[
            "psychographics.values",
            "psychographics.beliefs",
            "psychographics.lifestyle",
            "psychographics.personality_traits",
            "psychographics.media_consumption",
        ],
        prompt_context=(
            "Ahora explora QUE PIENSA y SIENTE esta persona. ¿Que valoran mas? "
            "¿Que creen que es verdad sobre su situacion? ¿Como es su estilo "
            "de vida? ¿Que contenido consumen? ¿Que personalidad tienen?"
        ),
        coverage_threshold=0.7,
    ),
    InterviewBlock(
        id="pain_desire",
        label="Dolores y Deseos",
        campos_objetivo=[
            "pain_points",
            "desires",
            "pain_points.emotional_impact",
            "desires.urgency",
        ],
        prompt_context=(
            "Profundiza en los DOLORES (frustraciones, miedos, obstaculos) y "
            "DESEOS (aspiraciones, suenos, metas). Para cada dolor, pregunta "
            "como les HACE SENTIR. Para cada deseo, distingue entre lo que "
            "DICEN querer vs lo que REALMENTE quieren."
        ),
        coverage_threshold=0.8,
    ),
    InterviewBlock(
        id="objections",
        label="Objeciones y Barreras",
        campos_objetivo=[
            "objections",
            "anti_patterns",
            "purchase_triggers",
        ],
        prompt_context=(
            "Identifica las OBJECIONES: que razones da para NO comprar. "
            "Para cada objecion, busca la root_cause (la objecion real detras "
            "de la excusa). Tambien identifica los TRIGGERS que los hacen comprar "
            "y los ANTI-PATTERNS (comportamientos de personas que NO son tu cliente)."
        ),
        coverage_threshold=0.7,
    ),
    InterviewBlock(
        id="channels_journey",
        label="Canales y Journey de Compra",
        campos_objetivo=[
            "preferred_channels",
            "buyer_journey.awareness",
            "buyer_journey.consideration",
            "buyer_journey.decision",
        ],
        prompt_context=(
            "Mapea DONDE vive esta persona digitalmente y COMO compra. "
            "¿Que redes sociales usa y COMO las usa? (no solo cual, sino "
            "para que — inspiracion, investigacion, compra). Mapea su journey: "
            "¿como descubren soluciones? ¿como evaluan? ¿como deciden?"
        ),
        coverage_threshold=0.7,
    ),
]

BUYER_PERSONA_INTERVIEW_CONFIG = InterviewConfig(
    domain="buyer_persona",
    objetivo=(
        "Construir un buyer persona detallado que guie toda la "
        "estrategia de marketing y ventas"
    ),
    bloques=BUYER_PERSONA_BLOCKS,
    output_schema_path="modules.brand.domain.buyer_persona.BuyerPersona",
    datos_previos_fields=["name", "demographics", "pain_points", "desires"],
    tono=(
        "Eres un investigador de mercado experto. Haces preguntas profundas, "
        "no superficiales."
    ),
    expertise_template="buyer_persona_expertise",
    document_extraction_template="buyer_persona_doc_extraction",
    rag_collection=None,
)

register_interview_config("buyer_persona", BUYER_PERSONA_INTERVIEW_CONFIG)
