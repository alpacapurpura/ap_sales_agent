# PI-2-copilot-improvement — Mejorar Copilot

## Meta

| Campo | Valor |
|---|---|
| PI ID | PI-2-copilot-improvement |
| Estado | active — S1+S2+S3 shipped (PR-1 + PR-2 shipped 2026-04-30), S4 next |
| Tema | Mejoras al copilot — interfaz primaria Nicolify |
| Owner PM | /pm |
| Inicio | 2026-04-29 |
| Cierre estimado | TBD según S2 (cross-stack FE swap) o decisión cierre PI |
| Cierre real | — |
| Sprints completados | S1-copilot-maintenance-batch (3/3 PRs shipped 2026-04-29) · S2-copilot-cero-deuda-stack (3/3 PRs shipped 2026-04-30, PR-3 PARTIAL DEUDA detectada → S3 cleanup) · S3-copilot-llm-stack-convergence (2/2 PRs shipped 2026-04-30, ModelRole único + LiteLLM Proxy live) |
| Sprints planificados | S4-copilot-model-registry-runtime (DB registry + GrowthBook, 2 PRs ready) · S5-copilot-eval-gate-pre-promote (eval gate UI + final cleanup, 2 PRs ready) |

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

### S2 plan resumen (sprint copilot-cero-deuda-stack — shipped 2026-04-30)

| PR | Folder | Scope | Esfuerzo | Verdict |
|---|---|---|---|---|
| PR-1 | `fe-swap-suggestions-api` | Cross-stack BE endpoints + FE swap stub + voice migration | L | shipped PASS BE+FE |
| PR-2 | `pure-expansion-providers` | 3 providers nuevos + sales_agent port + pure expansion offer_section_tools | M | shipped PASS |
| PR-3 | `llm-cost-optimization` | LLM infra DeepSeek V4-Flash + eval gate framework + migration | L | shipped PASS PARTIAL (wiring DEFERRED PR-4) |

### S3-S4-S5 plan ready (bootstrap 2026-04-30 post audit failure PR-3)

**Discovery audit failure PR-3** (Chris detectó capa LLM duplicada al preguntar "para qué se usan AI_MODEL/AI_PROVIDER actuales") cambió plan original "S3-copilot-llm-wiring-runtime" → 3 sprints encadenados con SSoT correcto.

**S3-copilot-llm-stack-convergence** (DONE 2026-04-30):
- PR-1 cleanup PR-3 + convergencia ModelTier→ModelRole + activar DeepSeek V4-Flash NANO+FAST — **shipped** ✅ (allowlist 19→0, cost reduction 4-15x activated)
- PR-2 LiteLLM Proxy intro como motor multi-provider centralizado — **shipped** ✅ (Docker svc visionarias_litellm v1.83.10-stable + 18 D-decisions + 24 tests)

**S4-copilot-model-registry-runtime** (after S3):
- PR-1 DB registry `llm_role_binding` + admin Streamlit `/admin/llm-models` hot-swap <60s — esfuerzo L
- PR-2 GrowthBook OSS per-tenant override + A/B + kill-switch — esfuerzo M

**S5-copilot-eval-gate-pre-promote** (after S4):
- PR-1 eval gate framework wiring admin UI + CI integration `@pytest.mark.eval_gate` — esfuerzo M-L
- PR-2 cleanup definitivo allowlist 0 entries + PI-2 retro + archive — esfuerzo S

**Multicanal Bloque A (Telegram bridge)** = movido a PI-3 dedicado post PI-2 cierre. Razón: scope cohesivo separado, no compite con LLM stack convergencia.

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
