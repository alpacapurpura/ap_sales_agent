# PM-NICO — Índice

> SSoT funcional Nicolify: producto vivo + proyectos en curso + historia + ideas + opportunities.
> Cargado siempre por `/pm`. Resto de archivos = lookup on-demand. **No cargar todo.**

## Paradigma

| Capa | Carpeta | Significado |
|---|---|---|
| **Producto vivo** | `current-state/{m}.md` | Lo que existe HOY funcional con lineage |
| **Proyectos activos** | `pis/active/PI-{N}/` | PIs en discovery/planning/ejecución |
| **Historia proyectos** | `pis/archive/PI-{N}/` | PIs cerrados con `retro.md`. Read-only |
| **Discovery validado** | `opportunities/{slug}.md` | Problemas con JTBD claro, listos para entrar a PI |
| **Ideas raw** | `ideas/{slug}.md` | Brainstorming sin validar |

## Mapa rápido

| Pregunta | Archivo |
|---|---|
| ¿Visión producto? | [vision-compressed.md](vision-compressed.md) |
| ¿Qué hay en el roadmap? | [roadmap.md](roadmap.md) |
| ¿Qué existe HOY funcionalmente? | `current-state/{módulo}.md` |
| ¿Qué oportunidad estoy explorando? | `opportunities/{slug}.md` |
| ¿Idea cruda sin validar? | `ideas/{slug}.md` |
| ¿Qué PI está activo? | `pis/active/PI-{N}-{theme}/` |
| ¿PIs cerrados? | `pis/archive/PI-{N}-{theme}/` |
| ¿Cuál es el sprint actual del PI? | `pis/active/PI-{N}-*/sprints/S{N}-*/sprint.md` |
| ¿Cuál es el siguiente PR? | `pis/active/PI-{N}-*/sprints/S{N}-*/prs/PR-{n}-{slug}/PR.md` |
| ¿Hay research relevante? | `research/{date}-{slug}.md` |
| ¿Cómo trabajamos (proceso)? | [process/INDEX.md](process/INDEX.md) |
| Jerga negocio | [glossary.md](glossary.md) |
| Templates | `process/sprint-template.md` + `process/pr-folder-template/` + `process/handoff-template.md` |
| Sesiones paralelas | `process/parallel-sessions-protocol.md` |

## current-state/ (16 átomos)

| Módulo | Estado | Archivo |
|---|---|---|
| iam | activo | [iam.md](current-state/iam.md) |
| brand | activo | [brand.md](current-state/brand.md) |
| offer | activo | [offer.md](current-state/offer.md) |
| landing | activo | [landing.md](current-state/landing.md) |
| sales_agent | activo | [sales-agent.md](current-state/sales-agent.md) |
| copilot | activo | [copilot.md](current-state/copilot.md) |
| crm | activo | [crm.md](current-state/crm.md) |
| scheduling | activo | [scheduling.md](current-state/scheduling.md) |
| analytics | activo | [analytics.md](current-state/analytics.md) |
| connections | activo | [connections.md](current-state/connections.md) |
| assets | activo | [assets.md](current-state/assets.md) |
| tenant_domains | activo | [tenant-domains.md](current-state/tenant-domains.md) |
| commercial_calendar | mínimo | [commercial-calendar.md](current-state/commercial-calendar.md) |
| advertising | placeholder | [advertising.md](current-state/advertising.md) |
| social_media | placeholder | [social-media.md](current-state/social-media.md) |
| campaigns | nuevo (PI activo) | [campaigns.md](current-state/campaigns.md) |

## PIs activos (`pis/active/`)

| PI | Tipo | Tema | Estado | Archivo |
|---|---|---|---|---|
| PI-3 | feature | sales-agent-improvement | discovery | [pis/active/PI-3-sales-agent-improvement/PI.md](pis/active/PI-3-sales-agent-improvement/PI.md) |
| PI-4 | **maintenance** (rolling) | brand-evolutive-maintenance | S1 in-progress (PR-1-drop-buyer-persona-fields ready) | [pis/active/PI-4-brand-evolutive-maintenance/PI.md](pis/active/PI-4-brand-evolutive-maintenance/PI.md) |
| PI-5 | feature | copilot-multicanal-telegram | discovery (research in progress) | [pis/active/PI-5-copilot-multicanal-telegram/PI.md](pis/active/PI-5-copilot-multicanal-telegram/PI.md) |

## PIs archivados (`pis/archive/`)

| PI | Cierre | Retro |
|---|---|---|
| PI-1-campaigns-module | 2026-04-30 | [retro.md](pis/archive/PI-1-campaigns-module/retro.md) |
| PI-2-copilot-improvement | 2026-04-30 | [retro.md](pis/archive/PI-2-copilot-improvement/retro.md) |

## Estructura PR-folder

Cada PR vive en su propia carpeta auto-contenida:

```
prs/PR-{n}-{slug}/
├── PR.md                       ← PM
├── CONTRACT.md                 ← architect
├── UI-SPEC.md, design.md, mockups/ ← ux-flow-architect (si aplica)
├── prompts/01-architect-start.md ... 04-pm-close.md ← PM pre-coce
├── IMPL-LOG.md                 ← builder
├── REVIEW.md                   ← auditor
├── RESULT.md                   ← PM (cierra loop)
└── phases/                     ← solo PRs muy amplios
```

Template canónico: [process/pr-folder-template/](process/pr-folder-template/)

## Metodología

PM aplica en orden conversacional típico:

1. **JTBD** → entender job real usuario.
2. **OST** (Torres) → desired outcome → opportunities → solutions → experimentos.
3. **Story Mapping** (Patton) → backbone + walking skeleton MVP.
4. **Now/Next/Later** (Bastow) → roadmap sin fechas falsas.
5. **PRD** (Pocock-style multi-stage interview) → entregable PR.md por solución elegida.
6. **RICE/WSJF** → priorizar cuando conflicto.
7. **Working Backwards** (Amazon press release) → validar viabilidad antes construir.
8. **Dual-Track Agile** (Cagan) → discovery refine en paralelo a delivery execution.

Reference files: `.claude/skills/pm/references/`.

## Reglas

1. **No cargar todo.** Lectura selectiva por path.
2. **Update obligatorio.** PR shipped → update `current-state/{m}.md` con lineage. Rule `pm-nico-ssot.md`.
3. **Anti-orfandad.** Cada PR-folder vive en `sprints/SN-*/prs/`. Cada opportunity en `opportunities/`. Cada idea en `ideas/`.
4. **Caveman.** Atómicos compactos. Tablas > párrafos.
5. **Convo español.** Artifacts español también.
6. **Copilot-first.** Cada PR responde "¿operable desde copilot?" obligatorio.
7. **PR es CARPETA, no archivo.** Template `process/pr-folder-template/`.
8. **PIs cerrados → `archive/`.** Mantenés histórico read-only.
9. **PRs amplios cohesivos.** Opus 4.7[1M] permite scope grande. Sprint = 1-3 PRs.
10. **Sesiones paralelas → `parallel-sessions-protocol.md`** (M1-M6).
11. **Maintenance tracks (rolling) NO cuentan cap Now.** Sprint batch items micro. Upgrade a feature PI si scope crece.

## Punteros externos

- Vision original: `/home/chris/AISALESHT/docs/domains/vision/product-vision.md`
- Domains INDEX (técnico): `/home/chris/AISALESHT/docs/domains/INDEX.md`
- UX flow architect: `.claude/skills/ux-flow-architect/SKILL.md` (handoff post-PR ready)
- PM legacy notes: `docs/pm/campaigns/` (input PI-1, a borrar después S0 cierre)
