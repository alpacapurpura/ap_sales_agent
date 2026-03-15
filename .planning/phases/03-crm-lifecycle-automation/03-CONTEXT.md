# Phase 3: CRM Lifecycle Automation - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement automated lifecycle stage transitions on customer_profiles based on scoring rules, business events (sales), and time-based detection (inactivity, churn). Add a domain event system for cross-module communication and a dedicated audit trail for all transitions. This phase makes CRM lifecycle data meaningful so downstream stages (4-10) can count profiles per stage accurately.

</domain>

<decisions>
## Implementation Decisions

### Scoring Thresholds & Rules
- **Fixed global thresholds** — same for all tenants (e.g. >10=LEAD, >40=MQL, >70=SQL). Can be made per-tenant later
- **Category-based scoring** with three dimensions: Engagement (opens, clicks, views), Intent (form fills, checkout starts, meeting requests), Fit (matches ideal customer profile via FinancialCapacity, SophisticationLevel, BusinessStage enums)
- **Event weights stored in Python config dict** (dataclass in CRM domain). Change requires deploy, versioned in git
- **Recalculation on every journey_event write** — real-time score update and threshold check
- **Stage skipping allowed** — if score jumps from 5 to 75, go directly from SUBSCRIBER to SQL. No forced sequential progression
- **Score is additive from events + time-based percentage decay** — see Score Decay section

### Score Decay
- **Percentage decay** — lose X% of current score per day of inactivity (rate to be determined during research)
- **Floor at 0** — score can never go negative
- **Backward transitions allowed** — if score drops below a threshold, profile moves back (e.g. MQL→LEAD)
- **Decay paused for CUSTOMER stage** — profiles that reached CUSTOMER via sale don't decay. Prevents CUSTOMER→SQL backward transition. Inactivity detection still applies separately

### Sale-Triggered Transitions
- **Domain event pattern** — SaleService emits 'sale_completed' event. CRM lifecycle handler subscribes and updates stage. Sales module doesn't import CRM directly
- **CONVERSION sale → lifecycle_stage = CUSTOMER** regardless of current stage (sale overrides scoring)
- **EXPANSION sale → increment lifetime_value, keep CUSTOMER stage**. EVANGELIST is reserved for referral/NPS behavior (Phase 10)
- **CHURNED reactivation** — new sale on a CHURNED profile restores lifecycle_stage to CUSTOMER and increments lifetime_value
- **Events processed after DB commit** — if handler fails, sale still exists; lifecycle update can be retried

### Domain Event Infrastructure
- **App-wide reusable EventBus in shared module** — any module can publish/subscribe. Future-proofs for Sales Agent events, connection revocation, etc.
- **After-commit processing** — event handlers fire after the triggering transaction commits. Handler failure doesn't roll back the original action
- **Implementation approach: Claude's discretion** — choose between in-process mediator or ARQ async queue based on existing patterns

### Inactivity & Churn Detection
- **Any journey_event counts as activity** — page_view, email_opened, message_sent all reset the inactivity timer
- **Dual detection strategy**: Scheduled batch job for bulk detection (this phase) + on-demand calculation for single-profile detail (deferred to future milestone)
- **Inactivity threshold: Claude's discretion** — research creator/infoproductor business cycles and pick a sensible default. Configurable in Python config dict
- **CHURNED triggered only by explicit cancellation events** (Shopify/Stripe webhooks). Inactivity flags is_inactive=true but does NOT change lifecycle_stage
- **Inactivity ≠ Churn** — inactive is a flag, churned is a lifecycle stage. They are independent concepts

### Transition Audit Trail
- **Dedicated lifecycle_transitions table**: (id, profile_id, tenant_id, from_stage, to_stage, reason, triggered_by, metadata JSONB, occurred_at)
- **triggered_by schema: Claude's discretion** — design the field structure based on what downstream dashboard queries will need (scoring_rule, sale_event, churn_event, manual, decay are the known trigger types)
- **Log everything** — forward, backward, sale-triggered, churn, reactivation, decay-driven. Complete history
- **Manual override supported** — admin can force a stage change via API, recorded as triggered_by='manual' with admin user in metadata

