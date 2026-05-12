---
story_id: luana-campaigns-extension-sdk
arch_version: 1
last_modified: 2026-05-12
drafted_by: /architect-orchestrator (claude-opus-4-7) — single spawn full-stack consolidated
authority: 01-spec.md + outcome §7.5 verbatim + checkpoint frontmatter binding_decisions + Story 6+7 precedent + 03-arch-be.md detailed
blocked_by: luana-sales-agent-engine (Story 7) done 2026-05-12
surfaces:
  - "Backend Python: 3 NEW packages (luana-core-campaigns lift + luana-core-extension-sdk + apps/test-brand smoke)"
  - "Frontend TypeScript: 1 NEW package (@luana/extension-sdk — type mirror only, FE-mirror partial scope EP-6/EP-10/EP-18)"
  - "Documentation: docs/extension-points.md (1 NEW file)"
deviations_from_spec:
  - "All 5 open questions OQ-1..OQ-5 resolved in 03-arch-be.md frontmatter. Architect confirms: 26 Python workspace members + 7 TS workspace members post-Story-8."
  - "TS mirror = HAND-MAINTAINED for v0.0.8-alpha (codegen deferred Story 9+). V-F-ts-1 arch test compares Python dataclasses.fields() against TS interface keys via AST parse."
---

# Story 8 — Consolidated Full-Stack Architecture — Campaigns Lift + Extension SDK Formalization

> **Surface ownership rule (drives builder routing in 06-tickets.yaml):**
>
> | Surface | Builder | Auditor | Notes |
> |---|---|---|---|
> | `core/luana-core-campaigns/**` (campaigns lift) | **`builder-backend` (Sonnet)** | `auditor-backend` (Opus) | Mechanical lift mode §7.3. No agentic logic. |
> | `core/luana-core-extension-sdk/**` (Python SDK skeleton + foundation + EP-6..EP-18 stubs) | **`builder-backend` (Sonnet)** | `auditor-backend` (Opus) | Pure contract code. Zero workspace deps. |
> | `core/luana-core-extension-sdk/_adapters.py` (EP-3 + EP-4 read-only wrappers — D-T1 cardinal touches Stories 6+7 frozen registries semantically) | **`builder-agentic` (Opus)** | `auditor-agentic` (Opus) | R23 trigger — wraps frozen agentic registries. Opus REQUIRED. |
> | `core/luana-core-extension-sdk/extension_points.py` EP-1..EP-5 critical methods (executable — adapter integration) | **`builder-agentic` (Opus)** | `auditor-agentic` (Opus) | R23 trigger — EP-3/EP-4 method bodies invoke adapters wrapping Stories 6+7. Opus REQUIRED. |
> | `core/@luana/extension-sdk/**` (TS type mirror) | **`builder-frontend` (Sonnet)** | `auditor-frontend` (Sonnet) | Type-only export, zero runtime. Manual mirror EP-6/EP-10/EP-18. |
> | `apps/test-brand/**` (smoke pack) | **`builder-backend` (Sonnet)** | `auditor-backend` (Opus) | Test app. Production_code=false. |
> | `docs/extension-points.md` (recipe + per-vertical examples) | **`builder-backend` (Sonnet)** | `auditor-backend` (Opus) | Documentation. Spanish neutro applies. |
> | Arch fitness tests (`core/tests/architecture/test_story8_*.py` x 12 tests) | **`builder-backend` (Sonnet)** | `auditor-backend` (Opus) | Tests cement cardinal invariants V-NF-* + V-AG-new-story-8. |

## §0. Architect run on

- **Date:** 2026-05-12 (current per `date -u +%Y-%m-%d`)
- **Architect knowledge cutoff:** Opus 4.7 = January 2026. For state-of-the-art Python frozen dataclass + SDK registry patterns (Python 3.12 slots+kw_only canonical 2026), researched live via WebSearch — captured §15 Research Notes.

## §1. Topology Overview

### §1.1 Backend topology (full detail in 03-arch-be.md §1)

