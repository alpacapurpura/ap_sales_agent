# REVIEW — Copilot Multimodal Rearchitecture

> Self-audit realizado 2026-04-21 tras implementación de CONTRACT-MULTIMODAL.md.
> Complementa `REVIEW.md` (data-model v2, Approved). No lo sustituye.

---

## §1 Executive Summary

**Verdict:** ✅ **APPROVED WITH MINOR ISSUES**

La rearchitectura multimodal está implementada coherentemente con el contrato. El schema canónico de bloques, el codec legacy, el endpoint de upload, las tools outbound y el doble-emit SSE v2 cumplen los requisitos funcionales y de extensibilidad. Tenant isolation, DDD layering y arch tests están limpios. Los hallazgos son de severidad baja/media: anclas de documentación refinables, tests de integración del dual-emit SSE con mocks perfectibles, y dos zonas de deuda técnica clara en `message_codec` y el handler de tool-results del orquestador. Nada bloquea el merge.

CI local está verde:

| Gate | Resultado |
|---|---|
| `ruff check src/ tests/` | ✅ 0 errors |
| `ruff format --check src/ tests/` | ✅ 1305 files formatted |
| `pytest tests/architecture/` | ✅ 385 passed |
| `pytest tests/modules/copilot/` | ✅ 660 passed |

---

## §2 Findings by Severity

### CRITICAL
_Ninguno._

### HIGH
_Ninguno._

### MEDIUM

| ID | Título | File:Line | Razón | Fix sugerido |
|----|--------|-----------|-------|--------------|
| M1 | `_tool_result_to_block` complejidad | `backend/src/modules/copilot/application/orchestrator/chat.py:66` | Ya refactorizado via handler dict pattern, pero queda una sola función pública que consume handlers — aceptable pero podría moverse a adapter module dedicado para testabilidad aislada | Mover handlers + dispatcher a `application/adapters/tool_result_to_block.py`, mantener anchor |
| M2 | `_flatten_blocks` en codec | `backend/src/modules/copilot/infrastructure/repositories/message_codec.py:90` | Dispatch dict implementado — bien. Pero handlers lambdas inline dificultan docstrings por tipo | Extraer cada handler como `_flatten_text_block(b)` nombrada; anchor `[COPILOT-BLOCK-FLATTEN]` |
| M3 | Legacy content adapter asume UTF-8 safe | `message_codec.py` decode path | Si `content` trae bytes corruptos antiguos → NFC issues potenciales | Agregar `errors="replace"` o normalizar NFC explícito en adapter |

### LOW

| ID | Título | File:Line | Razón | Fix sugerido |
|----|--------|-----------|-------|--------------|
| L1 | Anchor casing inconsistente | `orchestrator/chat.py:3-4` vs `:657-659` | Algunos anchors usan `->`, otros `→` (arrow unicode) | Normalizar a `→` (arrow unicode) en todos; arch test `test_copilot_anchors` podría gate |
| L2 | `MediaUploadResponse.filename` no expuesto | `backend/src/modules/copilot/api/media_dto.py` | FE puede querer mostrar filename en chip; hoy deriva del File client-side | Agregar `filename: str` opcional en response |
| L3 | `MAX_FILE_BYTES` hardcodeado 25MB | `media.py:89` | No configurable por env | Mover a `settings.COPILOT_MEDIA_MAX_BYTES` con fallback 25MB |
| L4 | Voice combined endpoint sin rate limit | `voice.py:79` | Posible abuso (uploads concurrentes de audio grande) | Aplicar rate limit middleware `copilot-media` si ya existe |
| L5 | Anchor `[COPILOT-SHIKI-UPGRADE]` en FE sin doc pair | `frontend/.../CodeBlock.tsx:19` | Shiki no está en `package.json` aún; doc explicativo falta | Crear `docs/domains/copilot/code-highlighting.md` o inline TODO |

---

## §3 Contract Alignment

