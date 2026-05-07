# 05-guidelines.md — Growth Studio Folder Parity

> Owner: `/architect`. Patterns required + forbidden + files in scope para `/dev-team` autonomous build.

## Patterns required

### FSD-Lite homologation
- **Folders canonical** post-refactor: `pages/` + `actions/` + `schemas/` + `api/` + `components/` + `hooks/` + `lib/` + `types/` + `utils/` + opcional `__tests__/` + `store/`.
- **Factory propia adapter mode** — growth tiene shape distinto a brand/offer (`stage-slugs.ts` + `StageDispatcher.tsx` + `channel-slugs.ts` + `ChannelDispatcher.tsx` + `pages/tiers/{0..3}-*.ts` en lugar de `section-slugs.ts` + `SectionDispatcher.tsx`).
- **Routes Server Component delgados** delegate to dispatchers. Pattern brand/offer.
- **Registries SSoT** en `lib/registries/{stage,channel,dashboard}-registry.ts` — cero hardcoded slugs en code path.

### Channel slugs canonical
- Spec v1 friendly names ERROR; canonical confirmed via grep:
  - `meta-ads` ✓
  - `yt-organic` (NOT `youtube-organic` — folder name)
  - `email-nurture` (NOT `mail`)
  - `ig-organic` ✓
  - `website-total` (NOT `website`)
- Use canonical en code + tests + docs.

### Stage slugs canonical (5)
- `atraccion-captura`
- `nutricion-oportunidad`
- `ventas`
- `adopcion`
- `expansion-evangelizacion`

### TDD obligatorio
- Arch tests RED antes refactor.
- Vitest unit RED antes implementación.
- Playwright smoke RED antes routes migration.

### Migration patterns (per spec ratification log)
- **Q1 store:** zustand local `growth-studio/store/sync-store.ts` (NEW). Coexiste con copilot-store + shell-mutex-store (story 1) — zero overlap.
- **Q2 VR replace:** delete `__tests__/visual-regression-drawer-bowtie.test.tsx`, replace con story 1 VR pattern (Playwright + masking, lift cross-studio). DEPENDS story 1 T-8 helpers shared.
- **Q3 routes thin:** Server Component delgado `app/(main)/[tenantId]/(dashboard)/growth-studio/[stage]/page.tsx` import `StageDispatcher` from `pages/`.
- **Q4 config migration:** **grep first** all consumers `import.*config/` → list → atomic find-replace en mismo commit cubierto por arch test.
- **Q5 4-tier rename break-and-fix atomic:** mismo commit move `tier0-*.ts` to `pages/tiers/0-summary.ts`; tiers 1-3 use WRAPPER re-exports for 1 ciclo deprecation, then remove.

## Patterns forbidden

- ❌ Hardcoded stage slugs en code path fuera `lib/registries/stage-registry.ts` (arch test bloquea).
- ❌ Hardcoded channel slugs fuera `lib/registries/channel-registry.ts` (arch test bloquea).
- ❌ Hardcoded "5 stages" array literal fuera registry.
- ❌ React Context para state que pertenece a feature-local — usar zustand store (Q1).
- ❌ `useState` en routes/page.tsx — Server Component prefer.
- ❌ Cross-feature import outside FSD-Lite matrix.
- ❌ Modificar `components/strategy-canvas/**` (bowtie superior, invariante negocio).
- ❌ Modificar `components/metrics-dashboard/**` internals (panel métricas, invariante).
- ❌ Lift 4-tier loading a `shared/` (sin segundo consumer — solo growth lo usa).
- ❌ `// eslint-disable` sin justification.
- ❌ `any` TypeScript.
- ❌ Modificar `frontend/src/__tests__/architecture/test-growth-studio-copilot-offset.test.ts` directamente — story 1 owns rename. 2A trabaja con renamed path post story 1 T-7 lands.
- ❌ Voseo en strings (zero new strings esperado, pero glosario aplica).
- ❌ Default exports excepto Next.js page components.
- ❌ Crear nuevo `*_METADATA` map en FE (per `.claude/rules/offer-catalogs.md` análogo — registries SSoT only).

