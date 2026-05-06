# PR-1-drawer-bowtie-fixes

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-1-drawer-bowtie-fixes |
| Sprint padre | S1-drawer-bowtie-hotfix |
| PI padre | PI-8-growth-studio-stability |
| Estado | shipped |
| Tipo | bug (FE-only, layout) |
| Esfuerzo | S |
| Owner PM | /pm |
| Claimed by session | — |

## Problema (user-facing)

User clickea ChannelRow en Growth Studio → drawer derecho abre y la visualización rompe:
- **Mobile:** copilot ocluye drawer (z-index ladder mal).
- **Desktop:** bowtie superior NO respeta copilot offset → distorsionado.
- **Edge cases viewport:** breakpoints angostos rompen layout.

## Outcome esperado

Click ChannelRow en cualquier stage / cualquier viewport / con copilot abierto → drawer abre correctamente, bowtie respeta espacio copilot, sin solapamiento, sin distorsión. Cero regresión funcional.

## Walking skeleton (mínimo viable cohesivo)

3 fixes mecánicos en archivos existentes + tests regresión:

1. **z-index ladder fix** — `CopilotSidebar.tsx:125` mobile `z-50` vs `DetailPanel.tsx:54` panel `z-[45]` → bumpear panel mobile a `z-[60]` (panel = "active focus" del user supera copilot).
2. **Bowtie respeta copilot offset** — `StageSummaryRow.tsx:55` (`min-w-[800px]` clip-path) wrappear parent con `useCopilotOffset()` hook + `paddingRight: copilotWidth` style. Localized.
3. **Viewport edge cases** — revisar transitions copilot collapsed↔expanded + breakpoints sm/md/lg/xl. Asegurar `useCopilotOffset` consumed en TODOS fixed/portal elements de growth-studio.

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A** — 3 fixes mecánicos localizados | <1 día, blast radius bajo, no toca componentes visuales, fix verificado architect file:line | Deja smell semántico dual UX (drawer + nested route) sin resolver | **ELEGIDA** |
| B — Refactor estructural antes del fix | Resuelve smell semántico cleanly | Bloquea fix bug latente 1-2 semanas, scope creep, masa 177 components | descartada — bug urge ship rápido, smell decisión PI-10 |
| C — Reescribir `DetailPanel` para auto-handle copilot offset | Reusable cross-studios | Toca Brand+Offer (riesgo regresión cross-studio), scope creep | descartada — `useCopilotOffset` ya existe + ya wired en `DetailPanel` |

## Validación técnica preliminar (Technical Sanity Check)

> PM spawned `nicolify-architect` (Opus, read-only) durante discovery 2026-05-01. Architect verificó código directo. Brief sintético abajo. CONTRACT formal NO requerido (architect not mandatory para FE bug fix sin shared/ touch).

**Architect findings file:line verificados:**

- `frontend/src/components/ui/detail-panel.tsx:54` → `DetailPanel` ya consume `useCopilotOffset()` correctamente desktop (`right: ${copilotWidth}px`, `z-[45]` panel + overlay). Mobile gap: panel `z-[45]` vs copilot mobile `z-50` → copilot ocluye panel mobile.
- `frontend/src/features/copilot/components/CopilotSidebar.tsx:125` → desktop usa flex-col widths state-driven (NO fixed); mobile salta a `fixed inset-y-0 right-0 z-50`. Mobile-only conflict.
- `frontend/src/features/growth-studio/components/metrics-dashboard/stage-widgets/StageSummaryRow.tsx:55` → bowtie `min-w-[800px]` clip-path NO respeta `right: copilotWidth` offset. Reflow distorsiona viewports angostos con copilot expanded.
- `frontend/src/features/growth-studio/components/metrics-dashboard/context/GrowthStudioContext.tsx:270` → `handleChannelClick` abre overlay drawer (`?channel=` query param) Y existe ALSO ruta nested `[stage]/[channelSlug]/page.tsx`. Dual UX path → smell semántico, NO blocker bug, **decisión PI-10 NO toca PI-8**.

**Modules afectados:**
- `frontend/src/features/growth-studio/components/metrics-dashboard/stage-widgets/StageSummaryRow.tsx`
- `frontend/src/components/ui/detail-panel.tsx`
- `frontend/src/features/copilot/components/CopilotSidebar.tsx`
- `frontend/src/features/growth-studio/__tests__/` (tests regresión nuevos)

**Blockers conocidos:** ninguno. Architect confirmó fixes independientes del refactor estructural PI-9.

**Tiempo estimado:** <1 día implement + tests + auto-audit loop.

## Existing systems audit (MANDATORY)

> Builder ejecuta este bloque ANTES de cualquier `Write` que crea archivo nuevo. Para PR-1 espera CERO archivos nuevos salvo tests regresión + arch fitness.

### 1. Grep cross-codebase obligatorio (output completo embebido en IMPL-LOG)

