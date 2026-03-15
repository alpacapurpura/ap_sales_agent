# Phase 3: CRM Lifecycle Automation - Research

**Researched:** 2026-03-15
**Domain:** CRM lifecycle scoring, domain events, batch inactivity detection
**Confidence:** HIGH

## Summary

This phase implements automated lifecycle stage transitions for customer profiles based on lead scoring rules, sale events, time-based decay, and churn detection. The codebase already has the foundational CRM schema (CustomerProfileModel, JourneyEventModel, SaleModel) with LifecycleStage enum covering all 8 stages. The key gap is that `PipelineService.move_stage()` is a `pass` placeholder and SaleService.create_sale() does not emit domain events.

The implementation requires four main subsystems: (1) a scoring engine that computes lead_score from journey_events and checks thresholds, (2) an in-process EventBus in the shared module for cross-module communication, (3) sale-triggered lifecycle transitions via domain events, and (4) a batch inactivity detection job on the ARQ worker. The existing ARQ infrastructure from Phase 2 (analytics workers) provides the pattern for scheduled batch jobs.

**Primary recommendation:** Use an in-process mediator pattern (not fastapi-events, not ARQ for events) because the codebase uses sync SQLAlchemy sessions. Build a simple EventBus class in `shared/domain/events.py` with after-commit hook registration. Keep it under 100 lines.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Fixed global thresholds -- same for all tenants (e.g. >10=LEAD, >40=MQL, >70=SQL). Can be made per-tenant later
- Category-based scoring with three dimensions: Engagement (opens, clicks, views), Intent (form fills, checkout starts, meeting requests), Fit (matches ideal customer profile via FinancialCapacity, SophisticationLevel, BusinessStage enums)
- Event weights stored in Python config dict (dataclass in CRM domain). Change requires deploy, versioned in git
- Recalculation on every journey_event write -- real-time score update and threshold check
- Stage skipping allowed -- if score jumps from 5 to 75, go directly from SUBSCRIBER to SQL. No forced sequential progression
- Score is additive from events + time-based percentage decay
- Percentage decay -- lose X% of current score per day of inactivity (rate to be determined during research)
- Floor at 0 -- score can never go negative
- Backward transitions allowed -- if score drops below a threshold, profile moves back (e.g. MQL to LEAD)
- Decay paused for CUSTOMER stage -- profiles that reached CUSTOMER via sale don't decay. Prevents CUSTOMER to SQL backward transition. Inactivity detection still applies separately
- Domain event pattern -- SaleService emits 'sale_completed' event. CRM lifecycle handler subscribes and updates stage. Sales module doesn't import CRM directly
- CONVERSION sale triggers lifecycle_stage = CUSTOMER regardless of current stage (sale overrides scoring)
- EXPANSION sale triggers increment lifetime_value, keep CUSTOMER stage. EVANGELIST is reserved for referral/NPS behavior (Phase 10)
- CHURNED reactivation -- new sale on a CHURNED profile restores lifecycle_stage to CUSTOMER and increments lifetime_value
- Events processed after DB commit -- if handler fails, sale still exists; lifecycle update can be retried
- App-wide reusable EventBus in shared module -- any module can publish/subscribe
- After-commit processing -- event handlers fire after the triggering transaction commits. Handler failure doesn't roll back the original action
- Any journey_event counts as activity -- page_view, email_opened, message_sent all reset the inactivity timer
- Dual detection strategy: Scheduled batch job for bulk detection (this phase) + on-demand calculation for single-profile detail (deferred)
- CHURNED triggered only by explicit cancellation events (Shopify/Stripe webhooks). Inactivity flags is_inactive=true but does NOT change lifecycle_stage
- Inactivity != Churn -- inactive is a flag, churned is a lifecycle stage. They are independent concepts
- Dedicated lifecycle_transitions table: (id, profile_id, tenant_id, from_stage, to_stage, reason, triggered_by, metadata JSONB, occurred_at)
- Log everything -- forward, backward, sale-triggered, churn, reactivation, decay-driven. Complete history
- Manual override supported -- admin can force a stage change via API, recorded as triggered_by='manual'
- Real columns (not computed_traits JSONB): lifetime_value (Float), last_activity_at (DateTime), is_inactive (Boolean) -- with indexes
- Migration defaults: Zero/null (lifetime_value=0, last_activity_at=null, is_inactive=false)
- Lead sources limited to 3 channels: direct messages (Sales Agent), Manychat actions (contact extraction), and Mailerlite (contact base)