```
        luana-core-platform (Story 2)
                ↑
        Stories 2-7 packages (23 — pre-Story-8 baseline)
                ↑
        ┌─────────────┴─────────────┐
        │                            │
luana-core-campaigns         luana-core-extension-sdk  ★ NEW STORY 8 ★
  (lift mode §7.3)            (NEW — zero workspace deps)
        │                            │
        ↓                            ↑
   consumes Stories 2-3      apps/test-brand  ★ NEW STORY 8 ★
   (iam + observability      (smoke validation app)
    + idempotency + channels
    + events + platform)
```

### §1.2 Frontend topology (FE-mirror partial scope)

```
core/@luana/extension-sdk  ★ NEW STORY 8 ★
    │
    ├── src/index.ts                  # Type-only exports
    ├── src/brand-context.ts          # BrandContext interface (9 fields)
    └── src/models.ts                 # SidebarRouteDef + LandingTemplateDef + WizardStepDef TS interfaces
        (3 EPs only — EP-6 sidebar BE+FE sync + EP-10 landing JSON schema + EP-18 wizard BE+FE sync)
```

Stories 11-13 brand FE apps will consume `@luana/extension-sdk` for compile-time validation of WizardStepDef + SidebarRouteDef when implementing brand-specific wizard + sidebar UIs.

### §1.3 Existing systems audit (NO-NEW-LAYER per `.claude/rules/anti-duplication.md`)

Per audit detail in 03-arch-be.md §1.2. Summary:

- **CONSUME** Stories 2-7 packages — campaigns minimal cross-module surface (iam + 6 shared subsystems only).
- **WRAP read-only via EP-3 + EP-4** Stories 6+7 frozen registries (D-T1 cardinal) — adapter pattern, byte-stable.
- **NEW** Extension SDK + BrandContext + 18 EP DataClass models + apps/test-brand smoke pack + docs deliverable.

**Anti-duplication inventory append (T-18 finalization):** Append row to `.claude/rules/anti-duplication.md` shared abstractions inventory:

> | Extension SDK / ExtensionPointRegistry / BrandContext / 18 EP DataClass models | `luana_core_extension_sdk.*` (Story 8) | Brand apps (Stories 11-13 + nicolify Story 10) |

## §2. Surface decomposition + builder/auditor routing

### §2.1 Backend (builder-backend Sonnet — 9 tickets — non-agentic)

Tickets T-1, T-2, T-3, T-4 (SDK foundation: workspace + skeleton + BrandContext + models/exceptions/protocols), T-7 (EP-6..EP-18 backlog stubs), T-9..T-13 (campaigns lift 5 tickets), T-14, T-15 (apps/test-brand FastAPI + smoke tests), T-16 (docs/extension-points.md), T-17 (arch fitness 12 tests), T-18 (finalization).

### §2.2 Agentic backend (builder-agentic Opus — 2 tickets — R23 trigger)

Tickets T-5 (ExtensionPointRegistry critical EP-1..EP-5 EXECUTABLE), T-6 (_adapters.py + EP-3+EP-4 read-only wrappers touching Stories 6+7 frozen registries semantically).

Rationale R23 trigger: T-5 + T-6 implementation **touches the boundary surface that interfaces with Stories 6+7 frozen registries**. While the SDK adapter code itself does NOT execute LLM calls or agentic orchestration, the **semantic correctness of wrapping byte-stable** requires Opus-level discipline — V-AG-3 Story 6 + Story 7 golden snapshots must continue GREEN, and a Sonnet-level mistake propagating private-surface access into adapters would break the cardinal invariant.

Per R23 + checkpoint binding_decisions: **production_code=false** at story level (Story 8 is contract surface, not runtime agentic). BUT T-5 + T-6 individual tickets touch agentic-adjacent surface → architect promotes to Opus eligibility despite story-level `production_code=false`. Sonnet may FALL BACK only if Chris explicitly overrides per ticket.

### §2.3 Frontend (builder-frontend Sonnet — 1 ticket)

Ticket T-8 (@luana/extension-sdk TS package — 3 type mirrors only, zero runtime, no React, no client/server boundary).

