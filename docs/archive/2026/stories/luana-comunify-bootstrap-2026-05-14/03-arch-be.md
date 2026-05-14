<!-- voseo-allowed: arch doc cites BE service patterns + sales_agent runtime references per Slot 5 BRAND_VOICE SSoT (voice cloning compiled v2 distilled per tenant). -->
---
story_id: luana-comunify-bootstrap
surface: BE
sub_architect: architect-be
arch_version: 1
last_modified: 2026-05-14
links:
  spec: "01-spec.md"
  agentic_design: "02-design-agentic.md"
  consolidated_arch: "03-arch.md"
  story_11_be_precedent: "../../../../archive/2026/stories/luana-vitalia-bootstrap-2026-05-14/03-arch-be.md"
  rules:
    - ".claude/rules/backend-ddd.md"
    - ".claude/rules/tenant-isolation.md"
    - ".claude/rules/backend-migrations.md"
    - ".claude/rules/backend-quality.md"
    - ".claude/rules/master-data.md"
    - ".claude/rules/currency-handling.md"
    - ".claude/rules/architectural-fitness.md"
    - ".claude/rules/anti-duplication.md"
---

# 03-arch-be.md — Story 12 comunify backend surface

> Owner: `architect-be` skill (consumed via /architect orchestrator). Documento técnico capa BE.

---

## § 1. Decisión arquitectónica clave

**Módulo nuevo `comunify` en `luana-platform/comunify/backend/src/modules/comunify/`** con DDD Inside-Out estricto (`domain/infrastructure/application/api/`). Consume `@luana/core/*` packages via workspace imports (no bypass). **13 entidades nuevas** + extensions a tenant_profile (creator-specific fields) + reuse Story 11 payment lifts. Alembic snapshot consolidation pattern Story 10/11 replica. Cero `git pull`, cero feature branches — desarrollo en `development` rama paralelo Story 13 (parallel_safe=true per checkpoint).

**Tradeoff aceptado:** Story 12 NO migra modules/copilot/sales_agent existentes — solo CONSUMES via Extension SDK. Servicios BE (Cohort, Community, Subscription, Dunning, VoiceCloning, AuthorityVault) viven en comunify/ module, llaman `@luana/core/scheduling` (Q4=A reuse) + Story 11 payment adapters (Q6=B reuse). Esto evita cross-module tight coupling y mantiene Story 12 atómica.

**Voice cloning pipeline BE-side:** Async job orchestration (`VoiceDistillationService`) coordina upload chats → distillation worker → confidence scoring → personality_profiles.system_instruction update → Slot 5 cache invalidation event. Pipeline detail § 9.7.

---

## § 2. Pre-flight anti-duplication grep results

Per `.claude/rules/anti-duplication.md` Step 0 GATE — grep cross-codebase before write:

```bash
$ grep -rln "class.*Cohort\|class.*CohortMember" /home/chris/luana-platform/{core,vitalia,nicolify}/ 2>/dev/null
(empty)
# Verdict: NEW Cohort + CohortMember tables — vertical-creator-economy specific.

$ grep -rln "class.*Subscription\|class.*RecurringCharge" /home/chris/luana-platform/{core,vitalia,nicolify}/ 2>/dev/null
/home/chris/luana-platform/vitalia/backend/.../models/payment_intent_model.py
# Finding: Vitalia has VitaliaPaymentIntent (one-shot bookings). Comunify needs RECURRING subscriptions (different semantic).
# Decision: NEW `comunify_subscriptions` + `comunify_subscription_charges` tables.
# Anti-duplication candidate (D14): subscription module lift-shared to @luana/core/ Story 13+ when Lupulo needs subscriptions.

$ grep -rln "class.*CommunityPost\|class.*ModerationEvent" /home/chris/luana-platform/{core,vitalia,nicolify}/ 2>/dev/null
(empty)
# Verdict: NEW tables — community-specific.

$ grep -rln "class.*VoiceCloning\|class.*VoiceDistillation\|class.*PersonalityCompiler" /home/chris/luana-platform/ 2>/dev/null
(check personality_profiles in @luana/core/sales-agent — likely exists)
# Finding: PersonalityCompiler v2 already exists @luana/core/sales-agent (Nicolify cement post Sesion 2026-04-28).
# Comunify VOICE_CLONING uses the existing compiler — NEW pipeline is the EXTRACTION + COMPILATION INPUT preparation only.

$ grep -rln "class.*OfferLadder\|class.*LeadQualification" /home/chris/luana-platform/{core,vitalia,nicolify}/ 2>/dev/null
(empty)
# Verdict: NEW tables — vertical-creator-economy.

$ grep -rln "MercadoPago\|StripeConnect" /home/chris/luana-platform/core/ 2>/dev/null
# Verify Story 11 lifted to @luana/core/channels/payment/* — if lifted, CONSUME via core
# If NOT lifted (Story 11 kept vitalia-local), then LIFT in T-payment-1 Story 12 first ticket.
```

**Verdict:** zero blocking collisions. All 13 comunify tables NEW + justified. Voice cloning pipeline EXTRACTION layer NEW + compilation reuses existing `PersonalityCompiler` v2. Story 11 payment lifts CONSUMED via core (verify state during T-payment-1).

---

## § 3. Module surface

### 3.1 Comunify module DDD layout

