"""Tests for ``url_inspiration_analyzer`` — pure parse + analyze."""

from __future__ import annotations

import pytest

from luana_core_copilot.application.tools.url_inspiration_analyzer import (
    InspirationAnalysis,
    analyze,
    parse_llm_output,
)


class TestParseLlmOutput:
    def test_parses_well_formed_json(self) -> None:
        raw = (
            '{"slug": "mujer-coraje", '
            '"summary": "Programa de transformación para mujeres adultas.", '
            '"brand_relevance_score": 0.8, '
            '"sub_elements": {"testimonials": ["t1"], "ctas": ["Inscribirme"], '
            '"value_props": ["12 semanas"], "visual_cues": ["dorado-vino"]}}'
        )
        out = parse_llm_output(raw, fallback_domain="example.com")
        assert out.slug == "mujer-coraje"
        assert "transformación" in out.summary
        assert out.brand_relevance_score == pytest.approx(0.8)
        assert out.sub_elements["testimonials"] == ["t1"]

    def test_handles_fenced_code_block(self) -> None:
        raw = '```json\n{"slug": "x", "summary": "Test", "brand_relevance_score": 0.5, "sub_elements": {}}\n```'
        out = parse_llm_output(raw, fallback_domain="x.com")
        assert out.slug == "x"

    def test_handles_prose_around_json(self) -> None:
        raw = (
            "Aquí va el análisis:\n"
            '{"slug": "y", "summary": "Aquí", "brand_relevance_score": 0.6, '
            '"sub_elements": {}}\n'
            "Eso es todo."
        )
        out = parse_llm_output(raw, fallback_domain="y.com")
        assert out.slug == "y"

    def test_clamps_score_above_one(self) -> None:
        raw = '{"slug":"x","summary":"t","brand_relevance_score": 5, "sub_elements": {}}'
        out = parse_llm_output(raw, fallback_domain="x.com")
        assert out.brand_relevance_score == 1.0

    def test_clamps_score_below_zero(self) -> None:
        raw = '{"slug":"x","summary":"t","brand_relevance_score": -1, "sub_elements": {}}'
        out = parse_llm_output(raw, fallback_domain="x.com")
        assert out.brand_relevance_score == 0.0

    def test_invalid_json_returns_fallback(self) -> None:
        out = parse_llm_output("not-json-at-all", fallback_domain="ex.com")
        assert out.brand_relevance_score == 0.3
        assert "ex-com" in out.slug or "inspiracion" in out.slug

    def test_truncates_long_summary(self) -> None:
        big = "a" * 1500
        raw = f'{{"slug":"x","summary":"{big}","brand_relevance_score":0.5,"sub_elements":{{}}}}'
        out = parse_llm_output(raw, fallback_domain="x.com")
        assert len(out.summary) <= 600

    def test_strips_voseo(self) -> None:
        raw = (
            '{"slug":"x","summary":"Esta marca te enseña qué tenés que hacer y mirá.",'
            '"brand_relevance_score":0.5,"sub_elements":{}}'
        )
        out = parse_llm_output(raw, fallback_domain="x.com")
        assert "tenés" not in out.summary.lower()
        assert "tienes" in out.summary

    def test_slug_falls_back_to_domain(self) -> None:
        raw = '{"slug":"","summary":"x","brand_relevance_score":0.5,"sub_elements":{}}'
        out = parse_llm_output(raw, fallback_domain="mujer-coraje.com")
        assert "mujer" in out.slug

    def test_sub_elements_normalized(self) -> None:
        raw = (
            '{"slug":"x","summary":"x","brand_relevance_score":0.5,'
            '"sub_elements":{"testimonials": ["t1"," ","t2"], "ctas": null}}'
        )
        out = parse_llm_output(raw, fallback_domain="x.com")
        assert out.sub_elements["testimonials"] == ["t1", "t2"]
        assert out.sub_elements["ctas"] == []
        assert out.sub_elements["value_props"] == []


class _StubLLM:
    """Capture `messages` (and optional `config`) and return a canned response."""

    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.calls: list[list] = []
        self.configs: list[dict | None] = []

    def invoke(self, messages: list, *, config: dict | None = None) -> object:
        self.calls.append(messages)
        self.configs.append(config)

        class _Resp:
            def __init__(self, text: str) -> None:
                self.content = text

        return _Resp(self.response_text)


class TestAnalyze:
    def test_full_pipeline_with_stub_llm(self) -> None:
        stub = _StubLLM(
            response_text=(
                '{"slug": "mujer-coraje", "summary": "Programa de despertar.", '
                '"brand_relevance_score": 0.7, "sub_elements": {"testimonials": ["t"]}}'
            ),
        )
        result = analyze(
            url="https://mujercoraje.com",
            why="competencia directa",
            brand_lighthouse="Marca: Visionarias. Audiencia: mujeres 35-55. Tono: humano, retador.",
            page_title="Mujer Coraje · Despertar",
            content_md="# Despertar\nPrograma de transformación.",
            fallback_domain="mujercoraje.com",
            llm=stub,
        )
        assert isinstance(result, InspirationAnalysis)
        assert result.slug == "mujer-coraje"
        assert result.brand_relevance_score == pytest.approx(0.7)
        # System + user message in payload
        assert len(stub.calls) == 1
        msgs = stub.calls[0]
        assert any("Visionarias" in m.content for m in msgs)
        assert any("Despertar" in m.content for m in msgs)

    def test_works_without_lighthouse(self) -> None:
        stub = _StubLLM(
            '{"slug":"x","summary":"x","brand_relevance_score":0.5,"sub_elements":{}}',
        )
        result = analyze(
            url="https://x.com",
            why="",
            brand_lighthouse=None,
            page_title=None,
            content_md="contenido",
            fallback_domain="x.com",
            llm=stub,
        )
        assert result.brand_relevance_score == pytest.approx(0.5)
        # Lighthouse fallback message included in user prompt
        assert any("no hay brand lighthouse" in m.content for m in stub.calls[0])

    def test_invoke_carries_internal_tag(self) -> None:
        """TP3 B1 — analyzer MUST tag its LLM invocation so the chat
        orchestrator drops the JSON tokens before they reach the user's
        block_delta channel."""
        stub = _StubLLM(
            '{"slug":"x","summary":"x","brand_relevance_score":0.5,"sub_elements":{}}',
        )
        analyze(
            url="https://x.com",
            why="",
            brand_lighthouse=None,
            page_title=None,
            content_md="contenido",
            fallback_domain="x.com",
            llm=stub,
        )
        assert stub.configs and stub.configs[0] is not None
        assert "copilot:internal" in stub.configs[0].get("tags", [])