### Claude's Discretion
- Domain event implementation (in-process mediator vs ARQ async queue)
- Inactivity threshold default value (research-informed)
- Exact scoring weights per event type and category
- Decay rate percentage per day
- triggered_by field schema design
- Additional customer_profile fields (after researching Salesforce/HubSpot patterns)
- Batch job scheduling (run alongside ETL or separate schedule)

### Deferred Ideas (OUT OF SCOPE)
- Identity resolution / cross-channel deduplication -- smarter unification strategy for same person across WhatsApp, Mailerlite, Instagram DM
- Sales Agent as qualifier -- Sales Agent's MQL/SQL classification feeding into lifecycle transitions
- On-demand inactivity calculation -- single-profile detail view showing exact inactivity status in real-time
- Per-tenant configurable thresholds -- UI for tenant-specific scoring thresholds and inactivity windows
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CRM-01 | Implement `move_stage()` with automated rules -- lead scoring thresholds trigger SUBSCRIBER->LEAD->MQL->SQL transitions | Scoring engine config, threshold dataclass, recalculation-on-event pattern, stage skipping logic |
| CRM-02 | Sales module writes `lifecycle_stage = CUSTOMER` on `customer_profiles` when a CONVERSION sale completes | EventBus design, SaleService event emission, after-commit handler pattern |
| CRM-03 | Sales module writes lifecycle updates on EXPANSION sale events and increments `lifetime_value` | EventBus handler for EXPANSION events, lifetime_value column migration |
| CRM-04 | Inactivity detection -- mark customers as inactive after N days without `journey_events` | Batch job on ARQ, last_activity_at column, is_inactive flag, configurable threshold |
| CRM-05 | Churn detection -- `lifecycle_stage = CHURNED` triggered by subscription cancellation events | Cancellation event handler, webhook event processing, lifecycle_transitions audit |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy | 2.0 (sync) | ORM, migrations base | Already in use, sync sessions throughout CRM module |
| Alembic | existing | Schema migrations | Already configured with all CRM models registered in env.py |
| Pydantic v2 | existing | DTOs, domain entities, event schemas | BaseEntity pattern established |
| ARQ | existing | Background job scheduling | Phase 2 established worker + scheduler pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| dataclasses (stdlib) | 3.11+ | Scoring config, event weights | Immutable config objects for scoring rules |
| SQLAlchemy events | 2.0 | after_commit hooks | Register post-commit callbacks for EventBus dispatch |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom in-process EventBus | fastapi-events | fastapi-events processes after HTTP response (ASGI middleware). Our events also fire from ARQ workers (no HTTP context). Custom EventBus is simpler and works everywhere |
| Custom in-process EventBus | python-mediator | External dependency for <100 lines of code. Not justified |
| Custom in-process EventBus | ARQ queue for events | Overkill for same-process event handling. ARQ adds Redis round-trip latency. Use ARQ only for scheduled batch jobs |

**No new pip dependencies required.** Everything uses stdlib + existing packages.

## Architecture Patterns

### Recommended Project Structure
```
backend/src/
├── shared/
│   └── domain/
│       └── events.py              # EventBus singleton + DomainEvent base class
├── modules/crm/
│   ├── domain/
│   │   ├── enums.py               # Existing LifecycleStage (no changes)
│   │   ├── customer.py            # Add new fields to domain entity
│   │   ├── scoring.py             # NEW: ScoringConfig dataclass, weights, thresholds
│   │   └── events.py              # NEW: CRM-specific event classes
│   ├── infrastructure/
│   │   ├── models/
│   │   │   ├── customer_model.py  # Add lifetime_value, last_activity_at, is_inactive, new fields
│   │   │   └── lifecycle_transition_model.py  # NEW: audit trail table
│   │   └── repositories/
│   │       ├── customer_repository.py  # Add bulk inactivity queries
│   │       └── lifecycle_repository.py # NEW: transition audit CRUD
│   ├── application/
│   │   └── services/
│   │       ├── lifecycle_service.py   # NEW: scoring engine, stage transitions, audit logging
│   │       └── sale_service.py        # MODIFY: emit sale_completed event after commit
│   └── api/
│       └── pipeline.py               # MODIFY: wire lifecycle_service
└── modules/analytics/
    └── workers/
        ├── tasks.py                   # ADD: inactivity detection task
        └── settings.py                # ADD: inactivity task to worker functions + cron
```

