"""Brand Studio interview configuration — 5 thematic blocks."""

from src.modules.copilot.domain.interview_config import (
    InterviewBlock,
    InterviewConfig,
    register_interview_config,
)

BRAND_INTERVIEW_CONFIG = InterviewConfig(
    domain="brand",
    objetivo="Completar Brand Studio",
    bloques=[
        InterviewBlock(
            id="identidad",
            label="Tu Identidad",
            campos_objetivo=[
                "story.origin_story",
                "story.mission",
                "story.vision",
                "identity.brand_name",
                "identity.industry",
                "positioning.values",
            ],
            prompt_context=(
                "Explora el origen del negocio, la motivación del fundador, y los valores "
                "que guían las decisiones. Pregunta qué problema vieron que nadie resolvía. "
                "Redacta origin_story como narrativa en tercera persona (problema→epifanía→acción). "
                "Misión: verbo + beneficiario + resultado transformador."
            ),
        ),
        InterviewBlock(
            id="posicionamiento",
            label="Tu Posicionamiento",
            campos_objetivo=[
                "positioning.uvp",
                "positioning.discriminator",
                "positioning.competitors",
                "positioning.consumer_insight",
                "positioning.benefits_functional",
                "positioning.benefits_emotional",
            ],
            prompt_context=(
                "Descubre qué hace diferente al negocio. ¿Contra quién compite? "
                "¿Qué dicen los clientes que hace distinto? Usa Brand Love Key: "
                "beneficio funcional, emocional, character, reason to believe. "
                "UVP formato: Para [quién] que [necesita], [producto] es [categoría] que [beneficio]."
            ),
        ),
        InterviewBlock(
            id="narrativa",
            label="Tu Narrativa",
            campos_objetivo=[
                "narrative.hero",
                "narrative.problem",
                "narrative.guide",
                "narrative.plan",
                "narrative.cta",
                "narrative.outcome",
            ],
            prompt_context=(
                "Aplica StoryBrand de Donald Miller. El cliente es el héroe, "
                "la marca es el guía. Identifica el problema externo, interno y filosófico. "
                "El plan son 3-4 pasos simples. CTA directo. Success/failure outcome."
            ),
        ),
        InterviewBlock(
            id="publico",
            label="Tu Público",
            campos_objetivo=[
                "avatars.primary_demographics",
                "avatars.pain_points",
                "avatars.desires",
                "avatars.objections",
                "avatars.channels",
            ],
            prompt_context=(
                "Descubre quién es el cliente ideal. No pedir datos demográficos como encuesta — "
                "preguntar historias: ¿quién te compra? ¿qué les duele? ¿qué sueñan lograr? "
                "¿qué les frena de comprar? ¿dónde pasan tiempo online?"
            ),
        ),
        InterviewBlock(
            id="identidad_creativa",
            label="Tu Identidad Creativa",
            campos_objetivo=[
                "identity.archetype",
                "identity.tone_of_voice",
                "identity.personality_traits",
                "visuals.visual_direction",
                "visuals.mood_keywords",
            ],
            prompt_context=(
                "Explora personalidad y tono de marca. Usa arquetipos de Jung — "
                "ofrecer alternativas con recomendación basada en lo ya capturado. "
                "Tono: cercano/formal, retador/cálido, etc. Dirección visual: keywords de mood."
            ),
        ),
    ],
    output_schema_path="modules.brand.domain.aggregates.BrandSettings",
    datos_previos_fields=[
        "identity.brand_name",
        "identity.website",
        "identity.industry",
        "story.origin_story",
        "story.mission",
    ],
    tono="consultor senior, cercano, directo, experto en branding",
    expertise_template="brand_expertise",
    rag_collection="brand_examples",
    document_extraction_template="brand_doc_extraction",
)

register_interview_config("brand", BRAND_INTERVIEW_CONFIG)