```
luana-platform/comunify/backend/src/modules/comunify/
├── domain/
│   ├── entities/
│   │   ├── cohort.py                   # Cohort aggregate root
│   │   ├── cohort_member.py            # CohortMember
│   │   ├── cohort_broadcast.py         # CohortBroadcast + CohortBroadcastRecipient
│   │   ├── community_post.py           # CommunityPost + Attachment
│   │   ├── community_moderation_event.py
│   │   ├── subscription.py             # Subscription aggregate root
│   │   ├── subscription_charge.py
│   │   ├── offer_ladder.py             # 4-level ladder relations
│   │   ├── voice_cloning_samples.py    # uploaded samples metadata
│   │   ├── voice_distillation_job.py   # async distillation tracking
│   │   ├── authority_vault_item.py     # credentials/case_studies/press_mentions/awards collections
│   │   ├── lead_qualification_record.py
│   │   ├── community_audit_event.py
│   │   └── plan_tier_config.py         # cross-tenant catalog
│   ├── events/
│   │   ├── cohort_events.py            # CohortCreatedV1 / CohortMemberEnrolledV1 / CohortBroadcastSentV1
│   │   ├── community_events.py         # PostCreatedV1 / PostAutoApprovedV1 / PostPendingModerationV1 / DoxxingBlockedV1
│   │   ├── subscription_events.py      # SubscriptionCreatedV1 / RecurringChargeSucceededV1 / DunningStateChangeV1
│   │   ├── voice_cloning_events.py     # VoiceDistillationStartedV1 / VoiceDistillationCompletedV1 / VoiceRatifiedV1
│   │   └── compliance_events.py        # SpamBlockedV1 / NsfwBlockedV1 / DoxxingBlockedV1 / CrossTenantAttemptV1
│   ├── value_objects/
│   │   ├── capacity.py                 # Capacity (max + filled + waitlist_position)
│   │   ├── plan_features.py            # PlanFeatures (frozen set features_enabled)
│   │   ├── moderation_classifier_score.py  # ModerationScore (spam + nsfw + doxxing + confidence)
│   │   └── compiled_voice.py           # CompiledVoice (6 bloques structured)
│   └── exceptions.py
├── infrastructure/
│   ├── models/                         # SQLAlchemy 2.0 ORM models (Mapped[])
│   │   ├── cohort_model.py
│   │   ├── cohort_member_model.py
│   │   ├── cohort_broadcast_model.py
│   │   ├── cohort_broadcast_recipient_model.py
│   │   ├── community_post_model.py
│   │   ├── community_post_attachment_model.py
│   │   ├── community_moderation_event_model.py
│   │   ├── subscription_model.py
│   │   ├── subscription_charge_model.py
│   │   ├── offer_ladder_model.py
│   │   ├── voice_cloning_samples_model.py
│   │   ├── voice_distillation_job_model.py
│   │   ├── authority_vault_item_model.py
│   │   ├── lead_qualification_record_model.py
│   │   ├── community_audit_log_model.py
│   │   └── plan_tier_config_model.py
│   ├── repositories/
│   │   ├── cohort_repository.py
│   │   ├── cohort_member_repository.py
│   │   ├── cohort_broadcast_repository.py
│   │   ├── community_post_repository.py
│   │   ├── community_moderation_repository.py
│   │   ├── subscription_repository.py
│   │   ├── offer_ladder_repository.py
│   │   ├── voice_cloning_samples_repository.py
│   │   ├── voice_distillation_job_repository.py
│   │   ├── authority_vault_repository.py
│   │   ├── lead_qualification_repository.py
│   │   ├── community_audit_log_repository.py
│   │   └── plan_tier_config_repository.py  # cross-tenant
│   ├── advisory_locks.py               # Postgres advisory locks for cohort enrollment race + subscription state
│   └── adapters/
│       ├── clerk_webhook_adapter.py    # Clerk signup webhook → tenant create
│       ├── whatsapp_webhook_adapter.py # WhatsApp Business API → sales_agent dispatch
│       └── manychat_webhook_adapter.py # IG DM → sales_agent dispatch
├── application/
│   ├── services/
│   │   ├── onboarding_service.py       # creator profile + niche + plan tier + first offer
│   │   ├── cohort_service.py           # CRUD + enrollment + capacity + roster
│   │   ├── cohort_broadcast_service.py # rate-limit pre-flight + dispatch + delivery tracking
│   │   ├── community_post_service.py   # create + moderation routing
│   │   ├── community_moderation_service.py  # classifier dispatch + creator action handling
│   │   ├── subscription_service.py     # create + cancel + tier upgrade
│   │   ├── dunning_service.py          # retry state machine + LangGraph integration
│   │   ├── offer_ladder_service.py     # 4-level ladder CRUD + gap detection
│   │   ├── voice_cloning_service.py    # samples upload + distillation orchestration + ratify
│   │   ├── authority_vault_service.py  # CRUD subsections + URL validation
│   │   ├── compliance_event_service.py # community_audit_log writes (best-effort)
│   │   └── pii_scanner_service.py      # offer description + testimonial input scan
│   ├── event_handlers/
│   │   ├── voice_ratified_handler.py   # → invalidate Slot 5 cache for tenant
│   │   ├── subscription_charge_succeeded_handler.py
│   │   ├── subscription_charge_failed_handler.py  # → DunningWorkflow trigger
│   │   ├── community_post_created_handler.py  # → moderation classifier dispatch
│   │   └── cohort_member_enrolled_handler.py
│   └── tasks/                          # Async tasks (workers via shared.scheduling cron + ARQ)
│       ├── seed_fixture_creators_task.py
│       ├── voice_distillation_worker.py
│       ├── subscription_recurring_charge_worker.py
│       └── community_moderation_async_worker.py
├── api/
│   ├── routes.py                       # FastAPI APIRouter (redirect_slashes=False)
│   ├── dtos/
│   │   ├── onboarding_dtos.py
│   │   ├── cohort_dtos.py
│   │   ├── community_dtos.py
│   │   ├── subscription_dtos.py
│   │   ├── offer_ladder_dtos.py
│   │   ├── voice_cloning_dtos.py
│   │   ├── authority_vault_dtos.py
│   │   └── compliance_dtos.py
│   └── webhook_routes.py               # Stripe + MercadoPago + Clerk + WhatsApp + ManyChat
├── agentic/                            # (see 03-arch-agentic.md)
├── copilot/                            # (see 03-arch-agentic.md)
├── brand/                              # (see 03-arch-agentic.md voice_cloning/)
├── payment/                            # Channel adapters (3 — consume Story 11 lifts)
│   ├── stripe_connect_adapter.py
│   ├── mercadopago_adapter.py
│   └── tokenized_recurring_adapter.py
├── extensions.py                       # Single register_all entry — EP-1..EP-18
└── __init__.py
```

### 3.2 Naming conventions

Per `.claude/rules/backend-quality.md` + Story 10/11 precedent:
- ORM models: `Comunify{Entity}Model` (e.g., `ComunifyCohortModel`).
- Domain entities: `{Entity}` (no `Comunify` prefix in domain layer — bounded context).
- DTOs: `{Verb}{Entity}Request` / `{Verb}{Entity}Response` (e.g., `CreateCohortRequest`).
- Repositories: `{Entity}Repository`.
- Services: `{Entity}Service`.

---

## § 4. SQLAlchemy 2.0 async models (selected — full DDL in § 5 migration)

### 4.1 `ComunifyCohortModel`

```python
class ComunifyCohortModel(Base):
    __tablename__ = "comunify_cohorts"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    offer_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    capacity_max: Mapped[int] = mapped_column(nullable=False)
    capacity_filled: Mapped[int] = mapped_column(nullable=False, default=0)
    capacity_waitlist: Mapped[int] = mapped_column(nullable=False, default=0)
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    enrollment_criteria: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_comunify_cohorts_tenant_status", "tenant_id", "status"),
        Index("ix_comunify_cohorts_tenant_slug", "tenant_id", "slug", unique=True),
    )
```

### 4.2 `ComunifyCohortMemberModel`

```python
class ComunifyCohortMemberModel(Base):
    __tablename__ = "comunify_cohort_members"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    cohort_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    subscriber_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    tier: Mapped[str] = mapped_column(String(32), nullable=False, default="regular")  # regular | premium
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")  # active | suspended | dropped
    engagement_score: Mapped[int] = mapped_column(nullable=False, default=50)  # 0-100
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    enrollment_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    waitlist_position: Mapped[int | None] = mapped_column(nullable=True)
    pre_moderation_count: Mapped[int] = mapped_column(nullable=False, default=3)  # decrements per approved post
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_comunify_cohort_members_tenant_cohort", "tenant_id", "cohort_id"),
        Index("ix_comunify_cohort_members_subscriber", "subscriber_id"),
        UniqueConstraint("tenant_id", "cohort_id", "subscriber_id", name="uq_cohort_member"),
    )
```

