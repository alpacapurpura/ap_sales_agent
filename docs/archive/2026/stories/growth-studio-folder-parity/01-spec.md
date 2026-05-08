# 01-spec.md — Growth Studio Folder Parity (2A)

> Owner: `/po`. Spec ejecutable Gherkin AI-resistant. Scope = refactor estructural FE puro (folders + factory dispatchers + legacy purge + arch fitness extension + allowlist cleanup). NO incluye real actions/schemas (eso es 2B).

---
story_id: growth-studio-folder-parity
type: service-story
module: analytics
capability: growth-studio-architecture
po_version: 2
last_modified: 2026-05-07T04:10:00Z
ratified_by_chris: true
links:
  outcome: "../../outcomes/growth-copilot-layout-unification.md"
  story_2b: "../growth-studio-actions-schemas-real/checkpoint.md"
  legacy_pi: "../../../archive/2026/legacy-pis/PI-9-growth-studio-architecture/PI.md"
  arch_test_parity: "../../../../frontend/src/__tests__/architecture/test-studio-structure-parity.test.ts"
  arch_test_offset: "../../../../frontend/src/__tests__/architecture/test-growth-studio-copilot-offset.test.ts"
---

## Resumen ejecutivo

Migrar `frontend/src/features/growth-studio/` a la estructura FSD-Lite homologada con Brand/Offer (canonical files + factory propia adaptada a 5 stages × N canales × 4-tier loading). Purgar `config/` + `context/` + `__mocks__/` legacy. Limpiar allowlist `test-growth-studio-copilot-offset` (6 dashboards adoptan `useCopilotOffset`). Arch fitness `test-studio-structure-parity` extendido modo adapter para que growth deje de estar excluido. Bowtie + métricas dashboard intactos pixel-perfect.

**Outcome user-facing:** zero (refactor estructural — usuario NO percibe cambio). Beneficio interno: arquitectura escalable + agregar canales sin refactor cada vez (próxima fase 2B + futuras).

## Acceptance Criteria (Gherkin AI-resistant)

### Scenario 1 — `folder-parity-canonical-files-exist` (`type: happy`)

**Given:**
- Pre-refactor: `frontend/src/features/growth-studio/` carece de `pages/`, `actions/`, `schemas/`.
- Brand/offer-studio tienen los 9 folders canonical FSD-Lite.

**When:**
- Refactor 2A se aplica.

**Then:**
- `growth-studio/pages/` existe y contiene canonical files factory propia:
  - `stage-slugs.ts` (5 entries: `atraccion-captura`, `nutricion-oportunidad`, `ventas`, `adopcion`, `expansion-evangelizacion`)
  - `StageDispatcher.tsx` (router stage → component)
  - `channel-slugs.ts` (N entries iniciales — canonical slugs verified vs source: `meta-ads`, `yt-organic`, `email-nurture`, `ig-organic`, `website-total`. Architect-fe ratified canonical post grep 2026-05-07; spec wording v1 friendly-names corregido a canonical.)
  - `ChannelDispatcher.tsx` (router channel → dashboard)
  - `pages/sections/` directorio con N archivos `*-page.tsx` (uno por stage mínimo)
  - `pages/tiers/` directorio con `tier0-summary.ts`, `tier1-overview.ts`, `tier2-group-detail.ts`, `tier3-stage.ts`
- `growth-studio/actions/` existe con `.gitkeep` (placeholder 2B).
- `growth-studio/schemas/` existe con `.gitkeep` (placeholder 2B).
- Folders legacy NO existen: `config/`, `context/`, `__mocks__/`.
- Bundle `growth-studio` tiene EXACTLY los 9 folders canonical: `actions/`, `api/`, `components/`, `hooks/`, `lib/`, `pages/`, `schemas/`, `types/`, `utils/` + opcionalmente `__tests__/` + `store/`.

**Graders:**
- `{ type: contract_test, path: "frontend/src/__tests__/architecture/test-studio-structure-parity.test.ts" }` — debe extender STUDIO_PAGE_DIRS para incluir `growth: pages/` con canonical_files set adapted (factory mode permite `stage-slugs.ts` + `StageDispatcher.tsx` además de `section-slugs.ts` + `SectionDispatcher.tsx`).
- `{ type: contract_test, path: "frontend/src/__tests__/architecture/test-feature-structure.test.ts" }` — verify growth-studio top-level folders set canonical.
- `{ type: state_check, target: filesystem, query: "ls frontend/src/features/growth-studio/{pages,actions,schemas}" }` — todos exist.
- `{ type: state_check, target: filesystem, query: "test ! -d frontend/src/features/growth-studio/{config,context,__mocks__}" }` — todos NO exist.

---

### Scenario 2 — `arch-fitness-rejects-hardcoded-channel` (`type: negative`)

