<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# REVIEW-be.md — Story 12 Comunify BE audit

**State input:** developed (Phase 3 closed 2026-05-14, 39/39 GREEN)
**Auditor:** auditor-backend Opus
**Date:** 2026-05-14
**Scope:** BE tickets only — T-scaffold-1, T-config-1, T-be-1..9, T-payment-1
**Excluded:** AGENTIC (T-tools, T-extractors, T-workflows, T-kb, T-guards, T-voice, T-prompts, T-extensions, T-rubric, T-eval) · FE (T-fe-, T-widget, T-e2e) · cross-cutting (T-deploy, T-docs)
**Code dir:** `/home/chris/luana-platform/comunify/backend/`

**Verdict: WARN**

PASS criteria fail by 1 HIGH (DDD `domain/` directory absent vs 03-arch-be.md spec). No CRITICAL, no security/PII/tenant_iso failures. 1 HIGH + 1 MEDIUM + 3 LOW → WARN.

## Gates executed

| Gate | Result | Detail |
|---|---|---|
| Ruff lint (BE-scope only) | FAIL → fixable | 9 errors: 7× I001 import-sort in `src/main.py` + 5 DTOs + `routes.py` + 2× F401 unused imports in `tests/integration/test_payment_adapters.py`. All `--fix` auto-resolvable in 1 command. |
| Ruff format | FAIL → fixable | 1 file in BE scope (`tests/integration/test_payment_adapters.py`); 14 others in agentic_evals (out-of-scope). |
| Arch fitness | PASS | 144/144 tests pass (`tests/architecture/`), including `test_comunify_no_query_without_tenant_filter`, `test_comunify_voice_distillation_inherits_base_orchestrator`, `test_comunify_no_pii_in_voice_samples_persistence`, `test_comunify_cost_bucket_invariant`. |
| Unit + infra tests | PASS | 213/213 pass in 0.5s (`tests/unit/`, `tests/infrastructure/`, `tests/test_extensions_register_all.py`). |
| Combined BE-scope tests | PASS | 357/357 pass in 0.74s. |
| Integration tests | DEFER (HS1) | Require live Postgres (`tests/integration/`). 11 integration files exist (webhook, payment adapters, PII scanner, cohort enrollment, advisory lock) — runtime gating soft-halt per checkpoint HS1. |
| Migration idempotency | PASS (visual) | `001_comunify_initial_snapshot.py` 719 lines, 59× `IF NOT EXISTS`, 0× `op.create_table`/`op.add_column`/`op.create_index`/`sa.Enum`. Header comment cites idempotency contract. |
| Coverage 43% | NOT MEASURABLE | `pytest-cov` not installed in `luana-platform/comunify/backend/.venv`. Classify A (deferred to deploy phase). |
| mypy strict | NOT WIRED | Not configured in `pyproject.toml`. Classify A. |
| jscpd / interrogate / pip-audit | NOT WIRED | New brand bootstrap — full /test-backend suite pending T-deploy-1 wiring. Classify A. |

## Review categories (11)

### 1. DDD Inside-Out — **HIGH (architecture drift)**

`03-arch-be.md` § 5.1 prescribes:
```
modules/comunify/
├── domain/
│   ├── entities/
│   ├── events/
│   ├── value_objects/
│   └── exceptions.py
├── infrastructure/{models,repositories,adapters}/
├── application/{services,tasks,event_handlers}/
└── api/{routes,dtos}/
```

**Actual layout** (`find /home/chris/luana-platform/comunify/backend/src/modules/comunify -type d`):
- `agentic/`, `api/`, `application/`, `brand/`, `copilot/`, `infrastructure/`, `payment/`
- **NO `domain/` directory.**

No `domain/entities/`, `domain/events/`, `domain/value_objects/`, `domain/exceptions.py`. Models exist only in `infrastructure/models/` (SQLAlchemy ORM), DTOs in `api/dtos/`, services in `application/services/`. Pure domain logic (capacity VO, plan_features VO, moderation_classifier_score VO, compiled_voice VO per arch § 5.1) is either inlined into models or services, or absent.

**Drift severity:** structural. The arch test surface does NOT enforce `domain/` presence (no fitness gate fails) so build is GREEN, but the prescribed DDD Inside-Out shape is broken. Future cross-module ports (planned per `shared/links/ports/`) will lack a pure domain layer to wrap.