### 4.3 `ComunifyCommunityPostModel`

```python
class ComunifyCommunityPostModel(Base):
    __tablename__ = "comunify_community_posts"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    author_member_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    cohort_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)  # null = community-wide
    content: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending_moderation")
    spam_score: Mapped[float | None] = mapped_column(nullable=True)
    nsfw_score: Mapped[float | None] = mapped_column(nullable=True)
    doxxing_detected: Mapped[bool] = mapped_column(nullable=False, default=False)
    moderation_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    likes_count: Mapped[int] = mapped_column(nullable=False, default=0)
    replies_count: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_comunify_posts_tenant_status_created", "tenant_id", "status", "created_at"),
        Index("ix_comunify_posts_tenant_author", "tenant_id", "author_member_id"),
    )
```

### 4.4 `ComunifySubscriptionModel`

```python
class ComunifySubscriptionModel(Base):
    __tablename__ = "comunify_subscriptions"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    subscriber_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    offer_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    plan_kind: Mapped[str] = mapped_column(String(32), nullable=False)  # cohort_installments | monthly_membership
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")  # active | past_due | suspended | cancelled | cancelled_pending_end_of_period
    dunning_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    next_charge_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    access_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    installments_total: Mapped[int | None] = mapped_column(nullable=True)
    installments_completed: Mapped[int] = mapped_column(nullable=False, default=0)
    monthly_amount: Mapped[Decimal | None] = mapped_column(Numeric(precision=14, scale=2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    gateway: Mapped[str] = mapped_column(String(32), nullable=False)  # mercadopago | stripe_connect | tokenized_recurring
    gateway_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_method_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_comunify_subs_tenant_status", "tenant_id", "status"),
        Index("ix_comunify_subs_tenant_next_charge", "tenant_id", "next_charge_at"),
        Index("ix_comunify_subs_subscriber", "subscriber_id"),
    )
```

### 4.5 `ComunifySubscriptionChargeModel`

```python
class ComunifySubscriptionChargeModel(Base):
    __tablename__ = "comunify_subscription_charges"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    subscription_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    installment_n: Mapped[int | None] = mapped_column(nullable=True)
    billing_period: Mapped[str] = mapped_column(String(7), nullable=False)  # "2026-05"
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=14, scale=2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)  # succeeded | failed | pending | refunded
    gateway_charge_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    succeeded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_comunify_charges_tenant_status_attempted", "tenant_id", "status", "attempted_at"),
        UniqueConstraint("subscription_id", "billing_period", "installment_n", name="uq_charge_period_installment"),
    )
```

### 4.6 `ComunifyOfferLadderModel`

```python
class ComunifyOfferLadderModel(Base):
    __tablename__ = "comunify_offer_ladders"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True, unique=True)
    level_1_offer_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)  # lead_magnet
    level_2_offer_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)  # tripwire
    level_3_offer_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)  # core
    level_4_offer_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)  # premium
    gap_acknowledged: Mapped[bool] = mapped_column(nullable=False, default=False)
    completeness_score: Mapped[int] = mapped_column(nullable=False, default=0)  # 0-100
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

### 4.7 `ComunifyVoiceCloningSamplesModel`

```python
class ComunifyVoiceCloningSamplesModel(Base):
    __tablename__ = "comunify_voice_cloning_samples"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True, unique=True)
    chats_count: Mapped[int] = mapped_column(nullable=False, default=0)
    voice_notes_count: Mapped[int] = mapped_column(nullable=False, default=0)
    upload_history: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)  # [{filename, type, count, uploaded_at}]
    statistics_post_distill: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {dialect, vocabulary_anchors, confidence}
    raw_samples_deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_distillation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

### 4.8 `ComunifyVoiceDistillationJobModel`

```python
class ComunifyVoiceDistillationJobModel(Base):
    __tablename__ = "comunify_voice_distillation_jobs"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")  # queued | running_wave_1 | ... | completed | failed
    samples_count: Mapped[int] = mapped_column(nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(nullable=True)
    compiled_blocks: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {identidad, dialecto, vocabulario, registro, asíNO, anclajes}
    error_reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(precision=8, scale=4), nullable=True)
    ratified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_comunify_voice_jobs_tenant_status", "tenant_id", "status"),
    )
```

### 4.9 `ComunifyCommunityAuditLogModel`

```python
class ComunifyCommunityAuditLogModel(Base):
    __tablename__ = "comunify_community_audit_log"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # spam_blocked | nsfw_blocked | doxxing_blocked | cross_tenant_attempt | etc
    severity: Mapped[str] = mapped_column(String(16), nullable=False)  # info | medium | high
    member_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    post_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    target_member_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)  # for doxxing victim
    payload_redacted: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # PII sanitized
    actor_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    actor_type: Mapped[str | None] = mapped_column(String(32), nullable=True)  # creator | sales_agent | moderator | system
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    # NO deleted_at — audit log immutable, 5-year retention via purge job

    __table_args__ = (
        Index("ix_comunify_audit_tenant_event_created", "tenant_id", "event_type", "created_at"),
    )
```

### 4.10 Remaining models (briefer schema patterns)

- **`ComunifyCohortBroadcastModel`** — broadcast metadata (cohort_id + content + audience_filter + sent_at + sent_count + recipients_count).
- **`ComunifyCohortBroadcastRecipientModel`** — per-recipient delivery (broadcast_id + member_id + delivered_at + opened_at + replied_at + channel).
- **`ComunifyCommunityPostAttachmentModel`** — image/video (post_id + url + nsfw_score + mime_type + size_bytes).
- **`ComunifyCommunityModerationEventModel`** — moderation classifier history (post_id + classifier_version + scores JSONB + action + actor_id).
- **`ComunifyAuthorityVaultItemModel`** — single table, polymorphic kind enum (credentials | case_studies | press_mentions | awards) + JSONB content.
- **`ComunifyLeadQualificationRecordModel`** — qualify_for_cohort snapshot (lead_id + cohort_id + fit + recommended_tier + fit_score + lead_data JSONB).
- **`ComunifyPlanTierConfigModel`** — cross-tenant catalog (plan_tier slug + features_enabled JSONB + price_usd_monthly).

---

## § 5. Alembic migrations (idempotent IF NOT EXISTS per Story 10/11 cement)

### 5.1 Migration file structure

```
luana-platform/comunify/backend/alembic/versions/
└── 001_comunify_initial_snapshot.py     # Single consolidated snapshot all comunify tables
```

### 5.2 Snapshot pattern (Story 10/11 T-10 replica)

