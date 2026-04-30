# Sprint S1 — copilot-maintenance-batch

## Meta

| Campo | Valor |
|---|---|
| Sprint ID | S1-copilot-maintenance-batch |
| PI padre | PI-2-copilot-improvement |
| Estado | in-progress |
| Inicio | 2026-04-29 |
| Cierre estimado | TBD (3 PRs cohesivos) |
| Cierre real | — |
| Owner PM | /pm |

## Objetivo (1 línea)

Cerrar las 5 recomendaciones DO del Bloque B en PRs cohesivos por boundary técnica: hardening voice/media, suggestions engine real, y backfill content→blocks. Dejar el módulo copilot estable + observable para PI-2 next sprints (suggestions UX, multicanal Telegram, discovery formal Bloque C).

## Pre-handoff (input desde sprint anterior)

- Decisiones tomadas: research file + ADR Bloque B 2026-04-29 (`pis/active/PI-2-copilot-improvement/decisions.md`)
- Surface disponible: copilot module estable post-redesign 2026-04 (observability rebuild + subagent isolation + extraction feedback shipped)
- Riesgos abiertos: Streamlit admin no tiene panel copilot aún (PR-1 lo agrega)
- Skills/agentes recomendados: `nicolify-architect` + `nicolify-backend` + `nicolify-backend-auditor` + `copilot-expert` skill obligatorio en cada PR

## Plan PRs (folders)

| PR | Folder | Descripción | Agentes/skills | Esfuerzo | Estado |
|---|---|---|---|---|---|
| PR-1 | `prs/PR-1-voice-media-hardening/` | Rate limit voice/upload + `COPILOT_MEDIA_MAX_BYTES` env-driven + DB roundtrip tests + Streamlit admin per-tenant defaults | `nicolify-architect` → `nicolify-backend` → `nicolify-backend-auditor` + `copilot-expert` | M | not-started |
| PR-2 | `prs/PR-2-suggestions-engine/` | Motor real suggestions reemplazando hint hardcoded en `offer_section_tools.py`. Adapter pattern + registry + tools transversales | `nicolify-architect` → `nicolify-backend` (+ `nicolify-agentic` si LangGraph) → `nicolify-backend-auditor` + `copilot-expert` | L | not-started |
| PR-3 | `prs/PR-3-backfill-content-blocks/` | Script Python idempotente + alembic data migration: legacy `content` field → `blocks` structured. Cleanup forward-compat dead code | `nicolify-architect` → `nicolify-backend` → `nicolify-backend-auditor` + `copilot-expert` | S | not-started |

Detalle de cada PR vive en `prs/PR-N-{slug}/PR.md`. Prompts pre-cocidos para handoffs en `prompts/`.

## Criterio éxito sprint

- [ ] Bloque B 5 recs DO entregadas (PR-1: #2+#5+#6, PR-2: #1, PR-3: #7) con tests verdes
- [ ] Streamlit admin extendido con panel per-tenant rate-limit voice (KISS)
- [ ] DB roundtrip tests cubren 1+ path crítico copilot media/voice persistence
- [ ] Suggestions engine reemplaza hint hardcoded sin romper offer_section_tools
- [ ] Backfill ejecutado en dev DB con `legacy content rows = 0` post-migration
- [ ] Cero refactor necesario en S2 (multi-canal Telegram) — copilot module sólido
- [ ] Todos los 3 PRs tienen `RESULT.md` escrito (loop cerrado)
- [ ] `current-state/copilot.md` actualizado con capabilities lineage

## Out of scope

| Item | Razón | Sprint destino |
|---|---|---|
| Wire copilot ↔ Telegram bridge | Bloque A — discovery propio + sales_agent connection layer research | S2-copilot-multicanal-telegram (PI-2) |
| Discovery formal Bloque C (H1-H4) | Requiere entrevista users + analytics | S3+ post-S2 |
| Cards UI nuevas para suggestions | Suggestions engine PR-2 = backend only. UI cards si Chris pide → PR FE separado | S1 PR-4 (opcional) o S2 |
| Refactor `_tool_result_to_block` (#3) | YA RESUELTO 2026-04-22 | — |
| `filename` en MediaUploadResponse (#4) | DISCARD — exclusión consciente | — |
| Doc Shiki code-highlighting (#8) | DISCARD — sin caso uso real | — |

## Decisiones a tomar durante sprint

(append-only conforme aparezcan)

| Fecha | Decisión | PR |
|---|---|---|
| ... | ... | ... |

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| PR-2 suggestions engine scope creep (LangGraph subagent vs simple tool) | Architect define scope estricto en CONTRACT.md ANTES de builder | architect |
| PR-3 backfill rompe filas legacy mal-formadas | Script idempotente + dry-run obligatorio + reporte rows-affected antes commit | builder |
| Streamlit admin panel rate-limit complica tenant config (overengineering) | Reusar patrón Streamlit existente. Default env, override per-tenant. KISS | architect |
| DB roundtrip tests rompen tests existentes con MagicMock | Mantener tests mock + agregar fixture DB en conftest separado, no reemplazar | builder |
| #1 suggestions engine requiere FE cards no anticipados | PR-2 = BE only. Si Chris quiere UI → PR FE separado en S1 PR-4 (opcional) o S2 | PM |

## Cierre

Al cerrar:
1. Llenar `learnings.md` (qué funcionó, qué no, sorpresas).
2. Llenar `handoff.md` (decisiones, surface, agentes recomendados S2-copilot-multicanal-telegram).
3. Marcar sprint `done` en este `sprint.md`.
4. Verificar 3 `prs/PR-*/RESULT.md` escritos (loop cerrado).
5. Si learnings impactan proceso global → append `../../../../process/process-learnings.md`.
6. Considerar arrancar S2 (multicanal Telegram, Bloque A).
