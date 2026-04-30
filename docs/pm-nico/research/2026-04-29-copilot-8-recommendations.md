# Research: Copilot 8 Recomendaciones — Validación Bloque B

> Fecha: 2026-04-29
> PI: PI-2-copilot-improvement
> Investigador: `Explore` agent + PM
> Output: validar las 8 recs capturadas en `PI.md > Bloque B`. Decidir do / postpone / discard.

## Resumen ejecutivo

| Veredicto | # recs | IDs |
|---|---|---|
| **DO** (válida, scope chico-medio) | 3 | #1, #2, #5 |
| **POSTPONE** (válida pero fuera S1) | 1 | #6 |
| **DEFER** (válida pero forward-compat OK hoy) | 1 | #7 |
| **SKIP — ya resuelta** | 1 | #3 |
| **DISCARD — invalida tras research** | 2 | #4, #8 |

**Recomendación PM:** S1 = PR-1 cohesivo "Voice/media hardening" combinando #2 + #5 + #6 (scope chico, calidad inmediata). #1 a S2 propio (scope mayor, requiere discovery suggestions). #3/#4/#8 cierre con decisión registrada. #7 backlog opcional.

## Tabla detallada

| # | Item original | Existe? | Estado actual | Veredicto | Razón |
|---|---|---|---|---|---|
| 1 | Motor real suggestions (swap stub) | Parcial | Sin motor real ni stub. `application/tools/offer_section_tools.py` improvisa hints hardcoded | **DO** (S2 propio) | Válida pero requiere arq propia + discovery. NO meter en S1 chico |
| 2 | Rate limit `/voice/upload-and-transcribe` editable per-tenant via Streamlit | Sí endpoint, NO rate limit | `api/voice.py:39` `_MAX_AUDIO_BYTES = 25MB` hardcoded. Sin throttling decorator | **DO** (S1) | Riesgo abuso Whisper real. Streamlit admin extender (no módulo nuevo). KISS |
| 3 | Refactor `_tool_result_to_block` → `application/adapters/` | Sí, ya refactorizado | `application/orchestrator/block_adapters.py` (176 LOC) — registry pattern, DDD-correct, desde 2026-04-22 | **SKIP** | Ya resuelto. Cerrar item |
| 4 | `filename` en `MediaUploadResponse` | NO field, exclusión consciente | `api/media_dto.py:27` comment: "intentionally excluded — only UUID is canonical" | **DISCARD** | Decisión consciente previa. `asset_id` permite lookup downstream |
| 5 | `COPILOT_MEDIA_MAX_BYTES` configurable via env | NO env, hardcoded duplicado | `api/media.py:84` + `api/voice.py:39` mismas constantes hardcoded. Comment: "configurable via env in future" | **DO** (S1) | DRY violation + falta config tenant-aware. Junto con #2 |
| 6 | Integración DB test roundtrip | Tests existen pero con mocks | `test_persist_emitted_blocks.py`, `test_media_upload.py`, `test_voice_combined.py` usan MagicMock — no fixture DB real | **DO** (S1, lite) | Mejora calidad observable. Scope chico si fixture compartido existe |
| 7 | Backfill script content → blocks | Forward-compat funciona, sin backfill | Migración `20260422_1200_copilot_multimodal.py` marker-only. Codec lee legacy v1 on-fly. Nueva data = blocks | **DEFER** (backlog opcional) | No bloquea nada. Backfill = limpieza eventual, sin urgencia |
| 8 | Doc `code-highlighting.md` (Shiki upgrade) | NO Shiki en frontend, NO doc | `frontend/package.json` sin `shiki`. Render actual: `react-markdown` + `rehype-sanitize` + `remark-gfm`. Sin caso uso pendiente | **DISCARD** | Sin caso uso real. Stack actual cubre código highlighting básico. Reabrir si user pide multi-lang colorizing |

## Recomendación de Sprint S1

**Tema S1:** copilot-voice-media-hardening

**Scope (1 PR cohesivo):**
- #2 — Rate limit voice/upload (per-tenant editable, default env)
- #5 — `COPILOT_MEDIA_MAX_BYTES` env-driven, unificar constantes media+voice
- #6 — DB test roundtrip real (al menos 1 path crítico: persist message+blocks)
- (admin extension Streamlit para defaults per-tenant, sin módulo nuevo)

**Scope **fuera** S1 (decididos):**
- #3 → cerrar como ya-resuelto en PI.md
- #4 → cerrar como discard en PI.md
- #8 → cerrar como discard en PI.md
- #7 → mover a backlog opcional (sección `## Backlog técnico` en PI.md)
- #1 → S2 propio: discovery + arq suggestions engine

**Justificación cohesión PR-1:** #2+#5+#6 todos tocan `modules/copilot/api/{media,voice}.py` + tests media/voice. Single boundary, single test surface, deploy atómico. <300 LOC esperado.

## Decisiones que requieren confirmación Chris

1. ¿Confirmás S1 con #2+#5+#6 cohesivo? (alternativa: separar #6 a sprint propio quality)
2. ¿#1 suggestions a S2 (post-S1) o queda Later si no hay dolor real reportado?
3. ¿#7 backfill content→blocks ok dejar como backlog opcional?
4. ¿Cerramos #3/#4/#8 con decisión registrada (no se vuelven a tocar)?

## Anclajes técnicos (paths exactos)

| Path | Relevancia |
|---|---|
| `backend/src/modules/copilot/api/media.py:84` | `_MAX_FILE_BYTES = 25MB` hardcoded |
| `backend/src/modules/copilot/api/voice.py:39` | `_MAX_AUDIO_BYTES = 25MB` hardcoded |
| `backend/src/modules/copilot/api/media_dto.py:27` | `MediaUploadResponse` (sin `filename`) |
| `backend/src/modules/copilot/application/orchestrator/block_adapters.py` | Refactor #3 ya hecho |
| `backend/src/modules/copilot/application/tools/offer_section_tools.py` | Hardcoded suggestions hint (#1 origin) |
| `backend/tests/modules/copilot/test_{persist_emitted_blocks,media_upload,voice_combined}.py` | Tests con MagicMock (#6) |
| `backend/alembic/versions/20260422_1200_copilot_multimodal.py` | Marker-only, sin backfill (#7) |
| `frontend/package.json` | Sin `shiki` (#8) |

## Próximo paso

PM espera confirmación Chris para:
- Materializar PR-folder S1 con scope confirmado
- Append decisiones a `pis/active/PI-2-copilot-improvement/decisions.md`
- Update `PI.md > Bloque B` reflejando estado real per-rec