## Files in scope (`/dev-team` edits ONLY these)

### NEW
- `frontend/src/features/growth-studio/pages/stage-slugs.ts`
- `frontend/src/features/growth-studio/pages/StageDispatcher.tsx`
- `frontend/src/features/growth-studio/pages/channel-slugs.ts`
- `frontend/src/features/growth-studio/pages/ChannelDispatcher.tsx`
- `frontend/src/features/growth-studio/pages/sections/atraccion-captura-page.tsx`
- `frontend/src/features/growth-studio/pages/sections/nutricion-oportunidad-page.tsx`
- `frontend/src/features/growth-studio/pages/sections/ventas-page.tsx`
- `frontend/src/features/growth-studio/pages/sections/adopcion-page.tsx`
- `frontend/src/features/growth-studio/pages/sections/expansion-evangelizacion-page.tsx`
- `frontend/src/features/growth-studio/pages/tiers/0-summary.ts` (MOVED from existing tier0-*)
- `frontend/src/features/growth-studio/pages/tiers/1-overview.ts` (WRAPPER re-export, deprecation 1 ciclo)
- `frontend/src/features/growth-studio/pages/tiers/2-group-detail.ts` (WRAPPER)
- `frontend/src/features/growth-studio/pages/tiers/3-stage.ts` (WRAPPER)
- `frontend/src/features/growth-studio/lib/registries/stage-registry.ts`
- `frontend/src/features/growth-studio/lib/registries/channel-registry.ts`
- `frontend/src/features/growth-studio/lib/registries/dashboard-registry.ts`
- `frontend/src/features/growth-studio/store/sync-store.ts`
- `frontend/src/features/growth-studio/actions/.gitkeep` (placeholder 2B)
- `frontend/src/features/growth-studio/schemas/.gitkeep` (placeholder 2B)
- `frontend/src/__tests__/architecture/test-no-hardcoded-stage-list.test.ts`
- `frontend/src/__tests__/architecture/test-no-hardcoded-channel-slugs.test.ts`
- `frontend/src/features/growth-studio/__tests__/folder-parity-canonical-files.test.ts`
- `frontend/src/features/growth-studio/__tests__/StageDispatcher.test.tsx`
- `frontend/src/features/growth-studio/__tests__/ChannelDispatcher.test.tsx`
- `frontend/src/features/growth-studio/__tests__/__mocks__/*` (MOVED from `growth-studio/__mocks__/`)
- `frontend/e2e/specs/smoke/growth-studio-stages.spec.ts`
- `frontend/e2e/visual/growth-studio-bowtie.spec.ts` (DEPENDS story 1 T-8 helpers)
- `frontend/e2e/visual/growth-studio-responsive.spec.ts`

### MODIFIED
- `frontend/src/__tests__/architecture/test-studio-structure-parity.test.ts` (adapter mode — STUDIO_PAGE_DIRS per-studio canonical config, factory propia OK para growth)
- `frontend/src/app/(main)/[tenantId]/(dashboard)/growth-studio/page.tsx` (Server Component delegate StageDispatcher)
- `frontend/src/app/(main)/[tenantId]/(dashboard)/growth-studio/[stage]/page.tsx` (Server delegate)
- `frontend/src/__tests__/architecture/test-shell-copilot-offset.test.ts` (drain `KNOWN_VIOLATIONS_GROWTH = new Set()` — DEPENDS story 1 T-7 rename)
- 6 dashboards `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/{youtube-organic,mail,meta-ads,ig-organic,website}/{Channel}Dashboard.tsx` + `ChannelConnectionModal.tsx` — adopt `useCopilotOffset` hook (offset compensation fixed/portal elements)
- `frontend/src/features/growth-studio/components/metrics-dashboard/api/stage-detail-api.ts` (9 dynamic-import consumers update path `__mocks__` → `__tests__/__mocks__`)
- Multiple growth-studio components — update imports `config/` → `lib/registries/` (atomic find-replace)
- Multiple growth-studio components — update imports `context/` → `store/` o `hooks/`

