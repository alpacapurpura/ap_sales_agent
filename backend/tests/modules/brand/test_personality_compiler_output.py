"""Verify that PersonalityCompiler output EXACTLY matches DimensionContract promises.

These tests enforce the CONTRACT between DimensionContract and PersonalityCompiler:
every instruction, negative constraint, linguistic pattern, and sample exchange
that the contract defines MUST appear verbatim in the compiled system_instruction.
"""

import pytest

from luana_core_brand_studio.domain.personality import (
    PERSONALITY_PRESETS,
    DimensionContract,
    PersonalityCompiler,
)

# All 6 preset keys — parametrize over them everywhere
_ALL_PRESET_KEYS = list(PERSONALITY_PRESETS.keys())

# Dimension names in the order the compiler processes them
_DIMENSIONS = ["energy", "warmth", "humor", "expressiveness", "narrative", "verbosity"]

# Threshold from the compiler (dims below this emit NUNCA constraints)
_NEGATIVE_THRESHOLD = 0.3


def _compile(preset_key: str) -> str:
    """Compile the system_instruction for a given preset key."""
    preset = PERSONALITY_PRESETS[preset_key]
    return PersonalityCompiler.compile(
        dimensions=preset.dimensions,
        patterns=preset.linguistic_patterns,
        exchanges=preset.sample_exchanges,
    )


