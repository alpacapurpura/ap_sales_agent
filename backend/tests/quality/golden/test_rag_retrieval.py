"""F10 — golden RAG retrieval regression set.

Each golden row pairs a user question with: (a) the curated source doc the
KB *should* surface, and (b) the methodology the LLM is expected to cite
in its answer. The judge dimensions are RAG-specific:
``retrieval_relevance``, ``citation_accuracy``, ``answer_groundedness``,
``completeness``.

By default the judge LLM is stubbed (returns 4.0 across dims) — same
``stub default + RUN_LLM_JUDGE=1`` opt-in pattern F9 cemented. The
weekly cron flips to real NANO; CI default keeps cost at 0.

# [COPILOT-MARKETING-KB-F10]
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from src.modules.copilot.application.observability.judge import (
    DEFAULT_THRESHOLD,
    CopilotJudge,
)
from src.modules.copilot.application.tools.knowledge_search import (
    knowledge_search_impl,
)

RAG_DIMENSIONS: tuple[str, ...] = (
    "retrieval_relevance",
    "citation_accuracy",
    "answer_groundedness",
    "completeness",
)


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


GOLDENS: tuple[RagGolden, ...] = (
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


def _stub_chunks_for(golden: RagGolden) -> list[dict]:
    base = [
        {
            "id": f"{golden.id}-0",
            "score": 0.91,
            "content": golden.expected_answer_excerpt,
            "category": "framework",
            "methodology": golden.expected_methodology,
            "domain": "offer",
            "breadcrumb": [golden.expected_source_doc.replace(".md", "").replace("_", " ")],
            "source_doc": golden.expected_source_doc,
            "chunk_index": 0,
            "tags": [],
        }
    ]
    base.extend(golden.extra_chunks)
    return base


class _StubStore:
    """In-test store that returns the golden's expected chunk on demand."""

    def __init__(self, golden: RagGolden) -> None:
        self.golden = golden

    def search(
        self,
        query: str,
        *,
        domain: str | None = None,
        methodology: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        return _stub_chunks_for(self.golden)


def test_rag_dataset_size() -> None:
    """Keep at least 8 goldens covering the canonical methodologies."""
    assert len(GOLDENS) >= 8
    methodologies = {g.expected_methodology for g in GOLDENS}
    expected_subset = {"hormozi", "storybrand", "cialdini", "aida", "jtbd", "4u", "nicolify_owned"}
    assert expected_subset <= methodologies


def test_rag_golden_ids_unique() -> None:
    ids = [g.id for g in GOLDENS]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("golden", GOLDENS, ids=lambda g: g.id)
def test_knowledge_search_returns_expected_methodology(golden: RagGolden) -> None:
    """The tool wrapper must surface the methodology label so the LLM cites it."""
    store = _StubStore(golden)
    output = knowledge_search_impl(golden.question, store=store)
    assert "Cita el método" in output
    # methodology label must appear in the formatted markdown so the LLM
    # can pick it up when synthesising the answer.
    assert _METHODOLOGY_LABEL[golden.expected_methodology] in output


_METHODOLOGY_LABEL = {
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


@pytest.mark.parametrize("golden", GOLDENS, ids=lambda g: g.id)
def test_rag_answer_judged_above_threshold(golden: RagGolden, judge_llm) -> None:
    """The judged answer (with retrieved context) must score ≥3.5/5.

    Pipeline test in stub mode (default 4.0 across dims). Real NANO when
    ``RUN_LLM_JUDGE=1`` is set — surfaces genuine groundedness regressions.
    """
    judge = CopilotJudge(llm=judge_llm)
    retrieved = knowledge_search_impl(golden.question, store=_StubStore(golden))
    result = judge.evaluate(
        user_input=golden.question,
        assistant_output=golden.expected_answer_excerpt,
        context=retrieved,
    )
    assert result.passes_threshold, (
        f"RAG golden {golden.id!r} judged below threshold {DEFAULT_THRESHOLD}: "
        f"avg={result.avg_score} dims={[d.score for d in result.dimensions]} "
        f"meta={result.metadata}"
    )