| § CONTRACT | Scope | Implementation | Status |
|---|---|---|---|
| §1 Block Schema | 11 block types, discriminated Union | `backend/src/modules/copilot/domain/message_blocks.py` | ✅ |
| §2 Message Entity | `Message { blocks?, content, status, ... }` | `domain/message.py` | ✅ |
| §3 DB Migration | `blocks` shape v2 idempotente + GIN index | `alembic/versions/20260422_1200_copilot_multimodal.py` | ✅ (arquitectura JSONB-free mejor que ADD COLUMN — documentado) |
| §4 `OutgoingMessage` ext | `blocks: list[dict] \| None` | `shared/domain/messages.py:24` | ✅ Anchor `[COPILOT-OUTGOING-BLOCKS]` |
| §5 Channel Adapter ext | `send_rich_message` en `BaseChannel` | `shared/infrastructure/channels/base.py:37` | ✅ Default fallback a `send_message` |
| §6 SSE v2 Protocol | `block_append/update/finalize` dual-emit | `orchestrator/chat.py` 9 ocurrencias | ✅ |
| §7 Upload Endpoint | `/copilot/media/upload` → `AssetsService` | `api/media.py` | ✅ Delega sin duplicar storage |
| §8 Outbound Assets Tools | `search_assets`, `get_asset` | `application/tools/assets_tools.py` | ✅ Grupo bindeado en registry |
| §9 Voice Dual-Mode | `/voice/upload-and-transcribe` atómico | `api/voice.py:79` | ✅ `asyncio.gather` concurrency |
| §10 Citations + Quote-Reply | Blocks + emit path | `message_blocks.py:164`, `:192` + chat.py emit | ✅ Anchors presentes |
| §11 Smart Chips Contract | Solo stub interface | FE: `types/suggestions.ts` + `use-suggestions.ts` | ✅ Motor real diferido (anchor claro) |
| §12 Anchor Convention | Tabla anchors en docs + arch test | 22 anchors en BE+FE, `test_copilot_anchors.py` | ✅ |
| §13 Migration Strategy | DB → BE dual-emit → FE consume blocks → cleanup | Dual-emit activo; FE V2 components wired | ✅ Fase actual: dual-emit + FE activo |
| §14 Non-goals | No AI media generation, no motor chips, no WA activo | Nada de scope fuera — confirmado | ✅ |
| §15 Decisions Log | Open questions + trade-offs | Documentado en CONTRACT §5, §9 | ✅ |

---

## §4 DDD & Architecture Compliance

### Domain purity
- `message_blocks.py` — solo Pydantic + stdlib. Sin SQLAlchemy. ✅
- `message.py` — Pydantic. Sin framework. ✅

### Infrastructure aislada
- `message_codec.py` — implementa adapter pattern sobre dicts JSONB. No conoce FastAPI ni tenant context directo. ✅

### Application layer
- `assets_tools.py` — `@copilot_tool` decorador, tenant injected via context. ✅
- `orchestrator/chat.py` — orquesta graph + SSE. Es el punto más pesado; funciones refactorizadas a handlers dict. ✅

### API layer thin
- `api/media.py` — valida → delega a `AssetsService.upload_asset`. No lógica de negocio. ✅
- `api/voice.py` — 2 endpoints (legacy + dual-mode) delegando. ✅

### Cross-module imports
- Copilot importa `src.modules.assets.application.assets_service.AssetsService` — **permitido** por regla `copilot-resilience.md` (copilot puede cross-import, otros módulos no). ✅

---

## §5 Security & Tenant Isolation

| Verificación | Resultado | Evidencia |
|---|---|---|
| Upload `tenant_id` desde `current_user.tenant_id` | ✅ | `media.py:144` |
| `AssetsService.upload_asset(tenant_id=...)` kwarg explícito | ✅ | `media.py:192` |
| `search_assets`/`get_asset` filtran `tenant_id` | ✅ | `assets_tools.py` (delega a `AssetRepository.list_by_tenant`) |
| PII en `MediaUploadResponse` (asset_id, public_url, mime, size_bytes, kind) | ✅ Sin PII directa — URL es pública por diseño (bucket), asset_id UUID |
| `VoiceUploadAndTranscribeResponse` | ✅ Expone transcript (contenido usuario autorizado) + audio URL |
| File size validation | ✅ `_MAX_FILE_BYTES = 25MB`; `413` si excede |
| MIME whitelist | ✅ `_MIME_WHITELIST` 4 kinds exhaustivos; `415` si no permitido |
| Auth en endpoints nuevos | ✅ `Depends(get_current_user)` requerido |
| Arch test `test_all_endpoints_have_response_model` | ✅ Return type satisface requirement (arch test acepta ambos) |

