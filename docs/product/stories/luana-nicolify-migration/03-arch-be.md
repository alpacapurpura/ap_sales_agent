<!-- voseo-allowed: arch doc cites .claude/rules glossary + sales-agent-expert §3 verbatim per R25 -->
---
story_id: luana-nicolify-migration
arch_version: 1
sub_arch: backend (deep dive — codemod regex, package-by-package mapping, alembic consolidation, Trigger #11 workflow)
architect_owner: claude-opus-4-7
ratified_by_chris: false
last_modified: 2026-05-12
parent_doc: 03-arch.md
companion_docs:
  - 05-guidelines.md
---

# 03-arch-be — Story 10 Backend deep dive

> **Purpose:** package-by-package import rewrite mapping with codemod regex/AST rules + alembic snapshot consolidation strategy + fresh `nicolify_dev` DB workflow + Halt Trigger #11 (test mock missing) workflow.
>
> **Scope:** BE only. FE imports rewrite + Vercel reconfig in `03-arch.md §2 Feature 2`.

## 1. AISALESHT BE inventory (source state — pre Story 10)

### 1.1 Modules (`backend/src/modules/`) — 18 modules, ~1080 files-with-imports

| Module | Files with `from src.` | Target luana-core package | Wave |
|---|---|---|---|
| `brand` | 48 | `luana_core_brand_studio` | 1 |
| `offer` | 74 | `luana_core_offer_studio` | 1 |
| `landing` | 12 | `luana_core_landing` | 1 |
| `assets` | 16 | `luana_core_assets` | 1 |
| `connections` | 43 | `luana_core_connections` | 1 |
| `scheduling` | 13 | (verify Phase 0: not in 26 packages — may stay nicolify-local OR lift to `luana_core_scheduling` deferred Story 14) | 1 OR DEFERRED |
| `iam` | 16 | `luana_core_iam` | 1 |
| `crm` | 41 | `luana_core_crm` | 1 |
| `commercial_calendar` | 6 | `luana_core_commercial_calendar` | 1 |
| `analytics` | 91 | `luana_core_analytics_engine` | 1 |
| `campaigns` | 55 | `luana_core_campaigns` | 1 |
| `social_proof` | 31 | `luana_core_social_proof` | 1 |
| `tenant_profile` | 7 | `luana_core_tenant_profile` | 1 |
| `tenant_domains` | 9 | `luana_core_tenant_domains` | 1 |
| `advertising` | 15 | (verify Phase 0: not in 26 packages — may stay nicolify-local OR lift Story 14) | 1 OR DEFERRED |
| `social_media` | 0 (empty module — has only `__init__.py` scaffold) | (DEFER or DELETE empty scaffold per Phase 0) | DEFERRED |
| `copilot` | 150 | `luana_core_copilot` | **2 (agentic — Opus mandatory R23)** |
| `sales_agent` | 104 | `luana_core_sales_agent` | **2 (agentic — Opus mandatory R23)** |

**TOTAL BE module files with imports to rewrite:** ~831 files (sum minus 0 for empty `social_media`).

**Phase 0 spike Q (architect resolves before T-2 spawns):** verify `scheduling`, `advertising`, `social_media` package existence in luana-core. Currently `~/luana-platform/core/` list does NOT include `luana-core-scheduling`, `luana-core-advertising`, or `luana-core-social-media`. Three options:
- (A) These modules stay nicolify-local (move to `luana-platform/nicolify/backend/src/modules/{scheduling,advertising}/`). Imports `from src.modules.X` → `from nicolify_backend.modules.X` (no luana-core package).
- (B) Lift Story 14+ (next vertical-elevation cycle).
- (C) Phase 0 spike confirms they ARE in luana-core under different naming (verify `~/luana-platform/core/` list ÷ docs/migration-from-nicolify.md §3 mapping — `migration-from-nicolify.md §3` does NOT list these 3, supporting option A or B).

**Architect decision (this doc):** **Option A — stay nicolify-local** for `scheduling`, `advertising`, `social_media`. Rationale: they are Nicolify-vertical-specific (scheduling = Chris's tenant calendaring; advertising = Meta Ads integration nicolify-specific; social_media = empty scaffold not yet implemented). Stories 11-13 verticals (Vitalia healthcare, Comunify community, Lupulo beer) likely have DIFFERENT scheduling/advertising needs. Future Story 14+ may lift to core if cross-vertical pattern emerges.

**Sub-agent prompt for T-2/T-3/T-4:** ticket spec includes line "modules `{scheduling,advertising,social_media}` stay nicolify-local — rewrite `from src.modules.X` → `from nicolify_backend.modules.X` (or per architect Phase 0 final naming `nicolify.backend.src.modules.X` if BE workspace member uses that import root)".

### 1.2 Shared subsystems (`backend/src/shared/`) — 11 subsystems, ~114 files-with-imports

| Subsystem | Files with imports | Target luana-core | Wave |
|---|---|---|---|
| `agent_observability` | 18 | `luana_core_observability` (already lifted Stories 1-2 — base classes consumed by `luana_core_{copilot,sales_agent}`) | 2 |
| `events` | (count via grep — likely subset of domain_events) | `luana_core_events` | 2 |
| `domain_events` | 7 | `luana_core_events` (consolidated package) | 2 |
| `billing` | 17 | `luana_core_billing` | 2 |
| `compliance` | 11 | `luana_core_compliance` | 2 |
| `idempotency` | 3 | `luana_core_idempotency` | 2 |
| `infrastructure` (subsystems below) | 22 cumulative | per-subsystem mapping | 2 |
| `infrastructure/llm/` | (subset of 22) | `luana_core_llm` (router + providers + LiteLLM) | 2 |
| `infrastructure/{persistence,redis,...}` | (subset) | `luana_core_platform` (multi-purpose platform abstractions per Story 2) | 2 |
| `application` | 6 | per-purpose (`application/extraction/` → `luana_core_extraction`; rest → `luana_core_platform`) | 2 |
| `application/extraction/` | (subset) | `luana_core_extraction` | 2 |
| `api` | 1 | `luana_core_platform` | 2 |
| `domain` | 3 | per-purpose (e.g., `shared/domain/locale.py::TenantLocale` → `luana_core_platform.domain.locale`) | 2 |
| `links` | 22 | per consumer package re-export (ports are interface contracts — `luana_core_{module}.links.ports.{name}` per package) | 2 |
| `workers` | 4 | DEFERRED Story 10b (root workers + per-module workers/ subdirs) | DEFERRED |

**TOTAL BE shared files with imports to rewrite:** ~114 files (verifying T-1 baseline grep).

**Phase 0 architect-resolved mappings (sub-agent prompt T-7):**

| AISALESHT source | Target package | Notes |
|---|---|---|
| `from src.shared.agent_observability.recording.base_callback_handler` | `from luana_core_observability.recording.base_callback_handler` | Story 2 lifted SSoT (verified `~/luana-platform/core/luana-core-observability/`) |
| `from src.shared.agent_observability.recording.turn_envelope` | `from luana_core_observability.recording.turn_envelope` | Story 2 lifted (origen anti-duplication.md PR-1 hotfix 2026-05-01) |
| `from src.shared.agent_observability.recording.sanitization` | `from luana_core_observability.recording.sanitization` | PII sanitization SSoT |
| `from src.shared.agent_observability.cost.calculator` | `from luana_core_observability.cost.calculator` | Cost calculator + tier pricing |
| `from src.shared.agent_observability.cost.fx_resolver` | `from luana_core_observability.cost.fx_resolver` | `FXResolver.default()` factory |
| `from src.shared.agent_observability.cost.cost_recorder` | `from luana_core_observability.cost.cost_recorder` | Cost recorder (origen R3 downstream regression D4 2026-05-04) |
| `from src.shared.agent_observability.cost.pricing_resolver` | `from luana_core_observability.cost.pricing_resolver` | Pricing resolver |
| `from src.shared.agent_observability.persistence.{base_trace_event_repo,base_llm_call_repo,pricing_snapshot_repository,tenant_billing_config_repository}` | `from luana_core_observability.persistence.X` | Protocol bases |
| `from src.shared.agent_observability.channels.{format_for_channel,intent_detector}` | `from luana_core_channels.{format_for_channel,intent_detector}` | Story 2 — `luana_core_channels` separate package |
| `from src.shared.events.X` (DomainEvent base, EventBus) | `from luana_core_events.X` | Story 2 |
| `from src.shared.domain_events.outbox.X` | `from luana_core_events.outbox.X` | Outbox consolidated under `luana_core_events` |
| `from src.shared.billing.{application,domain,infrastructure}.X` | `from luana_core_billing.X` | Story 2 (BudgetGuard + OutboundRateLimiter) |
| `from src.shared.compliance.X` | `from luana_core_compliance.X` | Story 2 (ComplianceService) |
| `from src.shared.idempotency.X` | `from luana_core_idempotency.X` | Story 2 (IdempotencyKey, RedisRateLimiter) |
| `from src.shared.infrastructure.llm.router` | `from luana_core_llm.router` | Story 2 (LLMRouter — single dispatch via LiteLLM Proxy post 2026-05-06 canonicalization) |
| `from src.shared.infrastructure.llm.providers.{litellm,kimi,deepseek,openai,qwen,gemini}` | `from luana_core_llm.providers.{litellm,kimi,deepseek,openai,qwen,gemini}` | Adapters |
| `from src.shared.application.extraction.base_orchestrator` | `from luana_core_extraction.base_orchestrator` | Wave-based extraction base (`BaseExtractionOrchestrator`) consumed by brand/offer/landing/buyer_persona |
| `from src.shared.domain.locale` (`TenantLocale`) | `from luana_core_platform.domain.locale` | Multi-purpose platform module |
| `from src.shared.api.X` (FastAPI middleware/utilities) | `from luana_core_platform.api.X` | Multi-purpose |
| `from src.shared.application.X` (excluding extraction) | `from luana_core_platform.application.X` | Multi-purpose |
| `from src.shared.links.ports.{brand,offer,sales_agent,copilot,...}` | `from luana_core_{brand_studio,offer_studio,sales_agent,copilot}.links.ports.X` | **Per-consumer package re-export.** Each luana-core package exposes its ports under `links/ports/` subpackage. Cross-module port consumers import from the OWNING module's package (e.g., sales_agent reads brand data via `from luana_core_brand_studio.links.ports.brand import BrandDataPort`). Architect verifies Phase 0: read `core/luana-core-brand-studio/src/luana_core_brand_studio/links/ports/` to confirm convention. |
| `from src.shared.workers.X` | DEFERRED Story 10b | Halt Trigger #1 if encountered in shared/ during T-7 — escalate. |

### 1.3 Tests (`backend/tests/`) — ~1071 files, mock paths

Current baseline (verified 2026-05-12):
- Test files: 1071
- Tests with `patch("src.*")` mock paths: **0** (verified via `grep -r "patch.*['\"](src\." backend/tests/ | wc -l = 0`)

**Why this matters:** if T-1 baseline confirms 0 stale mock paths NOW, and rewrite introduces drift, new arch fitness test `test_no_legacy_src_mock_paths.py` catches regression immediately. If baseline shows >0 → fix-on-discovery within 5min cap (Decisión 5B); if non-trivial → Halt Trigger #11.

**Mock rewrite pattern (sub-agent prompt for each Wave 1+2 ticket):**
```python
# BEFORE
mocker.patch("src.modules.brand.application.brand_service.BrandService.update")

# AFTER
mocker.patch("luana_core_brand_studio.application.brand_service.BrandService.update")
```

**Note on `mocker.patch.object` patterns:** unaffected (operates on imported objects, not string paths) — only string-path patches need rewrite.

## 2. Package-by-package codemod regex/AST rules

> **Why libcst (NOT sed):** sed regex misses (a) `from src.modules.brand import X as Y` (alias), (b) multi-line imports `from src.modules.brand.X import (\n    A,\n    B,\n)`, (c) nested type annotations `dict[str, "src.shared.X.Y"]` (string literal class refs), (d) `getattr(src.modules.X, "Y")` (string usage), (e) `__import__("src.modules.X")` (dynamic). libcst handles all five robustly via AST traversal.

### 2.1 Codemod script structure (`scripts/codemod_be_imports.py` — T-2 produces)

```python
"""LibCST codemod rewriting AISALESHT → luana-core imports per Story 10 Feature 1.

Usage:
    python scripts/codemod_be_imports.py --package=brand --dry-run
    python scripts/codemod_be_imports.py --package=brand --apply

Per-package mapping from MAPPING dict below. Idempotent (re-running on already-rewritten
files is a no-op). Test mock paths in tests/ rewritten in same pass.
"""

import libcst as cst
from libcst import codemod

MAPPING = {
    # BE modules (18 total)
    "src.modules.brand": "luana_core_brand_studio",
    "src.modules.offer": "luana_core_offer_studio",
    "src.modules.landing": "luana_core_landing",
    "src.modules.assets": "luana_core_assets",
    "src.modules.connections": "luana_core_connections",
    "src.modules.iam": "luana_core_iam",
    "src.modules.crm": "luana_core_crm",
    "src.modules.commercial_calendar": "luana_core_commercial_calendar",
    "src.modules.analytics": "luana_core_analytics_engine",
    "src.modules.campaigns": "luana_core_campaigns",
    "src.modules.social_proof": "luana_core_social_proof",
    "src.modules.tenant_profile": "luana_core_tenant_profile",
    "src.modules.tenant_domains": "luana_core_tenant_domains",
    "src.modules.copilot": "luana_core_copilot",
    "src.modules.sales_agent": "luana_core_sales_agent",
    # Nicolify-local (Phase 0 Option A — stay local)
    "src.modules.scheduling": "nicolify_backend.modules.scheduling",
    "src.modules.advertising": "nicolify_backend.modules.advertising",
    "src.modules.social_media": "nicolify_backend.modules.social_media",
    # Shared (11 subsystems)
    "src.shared.agent_observability": "luana_core_observability",
    "src.shared.events": "luana_core_events",
    "src.shared.domain_events.outbox": "luana_core_events.outbox",
    "src.shared.domain_events": "luana_core_events",
    "src.shared.billing": "luana_core_billing",
    "src.shared.compliance": "luana_core_compliance",
    "src.shared.idempotency": "luana_core_idempotency",
    "src.shared.infrastructure.llm": "luana_core_llm",
    "src.shared.application.extraction": "luana_core_extraction",
    "src.shared.domain.locale": "luana_core_platform.domain.locale",
    "src.shared.api": "luana_core_platform.api",
    "src.shared.application": "luana_core_platform.application",
    "src.shared.domain": "luana_core_platform.domain",
    # Per-consumer port re-export (links/ports/)
    "src.shared.links.ports.brand": "luana_core_brand_studio.links.ports.brand",
    "src.shared.links.ports.offer": "luana_core_offer_studio.links.ports.offer",
    "src.shared.links.ports.sales_agent": "luana_core_sales_agent.links.ports.sales_agent",
    "src.shared.links.ports.copilot": "luana_core_copilot.links.ports.copilot",
    "src.shared.links.ports.crm_repos": "luana_core_crm.links.ports.crm_repos",
    "src.shared.links.ports.crm_enrichment": "luana_core_crm.links.ports.crm_enrichment",
    "src.shared.links.ports.analytics": "luana_core_analytics_engine.links.ports.analytics",
    "src.shared.links.ports.advertising": "nicolify_backend.modules.advertising.links.ports.advertising",
    "src.shared.links.ports.calendar": "luana_core_commercial_calendar.links.ports.calendar",
    "src.shared.links.ports.campaigns": "luana_core_campaigns.links.ports.campaigns",
    "src.shared.links.ports.channel_adapter": "luana_core_channels.links.ports.channel_adapter",
    "src.shared.links.ports.conversational_channel": "luana_core_channels.links.ports.conversational_channel",
    "src.shared.links.ports.domain_lookup": "luana_core_platform.links.ports.domain_lookup",
    "src.shared.links.ports.editable_fields": "luana_core_platform.links.ports.editable_fields",
    "src.shared.links.ports.edition_landing_clone": "luana_core_landing.links.ports.edition_landing_clone",
    "src.shared.links.ports.lead_resolution": "luana_core_crm.links.ports.lead_resolution",
    "src.shared.links.ports.message_handler": "luana_core_channels.links.ports.message_handler",
    "src.shared.links.ports.payment_connection": "luana_core_connections.links.ports.payment_connection",
    "src.shared.links.ports.access": "luana_core_iam.links.ports.access",
    # Workers DEFERRED (halt if encountered)
    # "src.shared.workers": DEFERRED Story 10b
    # "src.workers": DEFERRED Story 10b
}

class ImportRewriter(codemod.VisitorBasedCodemodCommand):
    """Rewrite from src.X import Y → from luana_core_X import Y. Handles aliases + nested."""

    def __init__(self, context, package=None):
        super().__init__(context)
        self.package = package  # filter scope (e.g., 'brand' → only files under src/modules/brand/)

    def leave_ImportFrom(self, original_node, updated_node):
        if updated_node.module is None:
            return updated_node
        module_str = self._dotted_name_to_str(updated_node.module)
        for src_prefix, target_prefix in sorted(MAPPING.items(), key=lambda kv: -len(kv[0])):
            if module_str == src_prefix or module_str.startswith(src_prefix + "."):
                new_module_str = target_prefix + module_str[len(src_prefix):]
                return updated_node.with_changes(
                    module=self._str_to_dotted_name(new_module_str)
                )
        return updated_node

    # Helpers _dotted_name_to_str, _str_to_dotted_name omitted for brevity (standard libcst patterns)
```

### 2.2 Codemod execution per-Wave ticket

**T-2 (brand + offer):**
```bash
cd /home/chris/AISALESHT/backend
python scripts/codemod_be_imports.py --package=brand --apply
python scripts/codemod_be_imports.py --package=offer --apply
python scripts/codemod_be_imports.py --tests-only --pattern="tests/modules/brand/" --apply
python scripts/codemod_be_imports.py --tests-only --pattern="tests/modules/offer/" --apply

# Verify
grep -rn "from src\." src/modules/brand/ src/modules/offer/ | wc -l  # should be 0
grep -rn "patch.*['\"]src\." tests/modules/brand/ tests/modules/offer/ | wc -l  # should be 0
.venv/bin/pytest tests/modules/brand/ tests/modules/offer/ -v --tb=short
.venv/bin/pytest tests/architecture/test_no_legacy_src_paths.py -v
```

**T-5 (copilot — agentic Opus mandatory):**
```bash
cd /home/chris/AISALESHT/backend
python scripts/codemod_be_imports.py --package=copilot --apply
python scripts/codemod_be_imports.py --tests-only --pattern="tests/modules/copilot/" --apply

# Verify anchor preservation (cap 36/36 — copilot-expert SSoT)
grep -rh "\[COPILOT-" src/modules/copilot/ | sort -u | wc -l  # 36

# Verify ratchet preservation (22 frozen copilot → módulo imports)
.venv/bin/pytest tests/architecture/test_no_new_copilot_module_imports.py -v
.venv/bin/pytest tests/architecture/test_copilot_anchors.py -v
.venv/bin/pytest tests/architecture/test_copilot_provider_compliance.py -v

# Verify module_registry convention post rename
# Pre-rename: src.modules.brand.copilot_provider:provider
# Post-rename: luana_core_brand_studio.copilot_provider:provider
# Architect verifies pattern preserved in luana-core-copilot Story 6 — read core/luana-core-copilot/src/luana_core_copilot/registry/module_registry.py line-by-line
.venv/bin/pytest tests/modules/copilot/ -v --tb=short
```

**T-6 (sales_agent — agentic Opus mandatory, parallel with T-5 ≤2 cap):**
```bash
cd /home/chris/AISALESHT/backend
python scripts/codemod_be_imports.py --package=sales_agent --apply
python scripts/codemod_be_imports.py --tests-only --pattern="tests/modules/sales_agent/" --apply

# Verify §3 NO TOUCH surfaces preserved (sales-agent-expert SSoT)
grep -rn "class CloserStudio\|SmartBufferService\|OutputManager\|enrollment_" src/modules/sales_agent/ 2>/dev/null | wc -l  # baseline count preserved
git diff src/modules/sales_agent/ -- '*closer_studio*' '*smart_*buffer*' '*output_manager*' '*enrollment_*'  # zero non-import changes

# 40 pre-existing failures preserved (Decisión 9B baseline)
.venv/bin/pytest tests/modules/sales_agent/ -v --tb=no 2>&1 | tail -5  # FAILED count matches T-1 baseline
```

**T-7 (shared/* cross-cutting — 11 subsystems sharded, Opus mandatory):**
```bash
# Sub-shard order (lowest blast radius first):
# 1. idempotency (3 files, no cross-module deps internal to shared)
# 2. compliance (11 files)
# 3. billing (17 files)
# 4. domain (3 files — locale VO)
# 5. application/extraction (6 files — base orchestrator consumed by brand/offer/landing)
# 6. domain_events + events (consolidated under luana_core_events)
# 7. infrastructure/llm (22 files — LLMRouter consumed cross-codebase)
# 8. agent_observability (18 files — base classes consumed by copilot+sales_agent — verify post T-5/T-6)
# 9. api + application (residual → luana_core_platform)
# 10. links/ports/ (22 files — per-consumer re-export — verify each port lives in its OWNING luana-core package)
# 11. workers DEFERRED → HALT if encountered

cd /home/chris/AISALESHT/backend
python scripts/codemod_be_imports.py --shared=idempotency --apply
python scripts/codemod_be_imports.py --shared=compliance --apply
# ... iterate per sub-shard ≤2 paralelo

# After all 11 sub-shards
grep -rn "from src\." src/shared/ 2>/dev/null | grep -v "src/shared/workers" | wc -l  # 0
.venv/bin/pytest tests/shared/ tests/architecture/ -v --tb=short
```

## 3. Alembic snapshot consolidation strategy (Feature 3 deep dive)

### 3.1 Phase 0 spike hybrid approach

**Step 1 — Capture current schema state:**
```bash
docker exec visionarias_postgres_dev pg_dump --schema-only -U postgres visionarias_logs > /tmp/aisaleshT_schema.sql
wc -l /tmp/aisaleshT_schema.sql  # capture LOC for audit
```

**Step 2 — Generate model-driven schema via alembic autogenerate on empty DB:**
```bash
psql -U postgres -c "CREATE DATABASE _autogen_test;"
cd /home/chris/AISALESHT/backend
DATABASE_URL=postgresql://postgres@localhost:5432/_autogen_test \
    .venv/bin/alembic revision --autogenerate -m "models_inferred_baseline" --message-format="raw"
# Output: alembic/versions/XXX_models_inferred_baseline.py
mv alembic/versions/XXX_models_inferred_baseline.py /tmp/models_inferred.py
psql -U postgres -c "DROP DATABASE _autogen_test;"
```

**Step 3 — Diff for drift detection:**
```bash
# Extract pg_dump tables sorted
grep -E "^CREATE TABLE|^ALTER TABLE.*FOREIGN KEY|^CREATE INDEX" /tmp/aisaleshT_schema.sql | sort > /tmp/pg_dump_ddl.txt

# Extract autogen tables (via Python script normalizing op.create_table() → CREATE TABLE form)
python scripts/normalize_alembic_autogen.py /tmp/models_inferred.py > /tmp/autogen_ddl.txt

diff /tmp/pg_dump_ddl.txt /tmp/autogen_ddl.txt > /tmp/schema_drift.diff
wc -l /tmp/schema_drift.diff
```

**Step 4 — Drift resolution per Halt Trigger #5:**

| Drift type | Resolution path |
|---|---|
| Column nullable mismatch (model NOT NULL, DB nullable, or vice versa) | Halt → Chris ratifies (A) update models to match prod, (B) include in snapshot, (C) defer Story 10b |
| Index missing in models (DB has, models don't) | Likely OK — include in snapshot per current DB state |
| Index missing in DB (models declare, DB doesn't) | Halt — model declared without migration generated. Investigate or defer. |
| Column default mismatch (model `default=utc_now()`, DB no default) | Halt — historical drift (per Scenario 3.2 origen case). Resolve per Chris ratify. |
| Table missing in autogen (only in pg_dump) | Likely orphaned table. Include in snapshot OR drop per Chris ratify. |
| Table missing in pg_dump (only in autogen) | Model added without migration generated. Investigate. |

### 3.2 Consolidated `001_initial_snapshot.py` structure

```python
"""Story 10 consolidated initial snapshot — reflects current visionarias_logs schema as of 2026-05-12.

This consolidation REPLACES the historical 131-migration chain. Apply on fresh nicolify_dev DB.

DDL pattern: idempotent raw SQL per .claude/rules/backend-migrations.md.
"""

revision = "001_initial_snapshot"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 1. Extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # 2. Enums (raw SQL, idempotent — DROP TYPE IF EXISTS pattern)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE expert_business_type AS ENUM (
                'profesional_salud', 'consultor_profesional', 'coach_mentor',
                'academia_infoproductor', 'anfitrion_productor', 'agencia_freelance',
                'marca_ecommerce', 'negocio_local', 'software_saas'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    # ... all 30+ enums in pg_dump enum order

    # 3. Tables (alphabetical-by-module per pg_dump output)
    op.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            slug VARCHAR(255) NOT NULL UNIQUE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMP WITH TIME ZONE
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_tenants_slug ON tenants (slug)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tenants_deleted_at ON tenants (deleted_at) WHERE deleted_at IS NULL")

    # ... all ~150+ tables per module:
    # - brand_settings (JSONB store)
    # - brand_personality_profiles
    # - offers, offer_value_levels, offer_archetypes, offer_type_presets, offer_format_catalog
    # - landing_pages, landing_templates
    # - copilot_conversations, copilot_trace_event, copilot_llm_call, copilot_mutation_journal, copilot_routing_log, copilot_workflow_metric, copilot_marketing_kb_chunks
    # - sales_agent_trace_event, sales_agent_llm_call, sales_agent_personality_profiles, sales_agent_routing_log
    # - analytics_*: stage_groups, official_metrics, channel_connections, etl_extraction_log
    # - campaigns_*, social_proof_*, crm_*, scheduling_*, advertising_*
    # - iam_users, iam_tenant_memberships
    # - model_pricing_snapshot (cross-agent)
    # - mv_daily_llm_cost_per_tenant_v2 (materialized view — last)

    # 4. Foreign keys (idempotent — checks pg_constraint via DO block)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE brand_settings ADD CONSTRAINT fk_brand_settings_tenant
                FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    # ... all FKs

    # 5. Triggers + functions (e.g., compute_cycle_start for billing)
    op.execute("CREATE OR REPLACE FUNCTION compute_cycle_start(...) ...")

    # 6. Materialized views
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_llm_cost_per_tenant_v2 AS
            SELECT ...
    """)

def downgrade():
    # NO downgrade for consolidated snapshot (story 10 = clean break)
    raise NotImplementedError("Consolidated snapshot — downgrade not supported")
```

### 3.3 Fresh `nicolify_dev` DB workflow sequence

```bash
# Step 1 — Stop old container (preserves data on volume — restart-able)
docker compose -f docker-compose.dev.yml stop postgres_dev

# Step 2 — Create new container with new POSTGRES_DB
# Architect Phase 0 Q: spin up secondary container `nicolify_postgres_dev` parallel OR reuse
# existing container with NEW DB name. Recommended: PARALLEL container (safer rollback during 24h soak).
# Update luana-platform/docker-compose.dev.yml:
#   nicolify_postgres_dev:
#     image: postgres:15
#     environment:
#       POSTGRES_DB: nicolify_dev
#       POSTGRES_USER: postgres
#       POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
#     ports: ["5433:5432"]  # different port to avoid collision during transition
#     volumes:
#       - nicolify_postgres_data:/var/lib/postgresql/data

docker compose -f /home/chris/luana-platform/docker-compose.dev.yml up -d nicolify_postgres_dev

# Step 3 — Verify new container healthy
docker exec nicolify_postgres_dev pg_isready -U postgres

# Step 4 — Apply consolidated migration
cd /home/chris/luana-platform/nicolify/backend
DATABASE_URL=postgresql://postgres@localhost:5433/nicolify_dev \
    uv run alembic upgrade head

# Step 5 — Verify head reports 001_initial_snapshot
DATABASE_URL=postgresql://postgres@localhost:5433/nicolify_dev \
    uv run alembic current
# Expected output: 001_initial_snapshot (head)

# Step 6 — Schema verification (diff vs pg_dump captured Step 1)
docker exec nicolify_postgres_dev pg_dump --schema-only -U postgres nicolify_dev > /tmp/nicolify_schema.sql
diff <(sort /tmp/aisaleshT_schema.sql | grep -v "^--\|^$\|SET ") \
     <(sort /tmp/nicolify_schema.sql | grep -v "^--\|^$\|SET ") > /tmp/schema_final_diff.txt
wc -l /tmp/schema_final_diff.txt
# Acceptable diff: cosmetic ordering, comments. Intolerable: missing tables/columns/FKs.

# Step 7 — Run BE tests against new DB (delta=0 enforcement)
DATABASE_URL=postgresql://postgres@localhost:5433/nicolify_dev \
    uv run pytest --json-report --json-report-file=/tmp/final-be-tests.json --tb=short

# Step 8 — Idempotency stress test (Scenario 3.3)
DATABASE_URL=postgresql://postgres@localhost:5433/nicolify_dev \
    uv run alembic upgrade head  # second run — must succeed no-op

# Step 9 — Schema hash check (before+after second alembic upgrade)
docker exec nicolify_postgres_dev pg_dump --schema-only -U postgres nicolify_dev | sha256sum
# Should match Step 6 output hash
```

### 3.4 AISALESHT DB drop (T-14 closure — Scenario 3.4)

```bash
# Preconditions (sub-agent verifies before psql DROP):
# 1. Smoke E2E Feature 5 passed GREEN (timestamp recorded)
# 2. 24h soak elapsed since smoke green
# 3. Chris explicit ratification marker in checkpoint.md `next_action: ratified_db_drop=true`

# Verification commands:
SMOKE_TIMESTAMP=$(cat docs/product/stories/luana-nicolify-migration/T-11-result.md | grep "smoke_green_at:" | awk '{print $2}')
NOW=$(date -u +%s)
DELTA=$((NOW - $(date -d "$SMOKE_TIMESTAMP" +%s)))
if [ "$DELTA" -lt 86400 ]; then
    echo "SOAK NOT ELAPSED — defer drop"
    exit 1
fi

# If preconditions met:
docker exec visionarias_postgres_dev psql -U postgres -c "DROP DATABASE visionarias_logs;"
docker compose -f /home/chris/AISALESHT/docker-compose.dev.yml down

# Audit trail
echo "AISALESHT DB visionarias_logs dropped at $(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    >> /home/chris/luana-platform/docs/product/stories/luana-nicolify-migration/T-14-impl-log.md
```

## 4. luana-core packages convention verification (Phase 0 spike — pre T-2/T-5/T-6 spawn)

Architect MUST verify the following Story 5/6/7 deliverables before sub-agent spawn. Failure to verify → silent rewrite errors discovered at test execution phase.

### 4.1 Convention: package import root naming

| AISALESHT path | luana-core directory | Python package name (in `pyproject.toml::project.name`) | Import root |
|---|---|---|---|
| `src/modules/brand/` | `core/luana-core-brand-studio/src/luana_core_brand_studio/` | `luana-core-brand-studio` (hyphens) | `from luana_core_brand_studio` (underscores) |
| `src/modules/copilot/` | `core/luana-core-copilot/src/luana_core_copilot/` | `luana-core-copilot` | `from luana_core_copilot` |
| `src/shared/agent_observability/` | `core/luana-core-observability/src/luana_core_observability/` | `luana-core-observability` | `from luana_core_observability` |
| (etc. — all 26 packages) | | | |

**Phase 0 verification commands:**
```bash
for pkg in /home/chris/luana-platform/core/luana-core-*; do
  pkg_name=$(basename $pkg)
  py_pkg=$(ls $pkg/src/ 2>/dev/null | head -1)
  echo "$pkg_name → import: $py_pkg"
done
```

If any package name doesn't follow `luana-core-X` → `luana_core_X` convention → architect updates MAPPING dict in `scripts/codemod_be_imports.py`.

### 4.2 Convention: copilot `module_registry` discovery

AISALESHT pattern (copilot-expert SSoT):
- Discovery convention: `src.modules.{name}.copilot_provider:provider` (e.g., `src.modules.brand.copilot_provider.provider`)
- Each module has `__init__.py` exposing `provider = ModuleProvider(...)` subclass of `BaseCopilotProvider`

luana-core pattern (post Story 5/6 lift — architect verifies):
- Should preserve: `luana_core_{name}.copilot_provider:provider`
- Architect reads `/home/chris/luana-platform/core/luana-core-copilot/src/luana_core_copilot/registry/module_registry.py` line-by-line to confirm `_discover_providers()` uses convention OR entry-points-based.
- If entry-points-based: each luana-core package's `pyproject.toml` declares `[project.entry-points."luana_core_copilot.providers"]` table. Architect verifies via `grep "luana_core_copilot.providers" core/luana-core-*/pyproject.toml`.

### 4.3 Convention: cross-module port re-export (`links/ports/`)

AISALESHT pattern (backend-ddd.md SSoT):
- All cross-module port interfaces live in `src/shared/links/ports/`
- E.g., `from src.shared.links.ports.brand import BrandDataPort`

luana-core pattern (post lift):
- Each port lives in its OWNING module's package (not in `shared`)
- E.g., `BrandDataPort` lives in `luana_core_brand_studio.links.ports.brand`
- Consumers import from owner: `from luana_core_brand_studio.links.ports.brand import BrandDataPort`

**Why this matters:** if luana-core consolidated all ports under `luana_core_platform.links.ports.*` (different convention) → MAPPING dict needs different rewrites. Architect verifies via `find core/luana-core-*/src -path "*links/ports*" -name "*.py"`.

**Architect Phase 0 verification (T-1 pre-spawn):**
```bash
echo "=== AISALESHT links/ports inventory ==="
ls /home/chris/AISALESHT/backend/src/shared/links/ports/

echo "=== luana-core links/ports per package ==="
find /home/chris/luana-platform/core/ -path "*links/ports*" -name "*.py" | head -30
```

If structure differs from "owner package re-export" → update MAPPING dict accordingly + document in `T-1-result.md` for sub-agents.

## 5. `/pm` SSoT migration (Feature 7) — paths to migrate

> **Concrete hardcoded-path audit (Halt Decisión 4A) — sub-agent T-13 must run BEFORE git mv:**

```bash
echo "=== Hardcoded /home/chris/AISALESHT/docs/product paths ==="
grep -rn "/home/chris/AISALESHT/docs/product" \
    /home/chris/AISALESHT/scripts/ \
    /home/chris/AISALESHT/.claude/ \
    /home/chris/AISALESHT/backend/tests/ \
    /home/chris/AISALESHT/backend/src/ \
    2>/dev/null

echo "=== Relative path references docs/product ==="
grep -rn "docs/product" \
    /home/chris/AISALESHT/scripts/ \
    /home/chris/AISALESHT/.claude/ \
    /home/chris/AISALESHT/backend/tests/scripts/ \
    2>/dev/null | head -20
```

**Expected outputs:**
- Hardcoded `/home/chris/AISALESHT/docs/product/...` should ideally be 0 (rules + scripts use relative paths). If ≥1 → Halt + Chris ratify replacement strategy.
- Relative `docs/product/...` references should survive `git mv` if both source + script live in same repo root (pre-move both in AISALESHT, post-move both in luana-platform). Architect verifies path traversal pattern via `pathlib.Path(__file__).parents[N]`.

**T-13 sequence:**

```bash
# Step 1 — Snapshot pre-move audit
cd /home/chris/AISALESHT
tar czf /tmp/pre-move-snapshot.tar.gz docs/product/ scripts/git-hooks/ scripts/generate_backlog.py scripts/reconcile_capabilities.py scripts/emit_process_metric.py scripts/_pii_patterns.py 2>/dev/null
echo "Snapshot size: $(du -sh /tmp/pre-move-snapshot.tar.gz | cut -f1)"

# Step 2 — Verify scripts pre-move
python scripts/generate_backlog.py --dry-run
python scripts/reconcile_capabilities.py --check
echo "Scripts pre-move: GREEN"

# Step 3 — git mv across repos
# Architect Phase 0 Q7 resolved: 2-step strategy
#   (a) Move filesystem AISALESHT/docs/product/ → luana-platform/docs/product/
#       (Note: luana-platform/docs/ already exists from Story 9 with ARCHITECTURE.md etc. — merge, not replace)
mkdir -p /home/chris/luana-platform/docs/product/
# rsync preserves git history attributes (not the git log itself — that's via commit narrative)
rsync -a /home/chris/AISALESHT/docs/product/ /home/chris/luana-platform/docs/product/
rm -rf /home/chris/AISALESHT/docs/product/

#   (b) Move scripts
mv /home/chris/AISALESHT/scripts/generate_backlog.py /home/chris/luana-platform/scripts/
mv /home/chris/AISALESHT/scripts/reconcile_capabilities.py /home/chris/luana-platform/scripts/
mv /home/chris/AISALESHT/scripts/emit_process_metric.py /home/chris/luana-platform/scripts/
mv /home/chris/AISALESHT/scripts/_pii_patterns.py /home/chris/luana-platform/scripts/  # OR lift to luana-core if cross-vertical
# Verify if _pii_patterns.py is lifted to luana-core already (per anti-duplication.md inventory)
grep -rn "_pii_patterns" /home/chris/luana-platform/core/ 2>/dev/null | head -3

#   (c) Move tests for scripts (R12 process metric tests etc.)
mkdir -p /home/chris/luana-platform/tests/scripts/
mv /home/chris/AISALESHT/backend/tests/scripts/* /home/chris/luana-platform/tests/scripts/ 2>/dev/null

# Step 4 — Update pre-commit hooks paths
# Source: /home/chris/AISALESHT/scripts/git-hooks/pre-commit Sections 4-9
# Target: /home/chris/luana-platform/scripts/git-hooks/pre-commit
# Sections updated:
#   Section 4 (downstream regression freshness gate): file path `backend/src/shared/.+\.py$` → `nicolify/backend/src/shared/.+\.py$` (or per architect — could become `core/luana-core-*/src/.+\.py$`)
#   Section 5 (voseo): glosario file path `.claude/rules/spanish-text.md` (relative — survives)
#   Section 6 (backlog freshness): regen `scripts/generate_backlog.py` (relative)
#   Section 7 (ruff): venv path `nicolify/backend/.venv/bin/ruff` (or `backend/.venv/` if BE not yet moved — architect verifies T-13 sequence post BE rewrite waves)
#   Sections 8-9 (PII patterns): `scripts/_pii_patterns.py` (relative)
cp /home/chris/AISALESHT/scripts/git-hooks/pre-commit /home/chris/luana-platform/scripts/git-hooks/pre-commit
sed -i 's|backend/.venv|nicolify/backend/.venv|g' /home/chris/luana-platform/scripts/git-hooks/pre-commit
# Verify
grep -n "backend/.venv\|nicolify/backend" /home/chris/luana-platform/scripts/git-hooks/pre-commit

# Step 5 — Test pre-commit hook fires (dummy commit)
cd /home/chris/luana-platform
echo "test pre-commit" >> docs/product/BACKLOG.md
git add docs/product/BACKLOG.md
GIT_EDITOR=true git commit -m "test: pre-commit hook verification (will revert)" --dry-run
git restore --staged docs/product/BACKLOG.md
git restore docs/product/BACKLOG.md

# Step 6 — Verify scripts post-move
cd /home/chris/luana-platform
python scripts/generate_backlog.py --check
python scripts/reconcile_capabilities.py --check
echo "Scripts post-move: GREEN"

# Step 7 — Commits
cd /home/chris/AISALESHT
git add -A docs/product/  # add deletions
git add -A scripts/  # add script deletions
git commit -m "chore(pm-ssot): migrate to luana-platform — closure pre-archive Story 10 Feature 7"

cd /home/chris/luana-platform
git add docs/product/ scripts/ tests/scripts/ scripts/git-hooks/
git commit -m "feat(pm-ssot): receive /pm SSoT from AISALESHT — Phase 4 merge Story 10 Feature 7"
```

## 6. Halt Trigger #11 workflow (test mock missing path — concrete)

**Trigger context:** sub-agent during T-2..T-7 rewrite encounters test like:
```python
# tests/modules/X/test_Y.py
def test_some_behavior(mocker):
    mocker.patch("src.shared.legacy_helper.compute_internal_thing", return_value="mocked")
    # ... test body
```

Codemod rewrites production imports `src.shared.legacy_helper` → `luana_core_X.legacy_helper`. But `luana_core_X` does NOT export `compute_internal_thing` (legacy helper never lifted Stories 1-8).

### Workflow:

```
1. Sub-agent detects: test failure with AttributeError or ModuleNotFoundError on rewrite mock path
2. Sub-agent runs verification:
   $ python -c "from luana_core_X.legacy_helper import compute_internal_thing"
   ModuleNotFoundError: No module named 'luana_core_X.legacy_helper'
3. Sub-agent verifies NOT a typo:
   $ grep -rn "def compute_internal_thing" /home/chris/luana-platform/core/
   # If 0 results → confirmed missing from luana-core
4. Halt-and-ask Trigger #11 raised:
   - Audit trail T-N-impl-log.md `## Halt Trigger #11 raised` section
   - Sub-agent reports to /dev-team orchestrator:
     ```
     halted -> docs/product/stories/luana-nicolify-migration/T-N-impl-log.md (Trigger #11 — test mock src.shared.legacy_helper.compute_internal_thing has no luana-core equivalent)
     ```
5. /dev-team orchestrator escalates Chris with 3-option choice:
   (A) Inline mock value into test (no patch):
       def test_some_behavior():
           # Mock value inlined — production code uses original (nicolify-local helper)
           result = some_function_under_test()
           assert result == "expected"
   (B) Lift symbol via Story 14 deferred:
       - Add to DEFERRED-FAILURES-STORY-10.md (or new DEFERRED-LIFTS-STORY-10.md)
       - Story 14 ticket: lift compute_internal_thing to luana_core_X
       - Test skipped with magic comment + Story 14 ticket reference
   (C) Skip test temporarily with magic comment:
       # luana-migration-defer: helper compute_internal_thing not lifted (see Story 14 ticket Q-XX)
       @pytest.mark.skip(reason="luana-migration-defer")
       def test_some_behavior():
           ...
6. Chris ratifies → sub-agent resumes with strategy chosen
7. T-N-impl-log.md records strategy + line numbers affected + Story 14 cross-reference if applicable
```

**Architect estimate (preview validators):** expect 5-15 instances of Trigger #11 during T-2..T-7 wave. Most likely root causes:
- Helper functions in `src/shared/X` that were NEVER lifted because Story 5/6/7 scope was modules only
- Test fixtures patching internal implementation details (refactor opportunity Story 14)
- Dead code paths (mock target = dead — discover + remove)

**Validator (Part 2 04-validators.yaml preview):** `V-NF-9 — Halt Trigger #11 instances documented`:
- `DEFERRED-FAILURES-STORY-10.md` lists all Trigger #11 invocations
- Story 14 ticket queue captures lifts deferred
- Auditor C5 verifies each Trigger #11 ratified by Chris (audit trail)

## 7. `pyproject.toml` / `package.json` configuration post-migration

### 7.1 nicolify/backend (Phase 0 architect spike — verify path exists)

**Path:** `/home/chris/luana-platform/nicolify/backend/pyproject.toml` (architect Q3 resolved: nested under nicolify/, NOT replacing nicolify/ stub)

```toml
[project]
name = "nicolify-backend"
version = "0.1.0"
description = "Nicolify SaaS backend — consumes luana-core-* packages"
requires-python = ">=3.12"
dependencies = [
    "luana-core-platform==0.1.0",
    "luana-core-llm==0.1.0",
    "luana-core-observability==0.1.0",
    "luana-core-events==0.1.0",
    "luana-core-channels==0.1.0",
    "luana-core-idempotency==0.1.0",
    "luana-core-billing==0.1.0",
    "luana-core-compliance==0.1.0",
    "luana-core-extraction==0.1.0",
    "luana-core-extension-sdk==0.1.0",
    "luana-core-iam==0.1.0",
    "luana-core-tenant-profile==0.1.0",
    "luana-core-tenant-domains==0.1.0",
    "luana-core-commercial-calendar==0.1.0",
    "luana-core-social-proof==0.1.0",
    "luana-core-assets==0.1.0",
    "luana-core-crm==0.1.0",
    "luana-core-analytics-engine==0.1.0",
    "luana-core-landing==0.1.0",
    "luana-core-connections==0.1.0",
    "luana-core-brand-studio==0.1.0",
    "luana-core-offer-studio==0.1.0",
    "luana-core-copilot==0.1.0",
    "luana-core-sales-agent==0.1.0",
    "luana-core-campaigns==0.1.0",
    # Nicolify-local (NOT in luana-core)
    "fastapi[standard]",
    "sqlalchemy>=2.0",
    "alembic",
    # ... other Nicolify-specific deps from AISALESHT/backend/pyproject.toml
]

[tool.uv.sources]
luana-core-platform = { workspace = true }
luana-core-llm = { workspace = true }
# ... all 26 packages workspace-local during dev

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### 7.2 nicolify/frontend (Feature 2 — verified spec §2)

**Path:** `/home/chris/luana-platform/nicolify/frontend/package.json`

```json
{
  "name": "@luana/nicolify-web",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint src/ --cache --max-warnings=0",
    "test:unit": "vitest run --coverage",
    "test:e2e:smoke": "E2E_BASE_URL=https://dev-app.nicolify.com playwright test --project=smoke"
  },
  "dependencies": {
    "@luana/api-client": "workspace:*",
    "@luana/ui-kit": "workspace:*",
    "@luana/format": "workspace:*",
    "@luana/hooks": "workspace:*",
    "@luana/schemas": "workspace:*",
    "@luana/design-tokens": "workspace:*",
    "@luana/extension-sdk": "workspace:*",
    "next": "^16.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@clerk/nextjs": "...",
    "@tanstack/react-query": "...",
    "tailwindcss": "..."
  }
}
```

### 7.3 pnpm-workspace.yaml update

```yaml
packages:
  - core
  - core/@luana/*
  - nicolify
  - nicolify/frontend         # NEW Story 10 Feature 2 — FE workspace member
  - vitalia
  - comunify
  - lupulo
```

### 7.4 luana-platform root pyproject.toml `[tool.uv.workspace]` update

```toml
[tool.uv.workspace]
members = [
    "core",
    "apps/test-brand",
    # 26 core packages (verified Story 9 alphabetical order)
    "core/luana-core-analytics-engine",
    # ... (all 26 — preserve Story 9 alphabetical)
    # Brand apps (TS workspace members)
    "nicolify",
    "nicolify/backend",         # NEW Story 10 Feature 1 — BE workspace member
    "vitalia",
    "comunify",
    "lupulo",
]
```

## 8. References

- Parent: `03-arch.md` (consolidated overview)
- Companion: `05-guidelines.md` (patterns required/forbidden + files in scope + skills loading)
- Spec: `01-spec.md` (9 features × 4 scenarios = 36 Gherkin)
- Migration mapping SSoT: `/home/chris/luana-platform/docs/migration-from-nicolify.md §3`
- Story 9 precedent: `/home/chris/AISALESHT/docs/archive/2026/stories/luana-v0-1-0-publish/03-arch-be.md`
- Rules cited:
  - `.claude/rules/backend-ddd.md` (DDD layers + cross-module via ports)
  - `.claude/rules/backend-migrations.md` (raw SQL `IF NOT EXISTS` idempotent)
  - `.claude/rules/tenant-isolation.md` (every query `.where(tenant_id == ...)`)
  - `.claude/rules/anti-duplication.md` (shared abstractions inventory, NEVER mirror)
  - `.claude/rules/anti-default-flip-audit.md` (NO flag flips Story 10)
  - `.claude/rules/auditor-downstream-regression.md` (R3 scope cumulative for shared/* changes)
  - `.claude/rules/hotfix-repro-mandatory.md` (N/A Story 10 not hot-fix)
- Skills consulted: `backend-expert`, `copilot-expert`, `sales-agent-expert`, `brand-expert`, `offer-expert`, `metrics-expert`, `tessl__langgraph`, `tessl__fastapi`
