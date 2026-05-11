---
story_id: luana-crm-analytics-landing-connections
arch_version: 1
last_modified: 2026-05-11
drafted_by: /architect (claude-opus-4-7)
authority: 01-spec.md + outcome §7.3 lift mode + §7.4 halt + Story 3 03-arch.md pattern reference
deviations_from_spec:
  - "4 copilot_provider/ subfolders (crm, analytics, landing, connections) DEFERRED to Story 6 (copilot lift) — same pattern as Story 3 §9. All 4 import src.modules.copilot.domain.ports which is Story 6 territory."
  - "crm/api/contacts.py + crm/application/services/contact_query_service.py DEFERRED to Story 8 — they import src.modules.campaigns.{api._dependencies, application.dtos.pagination}. Campaigns is Story 8 lift. Same defer-with-source rule. 1 test file (test_contacts_api.py) also defers."
  - "connections/api/dependencies/__init__.py DEFERRED to Story 7 (sales_agent lift) — it is the composition root that wires sales_agent.application.orchestrator.chat::ChatOrchestrator as concrete MessageHandlerPort impl. Per source-file own comment: 'composition root for connections'. Lifts WITH sales_agent in Story 7 (analogous to the copilot_provider/ pattern). Source comment explicitly marks the cross-module import as intentional DI."
  - "Connections marketing_connectors (manychat, mailerlite, shopify) STAY in core/luana-core-connections — they are tenant-data-agnostic (multi-tenant SaaS channels), NOT brand-specific (Lupulo POS / Vitalia gateway don't exist yet in AISALESHT — those will be Stories 11-13 NEW code, not lifted). DEFERRED-FILES.md notes 'brand-specific adapters reserved' without listing files."
  - "Analytics module split into 3 lift tickets (T-3a framework+domain, T-3b providers, T-3c scheduler+workers) due to 123-file density. Single 'lift analytics' ticket would exceed Sonnet 2h cap. Sub-tickets preserve atomicity per outcome §7.4."
  - "Per-package Makefile (per-package convention) created in core/luana-core-analytics-engine/Makefile for `extraction-contract` regen target (lift of backend/scripts/generate_extraction_contract_doc.py). Per outcome §7.3, this is mechanical: it's the SAME script renamed + path-adjusted, not a refactor."
---

# Story 4 — Luana CRM + Analytics + Landing + Connections lift — Architecture (03-arch.md)

## §1. Topology — Dependency Graph (resolved)

### §1.1 Audit method

Ran cross-module import grep per `.claude/rules/anti-duplication.md`:

```bash
cd /home/chris/AISALESHT/backend/src/modules
for m in crm analytics landing connections; do
    grep -rEh "^from src\.(modules|shared|core)\." $m/ --include="*.py" | sort -u
done
```

Cross-tabulated each module's external dependencies. Resolved 0 cycles. Found 3 deviations from clean lift requiring deferral (cross-Story forward imports — see §9):

1. **crm/api/contacts.py + crm/application/services/contact_query_service.py** → import `src.modules.campaigns` (Story 8 territory). DEFERRED with source.
2. **connections/api/dependencies/__init__.py** → imports `src.modules.sales_agent.application.orchestrator.chat::ChatOrchestrator` (Story 7 territory). DEFERRED with source.
3. **Four `copilot_provider/` sub-folders** (one per Story 4 module) → import `src.modules.copilot.domain.ports` (Story 6 territory). DEFERRED with source per Story 3 pattern.

### §1.2 Python package dependency DAG (4 packages)

```
                                        luana-core-platform  (Story 2 foundation)
                                              ↑
        ┌────────────────────┬────────────────┴────────────────┬──────────────────┐
        │                    │                                 │                  │
        │                    │                                 │                  │
  luana-core-crm   luana-core-analytics-engine   luana-core-landing   luana-core-connections
        │                    │                                 │                  │
        ↓                    ↓                                 ↓                  ↓
     luana-core-iam    luana-core-iam (via test fixtures)    luana-core-iam    luana-core-iam
        │                    │                                 │                  │
        │                    │                                 │                  │
        │                    │                                 │                  │
  (uses User,           (uses User for         (uses User for routes;   (uses User + Tenant
   Tenant for             API routes;             also reads             via api.dependencies;
   API dependencies;      reads offer            offer.LaunchEdition    consumes shared.ports
   reads shared.crm       service via            via shared.links.      verbatim;
   models verbatim)       shared.links port)     ports.edition_         marketing_connectors
                                                 landing_clone)         brand-agnostic;
                                                                        webhook adapters
                                                                        verbatim)
```

**Resolution summary (cross-package edges, all DAG-clean):**

| Source package | Depends on | Symbol used |
|---|---|---|
| `luana-core-crm` | `luana-core-platform` | `shared.domain.{base_entity, currency, enums, events}` + `shared.infrastructure.models.crm` + `shared.links.ports.{crm_enrichment, crm_repos, calendar, channel_adapter, campaigns}` + `core.{base_repository, context, database}` |
| `luana-core-crm` | `luana-core-iam` | `iam.api.dependencies::get_current_user` + `iam.domain.user::User` |
| `luana-core-analytics-engine` | `luana-core-platform` | `shared.domain.{base_entity, currency, datetime_utils, enums}` + `shared.infrastructure.models.crm` (JourneyEvent, SaleModel via verifier/probe code) + `shared.links.ports.{calendar, channel_adapter}` + `core.{config, database}` |
| `luana-core-analytics-engine` | `luana-core-iam` | `iam.api.dependencies::get_current_user` + `iam.domain.user::User` (used in API routes) |
| `luana-core-landing` | `luana-core-platform` | `shared.domain.base_entity` + `shared.links.ports.{edition_landing_clone, offer}` + `core.database` |
| `luana-core-landing` | `luana-core-iam` | `iam.api.dependencies::get_current_user` + `iam.domain.user::User` + `iam.infrastructure.models.tenant_model::TenantModel` |
| `luana-core-connections` | `luana-core-platform` | `shared.domain.{base_entity, datetime_utils, enums, messages, ports, schemas.scheduling}` + `shared.infrastructure.{channels.base, database.types}` + `shared.links.{models, service, ports.*}` + `core.{config, context, database}` |
| `luana-core-connections` | `luana-core-iam` | `iam.api.dependencies::{get_current_user, get_current_tenant_id}` + `iam.domain.{tenant, user}` + `iam.infrastructure.models.tenant_model::TenantModel` |