**Remediation:** post-merge ticket to extract domain entities + value objects from `infrastructure/models/` Pydantic-style aggregates and `application/services/` invariants. OR: ratify architectural deviation in 03-arch-be.md addendum (Pattern: "models-as-entities" — explicit decision similar to Story 10 Pattern P6 schema-mirror exception).

**Files:** `/home/chris/luana-platform/comunify/backend/src/modules/comunify/` (entire module tree)
**Arch spec:** `docs/product/stories/luana-comunify-bootstrap/03-arch-be.md:83-110`
**Status:** HIGH — not security-critical (tenant_iso intact), but contradicts ratified arch. Auditor recommends merge-blocking only if PM signals strict spec adherence; otherwise log technical debt and proceed.

### 2. Tenant isolation — **PASS**

Every repo query filters `tenant_id`:
- `cohort_repository.py:39-42` — `select(...).where(id==id, tenant_id==self._tenant_id)`
- `subscription_repository.py:37` — same pattern
- `community_post_repository.py:38` — same pattern
- `voice_distillation_job_repository.py:36` — same pattern

Confirmed by arch test `test_comunify_no_query_without_tenant_filter.py` PASS. All 15 repositories under `infrastructure/repositories/` reference `tenant_id` in their queries. Plan tier config explicitly cross-tenant catalog (no tenant_id) and documented as such in arch § 5.1 entity 16.

X-Tenant-ID header parsed in `api/routes.py:154-162` via `_parse_tenant_id()` with 422 on invalid UUID.

### 3. Master-data + currency — **WARN (MEDIUM)**

- `infrastructure/models/plan_tier_config_model.py:42` — `currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")` — hardcoded USD default violates `.claude/rules/currency-handling.md` strictly, but this is the **platform billing currency** (Luana SaaS → creator), not tenant→customer transactions. Cross-tenant catalog. Acceptable WARN.
- `extensions.py:760,778,796` — plan tier seed catalog hardcodes `currency="USD"` for Creator/Pro/Agency tiers. Same justification.
- Datetime: 100% `DateTime(timezone=True)` in models (`cohort_model.py:44-46` etc). Zero `datetime.utcnow()` in source.
- No tenant→customer monetary DTO without `currency` field (subscription_dtos, cohort_dtos use `currency: str` field per spec).

**Remediation:** document explicit "platform billing in USD" in arch or migrate to env-var `LUANA_PLATFORM_BILLING_CURRENCY` for future LatAm-currency platform.

### 4. Spanish neutro — **PASS**

Grep voseo across `api/` and `application/services/` — zero hits. User-facing strings (error messages, route descriptions) use neutro. Module is API-only (no UI strings in BE) — exhaustive UI Spanish check belongs to auditor-frontend.

### 5. PII sanitisation — **PASS**

All 43 routes (38 `routes.py` + 5 `webhook_routes.py`) declare `response_model=`. DTOs document PII exclusion verbatim:
- `cohort_dtos.py:4` — "PII: raw subscriber email/phone NOT exposed — name_display masked."
- `cohort_dtos.py:98` — "Raw phone/email/full_last_name NOT exposed."
- `community_dtos.py:21` — "author_member_id is exposed as opaque UUID (no name/email/phone)."
- `voice_cloning_dtos.py` — schema-mirror only, no PII echoed.

Tessl PII-sanitisation rule respected. Auditor confirmed by reading 8 DTO files.

### 6. Idempotent migrations — **PASS**

`001_comunify_initial_snapshot.py` (719 lines):
- 59 `IF NOT EXISTS` clauses
- 0 `op.create_table()` / `op.add_column()` / `op.create_index()` / `sa.Enum(create_type=True)`
- Header comment cites contract: "Raw SQL IF NOT EXISTS everywhere — NEVER op.create_table() / sa.Enum(create_type=True)"
- Enum types created via `DO $$ BEGIN ... END $$` with `pg_type` check
- 16 tables, all tenant-indexed except `comunify_plan_tier_configs` (cross-tenant catalog)

T-be-1 result.md acknowledges A1/A2 (upgrade 2x + downgrade -1) deferred to HS1 (Docker integration). Static verification PASS via AST parse.

