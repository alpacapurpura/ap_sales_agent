# PI-8-growth-studio-stability

## Meta

| Campo | Valor |
|---|---|
| PI ID | PI-8-growth-studio-stability |
| Inicio | 2026-05-01 |
| Estado | active |
| Tipo | mini-PI hotfix (FE-only, layout) |
| Owner PM | /pm |
| Origen | Chris reporta UX bug latente Growth Studio + tech sanity check architect 2026-05-01 |
| Sucesor | PI-9-growth-studio-architecture (estructura post-refactor) → PI-10-growth-studio-ux-homologation (rediseño UX) |

## Outcome esperado (user-facing)

**Growth Studio 100% navegable sin errores visuales en cualquier viewport (mobile + desktop) con copilot drawer abierto.**

Métrica única éxito: Chris navega Growth Studio → clickea ChannelRow en cada stage → drawer abre correctamente sin solapar copilot ni distorsionar bowtie superior. Mobile + desktop. Sin pérdida de funcionalidad existente.

## Problema (user-facing)

User clickea ChannelRow → drawer derecho (`ChannelDetailSidebar`) abre y la visualización rompe:
- **Mobile:** copilot mobile drawer (`z-50`) ocluye `DetailPanel` (`z-[45]`).
- **Desktop:** bowtie superior (`StageSummaryRow min-w-[800px]`) NO respeta `right: copilotWidth` offset → reflow distorsiona.
- **Edge cases viewport:** breakpoints angostos con copilot expanded rompen layout.

Architect verificó código directo (PI-7-arch-brief 2026-05-01) — **3 fixes mecánicos localizados, NO requiere refactor estructural**. Refactor estructural va en PI-9.

## Outcome alcanzado vs hipótesis

### H1 — 3 fixes mecánicos resuelven bug sin tocar componentes visuales
**Test:** Chris smoke navegación post-fix → drawer + bowtie correctos viewport S/M/L/XL en mobile + desktop. Cero pérdida funcionalidad existente.

### H2 — PR-1 single sprint single PR cohesivo (<1 día) ship rápido valor user
**Test:** PR-1 builder + auditor PASS en 1-2 ejecuciones Chris.

## Sprints + PRs plan

### Sprint S1-drawer-bowtie-hotfix (single sprint, single PR cohesivo)

**Scope:** 3 fixes layout localizados + tests regresión visual + arch fitness ratchet `useCopilotOffset` adopción.

**PR plan:**

| PR | Scope | Surface | Builder | Auditor |
|---|---|---|---|---|
| **PR-1-drawer-bowtie-fixes** | (1) z-index ladder fix mobile copilot vs panel; (2) bowtie wrap con `useCopilotOffset()`; (3) viewport edge cases breakpoints | Frontend FE-only (`features/growth-studio/components/metrics-dashboard/stage-widgets/` + `components/ui/detail-panel.tsx` + `features/copilot/components/CopilotSidebar.tsx`) | `nicolify-frontend` (Sonnet) | `nicolify-frontend-auditor` (Opus) |

**Decisión PR sizing:** 1 PR cohesivo porque:
- 3 fixes son interdependientes visualmente (validar z-ladder + offset + responsive juntos)
- Smoke test único Chris-mediated valida los 3
- Architect NO mandatory (no toca shared/, no crea archivos nuevos cross-module — solo edita 3 archivos existentes)
- Pre-flight context-builder NO mandatory (PR esfuerzo S, overhead spawn > savings)

## Anti-patterns explícitos PI-8 (architect-validated, Chris-confirmados)

PI-8 NO debe:
1. **Reescribir `metrics-dashboard/components/`** (177 archivos = masa PI-10 territorio)
2. **Consolidar dual UX path** drawer-overlay + nested-route (decisión PI-10)
3. **Hardcodear "5 stages" en code path** (driven by `STAGE_TO_SLUG` registry — PI-9 owns)
4. **Crear schemas en `schemas/`** (carpeta no existe yet — PI-9 owns)
5. **Promover 4-tier loading a `shared/`** (sin segundo consumer — PI-9 evalúa)
6. **Tocar `components/strategy-canvas/`** (PI-10 territorio)
7. **Asumir que `ChannelDetailSidebar` desaparece** (PI-10 decide drawer-vs-route)
8. **NO new files** salvo tests regresión visual (`__tests__/`)
9. **NO refactor `useCopilotOffset`** (extend uso, no rewrite)

## Riesgos

| Riesgo | Mitigación |
|---|---|
| z-index bump rompe otros consumers de `DetailPanel` (Brand/Offer Studios usan también) | Grep cross-codebase consumers + smoke regresión brand+offer post-fix |
| `useCopilotOffset` wrap parent rompe mobile layout existente | Test responsive viewport breakpoints + Chris smoke mobile |
| Edge case copilot collapsed vs expanded width transitions | Tests CSS transitions + chrome-devtools-verify mobile + desktop |
| 3 fixes mecánicos esconden 4to fix necesario | Chris smoke profundo navegación toda Growth Studio post-fix |

## Out of scope (DEFERRED a PI-9 + PI-10)

### Diferido a PI-9 (architecture)
- Estructura `pages/StageDispatcher` + `pages/channels/ChannelDispatcher`
- `actions/` scaffold + `schemas/` scaffold
- 4-tier hooks rename a `tiers/`
- Stage/channel registry SSoT (open-closed para agregar canales sin refactor)
- Arch fitness adapter mode + parity test extension

### Diferido a PI-10 (UX redesign)
- Decisión drawer-vs-route final
- Visual redesign components
- Flow consistency con brand/offer
- Dashboard layout refresh

## Aceptación PI

- [ ] PR-1 shipped con verdict PASS auditor
- [ ] Chris smoke real Growth Studio:
  - [ ] Drawer abre correctamente click ChannelRow en 5 stages
  - [ ] Bowtie superior NO se distorsiona con copilot expanded
  - [ ] Mobile (≤768px) sin solapamiento copilot/drawer
  - [ ] Desktop (≥1024px) bowtie respeta `right: copilotWidth`
  - [ ] Cero regresión funcional (4-tier loading + currency + multi-stage navigation)
- [ ] Tests regresión visual viewport breakpoints (sm/md/lg/xl) verdes
- [ ] Arch fitness ratchet: `useCopilotOffset` adoption en growth-studio fixed/portal elements
- [ ] `current-state/analytics.md` lineage append PR-1
- [ ] retro.md PI-8 + handoff a PI-9
- [ ] PI-8 archive

## Cross-references

- Architect tech sanity check: este chat 2026-05-01 (architect agent run, paths verificados file:line)
- Sucesor architecture: `pis/active/PI-9-growth-studio-architecture/PI.md`
- Sucesor UX: `pis/active/PI-10-growth-studio-ux-homologation/PI.md`
- Anti-duplication rule: `.claude/rules/anti-duplication.md`
- FSD rule: `.claude/rules/frontend-fsd.md`
- Chrome devtools verify skill: smoke browser-based mandatorio post-fix