Ejecutar y pegar SALIDA REAL en IMPL-LOG.md "Step 0 grep findings":

```bash
# 1a. Verificar useCopilotOffset existe + ubicación canónica
find /home/chris/AISALESHT/frontend/src -name "use-copilot-offset*" 2>/dev/null
grep -rn "useCopilotOffset\|copilotWidth" /home/chris/AISALESHT/frontend/src 2>/dev/null

# 1b. Verificar DetailPanel consumers (cross-studio impact assessment)
grep -rn "DetailPanel\|detail-panel" /home/chris/AISALESHT/frontend/src/features/ /home/chris/AISALESHT/frontend/src/components/ 2>/dev/null

# 1c. Verificar z-index existing baseline (no introducir nueva escalera ad-hoc)
grep -rn "z-\[4[0-9]\]\|z-\[5[0-9]\]\|z-\[6[0-9]\]\|z-50\|z-40" /home/chris/AISALESHT/frontend/src/features/copilot/ /home/chris/AISALESHT/frontend/src/components/ui/ 2>/dev/null

# 1d. Verificar StageSummaryRow consumers + parent wrappers
grep -rn "StageSummaryRow" /home/chris/AISALESHT/frontend/src/features/growth-studio/ 2>/dev/null
```

### 2. Inventario existing patterns

| Pattern existente | Path:line | Visible para PR-1 | Status |
|---|---|---|---|
| `useCopilotOffset` hook | `frontend/src/features/copilot/hooks/use-copilot-offset.ts` (verify path during build) | sí | exists, USE-AS-IS extend consumers |
| `DetailPanel` shared UI | `frontend/src/components/ui/detail-panel.tsx:54` | sí cross-studio | exists, EDIT z-index escalera |
| `CopilotSidebar` mobile drawer | `frontend/src/features/copilot/components/CopilotSidebar.tsx:125` | sí | exists, EDIT z-index si decisión inversa |
| `StageSummaryRow` bowtie | `frontend/src/features/growth-studio/components/metrics-dashboard/stage-widgets/StageSummaryRow.tsx:55` | sí | exists, WRAP parent con `useCopilotOffset` |

### 3. Decisión explícita por sistema (EXTEND / LIFT / NEW)

| Sistema | Decisión | Justificación |
|---|---|---|
| Z-index ladder | **EDIT existing values** (NO new scale) | Evitar fragmentar z-index ladder. Bumpear panel mobile a `z-[60]` o lower copilot a `z-[40]` decidido por builder vía smoke test (cuál rompe menos consumers). Documentar elección IMPL-LOG. |
| `useCopilotOffset` adoption | **EXTEND consumers** | Hook ya existe en `features/copilot/hooks/`. Solo agregar consumers (`StageSummaryRow` parent wrapper). NO reescribir hook. |
| Tests regresión visual | **NEW** (justificado: no existen tests para esta interacción cross-component) | Crear `__tests__/visual-regression-drawer-bowtie.test.tsx` en growth-studio. Sin equivalente cross-codebase. |
| Arch fitness `useCopilotOffset` adoption | **NEW** (justificado: invariante PI-8 protege PI-9/PI-10 contra regresión) | Crear `__tests__/architecture/test-growth-studio-copilot-offset.test.ts`. Sin equivalente. |

### 4. NEW justificación

Tests regresión visual + arch fitness ratchet son únicos a esta interacción (Growth ChannelRow click → DetailPanel + StageSummaryRow + CopilotSidebar coexisting). No hay test cross-component equivalente en codebase. Justificado.

### 5. Auditor enforcement

Auditor Cat 12 (mirror detection): builder NO crea archivos `useCopilotOffset.v2.ts` ni `DetailPanel.tsx` paralelo. Auditor verifica diff edita archivos existentes únicamente.

## Decisiones diferidas (explícitas)

- **Decisión drawer-vs-route consolidation** → PI-10 (decisión UX)
- **Stage/channel/dashboard registry SSoT** → PI-9 (decisión arquitectónica)
- **Visual redesign components** → PI-10
- **Decisión z-index final ladder global**: builder decide entre `z-[60]` panel mobile vs `z-[40]` copilot mobile vía análisis consumers. Documentar IMPL-LOG.

## Out of scope

- Refactor estructural growth-studio (`pages/`, `actions/`, `schemas/`) — PI-9
- Tocar `metrics-dashboard/components/` (177 archivos) — PI-9 + PI-10
- Tocar `components/strategy-canvas/` — PI-10
- Decisión drawer-vs-nested-route — PI-10
- Reescribir `useCopilotOffset` — solo extend consumers
- Cambios visuales (colores, espaciados, tipografía, layout components) — PI-10
- Hardcodear "5 stages" en code path (PI-9 owns registry)

## Copilot-first checklist