### Pattern 1: In-Process EventBus (After-Commit)
**What:** A lightweight publish/subscribe bus that defers handler execution until after the current DB transaction commits.
**When to use:** Cross-module communication where the publisher should not import the subscriber's domain.

```python
# shared/domain/events.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

@dataclass
class DomainEvent:
    event_name: str
    tenant_id: UUID
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = field(default_factory=dict)

class EventBus:
    """Simple in-process event bus with after-commit dispatch."""

    _handlers: Dict[str, List[Callable]] = {}

    @classmethod
    def subscribe(cls, event_name: str, handler: Callable) -> None:
        cls._handlers.setdefault(event_name, []).append(handler)

    @classmethod
    def publish(cls, event: DomainEvent, session=None) -> None:
        """Queue event for after-commit dispatch, or dispatch immediately if no session."""
        if session is not None:
            from sqlalchemy import event as sa_event
            # Register one-shot after_commit listener
            @sa_event.listens_for(session, "after_commit", once=True)
            def on_commit(sess):
                cls._dispatch(event)
        else:
            cls._dispatch(event)

    @classmethod
    def _dispatch(cls, event: DomainEvent) -> None:
        for handler in cls._handlers.get(event.event_name, []):
            try:
                handler(event)
            except Exception:
                logger.exception("Event handler failed for %s", event.event_name)
```

**Key design decisions:**
- Uses SQLAlchemy `after_commit` event listener for after-commit dispatch
- Handler exceptions are caught and logged, never propagate to caller
- Handlers run synchronously in the same process (adequate for lifecycle updates)
- Class-level (singleton) handlers dict -- register once at app startup

### Pattern 2: Scoring Engine as Config Dataclass
**What:** All scoring weights, thresholds, and decay rates defined as a frozen dataclass in the CRM domain layer.
**When to use:** Whenever scoring logic needs to be evaluated.

```python
# modules/crm/domain/scoring.py
from dataclasses import dataclass, field
from typing import Dict

@dataclass(frozen=True)
class ScoringWeights:
    """Event weights by category. Change requires deploy."""

    # Engagement (low-intent signals)
    engagement: Dict[str, float] = field(default_factory=lambda: {
        "page_view": 1.0,
        "email_opened": 2.0,
        "email_clicked": 3.0,
        "social_interaction": 1.5,
        "content_downloaded": 3.0,
    })

    # Intent (high-intent signals)
    intent: Dict[str, float] = field(default_factory=lambda: {
        "form_submitted": 5.0,
        "checkout_started": 8.0,
        "meeting_requested": 10.0,
        "pricing_viewed": 4.0,
        "demo_requested": 10.0,
        "message_sent": 3.0,        # DM via Sales Agent
        "contact_extracted": 5.0,    # Manychat extraction
    })

    # Fit (profile-based, one-time adjustments)
    fit: Dict[str, float] = field(default_factory=lambda: {
        "financial_capacity_high": 10.0,
        "financial_capacity_medium": 5.0,
        "sophistication_product_aware": 8.0,
        "sophistication_most_aware": 12.0,
        "business_stage_active": 10.0,
        "business_stage_idea": 5.0,
    })

@dataclass(frozen=True)
class ScoringThresholds:
    """Stage transition thresholds. Score >= threshold triggers transition."""
    lead: float = 10.0       # SUBSCRIBER -> LEAD
    mql: float = 40.0        # LEAD -> MQL
    sql: float = 70.0        # MQL -> SQL

@dataclass(frozen=True)
class DecayConfig:
    """Score decay settings."""
    daily_decay_rate: float = 0.05   # 5% per day of inactivity
    min_score: float = 0.0           # Floor

@dataclass(frozen=True)
class InactivityConfig:
    """Inactivity detection settings."""
    inactive_days: int = 14          # Days without journey_events

# Module-level singleton
SCORING_WEIGHTS = ScoringWeights()
SCORING_THRESHOLDS = ScoringThresholds()
DECAY_CONFIG = DecayConfig()
INACTIVITY_CONFIG = InactivityConfig()
```

