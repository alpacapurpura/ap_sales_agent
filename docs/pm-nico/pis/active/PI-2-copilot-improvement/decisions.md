# PI-2-copilot-improvement — Decisiones

> ADR-style. Append-only.

## 2026-04-29 — PI creado

**Decisión:** Crear PI dedicado para mejoras de copilot.

**Razón:** Copilot = interfaz primaria Nicolify (visión). Mejoras continuas deben ir en PI con foco, no como bug-fix-soup.

**Alternativas consideradas:** dejar como bug fixes ad-hoc → descartado (pierde visión coherente).

## 2026-04-29 — Bloque B 8 recomendaciones investigadas

**Decisión:** clasificar las 8 recs en DO/SKIP/DISCARD/DEFER tras research code-level (`research/2026-04-29-copilot-8-recommendations.md`).

| Rec | Veredicto | Razón |
|---|---|---|
| #1 suggestions engine | DO (S2 propio) | Sin motor real; scope mayor requiere arq + discovery propio |
| #2 rate-limit voice | DO (S1 PR-1) | Riesgo abuso Whisper real; `_MAX_AUDIO_BYTES` hardcoded sin throttling |
| #3 refactor `_tool_result_to_block` | SKIP | Ya resuelto 2026-04-22 (`block_adapters.py` registry pattern, DDD-correct) |
| #4 `filename` en `MediaUploadResponse` | DISCARD | Exclusión consciente (`asset_id` canónico, comentario en DTO) |
| #5 `COPILOT_MEDIA_MAX_BYTES` env | DO (S1 PR-1) | DRY violation; constantes media+voice duplicadas hardcoded |
| #6 DB test roundtrip | DO (S1 PR-1, lite) | Tests existen con MagicMock; faltan fixture DB real |
| #7 backfill content→blocks | DEFER (backlog) | Forward-compat funciona; sin urgencia. Backlog opcional |
| #8 doc code-highlighting Shiki | DISCARD | Shiki no integrado; sin caso uso; stack actual cubre |

**Alternativas consideradas:** meter las 8 en sprints separados → descartado (overkill, varias trivial). Forzar #1 a S1 → descartado (scope mayor + diluye foco hardening).

**Próximo paso:** confirmar S1 con Chris → materializar `PR-1-voice-media-hardening`.

## 2026-04-29 — Override Chris: hacer Bloque B completo en S1

**Decisión:** Chris descartó el plan PM de diferir #1 (S2) y #7 (backlog). Override: "hacerlas todas en S1, cerrar las que se terminen".

| Rec | Decisión final | Destino |
|---|---|---|
| #1 suggestions engine | DO en S1 | PR-2 `suggestions-engine` |
| #2 rate-limit voice | DO en S1 | PR-1 `voice-media-hardening` |
| #3 refactor block_adapter | CLOSED definitivo | — (ya resuelto 2026-04-22) |
| #4 filename MediaUploadResponse | CLOSED definitivo | — (decisión consciente) |
| #5 COPILOT_MEDIA_MAX_BYTES env | DO en S1 | PR-1 `voice-media-hardening` |
| #6 DB roundtrip tests | DO en S1 | PR-1 `voice-media-hardening` |
| #7 backfill content→blocks | DO en S1 | PR-3 `backfill-content-blocks` |
| #8 doc Shiki highlighting | CLOSED definitivo | — (sin caso uso) |

**Razón override:** Opus 4.7[1M] permite scope amplio cohesivo. Defer = arrastrar deuda. Cerrar Bloque B completo en S1 libera mente para Bloque A multicanal en S2.

**Alternativas consideradas:** PM propuso S1 chico + S2 con #1 + backlog #7 → Chris descartó por preferir cierre completo Bloque B en S1.

**Estructura S1 resultante:** `sprints/S1-copilot-maintenance-batch/` con 3 PRs (PR-1 voice/media hardening, PR-2 suggestions engine, PR-3 backfill content→blocks).

**Próximo paso:** ejecutar `prompts/01-architect-start.md` de PR-1 (sugerido por boundary técnica + esfuerzo M).

## Pendientes registrar

_Aquí se irán registrando decisiones tomadas durante discovery + ejecución._