- [x] **¿Operable conversacional desde copilot?** NO directamente — es bug fix layout, no capacidad nueva. Copilot sigue accesible toda Growth Studio post-fix (sin regresión).
- [ ] **Tools nuevos requeridos:** ninguno
- [ ] **Cards/UI nueva:** ninguna
- [x] **Razón NO copilot-operable:** layout fix invisible para copilot conversacional. User no "habla" con bug, el bug se resuelve transparente.

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt | Entregable |
|---|---|---|---|
| Pre-design | — (NO architect, sanity check ya hecho discovery) | — | — |
| UX | — (NO redesign, PI-10 owns) | — | — |
| Implementation | `nicolify-frontend` (Sonnet) | `prompts/02-builder-start.md` | code + tests + IMPL-LOG.md |
| Live verification | `chrome-devtools-verify` skill | builder invoca durante implement | smoke browser mobile + desktop |
| Audit | `nicolify-frontend-auditor` (Opus) — auto-spawned by builder | `prompts/03-auditor-start.md` | REVIEW.md |
| Cierre | `/pm` | `prompts/04-pm-close.md` | RESULT.md + current-state/analytics.md update |

**Skills obligatorios builder antes tocar código:**
- `frontend-expert` — FSD-Lite + Server/Client correctness
- `tessl__react-patterns` — accesibilidad + hooks correctness
- `chrome-devtools-verify` — live smoke mandatorio post-fix

## Surface impactada

| Tipo | Path | Cambio |
|---|---|---|
| FE component | `frontend/src/components/ui/detail-panel.tsx` | EDIT z-index escalera (panel mobile bump) |
| FE component | `frontend/src/features/copilot/components/CopilotSidebar.tsx` | POTENCIAL EDIT z-index si decisión inversa (lower copilot mobile) — builder decide |
| FE component | `frontend/src/features/growth-studio/components/metrics-dashboard/stage-widgets/StageSummaryRow.tsx` | WRAP parent con `useCopilotOffset()` + `paddingRight` |
| FE tests | `frontend/src/features/growth-studio/__tests__/visual-regression-drawer-bowtie.test.tsx` | NEW (regresión visual breakpoints) |
| FE arch fitness | `frontend/src/__tests__/architecture/test-growth-studio-copilot-offset.test.ts` | NEW (ratchet shrink-only — todos fixed/portal en growth-studio consumen `useCopilotOffset`) |
| current-state/ | `current-state/analytics.md` | append capability lineage PR-1 |

## Tests requeridos (TDD)

- `__tests__/visual-regression-drawer-bowtie.test.tsx` — RED ANTES fix:
  - Mobile (≤768px) drawer abre + copilot abierto → panel z-index > copilot
  - Desktop (≥1024px) bowtie respeta `right: copilotWidth` offset cuando copilot expanded
  - Breakpoints transition (768↔1024) sin reflow distorsionado
  - Cero regresión: 4-tier loading + currency display + stage navigation post-fix
- `__tests__/architecture/test-growth-studio-copilot-offset.test.ts` — arch fitness:
  - Scan `growth-studio/**` por `className="fixed"` o `createPortal`
  - Cada match → exigir import `useCopilotOffset` o uso de `DetailPanel` (que ya consume)
  - Allowlist shrink-only ratchet
- Smoke regresión Brand+Offer Studios:
  - `DetailPanel` consumers en Brand/Offer NO afectados por z-index bump
  - Brand authority panel + Offer ladder hint panel abren correctos
- `chrome-devtools-verify` Chris-mediated post-fix:
  - 5 stages × 2 viewports = 10 caminos
  - Drawer + bowtie + copilot coexisten sin solapamiento

## Aceptación

- [ ] Tests verdes (Vitest + arch fitness)
- [ ] Lint/tsc verdes
- [ ] `IMPL-LOG.md` completo con grep findings + EDIT decisions
- [ ] `gate-output.json` (Haiku) overall PASS
- [ ] `REVIEW.md` Opus auditor verdict PASS
- [ ] Chrome devtools smoke Chris-mediated 5 stages × mobile + desktop verde
- [ ] `RESULT.md` escrito por PM
- [ ] `current-state/analytics.md` lineage append
- [ ] Decisiones registradas en `pis/active/PI-8-growth-studio-stability/decisions.md`

## Riesgos

| Riesgo | Mitigación |
|---|---|
| z-index bump rompe Brand/Offer DetailPanel consumers | Grep consumers + smoke regresión Brand/Offer panels post-fix |
| `useCopilotOffset` wrap parent rompe StageSummaryRow clip-path | Tests responsive + chrome-devtools smoke breakpoints |
| Arch fitness ratchet false positives en archivos test/legacy | Allowlist initial conservadora + shrink-only |
| 3 fixes esconden 4to bug | Chris smoke profundo navegación toda Growth Studio post-fix |
| Decisión z-index final (panel up vs copilot down) tiene tradeoff oculto | Builder decide vía análisis consumers + documenta IMPL-LOG |

## Próximo paso (Track B)

Builder kick-off: ejecutar `prompts/02-builder-start.md`.
