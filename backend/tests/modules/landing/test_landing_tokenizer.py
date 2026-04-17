"""Pure-function tests for ``substitute_tokens`` (Phase 3).

The tokenizer walks mixed dict / list / str trees (exactly the shape of
``LandingPageConfig.model_dump()`` plus arbitrary Puck block trees) and
substitutes only the three edition-level tokens. All non-string leaves
MUST pass through untouched so numeric, boolean, and None values survive
a round-trip.
"""

from __future__ import annotations

from src.modules.landing.application.tokenizer import substitute_tokens


class TestSubstituteTokens:
    def test_replaces_known_token_in_string(self) -> None:
        out = substitute_tokens("Lanzamiento el {{start_date}}", {"start_date": "15 de mayo"})
        assert out == "Lanzamiento el 15 de mayo"

    def test_unknown_tokens_are_preserved(self) -> None:
        out = substitute_tokens("{{unknown}} y {{start_date}}", {"start_date": "X"})
        assert out == "{{unknown}} y X"

    def test_non_string_leaves_untouched(self) -> None:
        subs = {"start_date": "X"}
        assert substitute_tokens(42, subs) == 42
        assert substitute_tokens(None, subs) is None
        flag_value: bool = True
        assert substitute_tokens(flag_value, subs) is True

    def test_walks_lists(self) -> None:
        out = substitute_tokens(
            ["hola {{start_date}}", "fin {{end_date}}", 99],
            {"start_date": "lun", "end_date": "vie"},
        )
        assert out == ["hola lun", "fin vie", 99]

    def test_walks_nested_dict(self) -> None:
        out = substitute_tokens(
            {
                "headline": "Evento {{start_date}}",
                "meta": {
                    "location": "{{location}}",
                    "tags": ["{{start_date}}", "static"],
                },
            },
            {"start_date": "mayo 15", "location": "Lima"},
        )
        assert out == {
            "headline": "Evento mayo 15",
            "meta": {
                "location": "Lima",
                "tags": ["mayo 15", "static"],
            },
        }

    def test_is_non_mutating(self) -> None:
        source = {"h": "{{start_date}}", "items": ["{{end_date}}"]}
        _ = substitute_tokens(source, {"start_date": "A", "end_date": "B"})
        # Original must not be touched — deep copy semantics.
        assert source == {"h": "{{start_date}}", "items": ["{{end_date}}"]}

    def test_empty_substitutions_is_identity(self) -> None:
        src = {"h": "{{start_date}}"}
        assert substitute_tokens(src, {}) == {"h": "{{start_date}}"}

    def test_only_whitelisted_tokens_are_recognised(self) -> None:
        """We intentionally do NOT process free-form ``{{anything}}``.

        Guardrail against runaway substitution inside user-authored copy
        that happens to contain braces.
        """
        out = substitute_tokens(
            "{{date}} vs {{start_date}}",
            {"start_date": "OK", "date": "NEVER"},
        )
        # ``{{date}}`` is NOT in the token allowlist — unchanged.
        assert out == "{{date}} vs OK"