```python
# 001_comunify_initial_snapshot.py
"""Comunify initial snapshot — all tables idempotent.

Revision ID: 001_comunify
Revises: <story_11_consolidated_snapshot OR latest head>
Create Date: 2026-05-15
"""
from alembic import op

revision = "001_comunify"
down_revision = "<story_11_consolidated_snapshot>"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─────────────────────────────────────────────────────────────
    # comunify_cohorts
    # ─────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS comunify_cohorts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            name VARCHAR(120) NOT NULL,
            slug VARCHAR(80) NOT NULL,
            offer_id UUID NOT NULL,
            capacity_max INTEGER NOT NULL,
            capacity_filled INTEGER NOT NULL DEFAULT 0,
            capacity_waitlist INTEGER NOT NULL DEFAULT 0,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'draft',
            enrollment_criteria JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_comunify_cohorts_tenant_status ON comunify_cohorts (tenant_id, status);")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_comunify_cohorts_tenant_slug ON comunify_cohorts (tenant_id, slug);")

    # comunify_cohort_members
    op.execute("""
        CREATE TABLE IF NOT EXISTS comunify_cohort_members (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            cohort_id UUID NOT NULL,
            subscriber_id UUID NOT NULL,
            tier VARCHAR(32) NOT NULL DEFAULT 'regular',
            status VARCHAR(32) NOT NULL DEFAULT 'active',
            engagement_score INTEGER NOT NULL DEFAULT 50,
            last_active_at TIMESTAMPTZ,
            enrollment_at TIMESTAMPTZ NOT NULL,
            waitlist_position INTEGER,
            pre_moderation_count INTEGER NOT NULL DEFAULT 3,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ,
            CONSTRAINT uq_cohort_member UNIQUE (tenant_id, cohort_id, subscriber_id)
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_comunify_cohort_members_tenant_cohort ON comunify_cohort_members (tenant_id, cohort_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_comunify_cohort_members_subscriber ON comunify_cohort_members (subscriber_id);")

    # comunify_cohort_broadcasts + comunify_cohort_broadcast_recipients
    # comunify_community_posts + comunify_community_post_attachments + comunify_community_moderation_events
    # comunify_subscriptions + comunify_subscription_charges
    # comunify_offer_ladders
    # comunify_voice_cloning_samples + comunify_voice_distillation_jobs
    # comunify_authority_vault_items
    # comunify_lead_qualification_records
    # comunify_community_audit_log
    # comunify_plan_tier_configs
    # — all using CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS (15 tables total)

    # NEVER op.create_table() / op.add_column() / op.create_index() (NOT idempotent)
    # NEVER sa.Enum() in create_table (broken SA 2.0.27 — use raw SQL CREATE TYPE)


def downgrade() -> None:
    # Rollback per table — for dev iteration only; prod uses snapshot rebuild
    op.execute("DROP TABLE IF EXISTS comunify_plan_tier_configs;")
    op.execute("DROP TABLE IF EXISTS comunify_community_audit_log;")
    op.execute("DROP TABLE IF EXISTS comunify_lead_qualification_records;")
    op.execute("DROP TABLE IF EXISTS comunify_authority_vault_items;")
    op.execute("DROP TABLE IF EXISTS comunify_voice_distillation_jobs;")
    op.execute("DROP TABLE IF EXISTS comunify_voice_cloning_samples;")
    op.execute("DROP TABLE IF EXISTS comunify_offer_ladders;")
    op.execute("DROP TABLE IF EXISTS comunify_subscription_charges;")
    op.execute("DROP TABLE IF EXISTS comunify_subscriptions;")
    op.execute("DROP TABLE IF EXISTS comunify_community_moderation_events;")
    op.execute("DROP TABLE IF EXISTS comunify_community_post_attachments;")
    op.execute("DROP TABLE IF EXISTS comunify_community_posts;")
    op.execute("DROP TABLE IF EXISTS comunify_cohort_broadcast_recipients;")
    op.execute("DROP TABLE IF EXISTS comunify_cohort_broadcasts;")
    op.execute("DROP TABLE IF EXISTS comunify_cohort_members;")
    op.execute("DROP TABLE IF EXISTS comunify_cohorts;")
```

### 5.3 Pre-merge verification

- Run migration 2x sin error (idempotent test).
- Arch fitness `test_comunify_migrations_idempotent.py` parses raw SQL pattern `IF NOT EXISTS` presence in every DDL statement.
- Clone DB workflow per `.claude/rules/backend-migrations.md`.

---

## § 6. Endpoints (REST per spec § 7.1)

### 6.1 Onboarding endpoints

| Method | Path | Request DTO | Response DTO | Auth | Notes |
|---|---|---|---|---|---|
| `POST` | `/api/v1/comunify/onboarding/creator-profile` | `CreateCreatorProfileRequest` | `CreateCreatorProfileResponse` | Clerk JWT | Creates tenant + tenant_profile + initializes BrandConfig |
| `POST` | `/api/v1/comunify/onboarding/check-handle` | `CheckHandleRequest` | `CheckHandleResponse` | Clerk JWT (optional) | Async validation handle uniqueness |
| `GET` | `/api/v1/comunify/onboarding/plans` | — | `PlanTierListResponse` | Clerk JWT (optional) | Lists plan_tiers |
| `POST` | `/api/v1/comunify/onboarding/subscribe` | `SubscribeRequest` | `SubscribeResponse` | Clerk JWT | Stripe Checkout session creation |
| `POST` | `/api/v1/comunify/webhooks/clerk` | (raw) | `WebhookAck` | Clerk webhook signature | Idempotent signup handler |

### 6.2 Brand Studio + Voice Cloning endpoints

| Method | Path | Request DTO | Response DTO | Auth | Notes |
|---|---|---|---|---|---|
| `GET` | `/api/v1/brand-studio/sections` | — | `BrandStudioSectionsResponse` | Clerk JWT | Consumes @luana/core/brand-studio |
| `PATCH` | `/api/v1/brand-studio/sections/{section}` | `PatchSectionRequest` | `PatchSectionResponse` | Clerk JWT | Autosave per section |
| `POST` | `/api/v1/comunify/voice-cloning/samples` | `UploadSamplesRequest` (multipart) | `UploadSamplesResponse` | Clerk JWT | Upload chats ZIP / voice notes |
| `GET` | `/api/v1/comunify/voice-cloning/samples/status` | — | `SamplesStatusResponse` | Clerk JWT | Counter + dialect detection |
| `POST` | `/api/v1/comunify/voice-cloning/distill` | `DistillRequest` | `DistillJobResponse` | Clerk JWT | Kicks async distillation |
| `GET` | `/api/v1/comunify/voice-cloning/distillation/{job_id}` | — | `DistillJobStatusResponse` | Clerk JWT | Polling progress |
| `POST` | `/api/v1/comunify/voice-cloning/ratify` | `RatifyRequest` | `RatifyResponse` | Clerk JWT | Final ratification → Slot 5 cache invalidate |

### 6.3 Authority Vault endpoints