### §2.4 R23 + R3 + R26 enforcement

- **R23 (agentic production code Opus)** — T-5 + T-6 owner=builder-agentic Opus eligibility per §2.2 rationale.
- **R3 (downstream regression)** — T-17 includes full Stories 1-7 packages per-package pytest verification + Story 6 V-AG-3 + Story 7 V-AG-3 golden snapshots continue GREEN.
- **R26 (hot-fix repro mandatory)** — N/A (Story 8 is greenfield SDK + lift, NOT hot-fix).
- **R32 + R33 (capability reconciliation + BACKLOG freshness)** — `/pm` post-merge runs `scripts/reconcile_capabilities.py` + `scripts/generate_backlog.py` (auto via pre-commit hook Section 6).

## §3. Cardinal invariants cemented (13 total)

Per checkpoint frontmatter `binding_decisions` + spec §6:

| # | ID | Invariant | Cemented via |
|---|---|---|---|
| 1 | V-NF-1 | Workspace alphabetical (26 Python members + 7 TS members post-Story-8) | `test_workspace_members_alphabetical_story8.py` |
| 2 | V-NF-2 | pyproject version 0.0.8-alpha on 3 new Python pkgs + 1 new TS pkg | gate-runner grep |
| 3 | V-NF-3 | per-package dependencies explicit | gate-runner verify |
| 4 | V-NF-4 | AISALESHT `backend/src/modules/campaigns/` byte-stable (cardinal V-NF-4) | `test_aisalesht_campaigns_untouched_story8.py` |
| 5 | V-NF-5/6/7 | no publishConfig / .releaserc / release.yml | gate-runner grep |
| 6 | V-AG-3-story-6 | Story 6 5 copilot registries golden snapshot continues GREEN | Story 6 arch fitness re-run |
| 7 | V-AG-3-story-7 | Story 7 sales-agent ToolRegistry golden snapshot continues GREEN | Story 7 arch fitness re-run |
| 8 | V-AG-new-story-8 | EP-3 + EP-4 adapters expose ONLY public read methods (no private dispatch / mutation access) | `test_ep3_ep4_wrappers_read_only.py` (AST parse) |
| 9 | V-F-sdk-5 | BrandContext frozen dataclass with 9 fields per §7.5.2 D3 | `test_brand_context.py` |
| 10 | V-AG-namespace-allowlist | CC-4 namespace — 5 brand_slugs allowlist (nicolify/vitalia/comunify/lupulo/test-brand) | `test_brand_slug_namespace_allowlist.py` |
| 11 | V-AG-cc3-closed | CC-3 startup-only — registry.close() locks; subsequent register raises RegistrationClosedError | `test_cross_cutting_policies.py::test_C3_registration_closed` |
| 12 | V-AG-cc5-no-unregister | CC-5 inmutable — registry exposes NO `unregister_*` method (AttributeError on lookup) | `test_no_unregister_api.py` |
| 13 | V-AG-no-ep19 | NO EP-19 `vertical_agent_register` method in ExtensionPointRegistry (§7.5.4) | `test_no_ep19_method_in_registry.py` |

Plus 2 cement validators:

- V-F-docs-1 — `docs/extension-points.md` ships with §1-§5 + recipe + per-vertical examples (Vitalia + Comunify + Lupulo) per §7.5.2 D5=B + §7.5.4 NO EP-19 literal string
- V-F-test-brand-1 — apps/test-brand smoke pack tests 10 scenarios GREEN (lifespan 18 registrations + EP-1..EP-5 executable + EP-6..EP-18 NotImplementedError + CC-1..CC-5 enforcement)

## §4. Cross-cutting concerns

### §4.1 Tenant isolation

BrandContext.tenant_id + BrandContext.tenant_profile_id are MANDATORY frozen fields. Every EP handler signature accepts BrandContext — tenant routing enforced at registry dispatch level.

CC-4 namespace = brand isolation (vitalia.medical_consent_request CANNOT collide with lupulo.medical_consent_request; both register independently — cross-brand learning happens via /pm core promotion path per §7.5.6, NEVER cross-namespace consumption).

