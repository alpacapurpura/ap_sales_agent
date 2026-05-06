# PI-9-growth-studio-architecture

## Meta

| Campo | Valor |
|---|---|
| PI ID | PI-9-growth-studio-architecture |
| Inicio | TBD (bloqueado por PI-8 ship) |
| Estado | discovery (esqueleto, plan macro pendiente refine post PI-8) |
| Tipo | feature (refactor estructural FE — escalabilidad arquitectónica) |
| Owner PM | /pm |
| Origen | Discovery PM 2026-05-01 — Chris demanda arquitectura escalable (cientos clientes proyectados 1 mes) + architect tech sanity check |
| Predecesor | PI-8-growth-studio-stability (drawer hotfix) |
| Sucesor | PI-10-growth-studio-ux-homologation (UX redesign) |

## Outcome esperado (user-facing)

**Growth Studio arquitectónicamente homologada con Brand Studio + Offer Studio (mismas folders), Y con factory propia adaptada a sus invariantes (5 stages × N canales × 4-tier loading).** Agregar nuevo canal/dashboard requiere SOLO registrar en SSoT registry (zero refactor dispatcher).

Métrica única éxito: agregar canal ficticio "test-channel-x" requiere ≤3 archivos nuevos (config registry entry + dashboard component + schema validator) + ZERO modificación a `StageDispatcher` ni `ChannelDispatcher`. Verificable arch fitness test.

## Hipótesis driver (Chris-confirmadas)

- Cientos clientes proyectados 1 mes → arquitectura **escalable** mandatoria
- Roadmap Nicolify exige **agregar canales / editar dashboards / modificar stages** sin refactor cada vez
- Principios diseño: **alta cohesión + bajo acoplamiento + DRY + open-closed** (extension sin modification)

## Problema (technical)

Growth Studio FE NO sigue patrón post-refactor brand/offer:
- Falta `pages/` (SectionDispatcher SSoT)
- Falta `actions/` (server actions copilot integration)
- Falta `schemas/` (zod validators)
- Hardcoded "5 stages" en code path (no driven by registry)
- 4-tier loading hooks sin contrato explícito (rename pending `tiers/`)
- Arch fitness `test-studio-structure-parity.test.ts` excluye growth-studio
- 177 components organizados ad-hoc (vs 29 brand)

Architect confirmó (2026-05-01): pattern brand/offer **NO 1:1** transplantable. Growth necesita **factory propia** (StageDispatcher 5 stages + ChannelDispatcher N canales) que comparte folders pero no internals.

## Outcome alcanzado vs hipótesis

### H1 — Stage/Channel/Dashboard registry SSoT habilita open-closed
**Test:** agregar canal ficticio requiere solo entry en registry + dashboard component + schema. Zero modificación dispatcher.

### H2 — Folders homologadas (`pages/`+`actions/`+`schemas/`) habilitan futura cross-studio reuse
**Test:** copilot agent puede invocar `actions/` patrón growth igual que brand/offer.

### H3 — 4-tier loading sigue privado growth (sin ROI lift a shared)
**Test:** ningún otro studio consume 4-tier post PI-9.

### H4 — Arch fitness adapter mode (no paridad estricta) bloquea regresión
**Test:** test-studio-structure-parity verifica growth tiene folders correctas + factory mode "stage-dispatcher" registrado.

## Sprints + PRs plan (macro, refinar post PI-8 ship)

### Sprint S1-stage-channel-registry (TBD)

**Scope (preliminary):** Stage registry SSoT + Channel registry SSoT + Dashboard registry SSoT + StageDispatcher + ChannelDispatcher + route migration de 5 stages + 5 channel dashboards a `pages/`.

**PR plan preliminary:**

| PR | Scope | Surface | Builder | Auditor |
|---|---|---|---|---|
| PR-1-stage-channel-dashboard-registry | SSoT registries + dispatchers + route migration (sin tocar `metrics-dashboard/components/`) | Frontend FE | `nicolify-frontend` | `nicolify-frontend-auditor` |

### Sprint S2-actions-schemas-tiers-fitness (TBD)

**Scope (preliminary):** `actions/` scaffold + `schemas/` scaffold + 4-tier hooks rename `tiers/` + arch fitness extension adapter mode + parity test growth-mode.

**PR plan preliminary:**

