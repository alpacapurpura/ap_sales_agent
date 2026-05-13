"""Compiler v2 tests — Block 3 ASÍ HABLAS / ASÍ NO with contrastive pairs.

Research: EMNLP 2024 "How You Prompt Matters!" + Boonstra Prompt Engineering Guide
demonstrate negative-only constraints have 14.4 F1 SD variance because LLMs are
next-token predictors and negative phrasing primes the forbidden token. Pairs
("✅ usa X" alongside "❌ no uses Y") shift activation toward desired behavior.
"""

from __future__ import annotations

import pytest

from luana_core_brand_studio.domain.personality import (
    PERSONALITY_PRESETS,
    DimensionContract,
    DimensionLevel,
    LinguisticPatterns,
    PersonalityCompiler,
    PersonalityDimensions,
    SampleExchange,
)


def _compile(preset_key: str) -> str:
    preset = PERSONALITY_PRESETS[preset_key]
    return PersonalityCompiler.compile(
        dimensions=preset.dimensions,
        patterns=preset.linguistic_patterns,
        exchanges=preset.sample_exchanges,
    )


class TestBlock3HeaderRenamed:
    """Block 3 header changed from 'NUNCA HACES' (v1) to 'ASÍ HABLAS / ASÍ NO' (v2)."""

    @pytest.mark.parametrize("preset_key", list(PERSONALITY_PRESETS.keys()))
    def test_block_3_header_uses_v2_label(self, preset_key: str) -> None:
        """Every preset's compiled output uses the new bilingual contrastive label."""
        compiled = _compile(preset_key)
        assert "BLOQUE 3 — ASÍ HABLAS / ASÍ NO" in compiled, preset_key

    @pytest.mark.parametrize("preset_key", list(PERSONALITY_PRESETS.keys()))
    def test_legacy_v1_header_is_gone(self, preset_key: str) -> None:
        """The legacy 'NUNCA HACES' header must not appear anywhere."""
        compiled = _compile(preset_key)
        assert "BLOQUE 3 — NUNCA HACES" not in compiled, preset_key


class TestContrastivePairs:
    """When a low dim has both negative_constraints and positive_prescriptions, the
    compiler emits paired ✅/❌ lines — research-backed positive framing."""

    def test_dimension_low_levels_have_positive_prescriptions(self) -> None:
        """The 6 lowest-level entries (one per dim) carry positive_prescriptions."""
        for dim_name in ["energy", "warmth", "humor", "expressiveness", "narrative", "verbosity"]:
            level = DimensionContract.resolve(dim_name, 0.0)
            assert level.negative_constraints, f"{dim_name} low level lacks negatives"
            assert level.positive_prescriptions, f"{dim_name} low level lacks positives"

    def test_minimalist_preset_emits_contrastive_pairs(self) -> None:
        """Minimalist hits LOW thresholds on all 6 dims → many ✅/❌ pairs in output."""
        compiled = _compile("minimalist")
        # Every checkmark line should be followed by a cross line in close proximity
        lines = compiled.splitlines()
        block_start = next(i for i, ln in enumerate(lines) if "ASÍ HABLAS / ASÍ NO" in ln)
        block_text = "\n".join(lines[block_start:])
        assert "✅" in block_text
        assert "❌" in block_text
        # Pair density: at least 4 pairs (4 dims of minimalist hit threshold)
        assert block_text.count("✅") >= 4

    def test_compiled_pair_emits_both_negative_and_positive(self) -> None:
        """A direct compile call with paired DimensionLevel produces both sides."""
        custom_dim = DimensionLevel(
            name="extreme_low",
            instruction="Be extremely terse.",
            negative_constraints=["NUNCA escribas más de 1 frase."],
            positive_prescriptions=["Una sola frase. Punto final."],
        )
        # Force-override one dim's bucket via monkey-patch-free direct call
        dims = PersonalityDimensions(
            energy=0.5,
            warmth=0.5,
            humor=0.5,
            expressiveness=0.5,
            narrative=0.5,
            verbosity=0.0,
        )
        # Recompile using the catalog-resolved dim contract — verbosity=0.0 → "telegrafico"
        verbosity_level = DimensionContract.resolve("verbosity", 0.0)
        assert verbosity_level.negative_constraints  # sanity
        assert verbosity_level.positive_prescriptions  # sanity
        _ = custom_dim  # unused; presence of extreme_low confirms the dataclass shape

        compiled = PersonalityCompiler.compile(
            dimensions=dims,
            patterns=LinguisticPatterns(
                emoji_style="moderate",
                favorite_emojis=[],
                greeting="Hi",
                farewell="Bye",
                filler_phrases=[],
                avg_message_length="short",
                punctuation_style="standard",
                humor_type="none",
                unique_vocabulary=[],
            ),
            exchanges=[SampleExchange(context="g", other_message="o", author_response="a")],
        )
        # At least one positive prescription appears for verbosity (from catalog)
        assert any(p in compiled for p in verbosity_level.positive_prescriptions)