### Pattern 3: Lifecycle Transition Audit Trail
**What:** Every stage change is recorded in a dedicated table with full context.
**When to use:** All stage transitions -- scoring, sales, churn, manual, decay.

```python
# modules/crm/infrastructure/models/lifecycle_transition_model.py
from sqlalchemy import Column, String, DateTime, Enum, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from src.shared.domain.base_entity import Base
from src.modules.crm.domain.enums import LifecycleStage

class LifecycleTransitionModel(Base):
    __tablename__ = "lifecycle_transitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    from_stage = Column(Enum(LifecycleStage), nullable=True)  # null for initial
    to_stage = Column(Enum(LifecycleStage), nullable=False)

    reason = Column(String, nullable=False)     # Human-readable: "Score crossed MQL threshold (42.5 >= 40)"
    triggered_by = Column(String, nullable=False)  # Enum-like: scoring_rule | sale_event | churn_event | manual | decay

    score_at_transition = Column(Float, nullable=True)

    metadata = Column(JSONB, default=dict)      # Flexible context per trigger type
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())
```

**triggered_by schema recommendation:**
| Value | metadata contents |
|-------|-------------------|
| `scoring_rule` | `{"score": 42.5, "threshold": 40.0, "threshold_name": "mql", "triggering_event_id": "uuid"}` |
| `sale_event` | `{"sale_id": "uuid", "sale_stage": "CONVERSION", "amount": 99.0, "offer_id": "uuid"}` |
| `churn_event` | `{"source": "shopify", "subscription_id": "ext_id", "cancellation_reason": "..."}` |
| `manual` | `{"admin_user_id": "uuid", "note": "Manual override by admin"}` |
| `decay` | `{"previous_score": 45.0, "new_score": 35.0, "days_inactive": 3, "decay_rate": 0.05}` |
| `reactivation` | `{"sale_id": "uuid", "previous_stage": "churned"}` |

### Anti-Patterns to Avoid
- **Direct CRM import from Sales module:** Sales must emit events, not call CRM services directly. The EventBus decouples them.
- **Scoring in the API layer:** All scoring logic belongs in LifecycleService (application layer), never in routers.
- **Storing scores in computed_traits JSONB:** The decision specifies real columns. Do not backslide.
- **Using async in CRM services:** The entire CRM module uses sync SQLAlchemy sessions. Keep it sync. ARQ tasks create their own sync sessions via SessionLocal.
- **after_flush instead of after_commit:** Using after_flush would dispatch events before the transaction commits, which violates the "events processed after DB commit" constraint.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| After-commit event dispatch | Custom transaction tracking | SQLAlchemy `after_commit` event listener | SQLAlchemy already tracks transaction state reliably |
| Background job scheduling | Custom cron/timer thread | ARQ cron (existing from Phase 2) | Already proven, has retry, monitoring, Redis-backed |
| Score decay calculation | Real-time per-request decay | Batch recalculation in scheduled job | Computing decay for all profiles per-request is wasteful; batch at inactivity check time |
| Migration schema changes | Raw SQL | Alembic autogenerate | Already configured, handles enum types and JSONB |

**Key insight:** The inactivity batch job should compute decay AND check inactivity in the same pass. One query, two outcomes: update scores (with decay) and flag inactive profiles. Avoids scanning the table twice.

## Common Pitfalls

### Pitfall 1: Race Condition on Score Update
**What goes wrong:** Two concurrent journey_events for the same profile both read score=39, both add 2, both write 41. One update is lost.
**Why it happens:** No row-level locking on concurrent writes.
**How to avoid:** Use `SELECT ... FOR UPDATE` when reading the profile for score recalculation. In SQLAlchemy 2.0: `session.execute(select(CustomerProfileModel).where(...).with_for_update())`.
**Warning signs:** Scores seem to plateau or not reflect all events.

### Pitfall 2: Circular Event Dispatch
**What goes wrong:** Event handler emits another event, which triggers another handler, creating infinite loops.
**Why it happens:** Lifecycle transition fires "stage_changed" event, which triggers a handler that also transitions.
**How to avoid:** Keep event handlers focused. The scoring handler should NOT emit events. Only the originating action (journey_event write, sale creation) emits events. Transition logging is a side-effect, not an event.
**Warning signs:** Stack overflow or repeated transitions in audit log.

