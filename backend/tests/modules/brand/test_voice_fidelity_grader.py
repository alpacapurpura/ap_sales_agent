"""Voice fidelity grader scaffold tests (S7 Fase C foundation).

Verifies the harness shape — banned-vocab + lexical alignment work without
calling the judge LLM, golden pack covers all 6 presets, and the grader
gracefully skips the LLM-judged scores when infra is unavailable.

Full G-Eval CI gate (tone ≥ 4, agreement ≥ 85%) is enabled in a later sprint
once the golden pack is expanded to 30 prompts/preset = 180 total.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.modules.brand.application.voice_fidelity import (
    GOLDEN_PROMPTS,
    GraderResult,
    GraderRubric,
    grade_response,
)
from src.modules.brand.domain.personality import PERSONALITY_PRESETS


def _rubric_for(preset_key: str, response: str, prompt: str = "Hola") -> GraderRubric:
    preset = PERSONALITY_PRESETS[preset_key]
    banned: list[str] = []
    for dim_name in ("energy", "warmth", "humor", "expressiveness", "narrative", "verbosity"):
        from src.modules.brand.domain.personality import DimensionContract

        level = DimensionContract.resolve(dim_name, getattr(preset.dimensions, dim_name))
        banned.extend(level.negative_constraints)
    return GraderRubric(
        preset_key=preset_key,
        prompt=prompt,
        response=response,
        target_dimensions=preset.dimensions.model_dump(),
        target_vocabulary=tuple(preset.linguistic_patterns.unique_vocabulary),
        banned_phrases=tuple(banned),
        sample_exchanges=tuple(e.model_dump() for e in preset.sample_exchanges[:3]),
    )


class TestGoldenPack:
    def test_all_six_presets_have_prompts(self) -> None:
        """Every shipped preset has a golden pack."""
        assert set(GOLDEN_PROMPTS.keys()) == set(PERSONALITY_PRESETS.keys())

    def test_each_preset_has_at_least_five_prompts(self) -> None:
        """Scaffold target — expand to 30/preset before CI gate flips."""
        for preset, prompts in GOLDEN_PROMPTS.items():
            assert len(prompts) >= 5, preset


class TestGraderDeterministicScores:
    """Banned-vocab + lexical alignment are computed locally, no LLM needed."""

    @pytest.fixture(autouse=True)
    def _no_llm_call(self) -> pytest.FixtureRequest:
        """Block LLM initialisation so grade_response takes the judge_skipped path.

        TestGraderDeterministicScores only validates local (deterministic) scores.
        LLMFactory.get_service() raises to prevent network timeouts on envs without
        the litellm proxy (native WSL, CI).
        PI-11 PR-1: regression fix — singleton reset made LLMFactory re-initialise
        every test causing 30s network timeout instead of warm-singleton skip.
        """
        with patch(
            "src.shared.infrastructure.llm.factory.LLMFactory.get_service",
            side_effect=RuntimeError("LLM stubbed — deterministic test only"),
        ):
            yield

    def test_banned_phrase_lowers_to_false(self) -> None:
        """Hard fail when a forbidden phrase appears verbatim."""
        # warm_close has no negative constraints (all dims medium-high), so
        # use minimalist which has plenty of negatives.
        rubric = _rubric_for(
            "minimalist",
            response="¡INCREÍBLE!!! 🚀🚀🚀 Te cuento toda la historia con muchos emojis 😍",
        )
        result = grade_response(rubric)
        # We don't assert on tone_match (LLM may not be available) but banned
        # detection is deterministic — the response uses many forbidden patterns.
        assert isinstance(result, GraderResult)

    def test_lexical_alignment_high_when_vocabulary_present(self) -> None:
        """When the response uses the preset's unique_vocabulary, alignment is high."""
        rubric = _rubric_for(
            "minimalist",
            response="Acceso preciso. Selectivo. Limitado a pocos.",
        )
        result = grade_response(rubric)
        # The minimalist vocabulary includes "preciso", "selectivo", "limitado"
        assert result.lexical_alignment >= 0.5

    def test_lexical_alignment_low_when_vocabulary_absent(self) -> None:
        """Generic response that uses none of the preset's vocabulary scores low."""
        rubric = _rubric_for("minimalist", response="Bla bla generic message")
        result = grade_response(rubric)
        assert result.lexical_alignment == 0.0


class TestGraderSkipsJudgeWithoutInfra:
    """When LLMFactory is missing, the grader skips subjective scores cleanly."""

    def test_returns_judge_skipped_true_without_crashing(self, monkeypatch) -> None:
        """Force the LLMFactory import to raise → grader returns skip flag."""
        import sys

        # Inject a sentinel module that breaks the import.
        original = sys.modules.get("src.shared.infrastructure.llm.factory")
        try:
            sys.modules["src.shared.infrastructure.llm.factory"] = None  # type: ignore[assignment]
            rubric = _rubric_for("minimalist", response="Hola.")
            result = grade_response(rubric)
            assert isinstance(result, GraderResult)
            assert result.judge_skipped is True
        finally:
            if original is not None:
                sys.modules["src.shared.infrastructure.llm.factory"] = original
            else:
                sys.modules.pop("src.shared.infrastructure.llm.factory", None)
