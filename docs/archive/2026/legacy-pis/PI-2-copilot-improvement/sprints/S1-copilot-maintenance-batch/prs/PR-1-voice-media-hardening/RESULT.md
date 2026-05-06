# RESULT — PR-1-voice-media-hardening

> Owner: `/pm`. Cierre del loop. PM extrajo info de IMPL-LOG.md + REVIEW.md + commits.

## Meta cierre

| Campo | Valor |
|---|---|
| Estado final | shipped |
| Fecha cierre | 2026-04-29 |
| Commits principales | `ebf25d4c` (CONTRACT) · `2d0b9e0e` (feat código + tests + admin + IMPL-LOG) · `caacdffa` (fix auto-iter 1: 410 Gone legacy) · `8954eda5` (REVIEW PASS) |
| Branch merged a | development |
| Verdict auditor | PASS tras 1 iter auto-fix |

## Outcome real vs esperado

| Aspecto | Esperado | Real | Delta |
|---|---|---|---|
| Rate limit `/voice/upload-and-transcribe` | tenant cap configurable | 6 RPM default + per-tenant override DB + bucket Redis sliding-window | ✅ cumplido |
| `_MAX_AUDIO_BYTES` config | env override + per-tenant | env `COPILOT_MEDIA_MAX_BYTES` (default 25 MiB) + override DB CHECK ∈ [1 MiB, 100 MiB] | ✅ cumplido |
| Rate limit `/media/upload` | bucket separado | bucket `copilot-media-upload` 30 RPM default + per-tenant override | ✅ cumplido |
| Tests roundtrip DB real | reemplazar MagicMock | 42 tests verdes (domain, repo, resolver, voice rate limit, media env, media DB, admin smoke) | ✅ cumplido |
| Eliminar legacy `/voice/transcribe` | remove (Q1 PM) | **deprecated 410 Gone** + `X-Deprecation-Notice` (FE migration → PR follow-up cross-stack) | ⚠️ parcial — BE-side done, FE migration diferida |
| Admin Streamlit per-tenant | CRUD overrides | `pages/copilot-limits.py` + `modules/copilot_limits.py` con list/upsert/soft-delete | ✅ cumplido |
| Migration idempotente | raw SQL | `085_copilot_tenant_limits.py` con 2 tablas + 4 índices + 3 CHECKs (`IF NOT EXISTS` + partial unique tenant_id WHERE deleted_at IS NULL) | ✅ cumplido |

Veredicto general: ✅ cumplido (con FE migration legacy diferida).

## Surface entregada

| Tipo | Path | Notas |
|---|---|---|
| Tabla DB | `copilot_tenant_limits` | overrides per-tenant (1:1 partial unique vivo) |
| Tabla DB audit | `copilot_tenant_limits_audit` | append-only atomic con upsert/soft_delete |
| Migration | `backend/alembic/versions/085_copilot_tenant_limits.py` | raw SQL idempotente |
| Domain | `backend/src/modules/copilot/domain/tenant_limits.py` | frozen dataclass + invariantes |
| Models | `backend/src/modules/copilot/infrastructure/models/{tenant_limits,tenant_limits_audit}_model.py` | SQLA 2.0 |
| Repos | `backend/src/modules/copilot/infrastructure/repositories/tenant_limits_repository.py` | sync (Streamlit) + async (FastAPI) |
| Service | `backend/src/modules/copilot/application/services/limits_resolver.py` | env defaults + override + DB-error fallback |
| API DTO | `backend/src/modules/copilot/api/tenant_limits_dto.py` | Pydantic v2 |
| API endpoints | `backend/src/modules/copilot/api/voice.py` + `media.py` | rate limit por bucket + tenant-scoped max_bytes + 410 Gone legacy |
| Settings | `backend/src/core/config.py` | 3 env settings COPILOT_* (VOICE_RATE_LIMIT_PER_MIN=6, MEDIA_MAX_BYTES=26214400, MEDIA_UPLOAD_RATE_LIMIT_PER_MIN=30) |
| Admin module | `backend/src/admin/modules/copilot_limits.py` | sync repo + Streamlit forms |
| Admin page | `backend/src/admin/pages/copilot-limits.py` | nav entry registrada en `app.py` |
| Tests | `backend/tests/modules/copilot/test_*.py` × 7 + `tests/admin/test_copilot_limits_smoke.py` | 42 tests verdes |

## Capacidades agregadas (lineage para current-state)