### Pitfall 3: Decay Retroactively Changing CUSTOMER Stage
**What goes wrong:** A CUSTOMER profile has its score decayed below the SQL threshold, triggering backward transition to SQL.
**Why it happens:** Decay logic doesn't check for the CUSTOMER stage exemption.
**How to avoid:** Explicitly skip decay for profiles where lifecycle_stage = CUSTOMER (or where stage was set by a sale event). The scoring config enforces this: "Decay paused for CUSTOMER stage."
**Warning signs:** Paying customers showing up as SQL or MQL in dashboards.

### Pitfall 4: Alembic Enum Migration on PostgreSQL
**What goes wrong:** Adding new enum values to PostgreSQL enum types fails because Alembic's autogenerate doesn't handle ALTER TYPE ADD VALUE.
**Why it happens:** PostgreSQL enum types are immutable once created. You need explicit ALTER TYPE statements.
**How to avoid:** For the lifecycle_transitions table, use `String` for triggered_by (not a PG enum). For LifecycleStage, it already has all 8 values -- no new values needed.
**Warning signs:** Migration fails with "type already exists" or "value already present."

### Pitfall 5: after_commit Fires on Empty Commits
**What goes wrong:** SQLAlchemy `after_commit` fires even when `session.commit()` is called with no pending changes.
**Why it happens:** session.commit() always triggers the event.
**How to avoid:** Check `session.new` or `session.dirty` before registering the listener, or make the event handler idempotent.
**Warning signs:** Duplicate events in logs for unchanged records.

### Pitfall 6: Batch Job Updating Stale Data
**What goes wrong:** Batch inactivity job reads profiles, processes them, but another request modifies the profile between read and write.
**Why it happens:** Long-running batch job holds stale data.
**How to avoid:** Process in small batches (100-500 profiles at a time). Use UPDATE ... WHERE for atomic conditional updates rather than read-modify-write.
**Warning signs:** is_inactive flag toggling unexpectedly.

## Code Examples

### Scoring Recalculation on Journey Event Write
```python
# modules/crm/application/services/lifecycle_service.py
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from uuid import UUID
from src.modules.crm.infrastructure.models.customer_model import (
    CustomerProfileModel, JourneyEventModel
)
from src.modules.crm.domain.scoring import (
    SCORING_WEIGHTS, SCORING_THRESHOLDS, DECAY_CONFIG
)
from src.modules.crm.domain.enums import LifecycleStage

class LifecycleService:
    def __init__(self, db: Session):
        self.db = db

    def recalculate_score(self, profile_id: UUID, tenant_id: UUID) -> float:
        """Recalculate lead_score from all journey_events for a profile."""
        # Lock the profile row to prevent concurrent updates
        stmt = (
            select(CustomerProfileModel)
            .where(
                CustomerProfileModel.id == profile_id,
                CustomerProfileModel.tenant_id == tenant_id,
            )
            .with_for_update()
        )
        profile = self.db.execute(stmt).scalar_one()

        # Skip scoring for CUSTOMER stage (sale-driven, decay paused)
        if profile.lifecycle_stage == LifecycleStage.CUSTOMER:
            return profile.lead_score

        # Sum weights from all journey_events
        events = self.db.execute(
            select(JourneyEventModel)
            .where(
                JourneyEventModel.profile_id == profile_id,
                JourneyEventModel.tenant_id == tenant_id,
            )
        ).scalars().all()

        score = 0.0
        all_weights = {
            **SCORING_WEIGHTS.engagement,
            **SCORING_WEIGHTS.intent,
        }
        for event in events:
            weight = all_weights.get(event.event_name, 0.0)
            score += weight

        # Apply fit score from profile traits (one-time)
        score += self._calculate_fit_score(profile)

        # Clamp to floor
        score = max(score, 0.0)

        # Update profile
        profile.lead_score = score

        # Check thresholds and transition if needed
        new_stage = self._determine_stage(score)
        if new_stage != profile.lifecycle_stage:
            self._transition(profile, new_stage, reason=f"Score {score} crossed threshold")

        self.db.commit()
        return score

    def _determine_stage(self, score: float) -> LifecycleStage:
        if score >= SCORING_THRESHOLDS.sql:
            return LifecycleStage.SQL
        elif score >= SCORING_THRESHOLDS.mql:
            return LifecycleStage.MQL
        elif score >= SCORING_THRESHOLDS.lead:
            return LifecycleStage.LEAD
        return LifecycleStage.SUBSCRIBER
```

