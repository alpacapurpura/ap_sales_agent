# RESULT — PR-1-drawer-bowtie-fixes

> Owner: `/pm`. Cierre del loop.

## Meta cierre

| Campo | Valor |
|---|---|
| Estado final | shipped |
| Fecha cierre | 2026-05-01 |
| Commits | `00bf51f6` (fix growth-studio) · `3e37f05f` (gate-output docs) |
| Branch | development |
| Auditor verdict | PASS (nicolify-frontend-auditor Opus iter 1) |
| Gate output | `any_fail: false` |

## Outcome real vs esperado

| Aspecto | Esperado | Real | Delta |
|---|---|---|---|
| DetailPanel mobile ocluye copilot drawer | `DetailPanel z-[45]` tapado por `CopilotSidebar max-md:z-50` | `DetailPanel max-md:z-[60]` — panel arriba copilot mobile | ✅ |
| Bowtie respeta copilot width | `StageSummaryRow` ignora copilot → reflow visible | `paddingRight: copilotWidth` via `useCopilotOffset` memoized | ✅ |
| Arch fitness ratchet | Sin invariante — violation silenciosa futura posible | Nueva gate `test-growth-studio-copilot-offset.test.ts` — 6 KNOWN_VIOLATIONS allowlist PI-9/PI-10 territory | ✅ |
| Regresión cross-studio | Brand/Offer DetailPanel afectado | Cero regresión — bump `max-md:` solo (desktop z-[45] intacto) | ✅ |
| Smoke Chris-mediated | Verificación manual post-merge | **PENDIENTE** (PR S-sized, compensatory coverage: 7 tests visual regression + ratchet) | ⚠️ diferido |

Veredicto: ✅ cumplido (smoke manual diferido a Chris post-merge)

## Surface entregada

| Tipo | Path | Cambio |
|---|---|---|
| FE component | `frontend/src/components/ui/detail-panel.tsx` | `max-md:z-[60]` backdrop + panel (prev `z-[45]`) |
| FE component | `frontend/src/features/growth-studio/components/metrics-dashboard/stage-widgets/StageSummaryRow.tsx` | `useCopilotOffset` + `paddingRight` memoized outer container |
| FE test (NEW) | `frontend/src/features/growth-studio/__tests__/visual-regression-drawer-bowtie.test.tsx` | 6 tests — z-index ladder + viewport breakpoints |
| FE arch fitness (NEW) | `frontend/src/__tests__/architecture/test-growth-studio-copilot-offset.test.ts` | Ratchet shrink-only — 6 KNOWN_VIOLATIONS (PI-9/PI-10 territory) |

**NO tocado:** `CopilotSidebar.tsx` (no necesario tras z-[60] panel-up), `metrics-dashboard/components/` (PI-10), `strategy-canvas/` (PI-10).

## Capacidades corregidas (lineage)

```md
### Cap: Growth Studio — drawer/bowtie layout correcto multi-viewport
- Fix: PR-1 (PI-8, S1-drawer-bowtie-hotfix, commit 00bf51f6, 2026-05-01)
- Estado: live
- Detalle: DetailPanel mobile z-[60] sobre copilot z-50. StageSummaryRow respeta copilotWidth offset.
  Arch fitness ratchet (6 KNOWN_VIOLATIONS PI-9/PI-10 territory, shrink-only).
- Operable copilot: no (layout-only)
```

## Decisiones implementación

| ID | Decisión | Razón |
|---|---|---|
| D1 | Panel-up (`max-md:z-[60]`) vs copilot-down | Lower copilot rompe backdrop z-40; panel-up solo mobile = gap claro 10 unidades |
| D2 | Tradeoff `<Dialog>` z-50 debajo panel mobile | Dialogs nested en DetailPanel mobile son raros; DetailPanel ES la modal del flow. Escalate ladder si surge |
| D3 | `useMemo` para `outerStyle` | Evita nuevo `react-perf/jsx-no-new-object-as-prop` warning |
| D4 | Ratchet 6 KNOWN_VIOLATIONS allowlist | 5 channel dashboards + ChannelConnectionModal usan `createPortal/fixed` sin offset — PI-9/PI-10 territory, no tocar en PI-8 |

## Deuda técnica generada / heredada

| Item | Origen | Destino |
|---|---|---|
| 6 KNOWN_VIOLATIONS ratchet (channel dashboards portals) | Heredada PI-9/PI-10 territory | PI-9 reduce allowlist al homologar metrics-dashboard/components/ |
| 2 PRE-EXISTING CampaignTag Vitest fails | PI-1 route rename `ñ→n` sin fixture update | PR separado closer-studio fix |
| 2 storybook ESLint parserOptions errors | Pre-existing config | PR separado config |
| Clerk npm audit (high+critical) | Pre-existing deps | PR separado dep upgrade |
| Chris smoke manual | PR S-sized — builder sin Clerk session | Chris-mediated post-merge (5 stages × mobile + desktop) |

## Update obligatorios

- [x] `current-state/analytics.md` actualizado con fix lineage
- [x] `decisions.md` PI-8 appendeado
- [x] Sprint `learnings.md` llenado
- [x] `handoff.md` S1 llenado (única PR del sprint → sprint cerrado)
- [x] PI-8 `retro.md` escrito → mover a archive

## Próximo paso PM

PI-8 cerrado. Próximo en roadmap: **PI-9-growth-studio-architecture** (bloqueado por PI-8 ship → ahora desbloqueado).

---

PR-1 **shipped**. PI-8 **cerrado**. Loop completo.
