"""Auto-detect offer↔campaign/ad-set associations.

Strategies in priority order:
1. Landing URL match  (confidence HIGH)    — ads.creative_link_url vs offer.landing/checkout
2. Keyword match      (confidence MEDIUM)  — Jaccard similarity on normalized names
3. Objective heuristic (confidence LOW)    — campaign.objective vs offer.expected_metric

This service NEVER persists. It returns suggestions for the user to confirm.
Targets that already have an active association are skipped entirely.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.modules.advertising.application.dto.association_dto import (
    AssociationSuggestionDTO,
)
from src.modules.advertising.domain.enums import (
    OfferExpectedMetric,
    expected_metric_for_objective,
    resolve_expected_metric,
)
from src.modules.advertising.domain.text_matching import (
    jaccard_similarity,
    tokenize_es,
    urls_match,
)
from src.modules.advertising.infrastructure.repositories.association_repository import (
    AssociationRepository,
)
from src.modules.advertising.infrastructure.repositories.meta_catalog_repository import (
    MetaCatalog,
    MetaCatalogRepository,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.shared.domain.ports import OfferReadDTO, OfferReadPort

KEYWORD_MATCH_THRESHOLD = 0.5


@dataclass(frozen=True)
class _ExistingKey:
    target_type: str
    target_external_id: str


class OfferDetectionService:
    """Suggest offer associations for unassigned campaigns/ad sets."""

    def __init__(self, db: Session, offer_read_port: OfferReadPort) -> None:
        """Initialize OfferDetectionService."""
        self._db = db
        self._offer_read_port = offer_read_port
        self._catalog_repo = MetaCatalogRepository(db)
        self._association_repo = AssociationRepository(db)

    async def detect(self, tenant_id: UUID) -> list[AssociationSuggestionDTO]:
        """Run all strategies and return a deduplicated suggestion list."""
        catalog = self._catalog_repo.load(tenant_id)
        offers = await self._offer_read_port.get_offers_by_tenant(tenant_id)
        # Only active, non-draft, non-archived offers participate in detection.
        offers = [o for o in offers if (o.status or "active") not in {"archived", "draft"}]
        if not offers:
            return []

        existing_keys = self._collect_existing_targets(tenant_id)

        suggestions: dict[_ExistingKey, AssociationSuggestionDTO] = {}

        # 1) Landing URL match (HIGH) — works at ad_set level via ads' creative_link_url.
        self._match_by_landing_url(
            catalog=catalog,
            offers=offers,
            existing=existing_keys,
            out=suggestions,
        )

        # 2) Keyword match (MEDIUM) — at campaign level first, then ad_set.
        self._match_by_keywords(
            catalog=catalog,
            offers=offers,
            existing=existing_keys,
            out=suggestions,
        )

        # 3) Objective heuristic (LOW) — only when exactly 1 offer matches.
        self._match_by_objective(
            catalog=catalog,
            offers=offers,
            existing=existing_keys,
            out=suggestions,
        )

        return list(suggestions.values())

    # ── Strategy 1: landing URL ────────────────────────────────────────────
    def _match_by_landing_url(
        self,
        *,
        catalog: MetaCatalog,
        offers: list[OfferReadDTO],
        existing: set[_ExistingKey],
        out: dict[_ExistingKey, AssociationSuggestionDTO],
    ) -> None:
        # For each ad set, look at its ads' creative_link_url and try to match.
        for ad_set in catalog.ad_sets:
            key = _ExistingKey("ad_set", ad_set.external_id)
            if key in existing or key in out:
                continue
            ads = catalog.ads_for_ad_set(ad_set.external_id)
            if not ads:
                continue
            for ad in ads:
                if not ad.creative_link_url:
                    continue
                matched_offer = self._find_offer_by_url(ad.creative_link_url, offers)
                if matched_offer is not None:
                    reason = (
                        f"Landing URL del anuncio coincide con la landing/checkout "
                        f"de la offer '{matched_offer.public_name}'."
                    )
                    out[key] = AssociationSuggestionDTO(
                        target_type="ad_set",
                        target_external_id=ad_set.external_id,
                        target_name=ad_set.name,
                        suggested_offer_id=matched_offer.id,
                        suggested_offer_name=matched_offer.public_name,
                        association_type="auto_landing_url",
                        confidence="high",
                        reason=reason,
                    )
                    break

    @staticmethod
    def _find_offer_by_url(
        ad_url: str,
        offers: list[OfferReadDTO],
    ) -> OfferReadDTO | None:
        for offer in offers:
            if offer.landing_page_url and urls_match(ad_url, offer.landing_page_url):
                return offer
            if offer.checkout_page_url and urls_match(ad_url, offer.checkout_page_url):
                return offer
        return None

    # ── Strategy 2: keyword match ──────────────────────────────────────────
    def _match_by_keywords(
        self,
        *,
        catalog: MetaCatalog,
        offers: list[OfferReadDTO],
        existing: set[_ExistingKey],
        out: dict[_ExistingKey, AssociationSuggestionDTO],
    ) -> None:
        offer_tokens = [
            (
                offer,
                tokenize_es(offer.public_name) | tokenize_es(offer.internal_sku or ""),
            )
            for offer in offers
        ]

        # Campaign-level match
        for campaign in catalog.campaigns:
            key = _ExistingKey("campaign", campaign.external_id)
            if key in existing or key in out:
                continue
            best = self._best_token_match(campaign.name, offer_tokens)
            if best is not None:
                offer, score = best
                out[key] = AssociationSuggestionDTO(
                    target_type="campaign",
                    target_external_id=campaign.external_id,
                    target_name=campaign.name,
                    suggested_offer_id=offer.id,
                    suggested_offer_name=offer.public_name,
                    association_type="auto_keyword",
                    confidence="medium",
                    reason=(
                        f"El nombre de la campaña coincide con la offer "
                        f"'{offer.public_name}' ({score:.0%} de palabras en común)."
                    ),
                )

        # Ad-set level match (only for targets still unassigned)
        for ad_set in catalog.ad_sets:
            key = _ExistingKey("ad_set", ad_set.external_id)
            if key in existing or key in out:
                continue
            best = self._best_token_match(ad_set.name, offer_tokens)
            if best is not None:
                offer, score = best
                out[key] = AssociationSuggestionDTO(
                    target_type="ad_set",
                    target_external_id=ad_set.external_id,
                    target_name=ad_set.name,
                    suggested_offer_id=offer.id,
                    suggested_offer_name=offer.public_name,
                    association_type="auto_keyword",
                    confidence="medium",
                    reason=(
                        f"El nombre del ad set coincide con la offer "
                        f"'{offer.public_name}' ({score:.0%} de palabras en común)."
                    ),
                )

    @staticmethod
    def _best_token_match(
        text: str,
        offer_tokens: list[tuple[OfferReadDTO, set[str]]],
    ) -> tuple[OfferReadDTO, float] | None:
        text_tokens = tokenize_es(text)
        if not text_tokens:
            return None
        best: tuple[OfferReadDTO, float] | None = None
        for offer, tokens in offer_tokens:
            score = jaccard_similarity(text_tokens, tokens)
            if score >= KEYWORD_MATCH_THRESHOLD and (best is None or score > best[1]):
                best = (offer, score)
        return best

    # ── Strategy 3: objective heuristic ────────────────────────────────────
    def _match_by_objective(
        self,
        *,
        catalog: MetaCatalog,
        offers: list[OfferReadDTO],
        existing: set[_ExistingKey],
        out: dict[_ExistingKey, AssociationSuggestionDTO],
    ) -> None:
        # Precompute expected_metric per offer.
        offer_expected: list[tuple[OfferReadDTO, OfferExpectedMetric]] = [
            (
                o,
                resolve_expected_metric(
                    archetype=o.offer_type,
                    onboarding_action=o.onboarding_action,
                    is_lead_magnet=o.is_lead_magnet,
                    has_checkout_url=bool(o.checkout_page_url),
                ),
            )
            for o in offers
        ]

        for campaign in catalog.campaigns:
            key = _ExistingKey("campaign", campaign.external_id)
            if key in existing or key in out:
                continue
            expected = expected_metric_for_objective(campaign.objective)
            if expected is None:
                continue
            candidates = [o for o, m in offer_expected if m == expected]
            if len(candidates) != 1:
                continue
            offer = candidates[0]
            out[key] = AssociationSuggestionDTO(
                target_type="campaign",
                target_external_id=campaign.external_id,
                target_name=campaign.name,
                suggested_offer_id=offer.id,
                suggested_offer_name=offer.public_name,
                association_type="auto_objective",
                confidence="low",
                reason=(
                    f"El objetivo de la campaña coincide con la única offer "
                    f"que requiere esa métrica: '{offer.public_name}'."
                ),
            )

    # ── helpers ────────────────────────────────────────────────────────────
    def _collect_existing_targets(self, tenant_id: UUID) -> set[_ExistingKey]:
        active = self._association_repo.list_active(tenant_id)
        return {_ExistingKey(row.target_type, row.target_external_id) for row in active}


__all__ = ["OfferDetectionService"]