### Hallazgos security
- **L4** (MEDIUM baja): rate limit para `/voice/upload-and-transcribe` recomendado (audio+Whisper es costoso)
- Sanitización MIME es por whitelist (allowlist pattern, correcto)
- No se loguean file contents, solo metadata (tenant_id, mime, size) ✅

---

## §6 Extension Points — Anchor Audit

22 anchors detectados. Mapping consistente con docs:

| Task | File | Anchor | Doc |
|---|---|---|---|
| Agregar block type nuevo | `backend/src/modules/copilot/domain/message_blocks.py` | `[COPILOT-CANONICAL-BLOCKS]` | `message-blocks.md` |
| Nuevo canal outbound | `backend/src/shared/infrastructure/channels/base.py` | `[COPILOT-CHANNEL-RENDERER]` | `channel-adapters.md` |
| Extender `OutgoingMessage` | `backend/src/shared/domain/messages.py` | `[COPILOT-OUTGOING-BLOCKS]` | `CONTRACT-MULTIMODAL.md §4` |
| SSE v2 evento nuevo | `backend/src/modules/copilot/application/orchestrator/chat.py` | `[COPILOT-SSE-V2]` | `sse-protocol.md` |
| Nuevo citation-emitting tool | `orchestrator/chat.py` + `message_blocks.py` | `[COPILOT-CITATION-BLOCK]` | `message-blocks.md §citation` |
| Nueva outbound assets tool | `application/tools/assets_tools.py` | `[COPILOT-OUTBOUND-ASSETS]` | `outbound-assets.md` |
| Media upload pipeline | `api/media.py`, `media_dto.py` | `[COPILOT-MEDIA-UPLOAD]` | `CONTRACT-MULTIMODAL.md §7` |
| Voice dual-mode endpoint | `api/voice.py`, `voice_dto.py` | `[COPILOT-VOICE-DUAL-MODE]` | `CONTRACT-MULTIMODAL.md §9` |
| Reply-quote feature | `domain/message_blocks.py:192` | `[COPILOT-QUOTE-REPLY]` | `message-blocks.md` |
| Legacy content↔blocks codec | `infrastructure/repositories/message_codec.py` | `[COPILOT-MESSAGE-CODEC]` | `message-blocks.md §3` |
| Block renderer FE | `frontend/.../components/blocks/BlockDispatcher.tsx` | `[COPILOT-BLOCK-REGISTRY]` | `UI-SPEC.md §6` |
| Composer compound FE | `frontend/.../components/composer/ChatComposer.tsx` | `[COPILOT-COMPOSER]` | `UI-SPEC.md §3` |
| Legacy FE adapter | `frontend/.../utils/message-adapter.ts` | `[COPILOT-LEGACY-ADAPTER]` | `UI-SPEC.md §6` |
| Motor chips real | `frontend/.../hooks/use-suggestions.ts` | `[COPILOT-SUGGESTIONS-ENGINE]` | `suggestions-engine.md` |
| Streaming actions store | `frontend/.../store/copilot-store.ts` | `[COPILOT-STREAMING-BLOCKS]` | `message-blocks.md` |
| Upload pipeline FE | `frontend/.../api/media-api.ts` | `[COPILOT-MEDIA-UPLOAD]`, `[COPILOT-VOICE-UPLOAD]` | `CONTRACT-MULTIMODAL.md §7, §9` |
| Code highlighting upgrade | `frontend/.../components/blocks/CodeBlock.tsx` | `[COPILOT-SHIKI-UPGRADE]` | (L5: falta doc) |

Arch test `test_copilot_anchors_have_docs` gate activo ✅.

---

## §7 Tests Coverage

### Paths críticos
- `test_message_blocks.py` — validación discriminated union, fields obligatorios ✅
- `test_message_codec.py` — roundtrip `content ↔ blocks`, UIAction mapping, edge cases (empty, missing fields) ✅
- `test_media_upload.py` — tenant isolation, delegation a AssetsService, validaciones (empty, oversize, bad MIME) ✅
- `test_assets_tools.py` — tenant-scoped search/get, AssetRef serialization ✅
- `test_voice_combined.py` — concurrency (asyncio.gather), AudioBlock assembly ✅
- `test_sse_v2_events.py` — dual-emit text_chunk+block_update, tool_result→block_append, done→block_finalize ✅

