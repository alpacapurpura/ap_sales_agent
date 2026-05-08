# Growth Studio — FSD-Lite Feature

Módulo de analítica y estrategia de crecimiento.

## Estructura de carpetas (FSD-Lite)

```
growth-studio/
├── actions/        # Copilot actions (Pendiente — Story 2B)
├── api/            # Clientes HTTP y mappers
├── components/     # Componentes UI (bowtie, metrics-dashboard, strategy-canvas)
├── hooks/          # React hooks de dominio
├── lib/
│   └── registries/ # SSoT: stage-registry, channel-registry, dashboard-registry
├── pages/
│   ├── sections/   # Páginas por etapa (server components thin delegates)
│   ├── tiers/      # 4-tier loading: tier0-summary, tier1-overview, tier2-group-detail, tier3-stage
│   ├── StageDispatcher.tsx
│   ├── ChannelDispatcher.tsx
│   ├── stage-slugs.ts
│   └── channel-slugs.ts
├── schemas/        # Zod schemas (Pendiente — Story 2B)
├── store/          # Estado local Zustand (sync-store)
├── types/          # TypeScript types
└── utils/          # Utilidades
```

## Etapas (5 etapas Bowtie)

Las etapas canónicas se definen en `lib/registries/stage-registry.ts`:

- `atraccion-captura`
- `nutricion-oportunidad`
- `ventas`
- `adopcion`
- `expansion-evangelizacion`

## Canales (5 canales canónicos)

Los canales canónicos se definen en `lib/registries/channel-registry.ts`:

- `meta-ads`
- `yt-organic`
- `email-nurture`
- `ig-organic`
- `website-total`

## 4-tier loading (carga progresiva)

| Tier | Archivo | Descripción |
|---|---|---|
| 0 | `pages/tiers/tier0-summary.ts` | Resumen bowtie (sin DB) |
| 1 | `pages/tiers/tier1-overview.ts` | Vista general (lector de caché) |
| 2 | `pages/tiers/tier2-group-detail.ts` | Detalle por grupo (lector de caché) |
| 3 | `pages/tiers/tier3-stage.ts` | Consulta DB + escribe caché |

## Invariantes (no modificar sin aprobación)

- `components/strategy-canvas/*` — bowtie visual (pixel-invariante)
- `components/metrics-dashboard/*` internals — solo se acepta adopción del hook `useCopilotOffset`
- Slugs de etapa y canal solo se definen en `lib/registries/` (arch test bloquea hardcoding)

## Pending Story 2B

`actions/` y `schemas/` están pendientes de la Story 2B (`growth-studio-actions-schemas-real`).

Dependencia secuencial: la Story 2A (refactor FSD-Lite, THIS story) debe mergearse primero. La Story 2B implementará:

- 4 Copilot actions reales: `queryStageMetrics`, `queryChannelOverview`, `triggerETLRefresh`, `exportStageReport`
- 4 Zod schemas: `stage-filter-params`, `channel-config`, `kpi-selection`, `tier-loading`

Las carpetas `actions/` y `schemas/` existen como placeholder con `.gitkeep` para marcar la intención de la Story 2B sin código real.