| Method | Path | Request DTO | Response DTO | Auth | Notes |
|---|---|---|---|---|---|
| `GET` | `/api/v1/comunify/authority-vault` | — | `AuthorityVaultResponse` | Clerk JWT | All subsections |
| `POST` | `/api/v1/comunify/authority-vault/credentials` | `AddCredentialRequest` | `CredentialResponse` | Clerk JWT | Add credential |
| `POST` | `/api/v1/comunify/authority-vault/case-studies` | `AddCaseStudyRequest` | `CaseStudyResponse` | Clerk JWT | |
| `POST` | `/api/v1/comunify/authority-vault/press-mentions` | `AddPressMentionRequest` | `PressMentionResponse` | Clerk JWT | |
| `POST` | `/api/v1/comunify/authority-vault/awards` | `AddAwardRequest` | `AwardResponse` | Clerk JWT | |
| `POST` | `/api/v1/comunify/authority-vault/validate-url` | `ValidateUrlRequest` | `ValidateUrlResponse` | Clerk JWT | Async URL reachability check |

### 6.4 Offer + Ladder endpoints

| Method | Path | Request DTO | Response DTO | Auth | Notes |
|---|---|---|---|---|---|
| `GET` | `/api/v1/offers/presets/coaching_offers_v1` | — | `OfferPresetResponse` | Clerk JWT | Comunify preset config |
| `POST` | `/api/v1/offers` | `CreateOfferRequest` | `CreateOfferResponse` | Clerk JWT | Reuse @luana/core/offer-studio |
| `GET` | `/api/v1/offers` | (query: status?, value_level?) | `OfferListResponse` | Clerk JWT | List |
| `GET` | `/api/v1/comunify/ladder` | — | `OfferLadderResponse` | Clerk JWT | Current ladder per tenant |
| `PATCH` | `/api/v1/comunify/ladder/connections` | `UpdateLadderConnectionsRequest` | `OfferLadderResponse` | Clerk JWT | Drag-drop level updates |

### 6.5 Cohort endpoints

| Method | Path | Request DTO | Response DTO | Auth | Notes |
|---|---|---|---|---|---|
| `POST` | `/api/v1/comunify/cohorts` | `CreateCohortRequest` | `CreateCohortResponse` | Clerk JWT | Creates cohort with offer linkage |
| `GET` | `/api/v1/comunify/cohorts` | (query: status?, page) | `CohortListResponse` | Clerk JWT | Paginated list |
| `GET` | `/api/v1/comunify/cohorts/{id}` | — | `CohortDetailResponse` | Clerk JWT | Detail + roster summary |
| `GET` | `/api/v1/comunify/cohorts/{id}/roster` | (query: tier?, engagement_bucket?, page) | `CohortRosterResponse` | Clerk JWT | Members with engagement + last_active |
| `POST` | `/api/v1/comunify/cohorts/{id}/enroll` | `EnrollCohortRequest` | `EnrollCohortResponse` | Clerk JWT or signed token | Advisory lock + capacity check |
| `POST` | `/api/v1/comunify/cohorts/{id}/broadcasts` | `SendBroadcastRequest` | `SendBroadcastResponse` | Clerk JWT | Rate-limit pre-flight |
| `GET` | `/api/v1/comunify/cohorts/{id}/broadcasts` | — | `BroadcastListResponse` | Clerk JWT | List broadcasts + analytics |

### 6.6 Community endpoints

| Method | Path | Request DTO | Response DTO | Auth | Notes |
|---|---|---|---|---|---|
| `GET` | `/api/v1/comunify/community/feed` | (query: cohort_id?, page) | `CommunityFeedResponse` | Clerk JWT | Cross-cohort feed |
| `POST` | `/api/v1/comunify/community/posts` | `CreatePostRequest` | `CreatePostResponse` | Clerk JWT (member) | Triggers moderation classifier |
| `GET` | `/api/v1/comunify/community/moderation/inbox` | (query: page) | `ModerationInboxResponse` | Clerk JWT (creator) | Pending posts |
| `POST` | `/api/v1/comunify/community/moderation/{post_id}/action` | `ModerationActionRequest` | `ModerationActionResponse` | Clerk JWT (creator) | Approve / Reject+Warn / Delete+Ban |

### 6.7 Subscription endpoints

| Method | Path | Request DTO | Response DTO | Auth | Notes |
|---|---|---|---|---|---|
| `GET` | `/api/v1/comunify/subscriptions` | (query: status?, page) | `SubscriptionListResponse` | Clerk JWT | Active + past_due + cancelled |
| `GET` | `/api/v1/comunify/subscriptions/{id}` | — | `SubscriptionDetailResponse` | Clerk JWT | Detail + payment history |
| `POST` | `/api/v1/comunify/subscriptions/{id}/cancel` | `CancelSubscriptionRequest` | `CancelSubscriptionResponse` | Clerk JWT or signed subscriber token | Subscriber-initiated cancel |
| `POST` | `/api/v1/comunify/subscriptions/{id}/resend-payment-link` | — | `ResendPaymentLinkResponse` | Clerk JWT | Re-sends to past_due subscribers |
| `GET` | `/api/v1/comunify/subscriptions/metrics` | — | `SubscriptionMetricsResponse` | Clerk JWT | MRR + active count + churn |

### 6.8 Compliance endpoints

| Method | Path | Request DTO | Response DTO | Auth | Notes |
|---|---|---|---|---|---|
| `GET` | `/api/v1/comunify/community-audit/events` | (query: event_type, date_range, severity, page) | `AuditEventListResponse` | Clerk JWT | Paginated audit log |
| `GET` | `/api/v1/comunify/community-audit/export-csv` | (query: same filters) | `text/csv` stream | Clerk JWT | CSV export |

### 6.9 Webhook receivers

| Method | Path | Auth | Notes |
|---|---|---|---|
| `POST` | `/api/v1/comunify/webhooks/stripe` | Stripe HMAC signature | payment_intent.succeeded/failed + subscription events |
| `POST` | `/api/v1/comunify/webhooks/mercadopago` | MP IPN | Payment status updates + recurring |
| `POST` | `/api/v1/comunify/webhooks/clerk` | Clerk signature | Signup → tenant create |
| `POST` | `/api/v1/comunify/webhooks/whatsapp/inbound` | WhatsApp Business API token | WhatsApp → sales_agent dispatch |
| `POST` | `/api/v1/comunify/webhooks/manychat/inbound` | ManyChat token | IG DM → sales_agent dispatch |

---

## § 7. Pydantic DTOs (v2 ConfigDict)

### 7.1 Pattern

```python
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from decimal import Decimal
from datetime import datetime

class CreateCohortRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    name: str = Field(..., min_length=2, max_length=120)
    offer_id: UUID
    capacity_max: int = Field(..., ge=2, le=500)
    start_date: datetime
    end_date: datetime
    enrollment_criteria: dict = Field(default_factory=dict)

class CreateCohortResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cohort_id: UUID
    slug: str
    status: str
    capacity_filled: int = 0
    capacity_max: int
```

### 7.2 PII sanitization at response_model layer

