---
story_id: growth-studio-folder-parity
outcome: growth-copilot-layout-unification
state: developing
phase: BUILD_T6
last_artifact: docs/product/stories/growth-studio-folder-parity/T-6-result.md
last_modified: 2026-05-08T22:00:00Z
next_action: "T-6 DONE (pushed). Arch fitness adapter mode + 2 new arch tests (stage/channel slug SSoT). T-7 next: placeholders 2B (.gitkeep + routes verify)."
build_started_at: 2026-05-07T22:30:00Z
build_started_by: /dev-team
ratified_by_chris: true
ratified_at: 2026-05-07T04:15:00Z
ready_at: 2026-05-07T06:35:00Z
spawned_at: 2026-05-06T22:54:54Z
spawned_by: /po (sesión refining outcome unification 2026-05-06)
renamed_at: 2026-05-07T03:30:00Z
renamed_from: growth-studio-architectural-parity
parallel_safe: true
parallel_safe_with: ["app-shell-sidebar-copilot-decoupling"]
blocks: ["growth-studio-actions-schemas-real"]
blocked_reason: null
audit_iterations: 0
hotfix_metadata:
  repro_verified: false
  repro_command: null
  diagnosis_validates_handoff: null
---

# Story scope — Story 2A (folder parity)

**Tipo:** service-story (refactor FE — sin UI change visible al usuario)
**Skill spec:** `/po`
**Module primario:** `analytics` (FE: `frontend/src/features/growth-studio/`)

> Split decision (Chris ratified 2026-05-07): la story original
> `growth-studio-architectural-parity` se dividió en 2A (este file —
> folder parity puro + factory dispatchers + legacy purge + arch fitness)
> y 2B (`growth-studio-actions-schemas-real` — real copilot actions +
> real zod schemas, sequential después de 2A).

## Problema (confirmado por filesystem)

Growth Studio FE quedó fuera del refactor FSD-Lite que homologó Brand
Studio + Offer Studio (~1 mes atrás). Filesystem evidencia (2026-05-06):

```
brand-studio/   → schemas/ + pages/ + actions/ + components/ + types/ + lib/ + api/ + utils/ + hooks/
offer-studio/   → schemas/ + pages/ + actions/ + components/ + types/ + lib/ + api/ + utils/ + hooks/
growth-studio/  → __mocks__/ + __tests__/ + components/ + config/ + context/ + types/ + lib/ + api/ + utils/ + hooks/
                  ↑ FALTA: pages/ + actions/ + schemas/
                  ↑ SOBRA: config/ + context/ + __mocks__/ (legacy)
```

Architect previo (legacy PI-9 archived 2026-05-01): pattern brand/offer NO
1:1 transplantable. Growth necesita factory propia (StageDispatcher 5
stages + ChannelDispatcher N canales) compartiendo folders pero no
internals.

## Scope 2A (qué SÍ entra)

1. **Crear folders canonical:** `pages/`, `actions/`, `schemas/` con
   contenido factory propia (`stage-slugs.ts`, `StageDispatcher.tsx`,
   `channel-slugs.ts`, `ChannelDispatcher.tsx`, 4-tier hooks renamed
   bajo `pages/tiers/`).
2. **Legacy purge:**
   - `config/` → migrar contenido a `lib/registries/` (channel-registry,
     stage-registry, dashboard-registry como SSoT)
   - `context/` → distribuir contenido entre `hooks/` (custom hooks
     locales) + `store/` (zustand global state si aplica)
   - `__mocks__/` → mover a `__tests__/__mocks__/` (MSW migration defer
     a outcome separado futuro)
3. **Arch fitness extension:** `test-studio-structure-parity.test.ts`
   modo adapter — paridad folders + canonical files exists, NO mismo
   shape interno (factory propia OK).
4. **Allowlist cleanup:** 6 dashboards en `test-growth-studio-copilot-offset.test.ts`
   adoptan `useCopilotOffset` hook (o `DetailPanel` wrapper) → allowlist
   shrinks a 0.
5. **Placeholders 2B:** `actions/.gitkeep` + `schemas/.gitkeep` (real
   actions/schemas vienen en 2B story sequential).

## Scope 2A (qué NO entra)

- ❌ Real copilot actions (`queryStageMetrics`, `queryChannelOverview`,
  `triggerETLRefresh`, `exportStageReport`) — story 2B
- ❌ Real zod schemas (filter params, channel config, KPI selection,
  tier loading) — story 2B
- ❌ Visual / UX changes — story 3 (parked)
- ❌ Bowtie superior modifications — invariante
- ❌ Métricas dashboard visual modifications — invariante
- ❌ MSW migration — defer outcome separado

## Constraints heredados

- Bowtie superior (`components/strategy-canvas/`) — pixel intact
- Panel métricas (`components/metrics-dashboard/`) — pixel intact
- 4-tier loading (tier0/tier1/tier2/tier3) — sigue privado growth, NO
  se lifta a shared
- Arch fitness `test-studio-structure-parity.test.ts` excluye growth
  HOY → debe dejar de excluir post-refactor (modo adapter)
- FSD-Lite boundaries cross-feature
- TDD obligatorio: arch tests RED antes refactor

## Bitácora

- 2026-05-06 22:54 — `/po` (sesión refining unification) creó folder +
  checkpoint.md (state=refining). Folder structure diff confirmado.
  Spec pending refining propio.
- 2026-05-07 03:30 — `/po` (sesión refining unification 2nd pass): split
  story original en 2A (este file — folder parity) + 2B
  (`growth-studio-actions-schemas-real`). Renombre folder
  `growth-studio-architectural-parity` → `growth-studio-folder-parity`.
  Scope narrowed. Sequential 2A → 2B. Phase=PO_DRAFTING.

## Notas

- `parallel_safe: true` con story 1 (`app-shell-sidebar-copilot-decoupling`)
- BLOCKS story 2B (`growth-studio-actions-schemas-real`) — 2B necesita
  factory dispatchers + folders existir
- Architect Opus 4.7 OBLIGATORIO post-spec (refactor estructural
  cross-cutting, alto ROI)