### Sale Event Emission (After-Commit)
```python
# Modification to SaleService.create_sale()
from src.shared.domain.events import EventBus, DomainEvent

def create_sale(self, tenant_id, customer_id, offer_id, amount, ...):
    # ... existing logic ...
    sale = self.repository.save(sale)

    # Emit domain event (dispatched after commit)
    EventBus.publish(
        DomainEvent(
            event_name="sale_completed",
            tenant_id=tenant_id,
            payload={
                "sale_id": str(sale.id),
                "customer_id": str(customer_id),
                "stage": sale.stage.value,    # CONVERSION or EXPANSION
                "amount": sale.amount,
                "offer_id": str(offer_id),
            }
        ),
        session=self.repository.db
    )
    return sale
```

### Batch Inactivity Detection (ARQ Task)
```python
# Addition to analytics/workers/tasks.py (or new crm/workers/tasks.py)
async def run_inactivity_detection(ctx: dict) -> dict:
    """Batch job: flag inactive profiles and apply score decay."""
    from src.modules.crm.domain.scoring import INACTIVITY_CONFIG, DECAY_CONFIG
    from src.modules.crm.infrastructure.models.customer_model import (
        CustomerProfileModel, JourneyEventModel
    )
    from sqlalchemy import select, func, update
    from datetime import datetime, timedelta, timezone

    db_factory = ctx["db_factory"]
    db = db_factory()

    try:
        threshold_date = datetime.now(timezone.utc) - timedelta(days=INACTIVITY_CONFIG.inactive_days)

        # Find profiles whose latest journey_event is older than threshold
        # Use subquery for last_activity per profile
        latest_event = (
            select(
                JourneyEventModel.profile_id,
                func.max(JourneyEventModel.occurred_at).label("last_event_at")
            )
            .group_by(JourneyEventModel.profile_id)
        ).subquery()

        # Update is_inactive in batches
        # ... batch processing logic ...

        return {"status": "success", "profiles_flagged": count}
    finally:
        db.close()
```

## Additional Customer Profile Fields (Research-Informed)

Based on HubSpot and Salesforce default contact property schemas, the following fields are recommended for the customer_profiles migration. These support downstream phases 4-10.

### Recommended New Columns

| Column | Type | Default | Why Needed | Phase Used |
|--------|------|---------|------------|------------|
| `lifetime_value` | Float | 0.0 | Sum of all completed sale amounts | Phase 3 (CRM-03), Phase 9 (EXP-03) |
| `last_activity_at` | DateTime(tz) | null | Most recent journey_event occurred_at | Phase 3 (CRM-04), Phase 9 (ADO-04) |
| `is_inactive` | Boolean | false | Batch-computed inactivity flag | Phase 3 (CRM-04), Phase 9 (ADO-01) |
| `first_conversion_at` | DateTime(tz) | null | Date of first completed CONVERSION sale | Phase 8 (VEN-05) CAC calculation, Phase 9 (ADO-03) Time-to-Value |
| `first_seen_at` | DateTime(tz) | null | Date profile was created (mirrors created_at but explicit) | Funnel velocity metrics (Phase 5-8) |
| `lead_source` | String | null | Original acquisition channel (e.g., "manychat", "mailerlite", "sales_agent") | Phase 5 (CAP-02) capture attribution |
| `lead_source_detail` | String | null | Specific source detail (e.g., campaign name, DM channel) | Phase 5 (CAP-02) |

### Fields NOT Added (Rationale)

| Field | HubSpot/Salesforce Has It | Why Skip |
|-------|---------------------------|----------|
| `annual_revenue` | Yes (HubSpot) | B2C creator economy, not B2B. Revenue is per-sale, not annual company revenue |
| `job_title`, `company` | Yes (both) | Target users are individual creators, not enterprise contacts |
| `nps_score` | Yes (HubSpot) | Deferred to Phase 10 (Evangelization). Use computed_traits JSONB when needed |
| `owner_id` | Yes (Salesforce) | No sales rep assignment in this product -- AI Agent handles all |
| `likelihood_to_close` | Yes (HubSpot Enterprise) | ML-based prediction. lead_score + lifecycle_stage covers this for now |

