---
id: growth-copilot-layout-unification
state: validated
title: Growth Studio + Copilot — unificación arquitectural y de layout (paridad cross-studio)
why_now: |
  Dos pains convergentes hoy bloquean escalabilidad y degradan experiencia
  cross-app:

  1. **Shell layout starvation + mutex absence cross-app** (diagnosis
     corregida 2026-05-07 vía live repro chrome-devtools-verify): el
     symptom user-reported "sidebar se superpone con copilot" NO es
     z-index overlap (live repro confirma overlap=0px en TODAS las
     combinaciones medidas). Real root cause = (a) `main` element es
     `flex-1 min-w-0` sin floor → CopilotSidebar consume content space
     hasta degradar main. Worst case: viewport 768 × sidebar expandido ×
     copilot open = main 52px (catastrofico). (b) AppSidebar.isCollapsed
     y CopilotStore.isOpen independientes — sin mutex policy auto-collapse.
     (c) `useCopilotOffset` hook miente por 80-220px vs CopilotSidebar
     grid widths reales — todos modals/sheets mis-centered. (d) Mobile
     <768: AppSidebar carece left drawer (solo topbar 40px sin aria-label),
     no FAB para reabrir copilot. Cross-studio (offer/brand/growth/sales/
     settings/connections/scheduling). User explícito: "afecta otras
     funcionalidades más, es un tema arquitectural" (2026-05-06) —
     ratificado pero scope real expandido por evidence.

  2. **Growth Studio FE quedó fuera del refactor de hace ~1 mes** que
     homologó Brand Studio + Offer Studio (folders `pages/` + `actions/` +
     `schemas/`, dispatchers SSoT, arch fitness `test-studio-structure-parity`).
     Growth tiene `config/` + `context/` + `__mocks__/` legacy y NO tiene
     `pages/` ni `actions/` ni `schemas/`. Roadmap exige agregar canales
     sin refactor cada vez.

  Bowtie superior + métricas dashboard NO se tocan — visualmente están bien
  y son invariante de negocio (Chris, 2026-05-06).
target_end: null
priority: 1
created: 2026-05-06
last_modified: 2026-05-08
supersedes:
  - pi-9-growth-studio-architecture
  - pi-10-growth-studio-ux-homologation
story_ids:
  - app-shell-sidebar-copilot-decoupling           # state=developed (awaiting QA)
  - growth-studio-folder-parity                    # 2A — DONE 2026-05-08 (split 2026-05-07; was: growth-studio-architectural-parity)
  - growth-studio-actions-schemas-real             # 2B — DONE 2026-05-08 (capability growth-studio-copilot-actions promoted)
  - growth-studio-visual-coherence-pass            # parked
success_metrics:
  - "main content width ≥720px en TODO studio @ viewport ≥1024px (read-comfort floor garantizado por DashboardShell + mutex policy)"
  - "Mobile <768px: AppSidebar y Copilot drawers mutuamente exclusivos; FAB copilot persistente para reabrir; aria-labels descriptivos hamburger + FAB"
  - "useCopilotOffset hook y CopilotSidebar grid widths consumen mismas constantes SSoT (`copilot-shell-widths.ts`); dialogs/sheets centered correctamente (drift 0px vs ±80-220px pre-fix)"
  - "Z-index ladder centralizado en `lib/tokens/z-index.ts` + arch test enforza tokens en shell + copilot shell"
  - "Agregar canal ficticio 'test-channel-x' a Growth Studio requiere ≤3 archivos nuevos (registry + dashboard + schema) + ZERO modificación a StageDispatcher/ChannelDispatcher"
  - "Arch fitness test_studio_structure_parity verde para growth-studio (modo factory adaptado)"
  - "Bowtie superior + métricas dashboard intactos pixel-perfect post-refactor (screenshot regression)"
tags:
  - module:analytics
  - module:copilot
  - module:shared
  - type:refactor-fe
  - type:layout-fix
  - type:cross-cutting
related_ideas:
  - solo-mode-chat-first-layout                    # idea futura ideas-pool.yaml — depende de este outcome
---

# Growth Studio + Copilot — unificación arquitectural y de layout

Outcome único que reemplaza **PI-9 (architecture)** + **PI-10 (UX
homologation)**. Razón: desde el negocio (Chris) son **un solo problema**:
el layout app + Growth Studio quedaron mal y no escalan. Separarlos en 2
PIs era artefacto del paradigma viejo PI/Sprint. Paradigma actual (post
pm-redesign 2026-05) permite outcomes event-driven que mezclan refactor
arquitectural + UX cuando el business owner los ve unificados.

## Contexto que originó el outcome

### Pain 1 — sidebar global ↔ copilot bar overlap

Bug visual visible cross-app. User reporta: "la visualización del sidebar
en general, no solo en el growth studio, se ve mal, se superpone a la
barra del copilot". Afecta brand/offer/growth/copilot/sales/closer/
connections (todas las superficies que renderizan sidebar global +
copilot panel simultáneamente).

