# 03-arch.md — Growth Studio Folder Parity (consolidated)

> Owner: `/architect`. Single-surface story (FE only). Detalle completo en `03-arch-fe.md`.

---
story_id: growth-studio-folder-parity
arch_version: 1
last_modified: 2026-05-07T06:30:00Z
links:
  spec: "01-spec.md"
  arch_fe: "03-arch-fe.md"
  outcome: "../../outcomes/growth-copilot-layout-unification.md"
  story_1_coordination: "../app-shell-sidebar-copilot-decoupling/03-arch.md"
  story_2b_blocked: "../growth-studio-actions-schemas-real/checkpoint.md"
---

## Surfaces involved

- **BE:** no
- **FE:** **yes** — single sub-architect (architect-fe equivalent)
- **AGENTIC:** no

## FE arch (full detail in `03-arch-fe.md`)

### Decisión arquitectónica clave

Migrar `frontend/src/features/growth-studio/` a estructura FSD-Lite homologada con brand/offer-studio mediante **factory propia adapter mode**: mismos folders canonical (`pages/`, `actions/`, `schemas/`, `api/`, `components/`, `hooks/`, `lib/`, `types/`, `utils/` + opcional `__tests__/`, `store/`), pero contenido interno propio del dominio growth (StageDispatcher 5 stages × ChannelDispatcher N canales × 4-tier loading bajo `pages/tiers/`). Arch fitness `test-studio-structure-parity` modo adapter — verifica paridad de FORMA, no SHAPE interno.

### Architectural Decisions (8 ADs en 03-arch-fe.md)

- AD1 zustand local `growth-studio/store/sync-store.ts` (Q1)
- AD2 VR replace via story 1 pattern (Q2 — coordination point)
- AD3 routes thin Server Component delegate to dispatchers (Q3)
- AD4 `config/` migration grep-first + atomic find-replace (Q4)
- AD5 4-tier rename break-and-fix atomic — tier0 MOVE, tiers 1-3 WRAPPER re-exports (Q5)
- AD6 Factory propia adapter mode arch fitness `STUDIO_PAGE_DIRS` per-studio canonical config
- AD7 `KNOWN_VIOLATIONS_GROWTH = new Set()` post-2A (6 dashboards adopt useCopilotOffset)
- AD8 `getStageForChannel()` re-exported during atomic move

### Channel slug correction (2026-05-07 post architect-fe grep)

Spec scenario 1 v1 listó friendly names (`meta-ads`, `youtube-organic`, `mail`, `ig-organic`, `website`). Architect-fe grep cross-codebase confirmó canonical slugs reales:
- `meta-ads` ✓ (canonical match)
- `yt-organic` ✓ (NOT `youtube-organic` — folder name; canonical slug is short form)
- `email-nurture` ✓ (NOT `mail`)
- `ig-organic` ✓
- `website-total` ✓ (NOT `website`)

Spec v2 corregido a canonical 2026-05-07.

## Cross-cutting decisions

| Concern | Decision |
|---|---|
| Tenant isolation | N/A — story 2A no toca BE calls; preserve existing fetchClient consumers |
| A11y | Preserve existing — zero new strings esperado |
| i18n | Preserve existing — voseo glosario respect |
| Server/Client | Routes Server Component delgados; dispatchers Client si consume hooks/state |
| FSD-Lite boundaries | growth-studio self-contained post-refactor |
| Bundle | Refactor folders no aumenta bundle >5% NFR informativo |

## Coordination cross-story

| Coordination point | Owner | Resolution |
|---|---|---|
| Rename `test-growth-studio-copilot-offset.test.ts` → `test-shell-copilot-offset.test.ts` con scope-keyed allowlists | story 1 T-7 | **Story 1 T-7 lands BEFORE story 2A Fase 5 (allowlist drain)** — orchestrator merge sequencing constraint. |
| Visual regression shared helpers lift | story 1 T-8 | **Story 1 T-8 ships VR helpers BEFORE 2A Fase 4 (legacy VR delete + new VR add)**. Si story 2A llega antes → defer Fase 4 VR replacement, mantén legacy VR test. |
| `KNOWN_VIOLATIONS_GROWTH` set drain | story 2A | Set inside renamed `test-shell-copilot-offset.test.ts` (story 1 owns rename + scope-keyed split). 2A drains set to empty. |

## Migration plan (8 phases)

Phase 1: Registries SSoT (`lib/registries/{stage,channel,dashboard}-registry.ts`)
Phase 2: Factory dispatchers (`pages/StageDispatcher.tsx`, `pages/ChannelDispatcher.tsx`, `pages/sections/*-page.tsx`)
Phase 3: 4-tier rename `pages/tiers/{0..3}-*.ts` (break-and-fix atomic — tier0 MOVE; tiers 1-3 WRAPPER re-exports for 1 ciclo deprecation)
Phase 4: Legacy purge (`config/` → `lib/registries/`; `context/` → `store/`+`hooks/`; `__mocks__/` → `__tests__/__mocks__/`). VR replacement (depends story 1 helpers).
Phase 5: Allowlist cleanup 6 dashboards adopt `useCopilotOffset` → `KNOWN_VIOLATIONS_GROWTH = new Set()` (depends story 1 T-7 rename landed).
Phase 6: Arch fitness extension `test-studio-structure-parity` adapter mode + 3 NEW arch tests.
Phase 7: Placeholders 2B (`actions/.gitkeep` + `schemas/.gitkeep`).
Phase 8: Verify (vitest + Playwright smoke + VR + coverage parity).

## Riesgos cross-cutting

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Story 1 rename no lands antes 2A Fase 5 | medium | Defer Fase 5 hasta rename done. PR dependency tracker. |
| Story 1 VR helpers no shipped antes 2A Fase 4 | medium | Defer Fase 4 VR replacement; legacy VR test stays until story 1 lands. |
| 4-tier WRAPPER re-exports drift | low | Deprecation @ 1 ciclo + arch test detect new imports |
| Legacy `__mocks__` dynamic-import consumers (9 in stage-detail-api) | medium | Atomic find-replace + import path arch test |
| Channel slug canonical mismatch persists in user-facing copy | low | Spec v2 corrected; code grep confirmed |

## Hand off

Story state `refining → refined → ready` (post `04-validators` + `05-guidelines` + `06-tickets` cierre).

Next: `/dev-team` toma T-1 (Conv 2 autonomous build). Story 2B (`growth-studio-actions-schemas-real`) BLOCKED hasta 2A done.
