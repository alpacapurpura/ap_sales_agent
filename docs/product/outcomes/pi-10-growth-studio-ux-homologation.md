---
id: pi-10-growth-studio-ux-homologation
state: validated
title: Growth Studio — UX visual homologada cross-studio
why_now: |
  Usuario nuevo navega Brand Studio + Offer Studio + Growth Studio y siente
  "pertenecen a apps distintas". Coherencia visual + interacción cross-studio
  necesaria post Growth Studio architecture refactor (PI-9).
target_end: null
priority: 3
created: 2026-05-01
last_modified: 2026-05-05
migrated_from: docs/pm-nico/pis/active/PI-10-growth-studio-ux-homologation/
story_ids: []
success_metrics:
  - "Usuario nuevo navega Brand+Offer+Growth Studio sin sentir 'apps distintas' (visual + interaction coherentes)"
  - "Decisión drawer-vs-nested-route consolidada en una sola UX"
tags:
  - module:analytics
  - type:ux-redesign
blocked_by:
  - "PI-9 ship (architecture post-refactor) — predecesor"
---

# Growth Studio — UX visual homologada cross-studio

UX redesign + visual homologation Growth Studio. Mismos paradigmas interacción
(cards, drawers, navegación), misma estética, misma sensación que Brand Studio
+ Offer Studio. Decisión final dual UX path drawer-overlay vs nested-route
consolidada en una sola UX.

## Migration note
This outcome was migrated from legacy paradigm (`docs/pm-nico/pis/active/PI-10-growth-studio-ux-homologation/`)
on 2026-05-05 as part of Wave 2 PM redesign. Full original content archived at
`docs/archive/2026/legacy-pis/PI-10-growth-studio-ux-homologation/`.

Estado en migración: placeholder — sin discovery refinement. Bloqueado por PI-9
ship.

## Original content summary

Pendiente discovery refinement:
- UX/flow audit cross-studio post PI-9 ship (`ux-flow-architect` skill)
- Mockups iterativos con `nicolify-ux-designer` agent
- Decisión drawer-vs-nested-route final (con user feedback post PI-8 deploy)
- Component rewrite plan basado en UI-SPEC.md aprobado
- Validación scope con Chris

Plan macro preliminary:
- S1 ux-flow-audit-mockups: ux-flow-architect audit cross-feature navigation
  Growth+Brand+Offer; nicolify-ux-designer mockups iterativos `mockups/*.html`
  + UI-SPEC.md; decisión drawer-vs-route final
- S2 component-rewrite: rewrite UX siguiendo UI-SPEC; visual coherence con
  brand/offer (cards + spacing + typography + interaction); bowtie superior
  preserved
- S3 final-polish: a11y compliance audit; live verification Chris-mediated
  5 stages × mobile + desktop; smoke regresión cross-studio

Anti-patterns explícitos:
1. NO romper estructura PI-9 (registries + dispatchers + actions/+schemas/+tiers/)
2. NO quitar funcionalidad bowtie superior
3. NO reintroducir hardcoded UI sin pasar por registry