### §4.2 Currency + master data

N/A this story — Story 8 is contract surface (SDK) + campaigns lift (mechanical). Campaigns module preserves existing AISALESHT currency handling (no changes per V-NF-4).

### §4.3 PII sanitization

BrandContext fields are NOT PII (IDs + slugs + flag maps + locale strings). Safe to log. V-F-test-brand-1 includes `test_json_serializable_no_pii` scenario.

No `response_model=` updates needed — Story 8 ships zero new FastAPI routes (campaigns routes lift verbatim; SDK exposes Python API only; test-brand FastAPI app exposes nothing public).

### §4.4 Spanish neutro LatAm

Applies to `docs/extension-points.md` user-facing strings + commit messages + code comments visible in API responses. Pre-commit voseo hook applies.

Sales agent OUTPUT exception (per `.claude/rules/spanish-text.md`) N/A this story — no sales-agent runtime changes.

### §4.5 PII / response_model

N/A — Story 8 introduces no new FastAPI routes.

### §4.6 Native-first

Per `AGENTS.md`. Builders MUST run tests + lint native (`uv run pytest` + `uv run ruff`), NEVER docker exec. Per Story 7 precedent.

## §5. R3 downstream regression scope (auditor verification)

Per `.claude/rules/auditor-downstream-regression.md` SSoT table. Auditor T-17 + T-18 verification scope:

**Backend per-package pytest scope (gate-runner — Haiku invocation):**
- ALL Stories 1-7 packages (23 packages) per-package pytest GREEN — verify no regressions from workspace pyproject.toml append
- Story 8 NEW packages per-package pytest GREEN:
  - `cd ~/luana-platform && uv run pytest core/luana-core-campaigns/tests/ -x -q --tb=short`
  - `cd ~/luana-platform && uv run pytest core/luana-core-extension-sdk/tests/ -x -q --tb=short`
  - `cd ~/luana-platform && uv run pytest apps/test-brand/tests/ -x -q --tb=short`
- Aggregate workspace pytest (with same waiver pattern as Story 7 V-F-x-2 conftest collision):
  - `cd ~/luana-platform && uv run pytest core/ apps/ -x -q --tb=short --ignore=core/src --ignore=core/luana-core-copilot/tests/test_streaming_integration.py --ignore=core/luana-core-sales-agent/tests/eval_simulator/ --ignore=core/luana-core-sales-agent/tests/agentic_evals/`

**Stories 6 + 7 frozen registry golden snapshot re-run (V-AG-3 cement):**
- `cd ~/luana-platform && uv run pytest core/tests/architecture/test_story6_registries_byte_stable.py -x -q` (Story 6 V-AG-3)
- `cd ~/luana-platform && uv run pytest core/tests/architecture/test_story7_*.py -x -q` (Story 7 V-AG-1..V-AG-8)

Per R3 SSoT table append (T-18): add Story 8 surface rows per 03-arch-be.md §8.

## §6. Halt criteria (escalate Chris)

Per checkpoint frontmatter `halt_criteria_session_4` + 01-spec §12 risks:

1. Scope expansion needed (campaigns module refactor — outcome §7.3 violated)
2. EP signature decision surfaces during build NOT covered by outcome §7.5 (architect spec gap)
3. Auditor REJECTED + 3 auto-fix Opus iter all fail
4. Cumulative session 4 cost crosses $2500 → soft check-in (per outcome §7.2)
5. Builder cap_reached 10 iter on same ticket
6. AISALESHT touched by accident (V-NF-4 violated)
7. Stories 6+7 frozen registries breakage detected (EP-3/EP-4 wrappers no preserve contract byte-stable; V-AG-3 golden snapshots break)
8. EP-3 + EP-4 adapter wiring discovers Story 6+7 ToolRegistry/WorkflowRegistry lack `register_*_from_extension` public methods → per 03-arch-be.md §1.4 — adapters raise `NotImplementedError` gracefully; test-brand smoke pack injects None for both adapters (does NOT propagate registration to Story 6/7 registries — test-brand only validates SDK contract). Stories 11-13 brand bootstraps wire real adapters when they wire real registries. **NOT a halt — design intentional.**