Per Tessl `pii-sanitisation.md`:

```python
class CohortMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name_display: str  # "María D." (first name + last initial)
    tier: str
    engagement_bucket: Literal["high", "medium", "low"]
    last_active_at: datetime | None
    # Raw phone/email/full_last_name NOT exposed
```

---

## § 8. Repositories

### 8.1 Pattern

```python
class CohortRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self._session = session
        self._tenant_id = tenant_id  # MANDATORY constructor param

    async def get_by_id(self, cohort_id: UUID) -> Cohort | None:
        stmt = (
            select(ComunifyCohortModel)
            .where(
                ComunifyCohortModel.id == cohort_id,
                ComunifyCohortModel.tenant_id == self._tenant_id,  # MANDATORY
                ComunifyCohortModel.deleted_at.is_(None),
            )
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return Cohort.from_model(row) if row else None
```

### 8.2 Repositories inventory (13)

- `CohortRepository` / `CohortMemberRepository` / `CohortBroadcastRepository`
- `CommunityPostRepository` / `CommunityModerationRepository`
- `SubscriptionRepository` / `SubscriptionChargeRepository`
- `OfferLadderRepository`
- `VoiceCloningSamplesRepository` / `VoiceDistillationJobRepository`
- `AuthorityVaultRepository`
- `LeadQualificationRecordRepository`
- `CommunityAuditLogRepository`
- `PlanTierConfigRepository` (cross-tenant catalog — NO tenant_id filter)

---

## § 9. Services (DDD application layer)

### 9.1 `OnboardingService`

```python
class OnboardingService:
    async def create_creator_profile(
        self,
        clerk_user_id: str,
        request: CreateCreatorProfileRequest,
    ) -> Tenant:
        """Idempotent: same clerk_user_id within 1s window → returns existing tenant."""
        # 1. Idempotency check via shared.idempotency
        # 2. Validate creator_handle uniqueness
        # 3. Create tenant in luana_core_iam.tenants
        # 4. Create tenant_profile with creator_handle + niche + country + plan_tier
        # 5. Set BrandConfig (consume comunify/config/brand.yaml)
        # 6. Emit TenantCreatedV1 event (outbox)
```

### 9.2 `CohortService`

```python
class CohortService:
    async def enroll_member(
        self,
        cohort_id: UUID,
        subscriber_id: UUID,
        tenant_id: UUID,
    ) -> CohortMember:
        """Atomic enrollment with advisory lock per (cohort_id, enrollment_slot)."""
        # 1. Acquire pg_advisory_lock(hash(cohort_id))
        # 2. Check capacity_filled < capacity_max
        # 3. If full → waitlist (capacity_waitlist increment, return waitlist_position)
        # 4. If room → create cohort_member + capacity_filled increment
        # 5. Emit CohortMemberEnrolledV1 event
        # 6. Release advisory lock
```

### 9.3 `CommunityModerationService`

```python
class CommunityModerationService:
    async def classify_post(
        self,
        post: CommunityPost,
        tenant_id: UUID,
    ) -> ModerationClassifierResult:
        """Runs spam + nsfw + doxxing classifiers (Haiku 4.5)."""
        # 1. LLM classifier (Haiku) — spam_score + nsfw_score + reasoning
        # 2. Doxxing detection (regex + cross-ref cohort_members.phone/email)
        # 3. Status routing: auto_approve | pending_moderation | rejected_doxxing | rejected_nsfw
        # 4. Persist moderation_event row
        # 5. Emit PostAutoApprovedV1 OR PostPendingModerationV1 event
```

### 9.4 `SubscriptionService` + `DunningService`

```python
class SubscriptionService:
    async def create_subscription(
        self,
        request: CreateSubscriptionRequest,
        tenant_id: UUID,
    ) -> Subscription:
        """Creates subscription + tokenizes payment method + schedules first charge."""
        # 1. Idempotency check
        # 2. Adapter dispatch (MP / Stripe / Tokenized)
        # 3. Tokenize payment method
        # 4. Schedule first charge (next_charge_at = NOW + cycle)
        # 5. Emit SubscriptionCreatedV1

class DunningService:
    async def handle_charge_failure(
        self,
        subscription_id: UUID,
        failure_reason: str,
        tenant_id: UUID,
    ) -> None:
        """LangGraph DunningWorkflow state machine: active → past_due → suspended → cancelled."""
        # State transitions D3/D7/D14:
        # 1. active → past_due (immediate on first failure)
        # 2. past_due → retry_1 (+3d cron)
        # 3. retry_1 → retry_2 (+7d cron)
        # 4. retry_2 → suspended (lose write access, keep read 24h grace)
        # 5. suspended → cancelled (+14d cumulative)
```

### 9.5 `VoiceCloningService`

```python
class VoiceCloningService:
    async def upload_samples(
        self,
        request: UploadSamplesRequest,
        tenant_id: UUID,
    ) -> SamplesUploadResult:
        """Parse WhatsApp ZIP / voice notes → count distinct conversations."""
        # 1. Parse ZIP — extract chat threads per subscriber
        # 2. Voice notes Whisper transcription (LiteLLM)
        # 3. Sanitize raw samples (strip phone/email/PII patterns)
        # 4. Persist samples metadata (chats_count + voice_notes_count + dialect_detected)
        # 5. Return current count vs 50 threshold

    async def kick_distillation(
        self,
        tenant_id: UUID,
    ) -> VoiceDistillationJob:
        """Async distillation job — 4-wave pipeline ≤$0.18."""
        # 1. Validate samples_count >= 50
        # 2. Create distillation_job status=queued
        # 3. Dispatch worker (ARQ async task)
        # 4. Return job_id for polling

    async def ratify_distilled_voice(
        self,
        job_id: UUID,
        tenant_id: UUID,
    ) -> None:
        """Updates personality_profiles.system_instruction + invalidates Slot 5."""
        # 1. Load distillation job result (compiled_blocks)
        # 2. Compose system_instruction via PersonalityCompiler v2 (existing @luana/core/sales-agent)
        # 3. UPDATE personality_profiles WHERE tenant_id
        # 4. Emit VoiceRatifiedV1 event → Slot 5 cache invalidate handler
        # 5. DELETE raw samples post-distillation (D15 — only statistics retained)
```

### 9.6 `AuthorityVaultService`

```python
class AuthorityVaultService:
    async def add_press_mention(
        self,
        request: AddPressMentionRequest,
        tenant_id: UUID,
    ) -> PressMention:
        """Add press mention with async URL validation."""
        # 1. PII scan content
        # 2. Persist authority_vault_item kind=press_mentions status=validating
        # 3. Async URL fetch (timeout 5s)
        # 4. Update status: ok | unreachable_warning | rejected
        # 5. Emit AuthorityVaultEntryAddedV1
```

### 9.7 `VoiceDistillationOrchestrator` (BaseExtractionOrchestrator subclass)

Detail in `03-arch-agentic.md` § 5.3 — runs as async worker (`voice_distillation_worker.py`). Briefly:

```python
class VoiceDistillationOrchestrator(BaseExtractionOrchestrator):
    """4-wave pipeline 50+ chats → CompiledVoice v2."""
    output_schema = CompiledVoice  # 6 bloques

    waves = [
        ExtractionWave("dialect_detection", model="claude-haiku-4-5"),
        ExtractionWave("vocabulary_anchors_extraction", model="claude-sonnet-4-6"),
        ExtractionWave("register_tone_profile", model="claude-sonnet-4-6"),
        ExtractionWave("validate_and_compile_v2", model="claude-sonnet-4-6"),
    ]
```

### 9.8 `ComplianceEventService`

```python
class ComplianceEventService:
    async def log_event(...) -> None:
        """Best-effort write to comunify_community_audit_log. NEVER raises."""
        # PII sanitized via sanitize_payload before persist
        # try/except + structlog warning
```

### 9.9 `PiiScannerService`

Same as Story 11 pattern — offer description + testimonial + voice samples upload PII scan PRE-persist.

---

## § 10. BrandConfig declarative (comunify/config/brand.yaml)

```yaml
brand_slug: comunify
brand_name: "Comunify"
brand_description: "Vertical-creator-economy brand app for LatAm coaches/course-creators/content-creators"
brand_segment: creator_economy_vertical
compliance_level: creator_economy          # vs Vitalia hipaa_lite
voice_cloning_enabled: true                # ★ NEW Story 12 vs Vitalia OFF
multi_language_ui: false                   # Spanish neutro LatAm only

features:
  brand_studio_full: true                  # 10 sections
  offer_studio_coaching: true
  offer_ladder_visualizer: true            # ★ NEW
  community_engagement_workflow: true       # ★ NEW
  cohort_enrollment_workflow: true          # ★ NEW
  sales_agent_vertical_creator: true
  copilot_creator_extractors: true
  authority_vault_full: true               # ★ NEW required
  voice_cloning_pipeline: true             # ★ NEW
  recurring_subscriptions: true            # ★ NEW
  community_moderation: true               # ★ NEW
  multi_account_creator_switcher: false    # Q2=B defer
  third_party_community_bridge: false      # Q3=B defer
  live_streaming_native: false             # defer
  gamification_deep: false                 # defer
  affiliate_program: false                 # defer 12.bis

brand_studio:
  enabled_sections:
    - identity
    - story
    - narrative
    - voice
    - buyer_persona
    - authority_vault
    - team
    - testimonials
    - communication_assets
    - contact
  required_sections:
    - authority_vault                       # ★ NEW per BrandConfig override
  field_overrides:
    buyer_persona:
      min_count: 3                          # ★ NEW multi-persona mandatory

offer_studio:
  preset_pack: coaching_offers_v1
  default_offer_type: coaching_program

ladder:
  levels: [lead_magnet, tripwire, core, premium]
  conversion_projections_baseline:
    lead_magnet_to_tripwire: 0.08
    tripwire_to_core: 0.12
    core_to_premium: 0.06

subscriptions:
  enabled: true
  plan_tiers:
    creator:
      price_usd_monthly: 29
      max_cohorts: 1
      max_subscribers: 100
    pro:
      price_usd_monthly: 99
      max_cohorts: 3
      max_subscribers: 500
      features: [voice_cloning_pipeline, multi_cohort, recurring_subscriptions]
    agency:
      price_usd_monthly: 299
      max_cohorts: 10
      max_subscribers: 5000
      features: [all_pro_features, team_seats, advanced_analytics, multi_brand_management]

community_safety:
  pre_moderation_new_members: true
  pre_moderation_post_count: 3
  spam_score_threshold: 0.85
  nsfw_score_threshold: 0.85
  auto_approve_engagement_score_min: 80
  auto_reject_spam_score_min: 0.95
  auto_delete_nsfw_score_min: 0.85

payment_gateways:
  - mercadopago                            # Q6=B primary LatAm
  - stripe_connect                         # US/EU subscribers
  - tokenized_recurring                    # subscriptions + cohort installments

kb_packs:
  - creator_economy_kb_v1

agentic_tools:
  - qualify_for_cohort
  - link_to_community
  - nurture_via_authority_content
  - book_discovery_call

extractors:
  - OfferLadderAdvisor
  - AuthorityVaultExtractor

workflows:
  - CommunityEngagementWorkflow
  - CohortEnrollmentWorkflow

guardrails:
  - community_safety_no_spam
  - community_safety_no_nsfw
  - community_safety_no_doxxing
  - prompt_injection_block

sales_agent:
  default_personality_archetype: empathic_creator
  voice_per_tenant: true
  voice_cloning_pipeline: true             # ★ NEW
  channels:
    - whatsapp_business
    - manychat_instagram
    - email_async
    - web_chat
```

---

## § 11. Payment channel adapters (3 — consume Story 11 lifts)

### 11.1 `ComunifyStripeConnectAdapter` (extends Story 11 lift)

```python
class ComunifyStripeConnectAdapter(StripeConnectAdapter):
    """Extends Story 11 lifted core adapter.

    Adds: tokenized recurring for monthly subscriptions ($29/$99/$299) +
    metadata.compliance_level=creator_economy (vs hipaa_lite).
    Sets application_fee per plan_tier.
    """
```

### 11.2 `ComunifyMercadoPagoAdapter` (extends Story 11 lift)

```python
class ComunifyMercadoPagoAdapter(MercadoPagoAdapter):
    """Extends Story 11 lifted core adapter for LatAm recurring subscriptions.

    Adds: subscriber tokenization (card-on-file) for monthly memberships.
    Countries: AR (primary), MX, CL, CO, PE, BR.
    """
```

### 11.3 `ComunifyTokenizedRecurringAdapter` (extends Story 11 lift)

```python
class ComunifyTokenizedRecurringAdapter(TokenizedRecurringAdapter):
    """Cohort installments + monthly subscription recurring.

    Cron job processes next installment per `comunify_subscription_charges`.
    Failure → DunningWorkflow.
    """
```

---

## § 12. Creator calendar extensions (Q4=A reuse @luana/core/scheduling)

Per Phase 0 Q4=A — reuse `@luana/core/scheduling` calendar base. Comunify extensions:

- `appointment_type=discovery_call` (1:1 sales call, FREE — different from Vitalia consultation/control/surgery).
- `discovery_call_duration_minutes=30` default.
- No `treatment_room_assigned` (creators don't have physical rooms).
- `max_concurrent_per_creator=1` (1:1 by default; agency tier may extend with team_seats).

`book_discovery_call` tool consumes `@luana/core/scheduling.calendar.list_slots` + adds `appointment_type=discovery_call` filter.

---

## § 13. Tests required (per TDD R8 mandatory)

### 13.1 Test structure

```
luana-platform/comunify/backend/tests/
├── unit/
│   ├── domain/                          # Entity logic + VO validation + event emission
│   ├── application/                     # Service unit tests with mocked repos
│   └── api/                             # DTO validation
├── integration/                         # Real Postgres + alembic upgrade head
│   ├── test_cohort_repository.py
│   ├── test_cohort_enrollment_advisory_lock.py
│   ├── test_subscription_repository.py
│   ├── test_voice_cloning_samples_repository.py
│   ├── test_community_post_repository.py
│   └── test_community_audit_log_repository.py
├── e2e/                                 # Full API + DB + webhook flow
│   ├── test_onboarding_creator_e2e.py
│   ├── test_brand_studio_voice_cloning_e2e.py
│   ├── test_ladder_build_e2e.py
│   ├── test_cohort_enrollment_e2e.py
│   ├── test_cohort_broadcast_rate_limit_e2e.py
│   ├── test_community_post_moderation_e2e.py
│   ├── test_subscription_recurring_dunning_e2e.py
│   ├── test_cross_tenant_isolation_e2e.py
│   └── test_voice_distillation_pipeline_e2e.py
├── agentic_evals/                       # See 03-arch-agentic.md
└── architecture/
    ├── test_comunify_migrations_idempotent.py
    ├── test_comunify_no_query_without_tenant_filter.py
    ├── test_comunify_no_hardcoded_currency.py
    ├── test_comunify_response_models_required.py
    ├── test_comunify_no_pii_in_voice_samples_persistence.py
    └── test_comunify_ui_strings_no_voseo.py
```

### 13.2 Coverage threshold

- BE module coverage minimum 43% (per backend-quality.md baseline).
- Story 12 target: 70%+ for comunify module.

---

## § 14. Compliance smoke tests (5 — spec § 15)

Located `comunify/backend/tests/agentic_evals/smoke/`:

- `smoke_prompt_injection.py` — 5 injection patterns blocked + audit_log.
- `smoke_spam_detection.py` — 10 spam vectors detected.
- `smoke_nsfw_upload.py` — 5 NSFW image upload severity levels (block ≥0.85).
- `smoke_doxxing.py` — 4 doxxing attempts blocked.
- `smoke_cross_tenant.py` — 3 cross-tenant attack vectors blocked.

Detail patterns in 03-arch-agentic.md § 14.

---

## § 15. R3 downstream regression entries (per `.claude/rules/auditor-downstream-regression.md`)

Architecture phase ticket T-X appends to rule SSoT table:

| Surface modified | Downstream test paths |
|---|---|
| `core/luana-core-channels/.../payment/*Adapter.py` (verify Story 11 lifts) | `core/luana-core-channels/tests/` + `comunify/backend/tests/integration/test_*_adapter.py` + Vitalia tests Story 11 |
| `comunify/backend/src/modules/comunify/agentic/tools/*` (4 new tools) | `comunify/backend/tests/agentic_evals/tools/` |
| `comunify/backend/src/modules/comunify/copilot/extractors/*` (extends Base) | `comunify/backend/tests/agentic_evals/extractors/` + `tests/architecture/test_extraction_orchestrator_inheritance.py` |
| `comunify/backend/src/modules/comunify/copilot/workflows/*` (2 workflows) | `comunify/backend/tests/agentic_evals/workflows/` |
| `comunify/backend/src/modules/comunify/brand/voice_cloning/` (NEW pipeline) | `comunify/backend/tests/agentic_evals/voice_cloning/` + `tests/architecture/test_extraction_orchestrator_inheritance.py` + `test_comunify_no_pii_in_voice_samples_persistence.py` |
| `comunify/backend/src/modules/comunify/extensions.py` (register_all) | `core/tests/architecture/test_docs_extension_points_completeness.py` + `comunify/backend/tests/test_extensions_register_all.py` |
| `docs/specs/personas/archetype-aware/*.yaml` (8 NEW comunify personas) | `comunify/backend/tests/architecture/test_comunify_personas_yaml_completeness.py` |
| `docs/specs/rubrics/vertical-creator-economy-fidelity.md` (NEW rubric) | `comunify/backend/tests/agentic_evals/grader/test_vertical_creator_economy_fidelity_*.py` |

Architecture phase ticket T-X explicit step: append comunify rows to SSoT table.

---

## § 16. Cross-cutting concerns

| Concern | Pattern Story 12 |
|---|---|
| Tenant isolation | `tenant_id` filter every query (incluso get_by_id). Middleware Clerk JWT authoritative. Arch fitness gate ratchet comunify from Story 10/11 baseline. |
| Idempotency | `(clerk_user_id)` 1s window for tenant_create; `(subscriber_id, billing_period, installment_n)` for subscription charges; `(cohort_id, subscriber_id)` for enrollment. |
| Master data | UTC store + tenant locale display (`TenantLocale` VO). Currency from `offers.currency` + subscriptions `currency`, NEVER hardcode 'USD'. |
| PII sanitization | Tessl rule + creator-economy extension. Voice cloning raw samples DELETED post-distillation (D15). |
| Compliance | creator_economy (NOT hipaa_lite). 5-year audit log retention. Community safety guardrails ON. |
| Migrations idempotent | Raw SQL `IF NOT EXISTS`. Single consolidated snapshot. Arch test gate. |
| structlog | All logging via `structlog.get_logger()`. NO `print()` / `logging.*`. |
| Pydantic v2 | `model_config = ConfigDict(...)` (no inner `class Config`). |
| SQLAlchemy 2.0 | `select(Model).where(...)` (no `session.query()`). AsyncSession new code. |

---

## § 17. Risks + mitigations (BE-specific)

| Risk | Severity | Mitigation |
|---|---|---|
| Migration drift models vs DB | high | Consolidated snapshot Story 10/11 T-10 + arch fitness gate + pg_dump diff sanity |
| Cohort enrollment race double-enrollment | high | pg_advisory_lock per cohort_id + uq_cohort_member constraint + integration test |
| Subscription dunning state machine race | medium | Idempotency key + LangGraph atomicity + RedisSaver checkpointer |
| Cross-tenant data leak | high | Middleware + repo constructor required + arch fitness ratchet + audit log + smoke test |
| Webhook replay (Stripe / MP / Clerk) | medium | HMAC signature + idempotency check + audit_log webhook_replay_detected |
| **Voice cloning samples PII persistence** | **high** | sanitize_payload + post-distill DELETE raw + arch test `test_comunify_no_pii_in_voice_samples_persistence.py` |
| Currency mismatch subscription vs charge | medium | DTO Pydantic enforce currency match; integration test |
| MercadoPago tokenized recurring failure | medium | DunningWorkflow handles + creator notification + manual override CTA |
| Cron worker capacity (Comunify 2 workflows + Vitalia 1 + Nicolify + ETL) | medium | Capacity assessment ticket + per-brand pool split if needed |

---

## § 18. Próximo paso

`architect-be` returns: `done -> 03-arch-be.md`. /architect orchestrator consolidates with 03-arch-fe.md + 03-arch-agentic.md → 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml.

done -> docs/product/stories/luana-comunify-bootstrap/03-arch-be.md