## Scoring Weights and Decay Rate Recommendations

### Recommended Scoring Weights

Given the 3-channel reality (Sales Agent DMs, Manychat, Mailerlite) and creator-economy B2C context:

| Category | Event | Weight | Rationale |
|----------|-------|--------|-----------|
| **Engagement** | `page_view` | 1 | Low signal |
| **Engagement** | `email_opened` | 2 | Mailerlite open tracking |
| **Engagement** | `email_clicked` | 3 | Stronger engagement signal |
| **Engagement** | `social_interaction` | 1.5 | IG/TikTok like or comment |
| **Intent** | `form_submitted` | 5 | Landing page form fill |
| **Intent** | `message_sent` | 4 | DM conversation with Sales Agent |
| **Intent** | `contact_extracted` | 5 | Manychat captured email/phone |
| **Intent** | `checkout_started` | 8 | Shopify checkout initiation |
| **Intent** | `meeting_requested` | 10 | Highest intent short of purchase |
| **Intent** | `pricing_viewed` | 4 | Product page with pricing |
| **Fit** | `business_stage_active` | 10 | Active business = higher value |
| **Fit** | `financial_capacity_high` | 8 | Can afford premium offers |
| **Fit** | `sophistication_aware` | 6 | Product-aware or Most-aware |

### Recommended Thresholds

| Transition | Threshold | Context |
|------------|-----------|---------|
| SUBSCRIBER to LEAD | >= 10 | ~3-5 engagement events or 1 intent event |
| LEAD to MQL | >= 40 | Sustained engagement + at least 1-2 intent signals |
| MQL to SQL | >= 70 | Strong intent (meeting request + engagement history) |

### Recommended Decay Rate

**5% per day of inactivity** (daily_decay_rate = 0.05).

Rationale: Creator-economy sales cycles are short (7-30 days typically). At 5%/day:
- After 7 days inactive: score drops to ~70% of original (0.95^7 = 0.698)
- After 14 days inactive: score drops to ~49% (0.95^14 = 0.488)
- After 30 days inactive: score drops to ~21% (0.95^30 = 0.215)

This means a lead at MQL (score 40) who goes silent for 14 days drops to ~19.5, back to LEAD. Aggressive enough to keep the pipeline fresh, but not so aggressive that a weekend break causes demotion.

### Recommended Inactivity Threshold

**14 days** without any journey_event.

Rationale: Creator/infoproductor product cycles are typically weekly content + monthly launches. 14 days covers two content cycles. Aligns with the decay math above -- at 14 days the score has roughly halved, and the profile deserves an "inactive" flag for dashboard visibility.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual stage assignment | Automated scoring + thresholds | Standard since HubSpot/Pardot 2015+ | Eliminates manual CRM hygiene |
| Flat score (no decay) | Time-decayed scoring | Pardot Account Engagement, HubSpot 2024+ | Prevents stale leads from clogging pipeline |
| Direct service calls | Domain event bus | DDD standard pattern | Decouples bounded contexts |
| Real-time inactivity check | Batch + flag pattern | Standard for scale | Avoids N+1 queries on dashboard load |

## Open Questions

1. **Fit scoring trigger**
   - What we know: Fit scores (FinancialCapacity, SophisticationLevel, BusinessStage) come from profile traits, not journey_events
   - What's unclear: When are these traits set? Manual entry? Sales Agent classification? Brand Studio data?
   - Recommendation: Apply fit score on first calculation, store as a flag in computed_traits to avoid re-adding. Re-evaluate when traits change.

2. **Cancellation event source**
   - What we know: CRM-05 requires CHURNED triggered by Shopify/Stripe webhook cancellation events
   - What's unclear: Are Shopify/Stripe webhooks currently being received and stored as journey_events? The connections module exists but Shopify has known issues.
   - Recommendation: Create the handler and event contract. Use a manual API endpoint for testing. Real webhook integration deferred to when Shopify connection is repaired.

