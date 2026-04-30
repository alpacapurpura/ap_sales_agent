"""TDD — Registry with 4 providers: stable order, idempotency, uniqueness.

Tests written RED first per ``tdd-mandatory.md``.

PR-2-pure-expansion-providers / PI-2 S2.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def reset_engine():
    """Reset singleton between tests."""
    from src.modules.copilot.application.suggestions.registry import _reset_for_tests

    _reset_for_tests()
    yield
    _reset_for_tests()


class TestRegistryWith4Providers:
    def test_get_default_engine_registers_4_providers(self) -> None:
        """After bootstrap, engine has exactly 4 providers."""
        from src.modules.copilot.application.suggestions.registry import get_default_engine

        engine = get_default_engine()
        assert len(engine._providers) == 4, (
            f"Expected 4 providers, got {len(engine._providers)}: {[p.provider_id for p in engine._providers]}"
        )

    def test_get_default_engine_registers_in_stable_order(self) -> None:
        """Providers registered in order: offer → brand → sales_agent → copilot."""
        from src.modules.copilot.application.suggestions.registry import get_default_engine

        engine = get_default_engine()
        ids = [p.provider_id for p in engine._providers]
        assert ids == ["offer", "brand", "sales_agent", "copilot"], (
            f"Expected stable order offer/brand/sales_agent/copilot, got {ids}"
        )

    def test_get_default_engine_idempotent(self) -> None:
        """Second call returns same engine instance."""
        from src.modules.copilot.application.suggestions.registry import get_default_engine

        engine1 = get_default_engine()
        engine2 = get_default_engine()
        assert engine1 is engine2

    def test_get_default_engine_provider_ids_unique(self) -> None:
        """All provider_ids in the engine are unique."""
        from src.modules.copilot.application.suggestions.registry import get_default_engine

        engine = get_default_engine()
        ids = [p.provider_id for p in engine._providers]
        assert len(ids) == len(set(ids)), f"Duplicate provider_ids found: {ids}"