```md
### Cap: Rate limit voice + per-tenant media/voice limits
- Introducida: PR-1 (PI-2, S1, commit `2d0b9e0e` + `caacdffa`, 2026-04-29)
- Estado: live
- Operable copilot: no (infra capa BE — protege Whisper budget + cuota tenant)
- Surface admin: Streamlit `/admin/copilot-limits` (CRUD overrides per-tenant)
- Defaults: voice 6 RPM, media 25 MiB, /media/upload 30 RPM
- Cap upper override media: 100 MiB (CHECK editable post planes per-tenant)
- Legacy `/voice/transcribe`: 410 Gone (FE migration → PR follow-up)
```

## Decisiones tomadas durante implementación

| ID | Decisión | Razón | Origen |
|---|---|---|---|
| D-1 | Reuse `core/rate_limit.py` (no `shared/rate_limit/` nuevo) | Helper Redis sliding-window ya in-use copilot/api/chat.py — preserva ratchet copilot 22 frozen + DRY | CONTRACT §0 |
| D-2 | Tabla audit separada `copilot_tenant_limits_audit` | Append-only avoid write churn tabla principal + queries históricas | Q2 PM |
| D-3 | Default 6 RPM voice (no 10/20) | Cost-based: $0.006/min Whisper × 6 = $0.036/min/tenant cap | Q3 PM |
| D-4 | Cap upper 100 MiB media (no 500 MiB) | Industry standard SaaS microempresarios (Slack/Notion/Intercom). CHECK editable cuando lleguen planes Pro | Q4 PM |
| D-5 | Rate limit `/media/upload` ENTRA en este PR | Storage R2 confirmado vía `AssetsService.upload_asset` — cap independiente de bytes | Q5 PM |
| D-6 | Legacy `/voice/transcribe` → 410 Gone (no remove) | FE en `voice-api.ts:26` lo sigue llamando — FE migration cross-stack diferida PR follow-up | Auditor finding cat 12 → PM auto-fix iter 1 |
| D-7 | Migration prod-clone test diferido | Requiere docker exec activo — Chris responsable en `/test-backend` o pase prod | IMPL-LOG |

## Métricas medidas

| Métrica | Baseline | Cierre PR | Delta |
|---|---|---|---|
| Tests copilot/admin PR-1 | 0 (nuevos) | 42 verdes | +42 |
| Arch fitness | 649 | 649 | 0 (sin regresión) |
| Mypy errors archivos PR-1 | 0 | 0 | 0 |
| Iteraciones auto-fix | — | 1 | — (loop nuevo probado end-to-end) |

## Deuda técnica generada

| Item | Razón | Sprint destino |
|---|---|---|
| FE migration `/voice/transcribe` legacy → `/voice/upload-and-transcribe` | BE retorna 410 Gone, FE call rompe sin fallback. Cross-stack | S1 PR-4 (cross-stack opcional) o S2 |
| `RateLimitExceeded` message hardcoded "30 mensajes por minuto" | Pre-existente baseline `core/rate_limit.py`. Refactor parametrizable | S2+ |
| Migration prod-clone test execution | Diferido a pase prod (Chris docker exec) | Pre-pase prod |

## Update obligatorios hechos

- [x] `current-state/copilot.md` actualizado con capability lineage (sección "Capacidades actuales")
- [ ] `decisions.md` PI append (siguiente turno PM)
- [ ] Sprint `learnings.md` append (siguiente turno PM)
- [x] Capability legacy deprecada documentada (`/voice/transcribe` 410 Gone con plan migración)
- [ ] Última PR del sprint: NO (S1 tiene PR-2 + PR-3 pendientes)

## Lecciones para process-learnings

1. **Builder agents confunden paths cuando hay PRs con mismo número en PIs distintos** (PR-1 PI-1 vs PR-1 PI-2). Mitigación: regla M7 nueva en `parallel-safety.md` + prompts builder con prefijo PI explícito.
2. **Auto-loop builder→auditor→fix funciona** — verdict PASS tras 1 iter aplicando fix Q1 drift. Skill `pm` updated + templates `02-builder-start.md` reescritos para flujo nuevo.
3. **Reglas git INVIOLABLE** establecidas (NO pull, NO branch, NO force, NO revert sin aprobación) post incidente paralelo. CLAUDE.md + `.claude/rules/{parallel-safety,git-safety}.md` updated.

## Próximo paso PM

PR-2-suggestions-engine architect → spawn `nicolify-architect` con prompt `prompts/01-architect-start.md`.

---

PR-1 **shipped**. PM cierra archivo. Loop completo.
