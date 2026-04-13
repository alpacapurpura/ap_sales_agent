"""
Batch inactivity detection and score decay service.

Responsibilities:
- Flag profiles as inactive after INACTIVITY_CONFIG.inactive_days without activity
- Recover profiles that have become active again
- Apply daily_decay_rate score decay to inactive non-CUSTOMER profiles
- Trigger backward stage transitions when decayed score crosses thresholds
- Process in batches of 500 to avoid stale data

CUSTOMER stage profiles: decay is PAUSED but is_inactive flag still applies.
"""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.modules.crm.domain.enums import LifecycleStage
from src.modules.crm.domain.scoring import (
    DECAY_CONFIG,
    INACTIVITY_CONFIG,
    SCORING_THRESHOLDS,
)
from src.modules.crm.infrastructure.models.customer_model import CustomerProfileModel
from src.modules.crm.infrastructure.repositories.lifecycle_repository import (
    LifecycleRepository,
)

logger = logging.getLogger(__name__)

BATCH_SIZE = 500


class InactivityService:
    """Batch inactivity detection and score decay engine."""

    def __init__(self, db: Session):
        self.db = db
        self.lifecycle_repo = LifecycleRepository(db)

    def run_batch(self, tenant_id: UUID | None = None) -> dict[str, int]:
        """Run inactivity detection and score decay for all (or one) tenant.

        Returns dict with counts:
            profiles_flagged_inactive, profiles_recovered, scores_decayed, transitions
        """
        now = datetime.now(UTC)
        threshold_date = now - timedelta(days=INACTIVITY_CONFIG.inactive_days)

        stats = {
            "profiles_flagged_inactive": 0,
            "profiles_recovered": 0,
            "scores_decayed": 0,
            "transitions": 0,
        }

        # Process inactive profiles (last_activity_at < threshold OR NULL)
        offset = 0
        while True:
            stmt = select(CustomerProfileModel)
            if tenant_id is not None:
                stmt = stmt.where(CustomerProfileModel.tenant_id == tenant_id)
            stmt = stmt.limit(BATCH_SIZE).offset(offset)

            result = self.db.execute(stmt)
            profiles = list(result.scalars().all())

            if not profiles:
                break

            for profile in profiles:
                is_past_threshold = profile.last_activity_at is None or profile.last_activity_at < threshold_date

                if is_past_threshold:
                    # Flag as inactive
                    if not profile.is_inactive:
                        profile.is_inactive = True
                        stats["profiles_flagged_inactive"] += 1
                    else:
                        # Already inactive, still count for decay
                        stats["profiles_flagged_inactive"] += 0

                    # Apply score decay (skip CUSTOMER stage)
                    if profile.lifecycle_stage != LifecycleStage.CUSTOMER:
                        self._apply_decay(profile, now, stats)
                    # CUSTOMER: flag inactive but no decay
                    elif not profile.is_inactive:
                        # Was just set above
                        pass

                # Profile is active -- recover if previously inactive
                elif profile.is_inactive:
                    profile.is_inactive = False
                    stats["profiles_recovered"] += 1

            self.db.flush()
            offset += BATCH_SIZE

        return stats

    def update_last_activity(
        self,
        profile_id: UUID,
        tenant_id: UUID,
        activity_at: datetime,
    ) -> None:
        """Atomic UPDATE of last_activity_at for a profile."""
        stmt = (
            update(CustomerProfileModel)
            .where(
                CustomerProfileModel.id == profile_id,
                CustomerProfileModel.tenant_id == tenant_id,
            )
            .values(last_activity_at=activity_at)
        )
        self.db.execute(stmt)
        self.db.flush()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _apply_decay(
        self,
        profile: CustomerProfileModel,
        now: datetime,
        stats: dict[str, int],
    ) -> None:
        """Apply exponential score decay based on days inactive."""
        if profile.last_activity_at is None:
            # Treat NULL as very old -- use created_at or default to 365 days
            days_inactive = 365
        else:
            last_activity = profile.last_activity_at
            # Handle timezone-naive datetimes from SQLite test db
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=UTC)
            delta = now - last_activity
            days_inactive = max(delta.days, 0)

        if days_inactive <= 0:
            return

        original_score = profile.lead_score or 0.0
        decay_factor = (1 - DECAY_CONFIG.daily_decay_rate) ** days_inactive
        new_score = original_score * decay_factor
        new_score = max(new_score, DECAY_CONFIG.min_score)

        # Clamp negligible scores to floor (exponential decay asymptotes to 0)
        if new_score < 0.01:
            new_score = DECAY_CONFIG.min_score

        if new_score != original_score:
            profile.lead_score = new_score
            stats["scores_decayed"] += 1

            # Check for backward stage transition
            new_stage = self._determine_stage(new_score)
            if new_stage != profile.lifecycle_stage:
                self._backward_transition(
                    profile,
                    new_stage,
                    original_score,
                    new_score,
                    days_inactive,
                    stats,
                )

    def _determine_stage(self, score: float) -> LifecycleStage:
        """Determine lifecycle stage from score thresholds (same logic as LifecycleService)."""
        if score >= SCORING_THRESHOLDS.sql:
            return LifecycleStage.SQL
        if score >= SCORING_THRESHOLDS.mql:
            return LifecycleStage.MQL
        if score >= SCORING_THRESHOLDS.lead:
            return LifecycleStage.LEAD
        return LifecycleStage.SUBSCRIBER

    def _backward_transition(
        self,
        profile: CustomerProfileModel,
        new_stage: LifecycleStage,
        previous_score: float,
        new_score: float,
        days_inactive: int,
        stats: dict[str, int],
    ) -> None:
        """Record backward stage transition triggered by score decay."""
        old_stage = profile.lifecycle_stage
        profile.lifecycle_stage = new_stage

        self.lifecycle_repo.create_transition(
            profile_id=profile.id,
            tenant_id=profile.tenant_id,
            from_stage=old_stage,
            to_stage=new_stage,
            reason=f"Score decay: {previous_score:.1f} -> {new_score:.1f} after {days_inactive} days inactive",
            triggered_by="decay",
            score_at_transition=new_score,
            metadata={
                "previous_score": previous_score,
                "new_score": new_score,
                "days_inactive": days_inactive,
                "decay_rate": DECAY_CONFIG.daily_decay_rate,
            },
        )

        stats["transitions"] += 1

        logger.info(
            "Decay transition: %s -> %s for profile %s (score %.1f -> %.1f, %d days inactive)",
            old_stage.value if old_stage else "none",
            new_stage.value,
            profile.id,
            previous_score,
            new_score,
            days_inactive,
        )
