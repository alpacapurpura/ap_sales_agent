"""Enhanced tests for SemanticRouter.

Tests intent detection edge cases, system route initialization,
multi-turn accumulation, and tenant cache invalidation.
Signal accumulation is already tested in test_safety_and_signals.py;
these tests focus on the router's own logic.
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import numpy as np

from src.modules.sales_agent.application.services.semantic_router import (
    SYSTEM_ROUTES,
    SemanticRouter,
)

# ---------------------------------------------------------------------------
# System route initialization tests
# ---------------------------------------------------------------------------


class TestSystemRoutes:
    def test_system_routes_has_expected_categories(self):
        """SYSTEM_ROUTES should contain the core intent categories."""
        expected_keys = {
            "security_breach",
            "hard_disqualification",
            "objection_money",
            "objection_partner",
            "objection_trust",
            "objection_time",
            "objection_is_ai",
            "query_logistics",
            "query_payment_methods",
            "query_program_content",
            "pain_overwhelmed",
            "pain_stagnation",
            "desire_expansion",
            "buying_signal",
            "schedule_signal",
        }
        assert expected_keys.issubset(set(SYSTEM_ROUTES.keys()))

    def test_every_route_has_at_least_one_anchor(self):
        """Each system route should have at least one trigger phrase."""
        for route, anchors in SYSTEM_ROUTES.items():
            assert len(anchors) >= 1, f"Route '{route}' has no anchors"

    def test_all_anchors_are_non_empty_strings(self):
        """All anchor phrases should be non-empty strings."""
        for route, anchors in SYSTEM_ROUTES.items():
            for anchor in anchors:
                assert isinstance(anchor, str), f"Anchor in '{route}' is not a string"
                assert len(anchor.strip()) > 0, f"Empty anchor in '{route}'"


# ---------------------------------------------------------------------------
# detect_intent edge cases (mocked model)
# ---------------------------------------------------------------------------


class TestDetectIntentEdgeCases:
    @patch.object(SemanticRouter, "_model", MagicMock())
    @patch.object(SemanticRouter, "_system_embeddings", np.random.randn(5, 10))
    @patch.object(SemanticRouter, "_system_route_names", ["a", "b", "c", "d", "e"])
    def test_returns_none_for_short_text(self):
        """Text shorter than 2 characters -> (None, 0.0)."""
        result = SemanticRouter.detect_intent("a")
        assert result == (None, 0.0)

    @patch.object(SemanticRouter, "_model", MagicMock())
    @patch.object(SemanticRouter, "_system_embeddings", np.random.randn(5, 10))
    @patch.object(SemanticRouter, "_system_route_names", ["a", "b", "c", "d", "e"])
    def test_returns_none_for_empty_text(self):
        """Empty text -> (None, 0.0)."""
        result = SemanticRouter.detect_intent("")
        assert result == (None, 0.0)

    @patch.object(SemanticRouter, "_model", MagicMock())
    @patch.object(SemanticRouter, "_system_embeddings", np.random.randn(5, 10))
    @patch.object(SemanticRouter, "_system_route_names", ["a", "b", "c", "d", "e"])
    def test_returns_none_for_whitespace_only(self):
        """Whitespace-only text -> (None, 0.0)."""
        result = SemanticRouter.detect_intent("   ")
        assert result == (None, 0.0)

    def test_returns_none_below_threshold(self):
        """Low similarity score -> None intent."""
        # Mock the model to return a query embedding with low similarity to all routes
        mock_model = MagicMock()
        # Create embeddings that will produce low cosine similarity
        route_embeddings = np.eye(5, 10)  # 5 routes, 10-dim
        query_embedding = np.zeros(10)
        query_embedding[9] = 0.1  # very weak signal in last dimension
        mock_model.embed.return_value = iter([query_embedding])

        with (
            patch.object(SemanticRouter, "_model", mock_model),
            patch.object(SemanticRouter, "_system_embeddings", route_embeddings),
            patch.object(
                SemanticRouter, "_system_route_names", ["a", "b", "c", "d", "e"]
            ),
        ):
            intent, score = SemanticRouter.detect_intent("alguna cosa random xyz")
            # Score should be below default threshold of 0.65
            assert intent is None
            assert score < 0.65


# ---------------------------------------------------------------------------
# Multi-turn accumulation tests
# ---------------------------------------------------------------------------


class TestMultiTurnAccumulation:
    def test_accumulate_across_multiple_turns(self):
        """Accumulate signals across 3 turns with different buying intents."""
        signals = []

        # Turn 1: buying_signal
        with patch.object(
            SemanticRouter, "detect_intent", return_value=("buying_signal", 0.85)
        ):
            _, _, signals = SemanticRouter.detect_and_accumulate(
                "Quiero comprar", existing_signals=signals, tenant_id=None
            )
        assert len(signals) == 1
        assert signals[0]["type"] == "buying_signal"

        # Turn 2: schedule_signal (different type, should accumulate)
        with patch.object(
            SemanticRouter, "detect_intent", return_value=("schedule_signal", 0.78)
        ):
            _, _, signals = SemanticRouter.detect_and_accumulate(
                "Quiero agendar", existing_signals=signals, tenant_id=None
            )
        assert len(signals) == 2
        assert signals[1]["type"] == "schedule_signal"

        # Turn 3: query_payment_methods (different type, should accumulate)
        with patch.object(
            SemanticRouter,
            "detect_intent",
            return_value=("query_payment_methods", 0.72),
        ):
            _, _, signals = SemanticRouter.detect_and_accumulate(
                "Como pago?", existing_signals=signals, tenant_id=None
            )
        assert len(signals) == 3
        assert signals[2]["type"] == "query_payment_methods"

    def test_duplicate_intent_not_accumulated(self):
        """Same intent type across turns should not create duplicates."""
        signals = []

        with patch.object(
            SemanticRouter, "detect_intent", return_value=("buying_signal", 0.85)
        ):
            _, _, signals = SemanticRouter.detect_and_accumulate(
                "Quiero comprar", existing_signals=signals, tenant_id=None
            )
        assert len(signals) == 1

        with patch.object(
            SemanticRouter, "detect_intent", return_value=("buying_signal", 0.92)
        ):
            _, _, signals = SemanticRouter.detect_and_accumulate(
                "Quiero pagar ya", existing_signals=signals, tenant_id=None
            )
        # Should still be 1 (dedup)
        assert len(signals) == 1

    def test_non_buying_intents_never_accumulate(self):
        """Objection and other non-buying intents should not add to signals."""
        signals = []

        intents = [
            ("objection_money", 0.90),
            ("security_breach", 0.95),
            ("pain_overwhelmed", 0.80),
        ]
        for intent, score in intents:
            with patch.object(
                SemanticRouter, "detect_intent", return_value=(intent, score)
            ):
                _, _, signals = SemanticRouter.detect_and_accumulate(
                    "texto de prueba", existing_signals=signals, tenant_id=None
                )
        assert len(signals) == 0


# ---------------------------------------------------------------------------
# Tenant cache invalidation tests
# ---------------------------------------------------------------------------


class TestTenantCacheInvalidation:
    def test_invalidate_tenant_clears_cache(self):
        """After invalidate, tenant should not be in cache."""
        tenant_id = uuid4()
        # Manually add to cache
        SemanticRouter._tenant_cache[tenant_id] = (["route1"], np.array([[1, 0, 0]]))
        assert tenant_id in SemanticRouter._tenant_cache

        SemanticRouter.invalidate_tenant(tenant_id)
        assert tenant_id not in SemanticRouter._tenant_cache

    def test_invalidate_nonexistent_tenant_is_safe(self):
        """Invalidating a tenant that's not in cache should not raise."""
        tenant_id = uuid4()
        assert tenant_id not in SemanticRouter._tenant_cache
        # Should not raise
        SemanticRouter.invalidate_tenant(tenant_id)

    def test_detect_intent_uses_tenant_cache_when_present(self):
        """When tenant_id has cached routes, those should be used."""
        tenant_id = uuid4()
        # Set up a mock cached tenant route
        route_embeddings = np.eye(3, 10)  # 3 routes, 10-dim
        norms = np.linalg.norm(route_embeddings, axis=1, keepdims=True)
        route_embeddings = route_embeddings / norms
        SemanticRouter._tenant_cache[tenant_id] = (
            ["tenant_route_a", "tenant_route_b", "tenant_route_c"],
            route_embeddings,
        )

        # Mock model to return embedding that matches route 0
        mock_model = MagicMock()
        query_embedding = np.zeros(10)
        query_embedding[0] = 1.0  # matches tenant_route_a
        mock_model.embed.return_value = iter([query_embedding])

        with (
            patch.object(SemanticRouter, "_model", mock_model),
            patch.object(SemanticRouter, "_system_embeddings", np.eye(2, 10)),
        ):
            intent, score = SemanticRouter.detect_intent(
                "test query text", tenant_id=tenant_id
            )
            assert intent == "tenant_route_a"
            assert score > 0.9

        # Cleanup
        SemanticRouter._tenant_cache.pop(tenant_id, None)

    def test_detect_intent_falls_back_to_system_when_no_tenant_cache(self):
        """Without tenant cache, system routes should be used."""
        tenant_id = uuid4()
        assert tenant_id not in SemanticRouter._tenant_cache

        route_embeddings = np.eye(3, 10)
        norms = np.linalg.norm(route_embeddings, axis=1, keepdims=True)
        route_embeddings = route_embeddings / norms

        mock_model = MagicMock()
        query_embedding = np.zeros(10)
        query_embedding[1] = 1.0
        mock_model.embed.return_value = iter([query_embedding])

        with (
            patch.object(SemanticRouter, "_model", mock_model),
            patch.object(SemanticRouter, "_system_embeddings", route_embeddings),
            patch.object(
                SemanticRouter, "_system_route_names", ["sys_a", "sys_b", "sys_c"]
            ),
        ):
            intent, score = SemanticRouter.detect_intent(
                "test query", tenant_id=tenant_id
            )
            assert intent == "sys_b"
            assert score > 0.9