### New Fields on customer_profiles
- **Real columns** (not computed_traits JSONB): lifetime_value (Float), last_activity_at (DateTime), is_inactive (Boolean) — with indexes
- **Migration defaults**: Zero/null (lifetime_value=0, last_activity_at=null, is_inactive=false). Values correct after first batch job run
- **Research additional fields** — Investigate what Salesforce, HubSpot, and other major CRM platforms include on their lifecycle/contact models. Add any fields that are clearly needed for this milestone's downstream phases (4-10). This is a research task for gsd-phase-researcher

### Claude's Discretion
- Domain event implementation (in-process mediator vs ARQ async queue)
- Inactivity threshold default value (research-informed)
- Exact scoring weights per event type and category
- Decay rate percentage per day
- triggered_by field schema design
- Additional customer_profile fields (after researching Salesforce/HubSpot patterns)
- Batch job scheduling (run alongside ETL or separate schedule)

</decisions>

<specifics>
## Specific Ideas

- Lead sources for this project are limited to 3 channels: direct messages (Sales Agent handles), Manychat actions (contact extraction), and Mailerlite (contact base). Scoring weights should reflect this reality
- Identity resolution / cross-channel deduplication is critical — same person across WhatsApp, Mailerlite, Instagram DM must be unified. Basic `CustomerService.identify()` exists (UserID > Email > Phone priority) but needs smarter strategy. **Deferred to dedicated milestone**
- Sales Agent is also a qualifier — its MQL/SQL classification should eventually feed into lifecycle transitions. **Deferred to Sales Agent milestone**
- The user wants the schema to be comprehensive from day one — "revisa que hace Salesforce y otros grandes" — research phase should investigate major CRM lifecycle models before finalizing the field set
- Batch-first architecture from Phase 2 should be respected — daily inactivity detection runs alongside ETL pipeline

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `LifecycleStage` enum (crm/domain/enums.py): 8 stages already defined — SUBSCRIBER through CHURNED
- `CustomerProfile` domain entity: has lead_score (float), lifecycle_stage, computed_traits JSONB
- `CustomerProfileModel`: SQLAlchemy model with same fields, already has journey_events relationship
- `JourneyEventModel`: event_name, event_type, properties JSONB, occurred_at — the raw data for scoring
- `SaleService.create_sale()`: Already detects CONVERSION vs EXPANSION — just needs to emit domain event
- `SaleStage` enum: CONVERSION and EXPANSION already defined
- `CustomerService.identify()`: Basic identity resolution (UserID > Email > Phone priority)
- Scoring-related enums exist: FinancialCapacity, SophisticationLevel, AuthorityLevel, LeadTemperature, AvatarPersona

### Established Patterns
- DDD module boundaries: crm, sales, connections, analytics are separate bounded contexts
- Sync SQLAlchemy sessions (not async) in CRM module — service classes take Session in constructor
- Repository pattern: CustomerRepository, SaleRepository with standard CRUD
- ARQ task queue (from Phase 2) for async jobs — could be reused for batch inactivity detection
- Alembic for migrations

### Integration Points
- `PipelineService.move_stage()` (crm/application/services/lead_service.py:39): Current placeholder (`pass`) — replace with real implementation
- `SaleService.create_sale()` (crm/application/services/sale_service.py): Add domain event emission after sale creation
- `customer_profiles` table: Add new columns (lifetime_value, last_activity_at, is_inactive + research-informed fields)
- `shared` module: New EventBus infrastructure lives here for cross-module reuse
- ARQ worker (from Phase 2): Batch inactivity detection job can be added here

</code_context>

<deferred>
## Deferred Ideas

- **Identity resolution / cross-channel deduplication** — smarter unification strategy for same person across WhatsApp, Mailerlite, Instagram DM. Current basic resolution exists but needs a dedicated milestone for production-grade CDP dedup
- **Sales Agent as qualifier** — Sales Agent's MQL/SQL classification feeding into lifecycle transitions. Depends on Sales Agent milestone completion
- **On-demand inactivity calculation** — single-profile detail view showing exact inactivity status in real-time. Infrastructure for batch exists; on-demand deferred to future milestone
- **Per-tenant configurable thresholds** — UI for tenant-specific scoring thresholds and inactivity windows. Current approach uses global Python config dict

</deferred>

---

*Phase: 03-crm-lifecycle-automation*
*Context gathered: 2026-03-15*