**Given:**
- Refactor 2A done. Stage/Channel/Dashboard registries SSoT viven en `growth-studio/lib/registries/`.
- Dev intenta agregar canal nuevo "test-channel-x" hardcodeando case en `ChannelDispatcher.tsx` (sin agregarlo al registry).

**When:**
- Vitest run con `cd frontend && npx vitest run src/__tests__/architecture/`.

**Then:**
- Test `test-studio-structure-parity` o test específico nuevo (e.g. `test-growth-channel-from-registry.test.ts`) FAILS.
- Error message indica: "ChannelDispatcher must consume `channelRegistry` from `lib/registries/channel-registry.ts` — no hardcoded channel slugs allowed."
- Build CI bloquea.

**Graders:**
- `{ type: contract_test, path: "frontend/src/__tests__/architecture/test-growth-channel-from-registry.test.ts" }` — verifica `ChannelDispatcher.tsx` source NO contiene hardcoded slugs (regex match channel-slugs imported from registry only).
- `{ type: state_check, target: ratchet, expect: "no new violations introduced" }`.

---

### Scenario 3 — `bowtie-and-dashboard-pixel-perfect-post-refactor` (`type: edge`)

**Given:**
- Pre-refactor screenshots `components/strategy-canvas/*` (bowtie superior) + `components/metrics-dashboard/*` (panel métricas) en 5 stages × 3 viewports (375/1024/1440).
- Refactor 2A toca folders, NO toca `components/strategy-canvas/*` ni `components/metrics-dashboard/*` internals.

**When:**
- Vitest visual regression suite + Playwright smoke run post-refactor.

**Then:**
- Diff pixel-perfect (≤0.1% pixel diff threshold) entre pre-refactor y post-refactor screenshots.
- Bowtie funcional intact: 5 stages renderizan, transiciones drawer-bowtie OK.
- 4-tier loading hooks renamed bajo `pages/tiers/{0,1,2,3}-*.ts` consumidos por dashboards igual que pre-refactor (zero behavior change).

**Graders:**
- `{ type: contract_test, path: "frontend/src/features/growth-studio/__tests__/visual-regression-drawer-bowtie.test.tsx" }` — existing test pasa post-refactor.
- `{ type: integration, path: "frontend/e2e/specs/smoke/growth-studio-bowtie.spec.ts" }` — Playwright smoke 5 stages render OK.
- `{ type: state_check, target: imports, query: "grep -l 'from .*tiers/' frontend/src/features/growth-studio/components/" }` — consumers tier hooks updated path imports.

---

### Scenario 4 — `ratchet-allowlist-shrinks-and-fsd-isolation-respected` (`type: adversarial`)

**Given:**
- Pre-refactor: `test-growth-studio-copilot-offset.test.ts` allowlist tiene 6 entries (5 sidebar dashboards + 1 ChannelConnectionModal).
- Pre-refactor: `growth-studio/` puede importar de otros features (FSD violation cross-feature) — comportamiento legacy.
- Adversarial dev intenta:
  1. Agregar nueva entry al allowlist en lugar de adoptar `useCopilotOffset` en un dashboard nuevo.
  2. Importar componente desde `frontend/src/features/copilot/` directo en `growth-studio/` (cross-feature import).
  3. Hardcodear "5 stages" en code path fuera del registry SSoT.

**When:**
- Build CI run + arch fitness suite.

**Then:**
- Adversarial 1: arch test ratchet detecta nuevo violation NO whitelisted → FAIL build con mensaje "allowlist shrinks only — fix the violation, do NOT add to allowlist."
- Adversarial 2: ESLint `boundaries/dependencies` rule fails con mensaje "growth-studio cannot import from copilot — use shared port if cross-module needed."
- Adversarial 3: arch test `test-no-hardcoded-stage-list.test.ts` (NEW) detecta string literal "5 stages" o array hardcoded fuera de `lib/registries/stage-registry.ts` → FAIL.
- Allowlist post-2A: tamaño 0 (6 dashboards adoptaron hook).

**Graders:**
- `{ type: contract_test, path: "frontend/src/__tests__/architecture/test-growth-studio-copilot-offset.test.ts" }` — KNOWN_VIOLATIONS set vacío (`new Set()`).
- `{ type: contract_test, path: "frontend/src/__tests__/architecture/test-no-hardcoded-stage-list.test.ts" }` — NEW arch test, growth-studio source files NO contienen array de 5 stage slugs hardcoded.
- `{ type: state_check, target: eslint, query: "npx eslint src/features/growth-studio/ --no-eslintrc --config tools/strict-fsd.config.js" }` — 0 boundaries violations.
- `{ type: state_check, target: tsc, query: "npx tsc --noEmit" }` — 0 errors.

---

## Non-functional requirements

