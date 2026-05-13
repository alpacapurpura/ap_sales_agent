"""SemanticRouter — intent detection via cosine similarity.

Singleton-cached embedding router. System routes are loaded once at
startup from :data:`SYSTEM_ROUTES` (domain layer). Tenant-specific
routes (per-Offer trigger_phrases) are overlaid via
:func:`collect_tenant_anchors` and cached per ``tenant_id``.

S11B refactor: hardcoded ``SYSTEM_ROUTES`` dict moved to
``domain/semantic_routes.py``; tenant overlay logic moved to
``application/services/tenant_route_overlay.py``. Public API unchanged
(``detect_intent``, ``detect_and_accumulate``, ``register_tenant_routes``,
``invalidate_tenant``) so callers in chat orchestrator / nodes /
knowledge_builder don't move.

# [SALES-AGENT-SEMANTIC-ROUTER-REGISTRY-S11B] -> docs/domains/sales-agent/redesign-2026-04/phases/
# S11-shared-lift-orchestrator-decomp.md
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Self

import numpy as np
from fastembed import TextEmbedding
from luana_core_sales_agent.application.services.tenant_route_overlay import (
    collect_tenant_anchors,
)
from luana_core_sales_agent.domain.semantic_routes import SYSTEM_ROUTES

if TYPE_CHECKING:
    from uuid import UUID

logger = logging.getLogger(__name__)


class SemanticRouter:
    """Tenant-aware semantic router using cosine similarity.

    System routes (:data:`SYSTEM_ROUTES`) are loaded once at startup.
    Tenant-specific routes (from Offer objections trigger_phrases) are
    overlaid per-tenant and cached for performance.
    """

    _instance = None
    _model = None
    # System-level pre-computed embeddings
    _system_embeddings = None
    _system_route_names: list[str] = []
    # Per-tenant overlay cache: {tenant_id: (route_names, embeddings)}
    _tenant_cache: dict[UUID, tuple[list[str], np.ndarray]] = {}

    def __new__(cls) -> Self:
        """Implement __new__."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._initialize_model()
            cls._initialize_system_routes()
        return cls._instance

    @classmethod
    def _initialize_model(cls) -> None:
        """Load the embedding model once."""
        logger.info("Initializing Semantic Router model...")
        try:
            cls._model = TextEmbedding(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                cache_dir="/app/model_cache",
            )
        except Exception as e:  # noqa: BLE001 — agent resilience
            logger.warning(
                "Could not load multilingual model, falling back to default: %s",
                e,
            )
            cls._model = TextEmbedding(cache_dir="/app/model_cache")

    @classmethod
    def _initialize_system_routes(cls) -> None:
        """Pre-compute embeddings for system routes (runs once at startup)."""
        cls._system_route_names = []
        all_anchors = []

        for route, anchors in SYSTEM_ROUTES.items():
            for anchor in anchors:
                cls._system_route_names.append(route)
                all_anchors.append(anchor)

        try:
            embeddings_list = list(cls._model.embed(all_anchors))
            cls._system_embeddings = np.array(embeddings_list)
            norms = np.linalg.norm(cls._system_embeddings, axis=1, keepdims=True)
            cls._system_embeddings = cls._system_embeddings / norms
            logger.info(
                "Semantic Router initialized with %d system routes and %d anchors.",
                len(SYSTEM_ROUTES),
                len(all_anchors),
            )
        except Exception:
            logger.exception("Failed to compute system embeddings")
            cls._system_embeddings = None
            raise

    @classmethod
    def register_tenant_routes(cls, tenant_id: UUID, offers_data: list) -> None:
        """Build tenant-specific routes from Offer objections and overlay them.

        Call this during ``TenantKnowledgeBuilder.build_identity()`` to prime
        the cache. Translation logic lives in
        :func:`collect_tenant_anchors` (overlay module).
        """
        if cls._model is None:
            cls._initialize_model()
            cls._initialize_system_routes()

        tenant_route_names, tenant_anchors = collect_tenant_anchors(offers_data)

        if not tenant_anchors:
            # No tenant-specific routes, use system routes only
            cls._tenant_cache.pop(tenant_id, None)
            return

        try:
            embeddings_list = list(cls._model.embed(tenant_anchors))
            tenant_embeddings = np.array(embeddings_list)
            norms = np.linalg.norm(tenant_embeddings, axis=1, keepdims=True)
            tenant_embeddings = tenant_embeddings / norms

            # Combine system routes with tenant-specific routes
            combined_names = cls._system_route_names + tenant_route_names
            combined_embeddings = np.vstack([cls._system_embeddings, tenant_embeddings])

            cls._tenant_cache[tenant_id] = (combined_names, combined_embeddings)
            logger.info(
                "Registered %d tenant-specific anchors for tenant %s",
                len(tenant_anchors),
                tenant_id,
            )
        except Exception:
            logger.exception("Failed to register tenant routes for %s", tenant_id)

    @classmethod
    def detect_intent(
        cls,
        text: str,
        tenant_id: UUID | None = None,
        threshold: float = 0.65,
    ) -> tuple[str | None, float]:
        """Detect the intent of a given text using cosine similarity.

        If tenant_id is provided and has cached routes, uses tenant+system routes.
        Otherwise falls back to system routes only.

        Returns: (intent_name, score) or (None, 0.0) if below threshold.
        """
        if cls._model is None or cls._system_embeddings is None:
            cls._initialize_model()
            cls._initialize_system_routes()

        if not text or len(text.strip()) < 2:
            return None, 0.0

        # Select route set
        if tenant_id and tenant_id in cls._tenant_cache:
            route_names, embeddings = cls._tenant_cache[tenant_id]
        else:
            route_names, embeddings = cls._system_route_names, cls._system_embeddings

        # Embed input
        query_embedding = next(iter(cls._model.embed([text])))
        query_norm = np.linalg.norm(query_embedding)
        if query_norm > 0:
            query_embedding = query_embedding / query_norm

        # Cosine similarity
        scores = np.dot(embeddings, query_embedding)
        best_idx = np.argmax(scores)
        best_score = scores[best_idx]

        if best_score >= threshold:
            return route_names[best_idx], float(best_score)

        return None, float(best_score)

    @classmethod
    def detect_and_accumulate(
        cls,
        text: str,
        existing_signals: list,
        tenant_id: UUID | None = None,
    ) -> tuple[str | None, float, list]:
        """Detect intent AND accumulates buying signals.

        Returns (intent, score, updated_signals).
        """
        intent, score = cls.detect_intent(text, tenant_id)

        buying_intents = {"buying_signal", "schedule_signal", "query_payment_methods"}
        if intent in buying_intents and score >= 0.50:
            # Avoid duplicate signal types in the same turn
            existing_types = {s.get("type") for s in existing_signals}
            if intent not in existing_types:
                existing_signals = list(existing_signals)  # Don't mutate original
                existing_signals.append(
                    {
                        "type": intent,
                        "confidence": round(score, 3),
                        "turn": len(existing_signals),
                    },
                )

        return intent, score, existing_signals

    @classmethod
    def invalidate_tenant(cls, tenant_id: UUID) -> None:
        """Remove cached tenant routes (e.g., when offers are updated)."""
        cls._tenant_cache.pop(tenant_id, None)


__all__ = ["SYSTEM_ROUTES", "SemanticRouter"]
