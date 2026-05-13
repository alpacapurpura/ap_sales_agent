"""Lifecycle scoring engine with threshold-based stage transitions.

Responsibilities:
- Recalculate lead_score from journey_event weights + fit score
- Determine lifecycle stage from score thresholds
- Transition profiles forward/backward/skip when thresholds crossed
- Handle sale-triggered lifecycle changes (CONVERSION, EXPANSION, reactivation)
- Record every transition in lifecycle_transitions audit table
- Manual override (force_stage) for admin API

CUSTOMER stage profiles are exempt from scoring-driven transitions.
"""

import contextlib
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from luana_core_crm.domain.enums import LifecycleStage
from luana_core_crm.domain.scoring import SCORING_THRESHOLDS, SCORING_WEIGHTS
from luana_core_crm.infrastructure.models.customer_model import (
    CustomerProfileModel,
    JourneyEventModel,
)
from luana_core_crm.infrastructure.repositories.lifecycle_repository import (
    LifecycleRepository,
)
from luana_core_platform.domain.events import DomainEvent
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class LifecycleService:
    """Scoring engine and lifecycle stage manager."""

    def __init__(self, db: Session) -> None:
        """Initialize lifecycle service."""
        self.db = db
        self.lifecycle_repo = LifecycleRepository(db)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def recalculate_score(self, profile_id: UUID, tenant_id: UUID) -> float:
        """Recalculate lead_score from all journey_events and fit score.

        - Skips CUSTOMER profiles (returns current score).
        - Uses SELECT ... FOR UPDATE to prevent race conditions (Postgres).
        - Clamps score to floor 0.
        - Triggers threshold-based stage transition if stage changed.
        """
        profile = self._load_profile_for_update(profile_id, tenant_id)
        if profile is None:
            logger.warning("Profile %s not found for tenant %s", profile_id, tenant_id)
            return 0.0

        # CUSTOMER exempt from scoring-driven transitions
        if profile.lifecycle_stage == LifecycleStage.CUSTOMER:
            return profile.lead_score or 0.0

        # Sum event weights
        event_score = self._sum_event_weights(profile_id, tenant_id)

        # Add fit score (one-time)
        fit_score = self._calculate_fit_score(profile)

        total = max(event_score + fit_score, 0.0)

        profile.lead_score = total
        self._check_threshold_transition(profile, total)

        self.db.flush()
        return total

    def handle_sale_completed(self, event: DomainEvent) -> None:
        """Handle sale_completed event: CONVERSION or EXPANSION lifecycle change.

        - CONVERSION: profile -> CUSTOMER, set first_conversion_at, add to lifetime_value.
        - EXPANSION: add to lifetime_value, keep CUSTOMER stage.
        - CHURNED reactivation: profile -> CUSTOMER via reactivation.
        """
        payload = event.payload
        customer_id = UUID(payload["customer_id"])
        stage = payload["stage"]  # "CONVERSION" or "EXPANSION"
        amount = float(payload.get("amount", 0))
        sale_id = payload.get("sale_id", "")
        offer_id = payload.get("offer_id", "")

        profile = self._load_profile_for_update(customer_id, event.tenant_id)
        if profile is None:
            logger.warning(
                "handle_sale_completed: profile %s not found for tenant %s",
                customer_id,
                event.tenant_id,
            )
            return

        current_stage = profile.lifecycle_stage

        # Reactivation: CHURNED profile receiving a sale
        if current_stage == LifecycleStage.CHURNED:
            self._transition(
                profile,
                LifecycleStage.CUSTOMER,
                reason="Reactivation via sale",
                triggered_by="reactivation",
                metadata={"sale_id": str(sale_id), "previous_stage": "churned"},
            )
            profile.lifetime_value = (profile.lifetime_value or 0) + amount
            if not profile.first_conversion_at:
                profile.first_conversion_at = datetime.now(UTC)
            self.db.flush()
            return

        if stage == "CONVERSION":
            self._transition(
                profile,
                LifecycleStage.CUSTOMER,
                reason="CONVERSION sale completed",
                triggered_by="sale_event",
                metadata={
                    "sale_id": str(sale_id),
                    "amount": amount,
                    "offer_id": str(offer_id),
                },
            )
            if not profile.first_conversion_at:
                profile.first_conversion_at = datetime.now(UTC)
            profile.lifetime_value = (profile.lifetime_value or 0) + amount

        elif stage == "EXPANSION":
            profile.lifetime_value = (profile.lifetime_value or 0) + amount
            # Record audit trail for expansion too
            self.lifecycle_repo.create_transition(
                profile_id=profile.id,
                tenant_id=profile.tenant_id,
                from_stage=LifecycleStage.CUSTOMER,
                to_stage=LifecycleStage.CUSTOMER,
                reason="EXPANSION sale completed",
                triggered_by="sale_event",
                score_at_transition=profile.lead_score,
                metadata={
                    "sale_id": str(sale_id),
                    "amount": amount,
                    "offer_id": str(offer_id),
                },
            )

        self.db.flush()

    def handle_churn_event(self, event: DomainEvent) -> None:
        """Handle churn_detected event: set lifecycle_stage=CHURNED.

        - Idempotent: if already CHURNED, skip (no duplicate transition).
        - Works from any stage (CUSTOMER, SQL, MQL, etc.)
        - Creates audit record with triggered_by="churn_event".
        """
        payload = event.payload
        profile_id = UUID(payload["profile_id"])
        source = payload.get("source", "unknown")
        subscription_id = payload.get("subscription_id", "")
        cancellation_reason = payload.get("cancellation_reason", "")

        profile = self._load_profile_for_update(profile_id, event.tenant_id)
        if profile is None:
            logger.warning(
                "handle_churn_event: profile %s not found for tenant %s",
                profile_id,
                event.tenant_id,
            )
            return

        # Idempotent: already churned
        if profile.lifecycle_stage == LifecycleStage.CHURNED:
            logger.info(
                "handle_churn_event: profile %s already CHURNED, skipping",
                profile_id,
            )
            return

        self._transition(
            profile,
            LifecycleStage.CHURNED,
            reason=f"Subscription cancelled via {source}",
            triggered_by="churn_event",
            metadata={
                "source": source,
                "subscription_id": subscription_id,
                "cancellation_reason": cancellation_reason,
            },
        )
        self.db.flush()

    def force_stage(
        self,
        profile_id: UUID,
        tenant_id: UUID,
        new_stage: LifecycleStage,
        admin_user_id: str | None = None,
        note: str = "",
    ) -> None:
        """Manual override for admin API."""
        profile = self._load_profile_for_update(profile_id, tenant_id)
        if profile is None:
            return

        self._transition(
            profile,
            new_stage,
            reason=f"Manual stage override: {note}" if note else "Manual stage override",
            triggered_by="manual",
            metadata={
                "admin_user_id": str(admin_user_id) if admin_user_id else "",
                "note": note,
            },
        )
        self.db.flush()

    def promote_to_evangelist(
        self,
        profile_id: UUID,
        tenant_id: UUID,
        reason: str = "nps_promotion",
    ) -> tuple:
        """Transition lifecycle to EVANGELIST and generate referral code atomically.

        Return (profile, referral_code).
        """
        # Lazy import to avoid circular dependency
        from luana_core_crm.application.services.referral_service import (
            ReferralService,
        )

        profile = self._load_profile_for_update(profile_id, tenant_id)
        if profile is None:
            msg = f"Profile {profile_id} not found for tenant {tenant_id}"
            raise ValueError(msg)

        # Step 1: Transition lifecycle stage
        self._transition(
            profile,
            LifecycleStage.EVANGELIST,
            reason=f"Evangelist promotion: {reason}",
            triggered_by="admin",
            metadata={"promotion_reason": reason},
        )

        # Step 2: Generate referral code
        referral_service = ReferralService(self.db)
        referral_code = referral_service.generate_code(tenant_id, profile_id)

        self.db.flush()

        logger.info(
            "Customer %s promoted to EVANGELIST with referral code %s",
            profile_id,
            referral_code.code,
        )
        return (profile, referral_code)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_profile_for_update(
        self,
        profile_id: UUID,
        tenant_id: UUID,
    ) -> CustomerProfileModel | None:
        """Load profile with FOR UPDATE lock (degrades gracefully on SQLite)."""
        stmt = select(CustomerProfileModel).where(
            CustomerProfileModel.id == profile_id,
            CustomerProfileModel.tenant_id == tenant_id,
        )
        with contextlib.suppress(Exception):
            stmt = stmt.with_for_update()
        result = self.db.execute(stmt)
        return result.scalars().first()

    def _sum_event_weights(self, profile_id: UUID, tenant_id: UUID) -> float:
        """Sum scoring weights from all journey_events for this profile."""
        stmt = select(JourneyEventModel.event_name).where(
            JourneyEventModel.profile_id == profile_id,
            JourneyEventModel.tenant_id == tenant_id,
        )
        result = self.db.execute(stmt)
        event_names = [row[0] for row in result]

        # Merge engagement + intent weight dicts
        all_weights = {**SCORING_WEIGHTS.engagement, **SCORING_WEIGHTS.intent}

        total = 0.0
        for name in event_names:
            total += all_weights.get(name, 0.0)

        return total

    def _calculate_fit_score(self, profile: CustomerProfileModel) -> float:
        """One-time fit score from profile computed_traits.

        Maps:
        - financial_capacity: high -> financial_capacity_high, medium -> financial_capacity_medium
        - sophistication_level: product_aware -> sophistication_product_aware, most_aware -> sophistication_most_aware
        - business_stage: active -> business_stage_active, idea -> business_stage_idea
        """
        computed = profile.computed_traits or {}

        # Check if fit score already applied
        if computed.get("fit_score_applied"):
            return computed.get("fit_score_value", 0.0)

        fit_weights = SCORING_WEIGHTS.fit
        score = 0.0

        # Financial capacity
        fc = computed.get("financial_capacity", "").lower()
        if fc == "high":
            score += fit_weights.get("financial_capacity_high", 0.0)
        elif fc == "medium":
            score += fit_weights.get("financial_capacity_medium", 0.0)

        # Sophistication level
        sl = computed.get("sophistication_level", "").lower()
        if sl == "product_aware":
            score += fit_weights.get("sophistication_product_aware", 0.0)
        elif sl == "most_aware":
            score += fit_weights.get("sophistication_most_aware", 0.0)

        # Business stage
        bs = computed.get("business_stage", "").lower()
        if bs == "active":
            score += fit_weights.get("business_stage_active", 0.0)
        elif bs == "idea":
            score += fit_weights.get("business_stage_idea", 0.0)

        # Mark as applied if there was any fit score
        if score > 0:
            new_computed = dict(computed)
            new_computed["fit_score_applied"] = True
            new_computed["fit_score_value"] = score
            profile.computed_traits = new_computed

        return score

    def _determine_stage(self, score: float) -> LifecycleStage:
        """Determine lifecycle stage from score thresholds."""
        if score >= SCORING_THRESHOLDS.sql:
            return LifecycleStage.SQL
        if score >= SCORING_THRESHOLDS.mql:
            return LifecycleStage.MQL
        if score >= SCORING_THRESHOLDS.lead:
            return LifecycleStage.LEAD
        return LifecycleStage.SUBSCRIBER

    def _check_threshold_transition(
        self,
        profile: CustomerProfileModel,
        score: float,
    ) -> None:
        """Check if score warrants a stage transition."""
        new_stage = self._determine_stage(score)
        if new_stage != profile.lifecycle_stage:
            self._transition(
                profile,
                new_stage,
                reason=(
                    f"Score {'crossed' if new_stage.value > profile.lifecycle_stage.value else 'dropped below'}"
                    f" {new_stage.value.upper()} threshold ({score:.1f})"
                ),
                triggered_by="scoring_rule",
            )

    def _transition(
        self,
        profile: CustomerProfileModel,
        new_stage: LifecycleStage,
        reason: str,
        triggered_by: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Execute stage transition with audit trail."""
        old_stage = profile.lifecycle_stage
        profile.lifecycle_stage = new_stage

        self.lifecycle_repo.create_transition(
            profile_id=profile.id,
            tenant_id=profile.tenant_id,
            from_stage=old_stage,
            to_stage=new_stage,
            reason=reason,
            triggered_by=triggered_by,
            score_at_transition=profile.lead_score,
            metadata=metadata,
        )

        logger.info(
            "Lifecycle transition: %s -> %s for profile %s (reason: %s)",
            old_stage.value if old_stage else "none",
            new_stage.value,
            profile.id,
            reason,
        )
