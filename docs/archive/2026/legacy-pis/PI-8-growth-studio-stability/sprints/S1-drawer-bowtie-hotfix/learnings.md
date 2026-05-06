# Learnings — S1-drawer-bowtie-hotfix

> Sprint cerrado 2026-05-01. Único PR: PR-1 shipped (PASS auditor Opus iter 1).

## Técnicos

| # | Learning | Aplicación futura |
|---|---|---|
| L1 | `max-md:` Tailwind prefix resuelve z-index ladder mobile-specific sin tocar desktop — minimiza blast radius cross-studio | Aplicar en cualquier fix z-index mobile en FE |
| L2 | `useCopilotOffset` hook ya existía en `@/hooks/` (no en `features/copilot/hooks/` como decía PR.md) — PR.md spec path puede diferir del real | Arch brief debe verificar paths con `find` antes redactar spec |
| L3 | 6 archivos `createPortal/fixed` en growth-studio NO consumen offset — deuda real, no bug latente. Ratchet con KNOWN_VIOLATIONS es el mecanismo correcto para deferirlo a PI-9/PI-10 | Ratchet allowlist en arch fitness = deuda declarada visible |
| L4 | Builder sin Clerk session no puede hacer smoke E2E — compensatory coverage (visual regression tests + ratchet) es aceptable para PR S-sized | PR S-sized: smoke Chris-mediated es la pauta, no deuda |

## Proceso

| # | Learning | Aplicación futura |
|---|---|---|
| P1 | PI-8 single sprint / single PR shipped en 1 iter auditor — PI mini-hotfix es el formato correcto para bugs mecánicos localizados (3 fixes, no refactor) | Bug localizado ≤3 archivos → PI mini-hotfix, no encolar en PI grande |
| P2 | Architect (PI-7 arch brief) permitió que builder arranque directo sin fase architect en PR S — saving 1 ejecución Chris | Bugs con architect brief previo en PI padre → skip architect fase en PI hija |
| P3 | Gate-runner Haiku + auditor Opus auto-loop en 1 iter = eficiencia máxima | Auto-loop builder→auditor funciona bien en scope pequeño y cohesivo |
