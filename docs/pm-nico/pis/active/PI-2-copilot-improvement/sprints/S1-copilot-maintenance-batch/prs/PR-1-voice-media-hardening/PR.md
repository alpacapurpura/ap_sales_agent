# PR-1-voice-media-hardening

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-1-voice-media-hardening |
| Sprint padre | S1-copilot-maintenance-batch |
| PI padre | PI-2-copilot-improvement |
| Estado | ready |
| Tipo | infra + bug + test |
| Esfuerzo | M |
| Owner PM | /pm |
| Claimed by session | — |

## Problema (user-facing)

Endpoints copilot media+voice tienen 3 bugs latentes que comprometen costo + calidad sin que user lo vea:
1. `/voice/upload-and-transcribe` sin rate limit → tenant abusivo agota cuota Whisper compartida
2. `_MAX_FILE_BYTES` y `_MAX_AUDIO_BYTES` hardcoded en 25MB sin override env ni per-tenant
3. Tests media/voice usan MagicMock — ningún test verifica roundtrip DB real

JTBD invisible: "como Nicolify owner, quiero que un tenant no pueda quemar mi cuota Whisper subiendo audios indefinidamente, y quiero subir el límite a Pro tier sin redeploy".

## Outcome esperado

- Rate limit voice/upload sliding window con default env + override per-tenant editable desde Streamlit admin
- `COPILOT_MEDIA_MAX_BYTES` única constante leída de env, aplicada media + voice (DRY), per-tenant override opcional
- ≥1 test integración DB real cubre persist+read de mensajes con blocks (no MagicMock)
- Métrica observable: `copilot_voice_rate_limit_hits` cuando se rechaza request

## Walking skeleton (mínimo viable cohesivo)

1. Centralizar config: `core/config.py` lee `COPILOT_MEDIA_MAX_BYTES` (default 25MB), `COPILOT_VOICE_RATE_LIMIT_PER_MIN` (default 10)
2. Tabla `copilot_tenant_limits` (tenant_id, voice_rpm_override, media_max_bytes_override, updated_at)
3. `RateLimiter` Redis sliding window en `shared/rate_limit/` (reusable futuro)
4. Endpoint voice + media: leer config global → override per-tenant → enforce
5. Streamlit admin panel `pages/copilot_limits.py` con CRUD tenant overrides
6. Test integración: pytest fixture `db_session` real (no mock) → upload media → assert row + blocks shape

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A: rate limit en `shared/rate_limit/` reusable + Redis sliding window | Reusable PR-1 campañas + sales_agent. Lib redis-py ya en stack | LOC mayor (helper + tests) | ELEGIDA |
| B: rate limit decorator inline en `voice.py` | Scope mínimo PR-1 | No reusable. Code duplication futuro | descartada |
| C: rate limit middleware FastAPI global | Cubre todo el módulo | Overkill para 1 endpoint | descartada |

## Validación técnica preliminar (Technical Sanity Check)

- Modules afectados: `modules/copilot/api/{media,voice}.py`, `core/config.py`, `shared/rate_limit/` (nuevo), `admin/pages/copilot_limits.py`
- Blockers conocidos: `shared/rate_limit/` no existe — architect crea boundary
- Tiempo estimado: 1 sesión architect + 1-2 sesión builder + 1 sesión auditor
- Alternativas técnicas: rate limit con `slowapi` lib (descartado — Redis sliding window manual es ~30 LOC + cero dep nueva)

## Decisiones diferidas (explícitas)

- ¿Rate limit per-tenant también para `/media/upload` (no solo voice)? → POST-architect decide en CONTRACT
- ¿Métrica `copilot_voice_rate_limit_hits` va a Prometheus o solo structlog? → POST-architect decide

## Out of scope

- Rate limit otros endpoints copilot (chat, kb, etc.) — solo voice + media
- UI cards en frontend para mostrar rate limit hit (admin Streamlit es enough hoy)
- Backfill historical limits (tabla nueva = empty start)

