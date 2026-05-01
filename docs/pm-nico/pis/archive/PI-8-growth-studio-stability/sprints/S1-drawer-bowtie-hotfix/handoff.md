# Handoff — S1-drawer-bowtie-hotfix → PI-9

> Sprint cerrado. No hay sprint siguiente en PI-8. Handoff directo al próximo PI.

## Estado al cerrar

| Ítem | Estado |
|---|---|
| PR-1-drawer-bowtie-fixes | shipped (auditor PASS, commit `00bf51f6`) |
| Smoke Chris-mediated | PENDIENTE (5 stages × mobile + desktop) |
| PI-8 | cerrado → archive |

## Deuda explícita (no resuelta en PI-8)

| Item | Owner | Destino |
|---|---|---|
| 6 KNOWN_VIOLATIONS ratchet (channel dashboards portals sin useCopilotOffset) | PI-9 builder | PI-9 reduce allowlist al homologar metrics-dashboard/components/ |
| CampaignTag Vitest fails (2, route rename ñ→n PI-1) | PR separado | closer-studio maintenance |
| Storybook ESLint parserOptions (2 errors) | PR separado | config maintenance |
| Clerk npm audit (high+critical) | PR separado | dep upgrade |

## Próximo PI desbloqueado

**PI-9-growth-studio-architecture**: bloqueado por PI-8 ship → ahora desbloqueado.

Scope PI-9: registries SSoT + StageDispatcher + actions/schemas/tiers homologation. Refactor estructural que PI-8 dejó fuera explícitamente (metrics-dashboard/components/, strategy-canvas/).

Agente recomendado: `nicolify-architect` Opus → CONTRACT.md → `nicolify-frontend` builder.

## Invariante preservada

Arch fitness ratchet `test-growth-studio-copilot-offset.test.ts` activo. PI-9 builder debe:
1. Shrink `KNOWN_VIOLATIONS` conforme toca los 6 archivos allowlistados
2. Verificar ratchet sigue GREEN al final de cada PR PI-9