| Categoría | Requisito | Verificador |
|---|---|---|
| Performance | Build time `growth-studio` chunk no aumenta >10% | Next.js bundle analyzer pre/post |
| Mobile | Refactor NO afecta responsive (375/640/1024/1440) | Playwright resize test |
| Accesibilidad | WCAG AA preserved en bowtie + dashboard | axe-core (sin regresión vs pre-refactor baseline) |
| i18n | Spanish neutro en cualquier user-facing string nuevo (esperado: 0 strings nuevos) | Lint regex |
| Tenant isolation | Refactor NO toca queries — preservado por consumir lib/api/ existente | sin cambios en wire format |
| Tests coverage | growth-studio coverage NO baja vs baseline (~25%) | vitest coverage report comparison |
| Bundle size | growth-studio chunk size NO aumenta >5% | next/bundle-analyzer report |

## Constraints técnicos heredados

- `.claude/rules/frontend-fsd.md` — boundary matrix respetar
- `.claude/rules/frontend-quality.md` — ESLint 0 errors, TypeScript strict 0 errors
- `.claude/rules/architectural-fitness.md` — ratchet shrink-only allowlists
- `.claude/rules/anti-duplication.md` — Step 0 grep antes nuevo subsystem (registries SSoT)
- `.claude/rules/spanish-text.md` — voseo glosario (zero new strings esperado)
- `.claude/rules/tdd-mandatory.md` — arch tests RED antes refactor
- Skills cargar: `frontend-expert`, `metrics-expert` (entender 4-tier loading + channel registry origen)

## Plan de migración (sugerencia para architect)

1. **Fase 1 — Registries SSoT (`lib/registries/`):** crear `stage-registry.ts` + `channel-registry.ts` + `dashboard-registry.ts` con datos hoy hardcoded.
2. **Fase 2 — Factory dispatchers (`pages/`):** `stage-slugs.ts` + `StageDispatcher.tsx` + `channel-slugs.ts` + `ChannelDispatcher.tsx`. Routes Next.js consumen.
3. **Fase 3 — 4-tier rename (`pages/tiers/`):** mover hooks 4-tier de paths actuales a `pages/tiers/{0..3}-*.ts`. Update consumers imports.
4. **Fase 4 — Legacy purge (`config/` + `context/` + `__mocks__/`):**
   - `config/` content → `lib/registries/`
   - `context/` content → `hooks/` (locales) o `store/` (zustand global)
   - `__mocks__/` → `__tests__/__mocks__/`
5. **Fase 5 — Allowlist cleanup:** 6 dashboards adoptan `useCopilotOffset`. Allowlist set vacío.
6. **Fase 6 — Arch fitness extension:** `test-studio-structure-parity` modo adapter incluye growth.
7. **Fase 7 — Placeholders 2B:** `actions/.gitkeep` + `schemas/.gitkeep`.
8. **Fase 8 — Verify:** vitest + Playwright smoke + visual regression GREEN. Coverage parity.

## Architect orientation hints

- Arch fitness extension mode adapter requiere refactor `STUDIO_PAGE_DIRS` const en `test-studio-structure-parity.test.ts`. Sugerencia: `STUDIO_PAGE_DIRS = { brand: { dir, canonical: ["section-slugs.ts", "SectionDispatcher.tsx"] }, offer: idem, growth: { dir, canonical: ["stage-slugs.ts", "StageDispatcher.tsx", "channel-slugs.ts", "ChannelDispatcher.tsx"] } }`.
- Cross-import grep antes registries: `grep -rn "channel.*registry\|stage.*registry" frontend/src/` — extend si existe shared abstraction (probable: NO — patrón nuevo growth-only).
- Consumer count tier hooks pre-rename — search-replace cuidadoso (script no manual).
- Visual regression baseline: capturar pre-refactor screenshots ANTES iniciar refactor.

## Ratification log (Chris 2026-05-07)

| Q | Pregunta | Decisión |
|---|---|---|
| 1 | `store/` zustand growth | **Crear nuevo `growth-studio/store/index.ts`** zustand local del feature. FSD-Lite pattern. Coexiste con copilot-store + shell-mutex-store (story 1). |
| 2 | `__tests__/visual-regression-drawer-bowtie.test.tsx` | **Replace con visual regression baseline pattern story 1** (Playwright + masking). Lift VR pattern shared cross-studio. |
| 3 | Routes `app/[tenantId]/growth-studio/[stage]/page.tsx` | **Sí — routes thin delegan a StageDispatcher** (patrón brand/offer Server Component delgado). |
| 4 | Consumers `config/` migration workflow | **Listar primero vía grep + plan migración + ejecutar find-replace cubierto por arch test** (Step 0 GATE per anti-duplication.md). |
| 5 | 4-tier hooks rename `pages/tiers/{0..3}-*.ts` | **Break-and-fix atomic** — rename + update todos consumers en mismo commit. Sin shim. Arch test enforza nuevos paths. |

## Hand off post ratificación

```
state: refining → refined  (si Chris ratifica scenarios + open questions resueltos)
next: /architect orchestrator → produce ready package (03-arch + 04-validators + 05-guidelines + 06-tickets)
```
