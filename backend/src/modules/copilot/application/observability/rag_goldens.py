"""F11.5 — RAG retrieval golden set (extracted from F10 test fixture).

Migrated from ``tests/quality/golden/test_rag_retrieval.py`` so the weekly
ARQ cron (``copilot_rag_eval.py``) can iterate the corpus without importing
test code into production.

Each ``RagGolden`` pairs a user question with the curated source doc the KB
*should* surface and the methodology the LLM is expected to cite. Tests
(stub mode in CI) and the cron (real KB on Mondays) read the same SSoT.

[COPILOT-RAG-EVAL-F11]
"""

from __future__ import annotations

from dataclasses import dataclass, field

RAG_DIMENSIONS: tuple[str, ...] = (
    "retrieval_relevance",
    "citation_accuracy",
    "answer_groundedness",
    "completeness",
)

METHODOLOGY_LABEL: dict[str, str] = {
    "nicolify_owned": "Metodología Nicolify",
    "storybrand": "StoryBrand",
    "hormozi": "Hormozi",
    "cialdini": "Cialdini",
    "aida": "AIDA",
    "pas": "PAS",
    "jtbd": "Jobs-to-be-Done",
    "fab": "FAB",
    "4u": "4U Headlines",
}


@dataclass(frozen=True, slots=True)
class RagGolden:
    """One golden RAG question with expected retrieval + citation."""

    id: str
    question: str
    expected_methodology: str
    expected_source_doc: str
    expected_answer_excerpt: str
    notes: str = ""
    extra_chunks: tuple[dict, ...] = field(default_factory=tuple)


RAG_GOLDENS: tuple[RagGolden, ...] = (
    RagGolden(
        id="hormozi-value-equation",
        question="¿Cómo construyo un grand slam offer con la value equation de Hormozi?",
        expected_methodology="hormozi",
        expected_source_doc="03_hormozi_grand_slam_offer.md",
        expected_answer_excerpt=(
            "Aplicando Hormozi value equation: dream outcome × likelihood / "
            "(time delay × effort). Un grand slam offer combina cinco bloques: "
            "promesa específica, stack de bonos por objeción, garantía agresiva, "
            "escasez genuina y urgencia activable."
        ),
    ),
    RagGolden(
        id="storybrand-hero-guide",
        question="Explícame el patrón hero/guide de StoryBrand para mi marca",
        expected_methodology="storybrand",
        expected_source_doc="01_storybrand_framework.md",
        expected_answer_excerpt=(
            "Según el BrandScript de StoryBrand: el cliente es el héroe, "
            "tu marca es el guía con autoridad y empatía. El plan corto y "
            "concreto reduce la ansiedad del héroe antes del CTA."
        ),
    ),
    RagGolden(
        id="cialdini-objection-trust",
        question="¿Qué principio de Cialdini uso para subir la confianza en mi landing?",
        expected_methodology="cialdini",
        expected_source_doc="04_cialdini_7_principios.md",
        expected_answer_excerpt=(
            "Aplicando los principios de Cialdini: social proof + authority "
            "son los dos que más mueven confianza. Testimonios específicos "
            "(con nombre y número) activan social proof; credenciales y "
            "casos demostrables construyen authority."
        ),
    ),
    RagGolden(
        id="aida-funnel-design",
        question="Diseñá el funnel para mi curso siguiendo AIDA",
        expected_methodology="aida",
        expected_source_doc="26_funnel_aida_journey.md",
        expected_answer_excerpt=(
            "Según AIDA aplicado al funnel: atención (top, anuncios + reels), "
            "interés (landing + lead magnet), deseo (email sequence + casos), "
            "acción (oferta + CTA único). Cada activo debe matchear su nivel."
        ),
    ),
    RagGolden(
        id="objection-pricing",
        question="Mi prospecto dice 'está caro'. ¿Cómo respondo?",
        expected_methodology="nicolify_owned",
        expected_source_doc="20_objection_pricing.md",
        expected_answer_excerpt=(
            "Según el playbook Nicolify de objeciones: antes de defender, "
            "diagnosticá. Pregunta '¿caro comparado con qué?'. Reframes que "
            "funcionan: costo de NO hacerlo, distribución temporal, ROI específico. "
            "Bajar precio comunica 'el precio era inflado' y daña confianza."
        ),
    ),
    RagGolden(
        id="archetype-coach-pricing",
        question="Soy coach 1-on-1 y no sé cómo cobrar — quiero subir precio sin perder clientes",
        expected_methodology="nicolify_owned",
        expected_source_doc="10_archetype_coach.md",
        expected_answer_excerpt=(
            "Según el playbook Nicolify para coaches 1-on-1: cobrá por "
            "transformación, no por hora. Subí precio cada 3-6 meses hasta "
            "equilibrar demanda. Ofrecé tier de continuidad post-programa "
            "para estabilizar ingresos."
        ),
    ),
    RagGolden(
        id="jtbd-discovery",
        question="¿Cómo descubro el verdadero job-to-be-done de mi cliente?",
        expected_methodology="jtbd",
        expected_source_doc="07_jtbd_framework.md",
        expected_answer_excerpt=(
            "Aplicando Jobs-to-be-Done: hacé entrevistas 'switch' a 5-10 "
            "clientes recientes preguntando cuándo se dieron cuenta del problema, "
            "qué probaron antes y qué tuvo que pasar para decidir. El JTBD "
            "tiene tres dimensiones: functional, emotional y social."
        ),
    ),
    RagGolden(
        id="4u-headline-rewrite",
        question="Tengo un headline que no convierte. ¿Cómo lo reescribo?",
        expected_methodology="4u",
        expected_source_doc="09_4u_headlines.md",
        expected_answer_excerpt=(
            "Aplicando el framework 4U de Masterson: pasalo por las cuatro "
            "preguntas (Useful, Urgent, Unique, Ultra-specific). Si dos están "
            "blandas, rewrite. La especificidad numérica casi siempre gana "
            "sobre la genérica."
        ),
    ),
)


__all__ = (
    "METHODOLOGY_LABEL",
    "RAG_DIMENSIONS",
    "RAG_GOLDENS",
    "RagGolden",
)
