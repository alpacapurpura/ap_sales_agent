# PI-2-copilot-improvement — Mejorar Copilot

## Meta

| Campo | Valor |
|---|---|
| PI ID | PI-2-copilot-improvement |
| Estado | active — S1 shipped, S2 candidato cross-stack FE swap |
| Tema | Mejoras al copilot — interfaz primaria Nicolify |
| Owner PM | /pm |
| Inicio | 2026-04-29 |
| Cierre estimado | TBD según S2 (cross-stack FE swap) o decisión cierre PI |
| Cierre real | — |
| Sprints completados | S1-copilot-maintenance-batch (3/3 PRs shipped 2026-04-29 — Bloque B 5 recs DO entregadas) |

## Outcome esperado

_Pendiente discovery formal._ Hipótesis preliminar: aumentar % de operaciones Nicolify que ocurren via copilot vs UI directa. Mejora consistencia + descubrimiento + autoadopción.

- Cuantitativo: TBD (¿% acciones via copilot? ¿retención day-7?)
- Cualitativo: User dice "siempre uso copilot, la UI es solo cuando necesito ver algo visual"

## Hipótesis

Pendientes discovery. Posibles:
- H1: Hay gaps de capacidades operables conversacionalmente entre módulos (algunos rich, otros pobres) → user inconsistente
- H2: Conversaciones largas pierden contexto (Lost-in-the-Middle) → frustración
- H3: User no descubre lo que copilot puede hacer → infrautiliza
- H4: Cards visuales podrían ser más ricas / interactivas

## Scope

### In (preliminar)

- TBD via discovery

### Out (preliminar)

- TBD

## PRs candidatos (capturados, pendientes refinamiento)

> Items capturados 2026-04-29. NO desarrollados aún. Discovery formal pendiente.

### Bloque A — Wire copilot multi-canal (transport)

| PR-candidato | Descripción | Notas |
|---|---|---|
| Copilot ↔ Telegram bridge (MVP) | Conectar copilot al canal Telegram. Pattern multi-canal extensible (próximo: WhatsApp, otros). Inspirarse en `sales_agent` connection layer ya existente | Chris: "empezaremos con telegram pero usa el patrón de diseño adecuado para cuando hayan más" |
| Copilot ↔ WhatsApp bridge | Reusar pattern del PR Telegram | Bloqueado por PR Telegram |

### Bloque B — Mantenimiento copilot (8 recomendaciones — cerrado discovery 2026-04-29)

> Research: `research/2026-04-29-copilot-8-recommendations.md`. Decisión Chris 2026-04-29: hacerlas todas en S1, cerrar definitivo las descartadas.

| # | Item | Veredicto | Destino |
|---|---|---|---|
| 1 | Motor real suggestions (swap stub) | DO | **S1 PR-2** `suggestions-engine` |
| 2 | Rate limit `/voice/upload-and-transcribe` per-tenant editable Streamlit | DO | **S1 PR-1** `voice-media-hardening` |
| 3 | Refactor `_tool_result_to_block` → `application/adapters/` | **CLOSED** | Ya resuelto 2026-04-22 (`block_adapters.py` 176 LOC, registry pattern DDD-correct) |
| 4 | `filename` en `MediaUploadResponse` | **CLOSED** | Exclusión consciente previa (`asset_id` canónico). Reabrir solo si user pide |
| 5 | `COPILOT_MEDIA_MAX_BYTES` configurable via env | DO | **S1 PR-1** `voice-media-hardening` (junto con #2) |
| 6 | Integración DB test roundtrip | DO | **S1 PR-1** `voice-media-hardening` (lite, fixture compartido) |
| 7 | Backfill script content → blocks | DO | **S1 PR-3** `backfill-content-blocks` |
| 8 | Doc `code-highlighting.md` (Shiki upgrade) | **CLOSED** | Sin Shiki integrado, sin caso uso. Stack actual cubre. Reabrir solo si user pide multi-lang highlighting |

### Bloque C — Discovery original (preliminar, ver Hipótesis arriba)

- TBD via discovery formal cuando arranquemos PI-2 kickoff post-S1

### S1 plan resumen (sprint copilot-maintenance-batch)

| PR | Folder | Scope | Esfuerzo |
|---|---|---|---|
| PR-1 | `voice-media-hardening` | #2 + #5 + #6 (rate-limit voice + env max-bytes + DB roundtrip tests) | M |
| PR-2 | `suggestions-engine` | #1 (motor suggestions real, swap stub) | L |
| PR-3 | `backfill-content-blocks` | #7 (script + alembic migration content→blocks) | S |

## Opportunities atendidas

_Pendiente captura post-discovery._

## Restricciones / Riesgos

- Restricción: cost/turn (Kimi K2.5 / DeepSeek V3 / GPT-4o tier routing) — cualquier mejora debe respetar budget
- Riesgo técnico: subagent isolation invariants ya tienen tests — no romper
- Riesgo: LangGraph + deepagents en producción — cambios estructurales con cuidado

## Decisiones clave

_Pendientes._

## Métricas seguimiento

_Pendientes._

## Discovery tasks pendientes

1. Entrevistar Chris: ¿qué dolor copilot reporta hoy? ¿qué le gustaría mejorar?
2. Lookup current-state copilot.md para gaps documentados
3. Research patrones agentic copilot 2026 (Replit Agent, Cursor, Claude Projects, custom GPTs en SaaS)
4. Captura señales analytics copilot (cost per conversation, success rate, drop-off)
5. Decidir scope (¿bug general o feature gigante? Probablemente un mix)
6. **Investigar 8 recomendaciones Bloque B** (ver "PRs candidatos"). Para cada una:
   - ¿Existe el stub/file/endpoint mencionado? Path exacto.
   - ¿Qué problema resuelve? ¿Lo tenemos resuelto distinto?
   - ¿Recomendamos hacerlo, postponerlo, descartarlo? Con razón.
   - Output: research file `docs/pm-nico/research/{date}-copilot-8-recommendations.md` con tabla.
7. **Discovery wire telegram (Bloque A)**: leer `backend/src/modules/sales_agent/` connection layer para identificar pattern reutilizable para copilot. Captura en `research/{date}-copilot-channel-bridge-pattern.md`.

## Cierre / Retro

Pendiente.