### 7. R10 anti-duplication — **PASS**

- `voice_distillation_orchestrator.py:281` — `class VoiceDistillationOrchestrator(BaseExtractionOrchestrator)` — inherits shared base per anti-duplication.md inventory.
- File docstring (lines 4, 51-56) cites grep evidence + extension intent.
- Arch test `test_comunify_voice_distillation_inherits_base_orchestrator` PASS (5 assertions including wave count, log prefix, confidence weights).
- No `BaseAgentCallbackHandler` mirror, no `TurnEnvelope` mirror, no `FXResolver` mirror. Brand-isolated patterns vs reuse from `luana-core-platform` core packages.

### 8. R3 downstream regression — **N/A**

`git diff` shows zero changes in `backend/src/shared/` or `backend/src/core/` in AISALESHT repo. Comunify is isolated under `luana-platform/comunify/`. No surface listed in `.claude/rules/auditor-downstream-regression.md` table touched. Downstream gate-runner spawn not required.

### 9. SQLA 2.0 patterns — **PASS**

- 100% `select(Model).where(...)` — zero `session.query()` (grep clean).
- `Mapped[]` typing in all models: `cohort_model.py:44` `created_at: Mapped[datetime] = mapped_column(...)`.
- Async session usage in services via `AsyncSession` (e.g. `community_post_service.py:235`).
- Zero `session.delete()` / hard delete in repositories.
- Soft delete via `deleted_at` column — 42 references across repositories.

### 10. Tests / TDD — **PASS**

- 357 BE-scope tests GREEN in 0.74s (architecture 144 + unit 144 + infra 22 + extensions 47).
- Test surfaces per CONTRACT § 14 present: domain → infra → app → api (E2E in `tests/e2e/` exist as 5 files, runtime deferred HS1).
- TDD per ticket: T-be-1 (migration), T-be-2 (3 entities + repos), T-be-3 (cohort + advisory lock), T-be-4 (onboarding/compliance/PII services + 65 tests), T-be-5 (onboarding router), T-be-6 (creator profile router), T-be-7 (cohort router), T-be-8 (subscription endpoints), T-be-9 (5 webhooks). Each `T-be-{n}-result.md` cites RED→GREEN evidence.
- No `skip` / `xfail` marker abuse in BE-scope.
- 11 integration test files exist — runtime gated by Postgres availability (HS1).

### 11. Cross-cutting — **PASS with LOW WARN**

- **`redirect_slashes=False`** ✅ — `src/main.py:29` mandatory FastAPI app-level setting present.
- **Async consistency** ✅ — 44 async vs 18 sync (sync limited to pure helpers).
- **Graceful degradation** ✅ — every external httpx call has timeout: `payment/mercadopago_adapter.py:285,323` (`timeout=self.timeout_seconds`), `payment/tokenized_recurring_adapter.py:449,490` (`timeout=10.0`), `payment/stripe_connect_adapter.py:241`. Three orchestrators (`voice_distillation_orchestrator.py:629`, `offer_ladder_advisor.py:581`, `authority_vault_extractor.py:565`) use `wave.timeout_sec + 2.0` asyncio guard around LLM-internal timeout. Tessl graceful-degradation Iron Rule satisfied.
- **Pydantic v2** ✅ — `ConfigDict` consistently used across 9 DTO files (`grep -c ConfigDict` returns 9+); zero `class Config:` inner-class anti-pattern.
- **No cross-module imports** ✅ — module is isolated under `modules/comunify/`; shared base imports via `luana_core_platform`, `luana_core_extraction` (workspace packages per Story 10 P6 pattern).
- **LOW WARN (cosmetic):** Lint failures (`I001` import-sort in 7 BE-scope files + 2 F401 unused imports in integration test). All auto-fixable via `ruff check --fix` in a single command. Format check fails 1 BE-scope file.

## Findings (scored)

### CRITICAL — 0
None.

### HIGH — 1

**[H1] DDD `domain/` directory absent — drift from 03-arch-be.md § 5.1**