## §7. Open questions resolved (architect-bounded — Chris escalate only if surfaces during build)

| OQ | Resolution |
|---|---|
| OQ-1 Workspace member count | **26 Python + 7 TS post-Story-8** (Story 7 baseline 23 + 3 new Python: luana-core-campaigns, luana-core-extension-sdk, apps/test-brand. TS: existing 6 at core/@luana/* + 1 new @luana/extension-sdk = 7). V-NF-1 uses exact count 26. |
| OQ-2 Scheduling lift in Story 8 | **NOT in scope** per 01-spec §4 + Story 7 §9.2 deferred-import pattern preserved. AppointmentModel + ProductModel stubs RE-ALLOWLIST with reason "deferred to scheduling lift (post-Story-8)". |
| OQ-3 EP-3 + EP-4 dispatch API | **Read-only adapter pattern** via `_SalesAgentToolRegistryAdapter` + `_CopilotWorkflowRegistryAdapter` internal classes (03-arch-be.md §1.4). Adapters call `register_*_from_extension` public method IF available on inner registry; else raise NotImplementedError gracefully. Stories 11-13 brand bootstraps wire real adapters. Story 8 test-brand injects None. |
| OQ-4 BrandContext feature_flags source | **OPAQUE dict[str, bool] — Story 8 does NOT prescribe source**. Brand apps inject FF map at request boundary via `get_brand_context(request) -> BrandContext` FastAPI dependency. Per-brand choice (Vitalia LaunchDarkly vs Comunify core/config flags vs Lupulo Redis flags — Stories 11-13 decide). Story 8 ships only the contract field. |
| OQ-5 TS mirror automation | **HAND-MAINTAINED for v0.0.8-alpha**. 3 TS interfaces only (EP-6 SidebarRouteDef + EP-10 LandingTemplateDef + EP-18 WizardStepDef). Codegen deferred Story 9+ if drift surfaces. V-F-ts-1 arch test enforces parity via AST parse of TS file vs Python `dataclasses.fields()`. |

## §8. Test surfaces (TDD-mandatory)

### §8.1 Tests RED-first per layer (TDD R1 mandatory)

- **Domain (SDK):** test_brand_context.py + test_models.py + test_exceptions.py — RED first per TDD (T-3, T-4 emit failing tests before implementation)
- **Infrastructure (SDK):** test_registry_surface.py + test_cross_cutting_policies.py — RED first (T-5 emits failing CC enforcement tests before extension_points.py logic)
- **Application (SDK + adapters):** test_ep1_through_ep5.py + test_ep6_through_ep18_signature_only.py + test_adapters_read_only.py — RED first (T-5 + T-6 + T-7)
- **Integration (test-brand smoke pack):** test_sdk_smoke.py — 10 scenarios (D1-D3 + C1-C5 + frozen) RED first (T-15 emits before T-14 implementation)
- **Campaigns lift:** 42 test files lift VERBATIM from AISALESHT — RED status preserved from AISALESHT baseline (no test rewrites)
- **Architecture fitness (12 NEW tests Story 8):** test_workspace_members_alphabetical_story8 + test_aisalesht_campaigns_untouched_story8 + test_no_publish_config_story8 + test_registry_surface + test_ep1_through_ep5 + test_ep6_through_ep18_signature_only + test_cross_cutting_policies + test_brand_context + test_ep3_ep4_wrappers_read_only + test_ts_types_mirror_python_dataclasses + test_docs_extension_points_completeness + test_no_ep19_method_in_registry + test_brand_slug_namespace_allowlist + test_no_unregister_api — RED first (T-17 emits before final integration)

## §9. Pyproject + workspace integration

See 03-arch-be.md §3.5, §3.6, §3.7, §3.8 for full pyproject.toml + package.json templates.

Workspace registration (T-1):
- Append 3 Python members alphabetical-ordered to `[tool.uv.workspace] members`
- Append 3 entries alphabetical to `[tool.uv.sources]`
- Apps directory: `apps/test-brand` — NEW workspace path. `members` array adds `apps/test-brand` after `core/luana-core-*` block.

pnpm-workspace.yaml already contains `core/@luana/*` glob — `@luana/extension-sdk` picks up automatically.

## §10. Migration notes

No DB migrations Story 8. Campaigns module lifts ALL existing models + repositories + migrations verbatim. AISALESHT Alembic migrations stay in AISALESHT (no migration changes to luana-platform per Story 7 precedent — migrations live in nicolify Story 10 territory).

Per `.claude/rules/backend-migrations.md` — Story 8 introduces zero new migrations. Existing campaigns tables in AISALESHT Postgres continue working unchanged.

## §11. File structure recap

See 03-arch-be.md §3.1, §3.2, §3.3, §3.4 for complete per-package file structures.

**NEW files Story 8 (total ~150 files):**
- luana-core-extension-sdk: 6 src files + 8 test files = 14 NEW files
- luana-core-campaigns: 80 src files + 42 test files = 122 LIFTED files (verbatim from AISALESHT)
- apps/test-brand: 3 src files + 1 test file = 4 NEW files
- core/@luana/extension-sdk: 4 src files + package.json + tsconfig.json = 6 NEW files
- core/tests/architecture/test_story8_*.py = 12 NEW arch fitness tests
- core/tests/architecture/_snapshots/story8_*.json = 1 NEW snapshot file (if any sha256-based)
- docs/extension-points.md = 1 NEW file

**MODIFIED files Story 8 (total 3 files):**
- luana-platform/pyproject.toml (T-1 — append 3 workspace members + 3 sources entries)
- luana-platform/core/DEFERRED-FILES.md (T-18 — append Story 8 deferrals + adapter wiring deferral)
- `.claude/rules/anti-duplication.md` (T-18 — append Extension SDK row + R3 SSoT table append in `.claude/rules/auditor-downstream-regression.md`)

## §12. Architecture fitness impact

Per 03-arch-be.md §7 — 12 NEW arch fitness tests Story 8. Pre-existing arch fitness tests Stories 1-7 continue GREEN (V-AG-3 Story 6 + Story 7 cardinal preserved).

Allowlist shrinkage: AppointmentModel + ProductModel stubs RE-ALLOWLIST with explicit reason. Per allowlist-shrink-only principle, allowlist NOT expanded — same allowlist with reason updated to "deferred to scheduling lift (post-Story-8)".

## §13. Capability YAML updates required (post-merge — `/pm` skill responsibility)

Per `docs/process/pm-redesign-2026-05.md` § Capability promotion at merge:
- **NEW capability:** `luana-core-campaigns` v0.0.8-alpha (lifted from AISALESHT capability "Campaigns engine") — promote at merge
- **NEW capability:** `luana-core-extension-sdk` v0.0.8-alpha (NEW) — promote at merge
- **NEW capability:** `@luana/extension-sdk` v0.0.8-alpha (NEW TS surface) — promote at merge
- Total outcome capabilities cumulative POST Story 8: **34 + 3 = 37 capabilities**

`/pm` post-merge runs `scripts/reconcile_capabilities.py` + `scripts/generate_backlog.py`.

## §14. Test surfaces summary

Per 03-arch-be.md §6 + spec §11:

| Category | Test surfaces | Count |
|---|---|---|
| Non-functional (V-NF-*) | workspace + version + AISALESHT untouched + no publish | 5 validators |
| Functional campaigns (V-F-campaigns-*) | per-package pytest + import paths migrated | 2 validators |
| Functional SDK (V-F-sdk-*) | 18 EP methods + EP-1..EP-5 executable + EP-6..EP-18 NotImplementedError + CC-1..CC-5 + BrandContext frozen | 5 validators |
| Functional TS (V-F-ts-*) | 3 TS types mirror Python | 1 validator |
| Functional test-brand (V-F-test-brand-*) | 10 smoke scenarios | 1 validator |
| Functional docs (V-F-docs-*) | extension-points.md §1-§5 + recipe + per-vertical examples | 1 validator |
| Agentic frozen (V-AG-3-story-6, V-AG-3-story-7) | Story 6 + Story 7 golden snapshots continue GREEN | 2 validators |
| Agentic new Story 8 (V-AG-new-story-8) | EP-3 + EP-4 adapters read-only | 1 validator |
| Downstream regression (V-D-*) | Stories 1-7 packages pytest + Story 6+7 frozen + AISALESHT BE/FE | 3 validators |

**Total validators: 21** (per spec §11 preview).

## §15. Research Notes (DATE-AWARE — captured 2026-05-12 via WebSearch)

### Python frozen dataclass + SDK registry pattern (2026 canonical)

- **Source:** https://docs.python.org/3/library/dataclasses.html — accessed 2026-05-12
- **Source:** https://www.pyblog.in/programming/python-dataclasses-the-complete-2026-guide-from-dataclass-to-slots-frozen-and-__post_init__/ — accessed 2026-05-12
- **Source:** https://rednafi.com/python/statically-enforcing-frozen-dataclasses/ — accessed 2026-05-12

**Key takeaways:**
1. **2026 canonical pattern** for SDK contract DataClasses: `@dataclass(frozen=True, slots=True, kw_only=True)`.
   - `frozen=True` — immutability enforcement (raises `FrozenInstanceError` on mutation attempt).
   - `slots=True` — memory efficiency + faster attribute access. **Compatible with frozen since Python 3.10+.**
   - `kw_only=True` — keyword-only construction. Explicit + self-documenting. Survives field reordering.
2. **Performance consideration:** Frozen dataclasses ~2.4× slower instantiation vs non-frozen (special `__setattr__` + `__delattr__` generation). For SDK contract types (BrandContext, 18 DataClass models) — instantiation happens at startup ~18 times. ZERO hot-path impact. Acceptable trade-off for immutability + thread-safety + hashability.
3. **Registry pattern with frozen DataClasses + ClassVar:** Use `typing.ClassVar` for class-level data not field-tracked (e.g., a `_registry: ClassVar[dict] = {}`). Story 8 doesn't use ClassVar — instance attribute pattern in ExtensionPointRegistry preferred (multiple registries can coexist for testing).
4. **Knowledge cutoff disclosure:** Opus 4.7 cutoff = January 2026. Python 3.13 + 3.14 features (improved `copy.replace`, enhanced slots support) post-cutoff. Researched live on 2026-05-12. Architect confirms `slots=True` + `frozen=True` combination is canonical 2026 pattern; Python 3.12+ supports both natively without complications.

### LangGraph + Anthropic prompt caching (irrelevant Story 8 — listed for completeness)

Story 8 does NOT touch LangGraph orchestrator code or Anthropic prompt caching slot architecture (preserved verbatim from Stories 6+7). EP-4 + EP-13 + EP-14 wrappers are signature-only — semantic dispatch NotImplementedError v0.1.0. No new patterns introduced.

### Native-first dev

Per `AGENTS.md` Section "Native-First (mandatory)" — accessed via project root 2026-05-12.
Builders MUST run lint + tests native (uv venv on luana-platform side, `.venv/bin/{ruff,pytest}` on AISALESHT side). NEVER docker exec.

## §16. Open Questions for PM

None — all 5 OQ-1..OQ-5 from spec §13 resolved in architect-bounded scope (see §7 + 03-arch-be.md frontmatter `deviations_from_spec`).

If during build a NEW design decision surfaces NOT covered by outcome §7.5 → halt criterion #2 triggers, /dev-team escalates Chris.

## §17. Next steps post-architect

1. `/pm` ratifies ready package via state transition `refined → ready`
2. `/dev-team` Session 4 autonomous build per outcome §7.2 + §7.4 cap extended to 3 stories Tier 3 sequential
3. `/auditor` Session 4 post-developed → CHECKPOINTS C1-C5
4. `/pm` merge → 3 capabilities promoted (luana-core-campaigns + luana-core-extension-sdk + @luana/extension-sdk) → Story 9 unblocked