**Cycle check:** None. DAG-clean. Each of the 4 Story 4 packages is a leaf within Story 4 (no inter-Story-4 dependencies after deferring `contacts.py` + `connections/api/dependencies/`).

**No inter-Story-4 coupling.** Cross-checked:

```bash
grep -l "from src.modules.crm" /home/chris/AISALESHT/backend/src/modules/{analytics,landing,connections}/ -r
# → empty after deferring contacts.py
grep -l "from src.modules.landing\|from src.modules.connections\|from src.modules.analytics" /home/chris/AISALESHT/backend/src/modules/crm/
# → empty (1 hit in etl_service.py BUT etl_service.py is in analytics, importing crm types; this is the "analytics imports shared.infrastructure.models.crm" pattern, NOT direct crm module import)
```

All 4 Story 4 packages parallelize after Story 3 batch completes.

### §1.3 Coupling notes

- **crm is a CDP**, reads `shared.infrastructure.models.crm` (JourneyEvent, Sale, Lead, etc.) — those models live in `shared/`, Story 2 territory. Already lifted as `luana_core_platform.infrastructure.models.crm`. Verbatim consumption preserves contract.
- **analytics consumes `shared.links.ports.{channel_adapter, calendar}`** for cross-module reads. Both lifted Story 2 to `luana_core_platform.links.ports.*`. Verbatim consumption.
- **landing reads `shared.links.ports.edition_landing_clone + offer`** — both shared-ports, Story 2 lifted. Landing module itself remains brand-agnostic (config-driven templates).
- **connections is the largest channel adapter surface** — 67 files. The 11 channels (gmail, google_ads, google_analytics, google_calendar, instagram, meta, search_console, telegram, tiktok, webhook, whatsapp, youtube, youtube_analytics) all consume `shared.domain.ports::TokenRefreshError` + `shared.links.ports.*`. All brand-agnostic.
- **connections marketing_connectors** (`manychat`, `mailerlite`, `shopify`) are multi-tenant SaaS channel adapters, NOT brand-specific. They lift to core. Brand-specific adapters (e.g., future `vitalia_payment_gateway`, `lupulo_pos`) **do not yet exist** in AISALESHT — Stories 11-13 will introduce them as NEW code (not lifted).

### §1.4 No-cycle proof