### DELETED
- `frontend/src/features/growth-studio/config/` (entire folder)
- `frontend/src/features/growth-studio/context/` (entire folder)
- `frontend/src/features/growth-studio/__mocks__/` (entire folder)
- `frontend/src/features/growth-studio/__tests__/visual-regression-drawer-bowtie.test.tsx` (replaced by Playwright VR — DEPENDS story 1 T-8)

### RENAMED
- `frontend/src/features/growth-studio/__mocks__/*` → `frontend/src/features/growth-studio/__tests__/__mocks__/*` (per Q ratified)

## Files NEVER touches (escalate to Chris)

- `frontend/src/components/shared/layout/**` (story 1 territory)
- `frontend/src/features/copilot/**` (story 1 + 2B territory)
- `frontend/src/__tests__/architecture/test-growth-studio-copilot-offset.test.ts` (story 1 owns rename — wait for it)
- `frontend/src/features/growth-studio/components/strategy-canvas/**` (bowtie invariante)
- `frontend/src/features/growth-studio/components/metrics-dashboard/components/**` internals (invariante visual — only adopt useCopilotOffset wrapper)
- `backend/src/**` (story FE only)
- `.claude/**`

## Reference docs (load before coding)

### Skills
- `frontend-expert` (FSD-Lite, refactor patterns)
- `metrics-expert` (4-tier loading conventions, channel registry)
- `playwright-expert` (E2E smoke + visual regression con masking)

### Rules
- `.claude/rules/frontend-fsd.md`
- `.claude/rules/frontend-quality.md`
- `.claude/rules/architectural-fitness.md`
- `.claude/rules/anti-duplication.md` (Step 0 grep — registries SSoT)
- `.claude/rules/offer-catalogs.md` (análogo SSoT pattern; growth aplicable)
- `.claude/rules/spanish-text.md`
- `.claude/rules/tdd-mandatory.md`

### Tessl skills
- `tessl__react-patterns`
- `tessl__nextjs-app-router-modularization` (Server+Client split)
- `tessl__vitest`

### Story artifacts
- `01-spec.md` v2
- `03-arch.md` consolidated
- `03-arch-fe.md` full FE design
- `../app-shell-sidebar-copilot-decoupling/03-arch.md` (coordination story 1)

## Migration phases reminder

Phase 1: Registries SSoT
Phase 2: Factory dispatchers
Phase 3: 4-tier rename atomic
Phase 4: Legacy purge + VR replacement (DEPENDS story 1 T-8)
Phase 5: Allowlist cleanup 6 dashboards (DEPENDS story 1 T-7 rename)
Phase 6: Arch fitness extension adapter mode + 2 NEW arch tests
Phase 7: Placeholders 2B
Phase 8: Verify

Cada phase commit-able individually. CI green at every boundary.

## Coordination con story 1 (CRITICAL sequencing)

| Story 1 ticket | Story 2A phase blocked | Resolution |
|---|---|---|
| T-7 (rename arch test + scope-keyed allowlists) | Fase 5 (allowlist drain) | Story 2A Fase 5 waits for story 1 T-7 merged. Story 2A Fase 1-4 + 6-8 parallel-safe. |
| T-8 (visual regression baselines + helpers) | Fase 4 (VR replacement) | Si T-8 no merged: 2A Fase 4 keeps legacy VR test. Defer replacement hasta T-8 lands. |

Orchestrator merge sequencing: prioridad story 1 T-7 + T-8 before 2A Fase 5+4 respective.
