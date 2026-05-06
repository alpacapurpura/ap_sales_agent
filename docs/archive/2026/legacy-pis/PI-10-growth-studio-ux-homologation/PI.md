# PI-10-growth-studio-ux-homologation

## Meta

| Campo | Valor |
|---|---|
| PI ID | PI-10-growth-studio-ux-homologation |
| Inicio | TBD (bloqueado por PI-9 ship) |
| Estado | placeholder (sin discovery refinement) |
| Tipo | feature (UX redesign + visual homologation) |
| Owner PM | /pm |
| Origen | Discovery PM 2026-05-01 — Chris demanda UX/UI homologada cross-studio |
| Predecesor | PI-9-growth-studio-architecture (estructura post-refactor lista) |

## Outcome esperado (user-facing)

**Growth Studio visualmente y experiencia-de-uso coherente con Brand Studio + Offer Studio.** Mismos paradigmas interacción (cards, drawers, navegación), misma estética, misma sensación. Decisión final dual UX path drawer-overlay vs nested-route consolidada en una sola UX (decisión PI-10).

Métrica única éxito: usuario nuevo navega Brand Studio + Offer Studio + Growth Studio sin sentir "pertenecen a apps distintas". Visual + interaction coherentes.

## Pendiente discovery refinement

Este PI es **placeholder** hoy. Requiere:
- UX/flow audit cross-studio post PI-9 ship (`ux-flow-architect` skill)
- Mockups iterativos con `nicolify-ux-designer` agent
- Decisión drawer-vs-nested-route final (con user feedback post PI-8 deploy)
- Component rewrite plan basado en UI-SPEC.md aprobado
- Validación scope con Chris

## Plan macro (preliminary, refinar al activarse)

### Sprint S1-ux-flow-audit-mockups (TBD)
- ux-flow-architect skill: audit cross-feature navigation Growth + Brand + Offer
- nicolify-ux-designer agent: mockups iterativos `mockups/*.html` + UI-SPEC.md
- Decisión drawer-vs-route final (Chris approve)

### Sprint S2-component-rewrite (TBD)
- Component rewrite UX siguiendo UI-SPEC
- Visual coherence con brand/offer (cards + spacing + typography + interaction)
- Bowtie superior preserved (no quitar funcionalidad)

### Sprint S3-final-polish (TBD)
- Accessibility a11y compliance audit
- Live verification Chris-mediated 5 stages × mobile + desktop
- Smoke regresión cross-studio

## Anti-patterns explícitos PI-10 (heredados PI-8 + PI-9)

PI-10 NO debe:
1. **Romper estructura PI-9** (registries + dispatchers + actions/+schemas/+tiers/)
2. **Perder funcionalidad existente** (bowtie + 4-tier + multi-currency + multi-stage + action triggers + 5 channel dashboards)
3. **Hardcodear stages/canales** (driven by PI-9 registries)
4. **Crear paradigmas UX nuevos sin reuse cross-studio** (DRY visual primitives)
5. **Refactor estructural** (PI-9 owns) — solo UX/visual

## Riesgos preliminary

| Riesgo | Mitigación |
|---|---|
| Scope creep "rediseño total" | UX-spec aprobado por Chris ANTES builder spawn |
| Decisión drawer-vs-route paraliza PI | Decidir explícitamente en S1 mockups Chris-approved |
| Visual homologation pierde identidad Growth (analytics-heavy) | Mantener density informacional growth + estética brand/offer |
| Component rewrite rompe 4-tier loading | Tests E2E + chrome-devtools smoke profundo |

## Out of scope

- Refactor estructural FE (PI-9 owns)
- Bug fixes layout (PI-8 owns, ya shipped)
- New features Growth (separar a PIs futuros)
- BE changes (Growth Studio FE-only)

## Aceptación PI (preliminary)

- [ ] PI-9 shipped + PI-9 retro
- [ ] UX flow audit + UI-SPEC.md + mockups Chris-approved
- [ ] Component rewrite shipped sin pérdida funcionalidad
- [ ] Decisión drawer-vs-route final shipped
- [ ] Chris smoke 5 stages × mobile + desktop OK
- [ ] Cross-studio coherence Chris-validated
- [ ] retro.md PI-10 + archive

## Cross-references

- Predecesor: `pis/active/PI-9-growth-studio-architecture/PI.md`
- Predecesor original: `pis/active/PI-8-growth-studio-stability/PI.md`
- UX skills: `ux-flow-architect`, `nicolify-ux-designer`, `ux-disruptivo`
- Brand reference (UX baseline): `frontend/src/features/brand-studio/`
- Offer reference: `frontend/src/features/offer-studio/`