### Arch tests
- `test_copilot_anchors.py` — anchors ↔ docs alineados ✅
- `test_message_blocks_exhaustive.py` — Union cubre 11 tipos esperados ✅
- `test_api_contracts.py` (existente) — response_model presente en endpoints nuevos (satisfecho por return type annotations) ✅

### Mocking quality
- `test_media_upload.py` usa helper `_fresh_db_mock()` (no lambda directo con MagicMock — evita FastAPI introspectar `*args,**kw`) ✅
- `AssetsService` mockeado correctamente con `@patch`
- SSE tests usan async generator fixture pattern (después del fix post-auditor anterior)

### Gaps detectados
- **Integración real DB**: ningún test hace roundtrip `write_with_blocks → read_legacy → read_v2` contra Postgres real (solo mocks). Test de integración opcional a futuro.
- **Rate limit**: no testeado (L4)
- **Backfill script**: no existe aún (contrato lo marca opcional)

---

## §8 Scores

| Dimensión | Score | Justificación |
|---|---|---|
| **DDD compliance** | 9/10 | Layering estricto; único nit: `_tool_result_to_block` podría vivir en `application/adapters/` en vez de inline en orchestrator |
| **Security & tenant isolation** | 9/10 | Tenant scoping exhaustivo. -1 por falta de rate limit en voice endpoint (L4) |
| **Contract alignment** | 10/10 | 15/15 secciones del CONTRACT implementadas; decisiones §5/§9 documentadas en contrato |
| **Extension readiness** | 9/10 | 22 anchors con docs. -1 por L5 (SHIKI anchor sin doc pair) |
| **Test quality** | 8/10 | 660 passing con edge cases buenos. -2 por ausencia de test de integración DB real y rate limit |
| **Docs alignment** | 10/10 | CONTRACT + 5 docs operativos + UI-SPEC + INDEX. Navegación clara. |
| **TOTAL** | **55/60** | **91.6%** — apto para producción |

---

## §9 Recommendations (próximas iteraciones)

### Prioridad alta (1-2 sprints)
1. **Activar WhatsApp outbound** — extender `WhatsAppAdapter.send_rich_message` traduciendo bloques a WA Media API (messaging template + media). Es el test real de la abstracción canonical. Documentar en `channel-adapters.md`.
2. **Motor real de suggestions** — swap `use-suggestions.ts` stub por endpoint BE `POST /api/v1/copilot/suggestions` alimentado por completion-snapshot + route + conversation context. Anchor ya listo.
3. **Rate limit voice endpoint (L4)** — middleware con scope `copilot-media` en `/voice/upload-and-transcribe`.

### Prioridad media (sprint futuro)
4. **Refactor `_tool_result_to_block`** (M1) — mover a `application/adapters/tool_result_to_block.py` con handlers nombrados, tests aislados por handler.
5. **Refactor `_flatten_blocks`** (M2) — handlers nombrados en vez de lambdas inline para docstrings por tipo.
6. **Max file size configurable** (L3) — `settings.COPILOT_MEDIA_MAX_BYTES`.
7. **Filename en MediaUploadResponse** (L2) — FE evita derivar del File del cliente.
8. **Normalizar anchor arrows** (L1) — pick `→` consistente; gate en `test_copilot_anchors`.

### Prioridad baja (deuda tolerable)
9. **Integración DB roundtrip test** — `test_message_codec_integration.py` que valide persist→read en Postgres real contra `copilot_conversations.messages` JSONB.
10. **Backfill script `content → blocks`** — para consumers que quieran blocks en históricos. Opcional, no urgente.
11. **Sanitize NFC del legacy content** (M3) — en `message_codec._flatten_blocks` para mensajes antiguos con bytes corruptos.
12. **Doc `code-highlighting.md`** (L5) — documentar plan de integración Shiki + fallback.

### Fuera de scope (non-goals respetados)
- Generación AI de media (imágenes/audios sintéticos)
- Video streaming live
- Motor chips real con LLM

---

**Firma auditor:** self-audit post-implementación, 2026-04-21.
**Aprobación merge:** ✅ **APPROVED WITH MINOR ISSUES** — ninguno bloquea.
**Siguiente review:** tras activar WhatsApp outbound (valida extensión real del patrón canonical).