| PR | Scope | Surface | Builder | Auditor |
|---|---|---|---|---|
| PR-2-actions-schemas-scaffold | `actions/` + `schemas/` con placeholder + arch test exigir existencia | Frontend FE | `nicolify-frontend` | `nicolify-frontend-auditor` |
| PR-3-tiers-rename-fitness-extension | 4-tier hooks rename `tiers/{0,1,2,3}-*.ts` + arch fitness adapter mode + ratchet | Frontend FE | `nicolify-frontend` | `nicolify-frontend-auditor` |

**Decisión sprint sizing:** sprint S1 self-contained (SSoT registries son foundation). S2 puede correr en paralelo si PR-2 y PR-3 son independientes.

## Anti-patterns explícitos PI-9 (Chris-confirmados, heredados PI-8)

PI-9 NO debe:
1. **Reescribir `metrics-dashboard/components/`** (177 archivos = masa PI-10 territorio)
2. **Tocar visual / styling** (PI-10 owns)
3. **Lift 4-tier loading a `shared/`** (sin segundo consumer)
4. **Forzar paridad 1:1 con brand/offer** (factory propia OK + folders comunes)
5. **Hardcodear "5 stages"** anywhere — solo via registry
6. **Crear schemas reales** en `schemas/` (placeholder vacío + arch test que solo exige existencia — schemas reales emergen PI-10 forms)
7. **Decidir drawer-vs-route** en routing layer (PI-10 owns)
8. **Tocar `components/strategy-canvas/`** (PI-10 territorio)

## Riesgos

| Riesgo | Mitigación |
|---|---|
| StageDispatcher/ChannelDispatcher rompe routing existente | Tests E2E Playwright per stage + smoke Chris-mediated |
| Registry SSoT pattern crea complejidad innecesaria si no escala | Validar con 1 canal ficticio "test-channel-x" agregar requiere ≤3 archivos |
| Refactor toca masa 177 components implicit | Anti-pattern enforcement: NO tocar `metrics-dashboard/components/` durante migración |
| arch fitness extension breakage cross-studio (brand/offer afectados por adapter mode change) | Tests cross-studio + smoke regresión |
| 4-tier hooks rename rompe consumers existentes | Search-and-replace cuidadoso + tests cobertura mejorar |
| PI-9 crece scope que termina haciendo UX work | Strict gate auditor anti-pattern enforcement |

## Out of scope (DEFERRED a PI-10)

- Visual redesign components
- Decisión drawer-vs-nested-route consolidation
- UX flow homologation con brand/offer
- Component rewrite UX (cards, layouts nuevos)
- Dashboard styling refresh

## Aceptación PI

- [ ] PI-8 shipped + PI-8 retro escrita (precondición)
- [ ] PR-1 stage/channel/dashboard registry shipped PASS
- [ ] PR-2 actions/+schemas/ scaffold shipped PASS
- [ ] PR-3 tiers/+fitness extension shipped PASS
- [ ] Test "agregar canal ficticio test-channel-x requiere ≤3 archivos" verde
- [ ] Arch fitness `test-studio-structure-parity` adapter mode growth-mode green
- [ ] Cero regresión funcional Growth Studio (4-tier + currency + multi-stage + Chris smoke)
- [ ] `current-state/analytics.md` lineage append (capacidad "growth-studio architecture homologated")
- [ ] retro.md PI-9 + handoff a PI-10
- [ ] PI-9 archive

## Cross-references

- Predecesor: `pis/active/PI-8-growth-studio-stability/PI.md`
- Sucesor: `pis/active/PI-10-growth-studio-ux-homologation/PI.md`
- Architect tech sanity check 2026-05-01 — verificó growth ≠ brand/offer 1:1 (5 stages, 4-tier, channel-specific)
- Anti-duplication rule: `.claude/rules/anti-duplication.md`
- FSD rule: `.claude/rules/frontend-fsd.md`
- Brand reference (folder pattern): `frontend/src/features/brand-studio/{pages,actions,schemas}/`
- Offer reference: `frontend/src/features/offer-studio/{pages,actions,schemas}/`
- Arch fitness existing: `frontend/src/__tests__/architecture/test-studio-structure-parity.test.ts:29` (extender con growth-mode)

## Plan de refine post PI-8 ship

Cuando PI-8 cierre:
1. PM lee handoff PI-8 → PI-9 (anti-patterns confirmed + architect findings)
2. PM spawn `nicolify-architect` para producir CONTRACT.md detallado primer PR (registries + dispatchers)
3. PM materializa PR-folder PR-1 con CONTRACT + prompts pre-cocidos
4. Builder spawn (Sonnet) + auto-audit loop