class TestCompilerContractCompliance:
    """The compiled system_instruction must honour DimensionContract exactly."""

    # ------------------------------------------------------------------
    # 1. Dimension instruction text must appear in compiled output
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("preset_key", _ALL_PRESET_KEYS)
    @pytest.mark.parametrize("dim_name", _DIMENSIONS)
    def test_compiled_instruction_contains_dimension_rules(self, preset_key: str, dim_name: str):
        """Every resolved level's instruction appears verbatim in the compiled output."""
        preset = PERSONALITY_PRESETS[preset_key]
        dim_value = getattr(preset.dimensions, dim_name)
        level = DimensionContract.resolve(dim_name, dim_value)

        compiled = _compile(preset_key)

        assert level.instruction in compiled, (
            f"Preset '{preset_key}', dim '{dim_name}' (value={dim_value:.2f}, "
            f"level='{level.name}'): instruction text not found in compiled output.\n"
            f"Expected: {level.instruction!r}"
        )

    # ------------------------------------------------------------------
    # 2. Negative constraints for low dimensions must appear
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("preset_key", _ALL_PRESET_KEYS)
    def test_compiled_instruction_contains_negative_constraints(self, preset_key: str):
        """For every dimension < 0.3, ALL its negative constraints appear in compiled output."""
        preset = PERSONALITY_PRESETS[preset_key]
        compiled = _compile(preset_key)

        for dim_name in _DIMENSIONS:
            dim_value = getattr(preset.dimensions, dim_name)
            if dim_value < _NEGATIVE_THRESHOLD:
                level = DimensionContract.resolve(dim_name, dim_value)
                for constraint in level.negative_constraints:
                    assert constraint in compiled, (
                        f"Preset '{preset_key}', dim '{dim_name}' (value={dim_value:.2f}): "
                        f"negative constraint not in compiled output.\n"
                        f"Expected: {constraint!r}"
                    )

    # ------------------------------------------------------------------
    # 3. Linguistic patterns must appear in compiled output
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("preset_key", _ALL_PRESET_KEYS)
    def test_compiled_instruction_contains_linguistic_patterns(self, preset_key: str):
        """Greeting, farewell, and all filler_phrases appear in the compiled output."""
        preset = PERSONALITY_PRESETS[preset_key]
        patterns = preset.linguistic_patterns
        compiled = _compile(preset_key)

        assert patterns.greeting in compiled, (
            f"Preset '{preset_key}': greeting {patterns.greeting!r} not in compiled output."
        )
        assert patterns.farewell in compiled, (
            f"Preset '{preset_key}': farewell {patterns.farewell!r} not in compiled output."
        )
        for phrase in patterns.filler_phrases:
            assert phrase in compiled, f"Preset '{preset_key}': filler phrase {phrase!r} not in compiled output."

    # ------------------------------------------------------------------
    # 4. First 3 sample exchange responses must appear in compiled output
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("preset_key", _ALL_PRESET_KEYS)
    def test_compiled_instruction_contains_sample_exchanges(self, preset_key: str):
        """The first 3 sample exchange author_responses appear verbatim in the compiled output."""
        preset = PERSONALITY_PRESETS[preset_key]
        compiled = _compile(preset_key)

        exchanges_to_check = preset.sample_exchanges[:3]
        assert len(exchanges_to_check) >= 3, f"Preset '{preset_key}' has fewer than 3 sample exchanges — add more."

        for i, exchange in enumerate(exchanges_to_check):
            assert exchange.author_response in compiled, (
                f"Preset '{preset_key}', exchange #{i + 1} "
                f"(context='{exchange.context}'): author_response not in compiled output.\n"
                f"Expected: {exchange.author_response!r}"
            )

    # ------------------------------------------------------------------
    # 5. Identity anchor must be present
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("preset_key", _ALL_PRESET_KEYS)
    def test_compiled_instruction_ends_with_identity_anchor(self, preset_key: str):
        """The compiled output contains the immutable identity anchor phrase."""
        compiled = _compile(preset_key)

        assert "ESTA ES TU VOZ" in compiled, (
            f"Preset '{preset_key}': identity anchor 'ESTA ES TU VOZ' not in compiled output."
        )

    # ------------------------------------------------------------------
    # 6. Minimalist has the most negative constraints
    # ------------------------------------------------------------------

    def test_minimalist_has_most_negative_constraints(self):
        """'minimalist' has more NUNCA rules than any other preset."""

        def count_nunca(preset_key: str) -> int:
            compiled = _compile(preset_key)
            return compiled.count("NUNCA")

        minimalist_count = count_nunca("minimalist")
        for preset_key in _ALL_PRESET_KEYS:
            if preset_key == "minimalist":
                continue
            other_count = count_nunca(preset_key)
            assert minimalist_count >= other_count, (
                f"minimalist has {minimalist_count} NUNCA rules, but '{preset_key}' has "
                f"{other_count} — minimalist should have the most."
            )

    # ------------------------------------------------------------------
    # 7. warm_close and minimalist are opposites
    # ------------------------------------------------------------------

    def test_warm_close_and_minimalist_are_opposites(self):
        """warm_close and minimalist produce clearly different compiled outputs."""
        warm_compiled = _compile("warm_close")
        minimalist_compiled = _compile("minimalist")

        # warm_close uses 😊 emoji; minimalist must not
        assert "😊" in warm_compiled, "warm_close should contain '😊' emoji."
        assert "😊" not in minimalist_compiled, "minimalist should NOT contain '😊' emoji."

        # minimalist has "NUNCA uses emojis" constraint; warm_close must not
        assert "NUNCA uses emojis bajo ninguna circunstancia" in minimalist_compiled, (
            "minimalist compiled output should contain the zero-emojis NUNCA rule."
        )
        assert "NUNCA uses emojis bajo ninguna circunstancia" not in warm_compiled, (
            "warm_close compiled output should NOT contain the zero-emojis NUNCA rule."
        )

        # Verbosity rules differ: minimalist is telegráfico, warm_close is conciso
        minimalist_verbosity = DimensionContract.resolve("verbosity", 0.15)
        warm_verbosity = DimensionContract.resolve("verbosity", 0.4)
        assert minimalist_verbosity.name != warm_verbosity.name, (
            "minimalist and warm_close should have different verbosity levels."
        )
        assert minimalist_verbosity.instruction in minimalist_compiled
        assert minimalist_verbosity.instruction not in warm_compiled
        assert warm_verbosity.instruction in warm_compiled
        assert warm_verbosity.instruction not in minimalist_compiled
