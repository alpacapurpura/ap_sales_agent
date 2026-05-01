# Retro — PI-8-growth-studio-stability

| Campo | Valor |
|---|---|
| Cierre | 2026-05-01 |
| Duración | 1 día (mismo día apertura + cierre) |
| Sprints | 1 (S1-drawer-bowtie-hotfix) |
| PRs | 1 (PR-1-drawer-bowtie-fixes) |
| Esfuerzo real | S (3 archivos editados + 2 nuevos test files) |
| Auditor iters | 1 (PASS primer iter) |

## Outcome vs plan

| Hipótesis | Resultado |
|---|---|
| H1 — 3 fixes mecánicos resuelven bug sin refactor | ✅ CONFIRMADA. Builder ejecutó 3 fixes exactos per architect brief. Cero desvío scope. |
| H2 — PR-1 single sprint cohesivo < 1 día | ✅ CONFIRMADA. Builder → gate-runner → auditor → PASS en 1 iter. Tiempo total: < 4h |

## Qué salió bien

1. **Architect brief previo (PI-7)** eliminó fase architect en PI-8 → saving 1 ejecución Chris. Pattern reutilizable: arch brief en PI padre desbloquea mini-PI hija sin architect.
2. **Auto-loop builder→auditor en 1 iter** — scope S cohesivo = auditor no encontró fallos.
3. **Ratchet como instrumento de deuda declarada** — 6 KNOWN_VIOLATIONS nombradas explícitamente. PI-9 tiene lista clara.
4. **Blast radius controlado** — `max-md:` solo mobile. Desktop z-[45] intacto. Brand/Offer Studios cero regresión.
5. **Mini-PI como formato** — PI-hotfix single sprint/single PR es el formato correcto para 3 fixes localizados. No encolar en PI grande.

## Qué mejorar

1. **PR.md spec paths deben verificarse con `find`** — builder encontró discrepancia (`features/copilot/hooks/` vs `hooks/` raíz). Arch brief o PM deben verificar paths antes redactar spec.
2. **Smoke Chris-mediated pendiente** — PR S-sized no obliga chrome-devtools-verify, pero smoke manual sigue siendo necesario. Documentar como action item explícito en handoff.

## Deuda abierta (handoff PI-9)

| Item | Destino |
|---|---|
| 6 KNOWN_VIOLATIONS ratchet (channel dashboards portals) | PI-9 reduce shrink-only |
| CampaignTag Vitest fails (2) | PR separado closer-studio |
| Storybook ESLint parserOptions | PR separado config |
| Clerk npm audit | PR separado dep upgrade |
| Smoke manual Chris post-merge | Chris-mediated |

## Desbloqueos

PI-9-growth-studio-architecture → DESBLOQUEADO.

## Decisiones clave

| ID | Decisión | Impacto |
|---|---|---|
| D1 | Panel-up (z-[60]) vs copilot-down | Menor blast radius; alternativa C rompía backdrop |
| D2 | Tradeoff Dialog z-50 debajo panel mobile | Aceptado. Dialog nested en DetailPanel mobile = caso raro |
| D3 | Ratchet inicial 6 KNOWN_VIOLATIONS | Deuda declarada explícitamente; PI-9 la reduce |