Hipótesis del root cause: layout shell raíz (probable
`frontend/src/components/shared/layout/`) define z-index / dimensiones
fijas del sidebar y del copilot drawer sin contrato compartido →
overlap cuando ambos abren. Detalle exacto pendiente de live verification
con `chrome-devtools-verify` (story 1).

### Pain 2 — Growth Studio fuera del refactor FSD-Lite cross-studio

Filesystem confirma (2026-05-06):

```
brand-studio/   → schemas/ + pages/ + actions/ + components/ + types/ + lib/ + api/ + utils/ + hooks/
offer-studio/   → schemas/ + pages/ + actions/ + components/ + types/ + lib/ + api/ + utils/ + hooks/
growth-studio/  → __mocks__/ + __tests__/ + components/ + config/ + context/ + types/ + lib/ + api/ + utils/ + hooks/
                  ↑ FALTA: pages/ + actions/ + schemas/
                  ↑ SOBRA: config/ + context/ + __mocks__/ (legacy paradigma anterior)
```

Architect ya analizó (2026-05-01, archived legacy PI-9): pattern
brand/offer NO 1:1 transplantable. Growth necesita factory propia
(StageDispatcher 5 stages + ChannelDispatcher N canales) que comparte
folders pero no internals.

### Invariante negocio (no negociable)

- Bowtie superior (`growth-studio/components/strategy-canvas/`) — pixel
  intact
- Panel métricas (`growth-studio/components/metrics-dashboard/`) — pixel
  intact
- 4-tier loading (tier0 summary / tier1 overview / tier2 group-detail /
  tier3 stage) — sigue privado growth, no se lifta

## Stories que componen el outcome

> Split 2026-05-07: story original `growth-studio-architectural-parity`
> dividida en 2A + 2B por exceder cap (≤10 tickets/story). Story 1 scope
> expandido post live repro chrome-devtools-verify (diagnosis correction:
> bug NO es z-index overlap; real = content starvation + mutex absence +
> offset hook drift + mobile gaps). Skill: `/po` ambas (no `/po-ux` —
> bug-fix shell, no CRUD UI std).

| # | Story-id | Tipo | Skill spec | Scope |
|---|---|---|---|---|
| 1 | `app-shell-sidebar-copilot-decoupling` | service-story (refactor shell layout) | `/po` | Refactor shell layout (DashboardShell parent NEW + useShellMutex hook + min content width floor 720px @≥1024 + copilot-shell-widths SSoT + z-index tokens + AppSidebar mobile drawer NEW + CopilotFAB + arch test extension shell scope + ESLint custom rules). Live repro `00-live-repro.md` + diagnosis correction documentadas. |
| 2A | `growth-studio-folder-parity` | service-story (refactor FE) | `/po` | Crear `pages/` + `actions/` + `schemas/` con factory propia (StageDispatcher + ChannelDispatcher + 4-tier hooks). Purgar `config/` + `context/` + `__mocks__/`. Allowlist `test-growth-studio-copilot-offset` shrinks a 0 (rename a `test-shell-copilot-offset` parte de story 1). Arch fitness `test-studio-structure-parity` modo adapter. |
| 2B | `growth-studio-actions-schemas-real` | service-story (FE actions+schemas) | `/po` | Real copilot actions (4: queryStageMetrics + queryChannelOverview + triggerETLRefresh + exportStageReport) + real zod schemas (4: stage-filter-params + channel-config + kpi-selection + tier-loading). Sequential después de 2A. |
| 3 | `growth-studio-visual-coherence-pass` | UI polish (condicional, parked) | `/po-ux` | Solo si post-stories 1+2A+2B quedan inconsistencias visuales detectables. Probable que NO sea necesario. Mantenida `parked` hasta confirmación post-2B. |

Dependencias:
- Story 1 ↔ Story 2A: paralelo (parallel_safe, no overlap territorial)
- Story 2A → Story 2B: sequential (2B necesita factory + folders existir)
- Story 3: depende de 1 + 2A + 2B (puede no ejecutarse — gate post-2B)

Live repro story 1 mantiene chrome-devtools-verify dentro de refining
(00-live-repro.md como evidence pre-spec scenarios).

## Idea futura relacionada (parked, NO refinar aún)

`solo-mode-chat-first-layout` (capturada en `ideas-pool.yaml` 2026-05-06):
toggle UI top-bar invierte layout — copilot chat principal centro/izq,
contenido secundario derecha (estilo Claude Desktop / Cowork). Predecesor
implícito: este outcome (sin sidebar+copilot decoupling limpio + Growth
arch parity, SOLO Mode no es implementable limpio).

## Migration note — PI-9 + PI-10 superseded

Los 2 outcomes legacy se marcaron `state: dropped` con
`superseded_by: growth-copilot-layout-unification`:
- `docs/product/outcomes/pi-9-growth-studio-architecture.md`
- `docs/product/outcomes/pi-10-growth-studio-ux-homologation.md`

Audit trail original preservado en `docs/archive/2026/legacy-pis/PI-9-...`
y `docs/archive/2026/legacy-pis/PI-10-...` (snapshot inmutable).
