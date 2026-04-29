# PM-NICO — Índice

> SSoT funcional Nicolify presente + futuro. Cargado siempre por `/pm`.
> Resto de archivos = lookup on-demand. **No cargar todo.**

## Propósito

Mantener clara visión producto, estado actual funcional, oportunidades, planes (PIs), entregas (PRs). PM senior aplica método. Owner único = `/pm` skill. Sin Chris pidiendo update — automático.

## Mapa rápido

| Pregunta | Archivo |
|---|---|
| ¿Visión producto? | [vision-compressed.md](vision-compressed.md) |
| ¿Qué hay en el roadmap? | [roadmap.md](roadmap.md) |
| ¿Qué existe HOY funcionalmente? | `current-state/{module}.md` (16 átomos) |
| ¿Qué oportunidad estoy explorando? | `opportunities/{slug}.md` |
| ¿Qué PI está activo? | `pis/PI-{N}-{theme}/` |
| ¿Cuál es el sprint actual del PI? | `pis/PI-{N}/sprints/S{N}-*/sprint.md` |
| ¿Cuál es el siguiente PR? | `pis/PI-{N}/sprints/S{N}-*/prs/PR-{n}-{slug}.md` |
| ¿Hay research relevante? | `research/{date}-{slug}.md` |
| ¿Cómo trabajamos (proceso)? | [process/INDEX.md](process/INDEX.md) |
| Jerga negocio | [glossary.md](glossary.md) |
| Templates | `process/sprint-template.md` + `process/pr-template.md` + `process/handoff-template.md` |

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

## PIs activos

| PI | Tema | Estado | Archivo |
|---|---|---|---|
| PI-1 | campaigns-module | discovery | [pis/PI-1-campaigns-module/PI.md](pis/PI-1-campaigns-module/PI.md) |
| PI-2 | copilot-improvement | discovery | [pis/PI-2-copilot-improvement/PI.md](pis/PI-2-copilot-improvement/PI.md) |
| PI-3 | sales-agent-improvement | discovery | [pis/PI-3-sales-agent-improvement/PI.md](pis/PI-3-sales-agent-improvement/PI.md) |

## Metodología (referencias en skill)

PM usa estas. Orden conversación típico:

1. **JTBD** → entender job real usuario.
2. **OST** (Torres) → desired outcome → opportunities → solutions → experimentos.
3. **Story Mapping** (Patton) → backbone + walking skeleton MVP.
4. **Now/Next/Later** (Bastow) → roadmap sin fechas falsas.
5. **PRD** (Pocock-style multi-stage interview) → entregable PR.md por solución elegida.
6. **RICE/WSJF** → priorizar cuando conflicto.
7. **Working Backwards** (Amazon press release) → validar viabilidad antes construir.

Reference files: `.claude/skills/pm/references/`.

## Reglas

1. **No cargar todo.** Lectura selectiva por path.
2. **Update obligatorio.** Modificación dominio = update `current-state/{module}.md`. Rule `pm-nico-ssot.md`.
3. **Anti-orfandad.** Cada PR.md vive en `pis/PI-N/prs/`. Cada opportunity en `opportunities/`. Sin archivos sueltos.
4. **Caveman.** Atómicos compactos. Tablas > párrafos. Bullets > prosa.
5. **Convo español.** Artifacts español también.
6. **Copilot-first.** Cada PR responde "¿operable desde copilot?" obligatorio.

## Punteros externos

- Vision original: `/home/chris/AISALESHT/docs/domains/vision/product-vision.md`
- Domains INDEX (técnico): `/home/chris/AISALESHT/docs/domains/INDEX.md`
- UX flow architect: `.claude/skills/ux-flow-architect/SKILL.md` (handoff PR.md)
- PM legacy notes (a migrar): `docs/pm/campaigns/` (input para PI-1)
