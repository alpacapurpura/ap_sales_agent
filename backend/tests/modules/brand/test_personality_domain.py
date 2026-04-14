"""Tests for PersonalityProfile domain models — DimensionContract, Compiler, Presets."""

import pytest

from src.modules.brand.domain.personality import (
    PERSONALITY_PRESETS,
    DimensionContract,
    DimensionLevel,
    LinguisticPatterns,
    PersonalityCompiler,
    PersonalityDimensions,
    SampleExchange,
)


class TestDimensionContract:
    """DimensionContract resolves numeric values to concrete behavioral rules."""

    def test_energy_very_low_resolves_correctly(self):
        level = DimensionContract.resolve("energy", 0.1)
        assert level.name == "muy_baja"
        assert "Sin exclamaciones" in level.instruction
        assert len(level.negative_constraints) > 0
        assert "NUNCA uses signos de exclamación" in level.negative_constraints[0]

    def test_energy_high_resolves_correctly(self):
        level = DimensionContract.resolve("energy", 0.7)
        assert level.name == "alta"
        assert "exclamaciones frecuentes" in level.instruction.lower()
        assert level.negative_constraints == []

    def test_warmth_intimate_resolves_correctly(self):
        level = DimensionContract.resolve("warmth", 0.9)
        assert level.name == "intima"
        assert "yo también pasé por eso" in level.instruction.lower()

    def test_humor_serious_has_negative_constraints(self):
        level = DimensionContract.resolve("humor", 0.1)
        assert level.name == "serio"
        assert any("jaja" in c.lower() for c in level.negative_constraints)

    def test_all_dimensions_have_5_levels(self):
        for dim_name in ["energy", "warmth", "humor", "expressiveness", "narrative", "verbosity"]:
            levels = DimensionContract.get_levels(dim_name)
            assert len(levels) == 5, f"{dim_name} should have 5 levels"

    def test_boundary_values_resolve_to_correct_level(self):
        # 0.0 = first level, 0.2 = second level, etc.
        assert DimensionContract.resolve("energy", 0.0).name == "muy_baja"
        assert DimensionContract.resolve("energy", 0.2).name == "baja"
        assert DimensionContract.resolve("energy", 0.4).name == "media"
        assert DimensionContract.resolve("energy", 0.6).name == "alta"
        assert DimensionContract.resolve("energy", 0.8).name == "electrica"
        # Edge: exactly 1.0
        assert DimensionContract.resolve("energy", 1.0).name == "electrica"

    def test_invalid_dimension_raises(self):
        with pytest.raises(ValueError, match="Unknown dimension"):
            DimensionContract.resolve("invalid_dim", 0.5)

    def test_out_of_range_clamps(self):
        level_low = DimensionContract.resolve("energy", -0.5)
        assert level_low.name == "muy_baja"
        level_high = DimensionContract.resolve("energy", 1.5)
        assert level_high.name == "electrica"