## Copilot-first checklist

- [ ] ¿Operable conversacional desde copilot? **NO** — admin Streamlit es interfaz interna Nicolify (Chris), no tenant-facing
- [ ] ¿Qué tools nuevos requiere? Ninguno — copilot no expone rate-limit config a tenants
- [ ] ¿Cards/UI nueva? No (Streamlit admin existente extendido)
- [x] Si NO copilot → razón documentada: feature interna Nicolify para protección cuota Whisper, no flujo tenant

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt pre-coce | Entregable esperado |
|---|---|---|---|
| Pre-design | `nicolify-architect` + `copilot-expert` | `prompts/01-architect-start.md` | `CONTRACT.md` |
| Implementation | `nicolify-backend` + `copilot-expert` | `prompts/02-builder-start.md` | code + tests + IMPL-LOG.md |
| Audit | `nicolify-backend-auditor` + `copilot-expert` | `prompts/03-auditor-start.md` | `REVIEW.md` |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/copilot.md` update |

## Surface impactada

| Tipo | Path / nombre | Cambio |
|---|---|---|
| Tabla DB | `copilot_tenant_limits` | nueva (idempotente) |
| Config | `core/config.py` settings: `COPILOT_MEDIA_MAX_BYTES`, `COPILOT_VOICE_RATE_LIMIT_PER_MIN` | nuevas |
| Helper | `shared/rate_limit/sliding_window.py` | nuevo |
| API endpoint | `modules/copilot/api/voice.py` POST `/voice/upload-and-transcribe` | rate limit enforced |
| API endpoint | `modules/copilot/api/media.py` POST `/media/upload` | max-bytes via config + per-tenant override |
| Repository | `modules/copilot/infrastructure/repositories/tenant_limits_repo.py` | nuevo |
| Streamlit page | `admin/pages/copilot_limits.py` | nueva |
| Tests | `backend/tests/modules/copilot/test_voice_rate_limit.py`, `test_media_max_bytes.py`, `test_media_db_roundtrip.py` | nuevos |
| current-state/ | `current-state/copilot.md` | append capability "Rate limit voice + per-tenant media limits" + lineage |

## Tests requeridos (TDD)

- `test_voice_rate_limit.py` — 11 reqs/min con default 10 → 11vo retorna 429 + estructura error JSON
- `test_voice_rate_limit_per_tenant_override.py` — tenant con override 20 → 11vo pasa
- `test_media_max_bytes_env.py` — env `COPILOT_MEDIA_MAX_BYTES=10485760` (10MB) → upload 11MB falla 413
- `test_media_db_roundtrip.py` — POST /media/upload → fixture db_session real → assert row exists + blocks structure
- `test_tenant_limits_crud.py` — CRUD repo per-tenant overrides

## Aceptación

- [ ] Tests verdes (5 nuevos + existentes intactos)
- [ ] Lint/type check verdes (`ruff` + `mypy strict`)
- [ ] Migración alembic idempotente (`IF NOT EXISTS`)
- [ ] `IMPL-LOG.md` completo con sub-deliverables + commits
- [ ] `REVIEW.md` con verdict PASS (gate `/test-backend`)
- [ ] `RESULT.md` escrito por PM
- [ ] `current-state/copilot.md` actualizado con capability lineage
- [ ] Decisiones registradas en `decisions.md` PI-2

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Redis sliding window requiere lock distribuido si hay race | Usar Redis INCR + EXPIRE atómico, sin lock |
| Streamlit admin se rompe al cargar tabla nueva | Migración corre antes de redeploy admin (orden CI) |
| Tests DB roundtrip requieren postgres en CI | `/test-backend` ya levanta postgres docker; usar mismo fixture |
| Per-tenant override sin valor → caer a default | Repo retorna `None` → caller usa default config |