3. **Event registration timing**
   - What we know: EventBus.subscribe() needs to happen at app startup
   - What's unclear: Best place in FastAPI app lifecycle for event registration
   - Recommendation: Register handlers in a `register_event_handlers()` function called from FastAPI lifespan or main.py startup.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | `backend/pyproject.toml` (ruff only) -- no pytest config, uses defaults |
| Quick run command | `docker exec -t visionarias_brain_dev pytest tests/modules/crm/ -x -q` |
| Full suite command | `docker exec -t visionarias_brain_dev pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CRM-01 | Score recalculation triggers stage transitions (forward + backward + skip) | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/crm/test_lifecycle_scoring.py -x` | No -- Wave 0 |
| CRM-02 | CONVERSION sale event triggers CUSTOMER stage | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/crm/test_sale_lifecycle.py -x` | No -- Wave 0 |
| CRM-03 | EXPANSION sale increments lifetime_value, keeps CUSTOMER | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/crm/test_sale_lifecycle.py -x` | No -- Wave 0 |
| CRM-04 | Batch job flags inactive profiles after N days | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/crm/test_inactivity_detection.py -x` | No -- Wave 0 |
| CRM-05 | Cancellation event sets CHURNED stage | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/crm/test_churn_detection.py -x` | No -- Wave 0 |
| EventBus | After-commit dispatch, handler isolation | unit | `docker exec -t visionarias_brain_dev pytest tests/shared/test_event_bus.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `docker exec -t visionarias_brain_dev pytest tests/modules/crm/ -x -q`
- **Per wave merge:** `docker exec -t visionarias_brain_dev pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/modules/crm/__init__.py` -- package init
- [ ] `tests/modules/crm/conftest.py` -- CRM-specific fixtures (sample profiles, events, sales)
- [ ] `tests/modules/crm/test_lifecycle_scoring.py` -- covers CRM-01
- [ ] `tests/modules/crm/test_sale_lifecycle.py` -- covers CRM-02, CRM-03
- [ ] `tests/modules/crm/test_inactivity_detection.py` -- covers CRM-04
- [ ] `tests/modules/crm/test_churn_detection.py` -- covers CRM-05
- [ ] `tests/shared/__init__.py` -- package init
- [ ] `tests/shared/test_event_bus.py` -- EventBus unit tests

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `backend/src/modules/crm/` -- all domain entities, models, services, repositories read directly
- Codebase inspection: `backend/src/modules/analytics/workers/` -- ARQ worker pattern, scheduler, tasks
- Codebase inspection: `backend/src/core/database.py` -- sync SessionLocal, get_db dependency
- Codebase inspection: `backend/src/shared/domain/base_entity.py` -- Base declarative, BaseEntity Pydantic
- SQLAlchemy 2.0 docs: `after_commit` event listener for session-scoped post-commit hooks

### Secondary (MEDIUM confidence)
- [HubSpot default contact properties](https://knowledge.hubspot.com/properties/hubspots-default-contact-properties) -- lifecycle_stage, lead_score, last_activity_date, first_conversion fields
- [Salesforce Last Activity Date](https://help.salesforce.com/s/articleView?id=000385365&language=en_US&type=1) -- activity tracking patterns
- [fastapi-events GitHub](https://github.com/melvinkcx/fastapi-events) -- evaluated but rejected (requires ASGI middleware, doesn't work in ARQ workers)
- [Lead scoring best practices 2025](https://www.worknet.ai/blog/lead-scoring-best-practices) -- decay rates, tiered scoring
- [Pardot score decay](https://thespotforpardot.com/2024/01/05/how-to-deal-with-score-decay-in-account-engagement/) -- percentage decay model, half-life approach

### Tertiary (LOW confidence)
- Scoring weight values -- based on general B2C SaaS patterns adapted to 3-channel reality. Should be tuned with real data after Phase 3 ships.
- 14-day inactivity threshold -- informed by creator economy sales cycles but no direct data. Configurable, can be adjusted.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all patterns verified in codebase
- Architecture: HIGH -- EventBus pattern well-understood, codebase patterns clear
- Scoring weights/thresholds: MEDIUM -- reasonable defaults but need real-data tuning
- Pitfalls: HIGH -- based on known SQLAlchemy concurrency issues and PostgreSQL enum limitations

**Research date:** 2026-03-15
**Valid until:** 2026-04-15 (stable domain, no external API dependencies)