class TestPersonalityCompiler:
    """PersonalityCompiler produces 5-block system_instruction from profile data."""

    @pytest.fixture
    def warm_dimensions(self):
        return PersonalityDimensions(
            energy=0.65,
            warmth=0.85,
            humor=0.6,
            expressiveness=0.7,
            narrative=0.5,
            verbosity=0.4,
        )

    @pytest.fixture
    def minimalist_dimensions(self):
        return PersonalityDimensions(
            energy=0.15,
            warmth=0.25,
            humor=0.1,
            expressiveness=0.1,
            narrative=0.2,
            verbosity=0.15,
        )

    @pytest.fixture
    def patterns(self):
        return LinguisticPatterns(
            emoji_style="frequent",
            favorite_emojis=["😊", "🔥", "💪"],
            greeting="¡Hola! ¿Cómo estás?",
            farewell="¡Un abrazo!",
            filler_phrases=["mira", "te cuento"],
            avg_message_length="short",
            punctuation_style="expressive",
            humor_type="playful",
            unique_vocabulary=["genial", "increíble"],
        )

    @pytest.fixture
    def sample_exchanges(self):
        return [
            SampleExchange(
                context="greeting",
                other_message="Hola, buenas tardes",
                author_response="¡Hola! ¿Cómo estás? 😊 Qué bueno que me escribes!",
            ),
            SampleExchange(
                context="objection",
                other_message="Es muy caro",
                author_response="Te entiendo perfecto, mira, te cuento lo que le pasó a Laura 💛",
            ),
        ]

    def test_compile_produces_5_blocks(self, warm_dimensions, patterns, sample_exchanges):
        result = PersonalityCompiler.compile(warm_dimensions, patterns, sample_exchanges)
        assert "REGLAS DE PERSONALIDAD" in result or "energía" in result.lower()
        assert "HUELLA LINGÜÍSTICA" in result or "mira" in result
        assert "NUNCA HACES" in result or "REGLA SUPREMA" in result
        assert "¡Hola! ¿Cómo estás? 😊" in result  # sample exchange
        assert "ESTA ES TU VOZ" in result  # identity anchor

    def test_compile_includes_negative_constraints_for_low_dims(
        self, minimalist_dimensions, patterns, sample_exchanges
    ):
        result = PersonalityCompiler.compile(minimalist_dimensions, patterns, sample_exchanges)
        assert "NUNCA" in result
        assert "emojis" in result.lower()  # expressiveness=0.1 → no emojis
        assert "exclamación" in result.lower() or "exclamaciones" in result.lower()

    def test_compile_no_negative_constraints_for_high_dims(self, warm_dimensions, patterns, sample_exchanges):
        result = PersonalityCompiler.compile(warm_dimensions, patterns, sample_exchanges)
        # warm_close has no dims < 0.3, so NUNCA section should be minimal
        nunca_count = result.count("NUNCA")
        # Only the anchor at the end uses NUNCA
        assert nunca_count <= 3  # anchor has 1-2 NUNCAs

    def test_two_presets_produce_different_instructions(self):
        warm = PERSONALITY_PRESETS["warm_close"]
        mini = PERSONALITY_PRESETS["minimalist"]
        warm_result = PersonalityCompiler.compile(
            warm.dimensions,
            warm.linguistic_patterns,
            warm.sample_exchanges,
        )
        mini_result = PersonalityCompiler.compile(
            mini.dimensions,
            mini.linguistic_patterns,
            mini.sample_exchanges,
        )
        # They should be substantially different
        assert warm_result != mini_result
        assert "😊" in warm_result
        assert "😊" not in mini_result
        assert "NUNCA uses emojis" in mini_result
        assert "NUNCA uses emojis" not in warm_result


class TestPresets:
    """Verify all 6 presets are complete with 3 pillars."""

    def test_all_6_presets_exist(self):
        assert len(PERSONALITY_PRESETS) == 6
        expected_keys = {"warm_close", "electric", "serene", "direct", "narrative", "minimalist"}
        assert set(PERSONALITY_PRESETS.keys()) == expected_keys

    @pytest.mark.parametrize("key", ["warm_close", "electric", "serene", "direct", "narrative", "minimalist"])
    def test_preset_has_3_pillars(self, key):
        preset = PERSONALITY_PRESETS[key]
        # Pilar 1: Dimensions
        assert preset.dimensions is not None
        assert 0.0 <= preset.dimensions.energy <= 1.0
        # Pilar 2: Linguistic patterns
        assert preset.linguistic_patterns is not None
        assert len(preset.linguistic_patterns.filler_phrases) > 0
        assert preset.linguistic_patterns.greeting != ""
        # Pilar 3: Sample exchanges
        assert len(preset.sample_exchanges) >= 5
        contexts = {e.context for e in preset.sample_exchanges}
        assert "greeting" in contexts
        assert "objection" in contexts

    @pytest.mark.parametrize("key", ["warm_close", "electric", "serene", "direct", "narrative", "minimalist"])
    def test_preset_compiles_without_error(self, key):
        preset = PERSONALITY_PRESETS[key]
        result = PersonalityCompiler.compile(
            preset.dimensions,
            preset.linguistic_patterns,
            preset.sample_exchanges,
        )
        assert len(result) > 200  # Non-trivial output
        assert "ESTA ES TU VOZ" in result
