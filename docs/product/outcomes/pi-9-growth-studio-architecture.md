---
id: pi-9-growth-studio-architecture
state: dropped
superseded_by: growth-copilot-layout-unification
superseded_at: 2026-05-06
superseded_reason: |
  Unificado con PI-10 en outcome único `growth-copilot-layout-unification`.
  Razón (Chris 2026-05-06): desde negocio son un solo problema — layout app
  + Growth Studio no escalan + sidebar global se superpone a barra copilot
  cross-app. Separar architecture vs UX era artefacto paradigma viejo PI/Sprint.
title: Growth Studio — refactor estructural FE escalable
why_now: |
  Cientos de clientes proyectados 1 mes → arquitectura FE escalable mandatoria.
  Roadmap exige agregar canales/editar dashboards/modificar stages sin refactor
  cada vez. Growth Studio FE NO sigue patrón post-refactor brand/offer (falta
  pages/, actions/, schemas/, hardcoded "5 stages").
target_end: null
priority: 2
created: 2026-05-01
last_modified: 2026-05-06
migrated_from: docs/pm-nico/pis/active/PI-9-growth-studio-architecture/
story_ids: []
success_metrics:
  - "Agregar canal ficticio 'test-channel-x' requiere ≤3 archivos nuevos (registry + dashboard + schema) + ZERO modificación a StageDispatcher/ChannelDispatcher"
  - "Arch fitness test_studio_structure_parity verde para growth-studio en modo factory"
tags:
  - module:analytics
  - type:refactor-fe
blocked_by:
  - "PI-8 ship (drawer hotfix) — predecesor"
---

# Growth Studio — refactor estructural FE escalable

Refactor estructural Growth Studio FE para arquitectura escalable: homologada
con Brand Studio + Offer Studio (mismas folders) + factory propia adaptada
a sus invariantes (5 stages × N canales × 4-tier loading). Agregar nuevo
canal/dashboard requiere SOLO registrar en SSoT registry (zero refactor
dispatcher).

## Migration note
This outcome was migrated from legacy paradigm (`docs/pm-nico/pis/active/PI-9-growth-studio-architecture/`)
on 2026-05-05 as part of Wave 2 PM redesign. Full original content archived at
`docs/archive/2026/legacy-pis/PI-9-growth-studio-architecture/`.

Estado en migración: discovery — esqueleto plan macro pendiente refine post
PI-8 ship. No stories ratificadas aún.

## Original content summary

Problema técnico: Growth Studio FE NO sigue patrón post-refactor brand/offer:
- Falta `pages/` (SectionDispatcher SSoT)
- Falta `actions/` (server actions copilot integration)
- Falta `schemas/` (zod validators)
- Hardcoded "5 stages" en code path (no driven by registry)
- 4-tier loading hooks sin contrato explícito (rename pending `tiers/`)
- Arch fitness `test-studio-structure-parity.test.ts` excluye growth-studio
- 177 components organizados ad-hoc (vs 29 brand)

Architect confirmó (2026-05-01): pattern brand/offer NO 1:1 transplantable.
Growth necesita factory propia (StageDispatcher 5 stages + ChannelDispatcher
N canales) que comparte folders pero no internals.

Hipótesis driver:
- H1: Stage/Channel/Dashboard registry SSoT habilita open-closed
- H2: Folders homologadas habilitan futura cross-studio reuse (copilot agent invoke patrón growth = brand/offer)
- H3: 4-tier loading sigue privado growth (sin ROI lift a shared)
- H4: Arch fitness adapter mode (no paridad estricta) bloquea regresión

Sprint plan macro (preliminary): S1 stage-channel-registry → S2 actions/schemas
homologation → S3 component reorg + arch fitness gate.

Sucesor: PI-10 growth-studio-ux-homologation (UX redesign) — ahora outcome
`pi-10-growth-studio-ux-homologation` en este folder.