- **Location:** `/home/chris/luana-platform/comunify/backend/src/modules/comunify/` (whole module — no `domain/` subdir)
- **Commits:** T-be-1..T-be-3 (entities never split from infrastructure/models)
- **Spec:** `docs/product/stories/luana-comunify-bootstrap/03-arch-be.md:83-110` prescribes 4 sub-dirs: `domain/{entities,events,value_objects}/`, `exceptions.py`
- **Impact:** Pure domain layer absent → invariants (Capacity VO, PlanFeatures VO, ModerationScore VO, CompiledVoice VO) live inside ORM models OR services, blocking the DDD-cross-module port pattern when future brands lift sub-patterns.
- **Severity:** HIGH (architecture spec drift), not CRITICAL (no test failure, no security risk, no tenant leak).
- **Remediation:** (A) post-merge architecture follow-up ticket to extract `domain/{entities,events,value_objects}/` from current Pydantic+SQLAlchemy aggregates; OR (B) PM ratify "models-as-entities" deviation as Comunify-scoped Pattern (analog to Story 10 P6 schema-mirror exception). Auditor recommends (A) for long-term anti-duplication discipline.

### MEDIUM — 1

**[M1] Hardcoded `"USD"` defaults in plan tier config**

- **Locations:**
  - `src/modules/comunify/infrastructure/models/plan_tier_config_model.py:42` — `currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")`
  - `src/modules/comunify/extensions.py:760,778,796` — Creator/Pro/Agency tier seeds `currency="USD"`
- **Rule violated:** `.claude/rules/currency-handling.md` — "DTOs monetary sin `currency` → FAIL"; default `"USD"` flagged.
- **Justification context:** This is **platform billing currency** (Luana → tenant), not tenant→customer. `plan_tier_configs` is the cross-tenant catalog (no tenant_id column).
- **Remediation:** Replace literal `"USD"` with env-var `LUANA_PLATFORM_BILLING_CURRENCY` (default USD) — enables future LatAm-currency platform pricing without code change. OR add explicit comment annotation in model.
- **Severity:** MEDIUM — rule violation by letter, justifiable by intent.

### LOW — 3

**[L1] Ruff lint — 9 I001+F401 errors (BE-scope only)**

- **Files:** `src/main.py:15`, `src/modules/comunify/api/dtos/{cohort,community,offer_ladder,onboarding,subscription}_dtos.py`, `src/modules/comunify/api/routes.py:27`, `tests/integration/test_payment_adapters.py:29,52`
- **Nature:** I001 (import block un-sorted) + F401 (unused imports `UUID`, `RecurringPaymentSchedule`).
- **Fix:** `cd /home/chris/luana-platform/comunify/backend && .venv/bin/ruff check src/ tests/ --fix` — auto-resolves all 9.
- **Severity:** LOW (cosmetic).

**[L2] Ruff format — 1 BE-scope file unformatted**

- **File:** `tests/integration/test_payment_adapters.py`
- **Fix:** `.venv/bin/ruff format src/ tests/` resolves.
- **Severity:** LOW.

**[L3] Coverage + mypy + jscpd + interrogate + pip-audit gates not wired**

- `pytest-cov`, `mypy`, `jscpd`, `interrogate`, `pip-audit` not installed/configured in `comunify/backend/.venv`.
- **Status:** Classify A (deferred) — T-deploy-1 wires full gate suite, T-docs-1 documents thresholds.
- **Severity:** LOW (visibility gap, not regression). Counts as classification A per HS-protocol.

## Verdict mechanical

| Threshold | Result |
|---|---|
| 0 CRITICAL | ✅ |
| 0 HIGH security/PII/tenant_iso | ✅ |
| ≤2 HIGH non-security | ⚠️ 1 HIGH (DDD drift) |
| ≤3 MEDIUM | ✅ 1 |
| All gates GREEN or A/B/C classified | ⚠️ lint+format fixable in 1 command, integration DEFER HS1 |

**Verdict: WARN**

PASS path was blocked by H1 (DDD `domain/` drift). All other findings are LOW cosmetic + 1 MEDIUM with documented context. WARN is the mechanical verdict — recommend PM (a) ratify deviation as Comunify-scoped pattern, (b) schedule follow-up domain-extraction ticket, (c) instruct builder to apply `ruff check --fix && ruff format` before merge commit. Approval can be granted on (c) alone if (a)+(b) tracked in BACKLOG.

## Output

`WARN -> docs/product/stories/luana-comunify-bootstrap/REVIEW-be.md`