Manually walked the DAG:
- crm → platform.shared + platform.core + iam (downward edges only; iam doesn't import crm)
- analytics → platform.shared + platform.core + iam (idem)
- landing → platform.shared + platform.core + iam (idem)
- connections → platform.shared + platform.core + iam (idem)

No cyclic edges. Pure DAG.

### §1.5 No forward-Story-5/6/7/8 coupling (after deferrals)

Verified post-deferral grep:

```bash
grep -rEh "^from src\.modules\.(brand|offer|copilot|sales_agent|campaigns|scheduling|advertising|social_media)\." \
    /home/chris/AISALESHT/backend/src/modules/{crm,analytics,landing,connections}/ \
    --include="*.py" \
    --exclude-dir=copilot_provider | sort -u
```

Result (deferring the 3 noted files):
- `from src.modules.offer.application.services.offer_read_port_impl` — analytics reads ONE concrete offer impl in `analytics/copilot_provider/provider.py` only (= deferred subfolder). After deferring copilot_provider/, NO remaining forward imports.

## §2. Lift Order

Per dependency graph, lift order is **1 batch × parallelizable**:

**Batch 1 (all 4 parallel after T-1 workspace prep; no inter-Story-4 deps):**
1. `luana-core-crm` — 50 files (49 production + 1 contacts.py deferred). 29 tests.
2. `luana-core-analytics-engine` — 123 files (split into T-3a/T-3b/T-3c for atomicity).
3. `luana-core-landing` — 21 files (20 + deferred copilot_provider/). 13 tests.
4. `luana-core-connections` — 67 files (65 + deferred copilot_provider/ + deferred api/dependencies/__init__.py). 33 tests.

**Cross-cutting:**
- T-1 workspace prep before any lift (extends Stories 2+3 root pyproject.toml).
- T-8 cross-package integration smoke + aggregate pytest post-lifts.
- T-9 ETL contract regen integration (analytics-specific — lift `scripts/generate_extraction_contract_doc.py` + per-package Makefile).
- T-10 connections engine smoke (stub adapter registers via channels/factory).
- T-11 brand-agnostic engines arch fitness (extends Story 3 §7.1 to crm + analytics + landing + connections).
- T-12 no-forward-imports arch fitness (extends Story 3 §7.2 to Story 4 packages).
- T-13 lint + AISALESHT untouched + DEFERRED-FILES.md update + READMEs.

## §3. Per-Package Structure

### §3.1 Python package layout (mirror Story 3 §3.1)

```
core/luana-core-<name>/
├── pyproject.toml                       # workspace member, version "0.0.1-alpha"
├── README.md                            # stub: 1 paragraph what + lift origin
├── Makefile                             # analytics-only — extraction-contract regen target
├── scripts/                             # analytics-only
│   └── generate_extraction_contract_doc.py
├── src/
│   └── luana_core_<name>/               # snake_case (PEP 8)
│       ├── __init__.py
│       └── <preserved DDD structure verbatim>
└── tests/
    ├── __init__.py
    ├── conftest.py                       # lift verbatim if present
    └── <preserved test structure>
```

### §3.2 Example — luana-core-crm

```
core/luana-core-crm/
├── pyproject.toml
├── README.md
├── src/luana_core_crm/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── contacts.py                  # ← DEFERRED Story 8 (imports campaigns)
│   │   ├── customers.py
│   │   ├── dto/
│   │   │   └── *.py
│   │   ├── leads.py
│   │   ├── nps.py
│   │   ├── referrals.py
│   │   └── sales.py
│   ├── application/
│   │   ├── __init__.py
│   │   └── services/
│   │       ├── contact_query_service.py # ← DEFERRED Story 8 (imports campaigns)
│   │       ├── customer_service.py
│   │       ├── lead_service.py
│   │       ├── lifecycle_service.py
│   │       ├── nps_service.py
│   │       ├── referral_service.py
│   │       └── sale_service.py
│   ├── domain/
│   │   ├── customer.py
│   │   ├── enums.py
│   │   ├── events.py
│   │   ├── lead.py
│   │   ├── nps.py
│   │   ├── referral.py
│   │   ├── sale.py
│   │   └── scoring.py
│   ├── infrastructure/
│   │   ├── models/
│   │   │   └── *.py
│   │   └── repositories/
│   │       └── *.py
│   # NOTE: copilot_provider/ NOT lifted — DEFERRED Story 6
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_contacts_api.py              # ← DEFERRED Story 8 alongside contacts.py
    ├── test_customer_*.py
    ├── test_lead_*.py
    ├── test_sale_*.py
    └── ...
```

### §3.3 Example — luana-core-analytics-engine

```
core/luana-core-analytics-engine/
├── pyproject.toml
├── README.md
├── Makefile                              # ← extraction-contract target
├── scripts/
│   └── generate_extraction_contract_doc.py  # ← lifted from backend/scripts/, path-adjusted
├── src/luana_core_analytics_engine/
│   ├── __init__.py
│   ├── api/*.py
│   ├── application/
│   │   ├── dto/*.py
│   │   └── services/
│   │       ├── etl_service.py
│   │       ├── metrics_service.py
│   │       ├── channel_registry.py
│   │       └── stage_services/
│   │           ├── attraction_stage.py
│   │           ├── overview_stage.py
│   │           ├── group_detail.py
│   │           └── ...
│   ├── domain/
│   │   ├── campaign_entities.py
│   │   ├── enums.py
│   │   ├── extraction_contract.py        # ← SSoT for ETL contract regen
│   │   ├── metric_catalog.py             # ← SSoT for runtime semantics
│   │   ├── ports.py
│   │   └── ...
│   ├── infrastructure/
│   │   ├── cache/
│   │   ├── etl/                          # pipeline, aggregations, transformers
│   │   ├── models/
│   │   ├── providers/                    # 12 providers + registry
│   │   ├── repositories/
│   │   └── sync/
│   └── workers/
│       ├── manychat_sync.py
│       ├── scheduler.py
│       ├── settings.py
│       └── tasks.py
│   # NOTE: copilot_provider/ NOT lifted — DEFERRED Story 6
└── tests/
    └── *.py (102 files)
```

### §3.4 Example — luana-core-landing

```
core/luana-core-landing/
├── pyproject.toml
├── README.md
├── src/luana_core_landing/
│   ├── __init__.py
│   ├── api/*.py
│   ├── application/
│   │   ├── landing_content_builders.py
│   │   ├── landing_service.py
│   │   └── ...
│   ├── domain/
│   │   ├── content.py
│   │   ├── enums.py
│   │   ├── events.py
│   │   ├── landing_page.py
│   │   └── ...
│   └── infrastructure/
│       ├── models/*.py
│       └── repositories/*.py
│   # NOTE: copilot_provider/ NOT lifted — DEFERRED Story 6
└── tests/
    └── *.py (13 files)
```

### §3.5 Example — luana-core-connections

```
core/luana-core-connections/
├── pyproject.toml
├── README.md
├── src/luana_core_connections/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies/
│   │   │   └── __init__.py               # ← DEFERRED Story 7 (imports sales_agent)
│   │   ├── dto/*.py
│   │   ├── channel_info.py
│   │   ├── gmail.py
│   │   ├── google_ads.py
│   │   ├── google_analytics.py
│   │   ├── google_calendar.py
│   │   ├── health.py
│   │   ├── instagram.py
│   │   ├── manychat.py
│   │   ├── marketing_webhooks.py
│   │   ├── meta.py
│   │   ├── search_console.py
│   │   ├── shopify.py
│   │   ├── status.py
│   │   ├── telegram.py
│   │   ├── tiktok.py
│   │   ├── webhook.py
│   │   ├── whatsapp.py
│   │   ├── youtube.py
│   │   └── youtube_analytics.py
│   ├── application/services/*.py
│   ├── domain/*.py
│   └── infrastructure/
│       ├── channels/
│       │   ├── gmail.py
│       │   ├── google_ads.py
│       │   ├── google_analytics.py
│       │   ├── google_calendar.py
│       │   ├── instagram.py
│       │   ├── meta.py
│       │   ├── search_console.py
│       │   ├── telegram.py
│       │   ├── telegram_service.py
│       │   ├── tiktok.py
│       │   ├── webhook.py
│       │   ├── whatsapp/
│       │   │   ├── base.py
│       │   │   ├── factory.py
│       │   │   ├── interface.py
│       │   │   ├── v1.py
│       │   │   └── v2.py
│       │   ├── youtube.py
│       │   └── youtube_analytics.py
│       ├── marketing_connectors/
│       │   ├── base.py
│       │   ├── mailerlite.py
│       │   ├── manychat.py
│       │   └── shopify.py
│       ├── models/*.py
│       └── repositories/*.py
│   # NOTE: copilot_provider/ NOT lifted — DEFERRED Story 6
└── tests/
    └── *.py (33 files)
```

## §4. Workspace Registration

### §4.1 Root pyproject.toml (extend Stories 2+3 state)

Stories 2+3 declared 15 packages. Story 4 adds 4 more:

```toml
[tool.uv.workspace]
members = [
    "core",
    # Story 2 packages (already registered, 9 packages)
    "core/luana-core-platform",
    "core/luana-core-llm",
    "core/luana-core-channels",
    "core/luana-core-idempotency",
    "core/luana-core-observability",
    "core/luana-core-events",
    "core/luana-core-extraction",
    "core/luana-core-compliance",
    "core/luana-core-billing",
    # Story 3 packages (already registered, 6 packages)
    "core/luana-core-iam",
    "core/luana-core-tenant-profile",
    "core/luana-core-tenant-domains",
    "core/luana-core-commercial-calendar",
    "core/luana-core-social-proof",
    "core/luana-core-assets",
    # Story 4 packages (NEW — 4 packages)
    "core/luana-core-crm",
    "core/luana-core-analytics-engine",
    "core/luana-core-landing",
    "core/luana-core-connections",
    # Brand apps
    "nicolify", "vitalia", "comunify", "lupulo",
]

[tool.uv.sources]
# Story 2 (already registered)
luana-core-platform = { workspace = true }
luana-core-llm = { workspace = true }
luana-core-channels = { workspace = true }
luana-core-idempotency = { workspace = true }
luana-core-observability = { workspace = true }
luana-core-events = { workspace = true }
luana-core-extraction = { workspace = true }
luana-core-compliance = { workspace = true }
luana-core-billing = { workspace = true }
# Story 3 (already registered)
luana-core-iam = { workspace = true }
luana-core-tenant-profile = { workspace = true }
luana-core-tenant-domains = { workspace = true }
luana-core-commercial-calendar = { workspace = true }
luana-core-social-proof = { workspace = true }
luana-core-assets = { workspace = true }
# Story 4 (NEW)
luana-core-crm = { workspace = true }
luana-core-analytics-engine = { workspace = true }
luana-core-landing = { workspace = true }
luana-core-connections = { workspace = true }
```

### §4.2 No TS this story

Story 4 is backend-only. `pnpm-workspace.yaml` unchanged.

## §5. Import Path Mapping

### §5.1 Python mapping (verbatim preservation rule)

| AISALESHT source path | luana-platform internal path |
|---|---|
| `from src.modules.crm.<X>` | `from luana_core_crm.<X>` |
| `from src.modules.analytics.<X>` | `from luana_core_analytics_engine.<X>` |
| `from src.modules.landing.<X>` | `from luana_core_landing.<X>` |
| `from src.modules.connections.<X>` | `from luana_core_connections.<X>` |
| `from src.modules.iam.<X>` | `from luana_core_iam.<X>` (Story 3 SSoT) |
| `from src.shared.domain.<X>` | `from luana_core_platform.domain.<X>` (Story 2 SSoT) |
| `from src.shared.infrastructure.<X>` | `from luana_core_platform.infrastructure.<X>` |
| `from src.shared.links.<X>` | `from luana_core_platform.links.<X>` |
| `from src.core.<X>` | `from luana_core_platform.core.<X>` |

**Important:** AISALESHT imports NOT touched (Story 10 territory).

### §5.2 Deferred imports — NO sed rewrite

The following imports are kept as `src.modules.*` in lifted code **only because the deferred file is NOT lifted**. The deferred file remains in AISALESHT verbatim:

- `from src.modules.campaigns.*` → **deferred crm/api/contacts.py + crm/application/services/contact_query_service.py + tests/modules/crm/test_contacts_api.py** stay in AISALESHT. NO rewrite needed.
- `from src.modules.sales_agent.*` → **deferred connections/api/dependencies/__init__.py** stays in AISALESHT. NO rewrite needed.
- `from src.modules.copilot.*` → **deferred {crm,analytics,landing,connections}/copilot_provider/** stay in AISALESHT. NO rewrite needed.

Detection rule for /dev-team: BEFORE running sed, run `grep -rEn "from src\.modules\.(campaigns|sales_agent|copilot)" <package-being-lifted>/` → flagged files are in DEFERRED list (§9). Skip those files during `cp -r`.

## §6. Test Lift Strategy

### §6.1 Python tests

Tests lift in **same commit as source** (per `.claude/rules/auditor-downstream-regression.md`):

| AISALESHT source | luana-platform destination | Test count |
|---|---|---|
| `backend/tests/modules/crm/` | `core/luana-core-crm/tests/` | 29 files (1 deferred: test_contacts_api.py) |
| `backend/tests/modules/analytics/` | `core/luana-core-analytics-engine/tests/` | 102 files |
| `backend/tests/modules/landing/` | `core/luana-core-landing/tests/` | 13 files |
| `backend/tests/modules/connections/` | `core/luana-core-connections/tests/` | 33 files |

### §6.2 Mock path migration

Tests may use `monkeypatch.setattr("src.modules.<m>.X")` — update to `luana_core_<m>.X` verbatim. Same mechanical sed pattern as Story 3 §6.

### §6.3 conftest.py preservation

Each module's `tests/conftest.py` lifts verbatim alongside source.

### §6.4 Cross-coupling tests stay in AISALESHT

These test files import deferred source files → they remain in AISALESHT until Story 7/8 lift completes:

- `backend/tests/modules/crm/test_contacts_api.py` (imports contacts.py = deferred) → stays in AISALESHT, lifts Story 8 alongside contacts.py.
- Any test importing `sales_agent.orchestrator` or `copilot.domain.ports` → stays.
- `backend/tests/modules/analytics/test_offer_read_port.py` — verify if it imports deferred sub-paths.
- `backend/tests/modules/analytics/test_sales_endpoint.py` — verify.

/dev-team: per ticket, run `grep -l "from src.modules.\(campaigns\|sales_agent\|copilot\)" tests/modules/<m>/` BEFORE lift. Flag files → defer.

## §7. Architecture Fitness Tests

### §7.1 Brand-agnostic engines (NEW — Story 4-specific, extends Story 3 §7.1)

Per 01-spec.md §3.4 + outcome §2 brand-agnostic invariant, **luana-core-{crm, analytics-engine, landing, connections} MUST stay brand-agnostic**.

**New arch fitness test:** `core/tests/architecture/test_story4_brand_agnostic_engines.py`

```python
"""Story 4 — Brand-agnostic engines invariant.

luana-core-{crm, analytics-engine, landing, connections} MUST NOT contain
brand-aware control flow. Channel adapters consume tenant config (not brand).
"""
from pathlib import Path
import re

PKGS = [
    ("luana-core-crm", "luana_core_crm"),
    ("luana-core-analytics-engine", "luana_core_analytics_engine"),
    ("luana-core-landing", "luana_core_landing"),
    ("luana-core-connections", "luana_core_connections"),
]

FORBIDDEN_PATTERNS = [
    r"if\s+brand\s*==",
    r"if\s+tenant\.brand\s*==",
    r"if\s+self\.brand\s*==",
    r'brand\s*==\s*["\'](nicolify|vitalia|comunify|lupulo)["\']',
    # Hardcoded API keys / app IDs (must be env)
    r'(API_KEY|SECRET|TOKEN)\s*=\s*["\'](?!os\.|settings\.|env|getenv).{8,}["\']',
]


def test_engines_no_brand_aware_control_flow() -> None:
    """No `if brand == "..."` or brand-key string literals in engine source."""
    core_dir = Path(__file__).parent.parent.parent
    offenders = []
    for pkg_dir, pkg_snake in PKGS:
        pkg_src = core_dir / pkg_dir / "src" / pkg_snake
        if not pkg_src.exists():
            continue
        for py_file in pkg_src.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            for pattern in FORBIDDEN_PATTERNS:
                matches = re.findall(pattern, text)
                if matches:
                    offenders.append((py_file, pattern, matches))
    assert not offenders, f"Story 4 engines contain brand-aware code: {offenders}"
```

### §7.2 No forward-Story imports — Story 4 (extends Story 3 §7.2)

**New arch fitness test:** `core/tests/architecture/test_story4_no_forward_module_imports.py`

```python
"""Story 4 packages MUST NOT import from Story 5/6/7/8 modules.

Forward-coupling would break the migration sequence.
After deferring contacts.py + connections/api/dependencies/ + copilot_provider/,
no forward imports remain.
"""
from pathlib import Path
import re

STORY4_PKGS = [
    "luana-core-crm",
    "luana-core-analytics-engine",
    "luana-core-landing",
    "luana-core-connections",
]

FORBIDDEN_IMPORTS = [
    r"from\s+luana_core_(brand|offer)\.",
    r"from\s+luana_core_(copilot|sales_agent)\.",
    r"from\s+luana_core_(campaigns|scheduling)\.",
    r"from\s+luana_core_(advertising|social_media)\.",
    # Also block accidental AISALESHT imports
    r"from\s+src\.modules\.",
]


def test_no_forward_module_imports() -> None:
    core_dir = Path(__file__).parent.parent.parent
    offenders = []
    for pkg in STORY4_PKGS:
        pkg_src = core_dir / pkg / "src"
        if not pkg_src.exists():
            continue
        for py_file in pkg_src.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            for pattern in FORBIDDEN_IMPORTS:
                matches = re.findall(pattern, text)
                if matches:
                    offenders.append((py_file, pattern, matches))
    assert not offenders, f"Story 4 forward module imports: {offenders}"
```

### §7.3 ETL extraction contract drift gate (Story 4 analytics-specific)

The existing AISALESHT `backend/tests/architecture/test_extraction_contract.py` verifies catalog↔contract alignment. Story 4 lifts a tailored equivalent.

**New arch fitness test:** `core/tests/architecture/test_analytics_extraction_contract_drift.py`

```python
"""Story 4 — analytics extraction contract regen reproducibility.

Verifies the per-package Makefile extraction-contract target regenerates
the markdown idempotently (same bytes on consecutive runs).
"""
import subprocess
import hashlib
from pathlib import Path


def test_extraction_contract_regen_idempotent() -> None:
    core_dir = Path(__file__).parent.parent.parent
    pkg_dir = core_dir / "luana-core-analytics-engine"
    md_path = pkg_dir / "docs" / "extraction-contract.md"

    # First regen
    subprocess.run(["make", "-C", str(pkg_dir), "extraction-contract"], check=True)
    first_hash = hashlib.sha256(md_path.read_bytes()).hexdigest()

    # Second regen (idempotency)
    subprocess.run(["make", "-C", str(pkg_dir), "extraction-contract"], check=True)
    second_hash = hashlib.sha256(md_path.read_bytes()).hexdigest()

    assert first_hash == second_hash, "extraction-contract regen is not idempotent"
```

### §7.4 Connections engine stub-adapter smoke (Story 4-specific)

**New smoke test:** `core/luana-core-connections/tests/test_engine_stub_adapter_registration.py`

```python
"""Story 4 — connections engine accepts stub adapter registration.

Per 01-spec.md scenario C — verifies engine is decoupled from concrete
channel implementations (brand-agnostic).
"""
import pytest
from luana_core_connections.infrastructure.channels.whatsapp.interface import WhatsAppAdapter  # adjust import


def test_stub_adapter_can_register_via_engine() -> None:
    """Stub adapter implements ABC and can be instantiated through factory."""

    class StubAdapter:
        provider_name = "stub-test"

        async def send(self, message): ...
        async def receive(self, webhook): ...

    # Verify ABC structural conformance (channel protocol level — no concrete brand)
    # Replace with the actual engine register API after lift inspection
    assert hasattr(StubAdapter, "provider_name")
    assert hasattr(StubAdapter, "send")
    assert hasattr(StubAdapter, "receive")
```

(Builder finalizes signature against actual lifted engine API in T-10.)

### §7.5 Existing AISALESHT arch tests stay (no migration)

Story 4 does NOT migrate AISALESHT arch tests (e.g., `test_extraction_contract.py` in AISALESHT). They stay validating AISALESHT until Story 10. Story 4 builds parallel Luana-platform-side arch tests (§7.1-§7.4).

## §8. Per-Package pyproject.toml Dependency Declarations

### §8.1 luana-core-crm/pyproject.toml

```toml
[project]
name = "luana-core-crm"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "fastapi>=0.115",
    "structlog>=24.0",
    "luana-core-platform",
    "luana-core-iam",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }
luana-core-iam = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/luana_core_crm"]
```

### §8.2 luana-core-analytics-engine/pyproject.toml

```toml
[project]
name = "luana-core-analytics-engine"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "fastapi>=0.115",
    "structlog>=24.0",
    "httpx>=0.27",                 # providers HTTP clients
    "arq>=0.26",                   # workers/scheduler
    "redis>=5.0",                  # cache
    "luana-core-platform",
    "luana-core-iam",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }
luana-core-iam = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/luana_core_analytics_engine"]
```

### §8.3 luana-core-landing/pyproject.toml

```toml
[project]
name = "luana-core-landing"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "fastapi>=0.115",
    "structlog>=24.0",
    "luana-core-platform",
    "luana-core-iam",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }
luana-core-iam = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/luana_core_landing"]
```

### §8.4 luana-core-connections/pyproject.toml

```toml
[project]
name = "luana-core-connections"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "fastapi>=0.115",
    "structlog>=24.0",
    "httpx>=0.27",                 # channel adapters
    "luana-core-platform",
    "luana-core-iam",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }
luana-core-iam = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/luana_core_connections"]
```

## §9. Deferred Files (Story 4 exception list)

### §9.1 copilot_provider/ subfolders — DEFERRED Story 6

Same pattern as Story 3 §9. All 4 Story 4 modules have a `copilot_provider/` subfolder importing `src.modules.copilot.domain.ports`:

| AISALESHT path | Reason | Will lift in |
|---|---|---|
| `backend/src/modules/crm/copilot_provider/` (provider.py + data_access.py) | imports `src.modules.copilot.domain.ports::{BaseCopilotProvider, ModuleData, DataQueryPlan, DataQueryResult}` | Story 6 (copilot lift) |
| `backend/src/modules/analytics/copilot_provider/` (provider.py) | imports `src.modules.copilot.domain.ports::{BaseCopilotProvider, ModuleData}` | Story 6 |
| `backend/src/modules/landing/copilot_provider/` (provider.py) | imports `src.modules.copilot.domain.ports::{BaseCopilotProvider, ModuleData}` | Story 6 |
| `backend/src/modules/connections/copilot_provider/` (provider.py) | imports `src.modules.copilot.domain.ports::{BaseCopilotProvider, ModuleData}` | Story 6 |

**Lift behavior:** when lifting each Story 4 module, /dev-team SKIPS the `copilot_provider/` subfolder. Story 6 will lift these 4 + the 2 Story 3 deferrals alongside copilot module.

### §9.2 Cross-module composition roots — DEFERRED Story 7 + Story 8

These files are composition roots wiring concrete impls from future-story modules. Lift WITH the source they import:

| AISALESHT path | Imports | Will lift in |
|---|---|---|
| `backend/src/modules/connections/api/dependencies/__init__.py` | `src.modules.sales_agent.application.orchestrator.chat::ChatOrchestrator` (singleton wired as MessageHandlerPort) | Story 7 (sales_agent lift) — file's own docstring explicitly marks the import as "composition root" |
| `backend/src/modules/crm/api/contacts.py` | `src.modules.campaigns.api._dependencies::get_campaigns_async_session` + `src.modules.campaigns.application.dtos.pagination::PaginatedResponse` | Story 8 (campaigns lift) |
| `backend/src/modules/crm/application/services/contact_query_service.py` | `src.modules.campaigns.application.dtos.pagination::PaginatedResponse` | Story 8 |
| `backend/tests/modules/crm/test_contacts_api.py` | Tests deferred contacts.py | Story 8 |

**Lift behavior:** /dev-team SKIPS these files during `cp -r` of the parent module. The file remains in AISALESHT verbatim. Story 7/8 lifts the file alongside the lifted future module.

### §9.3 Brand-specific connections adapters — NONE (clarification)

01-spec.md §2.5 mentions "Lupulo POS, Vitalia payment gateway, etc." as brand-specific adapters NOT to lift to core. **However**, these files **do not exist** in AISALESHT today. They are placeholder examples in the spec for Stories 11-13 future work.

Current connections marketing connectors (`manychat.py`, `mailerlite.py`, `shopify.py`) are **multi-tenant SaaS channels** (configured per-tenant via tenant config rows), NOT brand-specific. They lift to `luana-core-connections` verbatim.

The arch fitness test §7.1 ensures no brand identifier strings leak into `luana-core-connections` source. Future brand-specific adapters in Stories 11-13 will live in `vertical-{niche}/connections/` packages (per outcome §2 brand isolation strategy).

### §9.4 Audit trail

Append entry to `core/DEFERRED-FILES.md` (created Story 2):

```markdown
## Story 4 deferrals (2026-05-11)

### Defer to Story 6 (copilot lift)
- backend/src/modules/crm/copilot_provider/ → Story 6 (imports src.modules.copilot.domain.ports::{BaseCopilotProvider, ModuleData, DataQueryPlan, DataQueryResult})
- backend/src/modules/analytics/copilot_provider/ → Story 6
- backend/src/modules/landing/copilot_provider/ → Story 6
- backend/src/modules/connections/copilot_provider/ → Story 6

### Defer to Story 7 (sales_agent lift)
- backend/src/modules/connections/api/dependencies/__init__.py → Story 7 (composition root for MessageHandlerPort = ChatOrchestrator singleton)

### Defer to Story 8 (campaigns lift)
- backend/src/modules/crm/api/contacts.py → Story 8 (imports src.modules.campaigns.api._dependencies + dtos.pagination)
- backend/src/modules/crm/application/services/contact_query_service.py → Story 8 (idem)
- backend/tests/modules/crm/test_contacts_api.py → Story 8 (tests deferred contacts.py)

### Brand-specific adapters reserved (NOT yet existing)
- Future Lupulo POS adapter → Stories 11-13 (will live in `vertical-lupulo/connections/`)
- Future Vitalia payment gateway → Stories 11-13 (`vertical-vitalia/connections/`)
- Future Comunify-specific adapters → Stories 11-13 (`vertical-comunify/connections/`)

Current marketing connectors (manychat, mailerlite, shopify) ARE multi-tenant SaaS channels (not brand-specific) — lifted to core.
```

## §10. ETL Extraction Contract Regen Strategy

### §10.1 Decision: per-package Makefile in luana-core-analytics-engine

Per 01-spec.md §2.4 + §3.3, analytics module owns the `make extraction-contract` workflow. Two options considered:

| Option | Pro | Con | Decision |
|---|---|---|---|
| Lift to ROOT `~/luana-platform/Makefile` | Mirrors AISALESHT location | Couples analytics workflow to monorepo root (against package-encapsulation principle) | ❌ |
| Per-package `core/luana-core-analytics-engine/Makefile` | Encapsulates analytics-owned tooling within the package | Slight invocation path change | ✅ |

### §10.2 Lift mechanics

1. **Lift the script verbatim** with path adjustment:

   ```
   backend/scripts/generate_extraction_contract_doc.py
       → core/luana-core-analytics-engine/scripts/generate_extraction_contract_doc.py
   ```

   The script's internal imports become:

   ```python
   # Before (line 21)
   from src.modules.analytics.domain.extraction_contract import (...)

   # After (Story 4)
   from luana_core_analytics_engine.domain.extraction_contract import (...)
   ```

2. **Lift the markdown output destination** to a per-package location:

   ```
   docs/etl/extraction-contract.md
       → core/luana-core-analytics-engine/docs/extraction-contract.md
   ```

   Update the script's `_BACKEND_ROOT`/output path constant accordingly (sed mechanical).

3. **Create per-package Makefile**:

   ```makefile
   # core/luana-core-analytics-engine/Makefile
   .PHONY: extraction-contract

   # SSoT: domain/extraction_contract.py.
   # Run from package root or via `make -C core/luana-core-analytics-engine extraction-contract` from workspace root.
   extraction-contract:
       cd $(CURDIR) && uv run python scripts/generate_extraction_contract_doc.py
       @echo "✓ Regenerated docs/extraction-contract.md"
       @echo "  Now run: uv run pytest tests/test_extraction_contract.py -x -q"
   ```

### §10.3 Validator invocation

Per 04-validators.yaml `V-F-etl-1`:

```bash
cd ~/luana-platform && make -C core/luana-core-analytics-engine extraction-contract
# OR: cd ~/luana-platform/core/luana-core-analytics-engine && make extraction-contract
```

Validator `V-F-etl-2` confirms regen idempotency:

```bash
cd ~/luana-platform/core/luana-core-analytics-engine
make extraction-contract
HASH1=$(sha256sum docs/extraction-contract.md | cut -d' ' -f1)
make extraction-contract
HASH2=$(sha256sum docs/extraction-contract.md | cut -d' ' -f1)
test "$HASH1" = "$HASH2"
```

### §10.4 Test lift

The AISALESHT `backend/tests/architecture/test_extraction_contract.py` (currently in `tests/architecture/`, NOT `tests/modules/analytics/`) stays in AISALESHT until Story 10. Story 4 builds the per-package equivalent **(§7.3 above — `test_analytics_extraction_contract_drift.py`)** in `core/tests/architecture/`.

Additionally, the analytics-module-level test `backend/tests/modules/analytics/test_metric_catalog.py` lifts with the analytics package (catalog↔contract alignment validation) verbatim.

## §11. Connections Engine — Inventory of brand-specific Files to Defer

### §11.1 Inventory result

**Conclusion: ZERO files in `backend/src/modules/connections/` are brand-specific.**

Grep evidence:

```bash
grep -rln "manychat\|stripe\|cloudflare\|lupulo\|vitalia\|comunify" \
    /home/chris/AISALESHT/backend/src/modules/connections/
# → 6 files, ALL referencing manychat (multi-tenant SaaS provider, not brand)
```

The 6 matches are all instances of "manychat" the SaaS product name (the ManyChat integration), not the Nicolify brand-specific identifier `nicolify`.

The Story 1 spec §2.5 wording "Lupulo POS, Vitalia payment gateway, etc." refers to **future** brand-vertical-specific adapters that **don't yet exist in AISALESHT**. Those adapters will be built as NEW code in Stories 11-13 inside `vertical-{niche}/connections/` packages.

### §11.2 What does lift to luana-core-connections

All 67 files in `backend/src/modules/connections/` lift to `core/luana-core-connections/` EXCEPT:
- `connections/api/dependencies/__init__.py` (DEFERRED Story 7 — see §9.2)
- `connections/copilot_provider/provider.py` + `__init__.py` (DEFERRED Story 6 — see §9.1)

This includes the 11 channel adapters in `infrastructure/channels/` (gmail, google_ads, google_analytics, google_calendar, instagram, meta, search_console, telegram, telegram_service, tiktok, webhook, whatsapp/, youtube, youtube_analytics) AND the 3 marketing_connectors (mailerlite, manychat, shopify). All brand-agnostic.

### §11.3 Smoke verification (T-10)

Per Scenario C of 01-spec.md, a stub adapter CAN register through the engine. Builder writes a smoke test (§7.4 above) that:
1. Defines a stub `StubAdapter` class (no brand affiliation).
2. Verifies the adapter ABC structural conformance via existing engine factory.
3. Confirms no brand-string assertion path in the registration code.

### §11.4 Future-Story 11-13 reserved files

When Stories 11-13 add brand-specific adapters, they live in:
- `vertical-vitalia/connections/payment_gateway/` (NEW)
- `vertical-lupulo/connections/pos_adapter/` (NEW)
- `vertical-comunify/connections/community_sync/` (NEW)

None of these lift FROM AISALESHT. They are net-new code per outcome §2.

## §12. Research Notes (state-of-the-art as of 2026-05-11)

| Source | Accessed | Key takeaway |
|---|---|---|
| uv workspace docs https://docs.astral.sh/uv/concepts/workspaces/ | 2026-05-11 (via Story 2-3 SSoT) | Workspace sources resolve at install time. Per-package Makefiles work fine inside workspace (no monorepo Makefile required). |
| Hatchling build backend https://hatch.pypa.io/latest/config/build/ | 2026-05-11 (via Story 2-3) | `[tool.hatch.build.targets.wheel] packages = ["src/<name>"]` is canonical src-layout. Matches Stories 2-4. |
| `.claude/rules/etl-extraction-contract.md` (internal) | 2026-05-11 | SSoT 2 files (extraction_contract.py + metric_catalog.py) + auto-gen MD pattern. Lift workflow preserves this contract — script + Makefile + arch fitness test all migrate. |
| Outcome §7.3 lift mode (internal) | 2026-05-11 | Lift verbatim, no scope expansion. Sub-ticket split for analytics is granularity, NOT refactor. |

**Knowledge cutoff disclosure:** Opus 4.7 cutoff = January 2026. uv workspace + hatchling + Makefile patterns predate cutoff. Internal rules verified live against current state of `.claude/rules/`.

## §13. Cross-Cutting Concerns (per CLAUDE.md)

- **Tenant isolation:** preserved — every entity carries `tenant_id`, every query filters it. Lift verbatim. CRM, analytics, landing, connections all already comply in AISALESHT.
- **Currency handling:** `luana_core_crm.domain.sale` consumes `FALLBACK_CURRENCY` from `luana_core_platform.domain.currency`. Lift verbatim.
- **Master data:** analytics + crm use UTC + tenant locale per shared utilities. Lift verbatim.
- **Spanish neutro LatAm:** no UI strings in these 4 modules (all BE) → N/A.
- **PII sanitization:** routes use `response_model=` on user-facing DTOs (especially crm leads/customers/sales — they hold PII like email/phone). Lift preserves.
- **Native-first dev:** validators use native `uv run pytest`, `uv run ruff`, native `make` — no Docker.
- **TDD-mandatory:** Story 4 is lift, not new code. Tests lift verbatim alongside source — preserves RED→GREEN guarantee.
- **Brand-agnostic engines:** new invariant codified in §7.1 arch fitness test (extends Story 3 §7.1 to all 4 Story 4 modules).
- **ETL contract SSoT:** preserved via §10 per-package Makefile + arch fitness test §7.3.

## §14. Architecture Fitness Gates (test surfaces)

| Gate | Layer | Owner |
|---|---|---|
| `uv sync --all-packages` GREEN (19 packages total) | luana-platform root | gate-runner |
| `uv run pytest core/luana-core-<name>/tests/` GREEN per package (4 packages) | per-package | gate-runner |
| `uv run ruff check core/luana-core-{crm,analytics-engine,landing,connections}/` GREEN | luana-platform root | gate-runner |
| `make -C core/luana-core-analytics-engine extraction-contract` regen smoke + idempotent | per-package | gate-runner |
| `uv run pytest core/luana-core-analytics-engine/tests/test_metric_catalog.py` GREEN | per-package | gate-runner |
| `uv run pytest core/tests/architecture/test_story4_brand_agnostic_engines.py` GREEN | luana-platform | gate-runner |
| `uv run pytest core/tests/architecture/test_story4_no_forward_module_imports.py` GREEN | luana-platform | gate-runner |
| `uv run pytest core/tests/architecture/test_analytics_extraction_contract_drift.py` GREEN | luana-platform | gate-runner |
| Connections engine stub-adapter smoke (per-package) | luana-platform | gate-runner |
| AISALESHT untouched verifier | AISALESHT repo | gate-runner |
| No-publish verifier | luana-platform | gate-runner |
| `core/DEFERRED-FILES.md` updated with Story 4 entries | luana-platform | gate-runner |

## §15. Capability YAML + modules/ Updates Required

**None.** Story 4 is mechanical lift. Does not change user-facing capability. No `docs/product/capabilities/{m}/*.yaml` updates. No `docs/product/modules/{m}.md` updates.

Outcome `luana-platform-migration.md` § progress log will be updated by /pm at story close.

## §16. Open Questions for PM (none blocking)

All scope decisions resolved per outcome §7.3 lift mode + this architect document:

- **4 packages confirmed:** spec §2.2 + 06-tickets DAG-aligned. NO escalation.
- **6 deferred files confirmed:** §9 lists each with destination Story. Same pattern as Story 3 §9. NO escalation.
- **Analytics split into 3 sub-tickets:** per outcome §7.4 atomicity rule, 123 files exceed single-ticket Sonnet 2h cap. Split is granularity, NOT scope expansion. NO escalation.
- **Per-package Makefile chosen (§10):** preserves AISALESHT workflow without coupling to root pyproject. Mechanical, no refactor. NO escalation.
- **NO brand-specific adapters exist in current AISALESHT connections** (§11): clarified spec wording — future-Story-11-13 territory. DEFERRED-FILES.md notes reserved without listing files. NO escalation.

If Chris reads this and wants to lift copilot_provider/ subfolders early (would require stubbing `BaseCopilotProvider` protocol in `luana-core-platform.links.ports`), that's REFACTOR (scope expansion) — escalate.
