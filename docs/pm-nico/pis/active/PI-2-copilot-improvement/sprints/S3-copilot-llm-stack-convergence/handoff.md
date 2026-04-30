# Handoff — S3 → S4

> Sprint S3-copilot-llm-stack-convergence done 2026-04-30.
> Next: S4-copilot-model-registry-runtime (PR-1 DB registry + admin UI + PR-2 GrowthBook per-tenant).

## Estado entregado por S3

### LLM stack convergencia completa

| Component | Estado |
|---|---|
| ModelRole único SSoT (`src.core.enums.ModelRole`) | ✅ live (S3 PR-1) |
| Capa duplicada `copilot/infrastructure/llm/` eliminada | ✅ DELETED total (S3 PR-1) |
| Allowlist `KNOWN_LEGACY_LLM_FILES` arch fitness | ✅ 0 entries mantenido |
| `.env.example` DeepSeek V4-Flash NANO+FAST | ✅ activo (S3 PR-1) |
| LiteLLM Proxy Docker svc `visionarias_litellm` | ✅ docker-compose declared (S3 PR-2) |
| `LiteLLMService` adapter único dispatch | ✅ shipped (S3 PR-2) |
| `MultiRoleLLMRouter` toggle-based refactor | ✅ shipped (S3 PR-2) |
| Migration 116 `visionarias_litellm_db` | ✅ shipped idempotente (S3 PR-2) |
| Recorder D-7 strip provider prefix | ✅ shipped (S3 PR-2) |
| Admin Streamlit `/admin/llm-virtual-keys` read-only | ✅ shipped (S3 PR-2) |
| 4 tests arch fitness LLM SSoT verde | ✅ test_llm_routing_ssot.py (3 PR-1 + D-18 PR-2) |

### Tests + quality gates baseline

- 791 tests verde (incluye 24 PR-2 nuevos)
- Lint: 0 errors PR-2 surface
- Format: 29 files clean
- Arch fitness: 4 tests verde (allowlist 0 mantenido)

## Decisiones cross-PR S3

| # | Decisión | PR | Rationale |
|---|---|---|---|
| D-CROSS-1 | DELETE > DEPRECATE shims | PR-1 | Cero `@deprecated` shims = cero deuda futura |
| D-CROSS-2 | Toggle emergency rollback OK temporary deuda | PR-2 | `LITELLM_PROXY_ENABLED=False` permite rollback sin redeploy. Eliminación física S4 PR-1 post-1-sprint verification |
| D-CROSS-3 | DB separada Prisma vs Alembic isolation | PR-2 | Sin esto, Prisma intentaría aplicar al schema general de Alembic |
| D-CROSS-4 | Cost tracking SSoT inmutable preservado | PR-2 | `model_pricing_snapshot` Nicolify NO se migra. LiteLLM auxiliar opcional |
| D-CROSS-5 | Allowlist=0 enforced ratchet | PR-1+PR-2 | NEW LAYER LiteLLM Proxy NO crece allowlist (D-18 usa AST scan distinto mecanismo) |

## Decisiones diferidas a S4

| Item | Razón defer | Sprint destino |
|---|---|---|
| Eliminación física legacy adapters (`openai.py`, `_openai_compat.py`, `deepseek.py`, `kimi.py`, `qwen.py`) | Verification 1-sprint en prod toggle ON | S4 PR-1 |
| `gemini.py` legacy elimination spike | Architect Q3 — spike 1 día verify Gemini en LiteLLM Proxy | S4 PR-1 |
| Master key rotation policy doc `docs/ops/` | Architect Q1 — defer S4 admin UI virtual keys CRUD | S4 PR-1 |
| Nicolify-friendly aliases (e.g., `nano-default` → `deepseek/deepseek-v4-flash`) | Architect Q5 — admin UI hot-swap lo justifica | S4 PR-1 |
| Integration test latency overhead (D-10) | Mock infra LiteLLM Proxy + OpenAI direct | S4 PR-1 admin UI workflow integration |
| Integration test fallback chain (D-5) | Mock LiteLLM Proxy 503 simulation | S4 PR-1 |
| `docker-compose.prod.yml` edit | Builder truncó pre-edit, post-stable verification dev | Pre-deploy prod task separada |

## Surface S4 disponible

### Tablas DB

- `model_pricing_snapshot` (Nicolify SSoT inmutable) — append-only, billing histórico
- `visionarias_litellm_db.LiteLLM_*` (Prisma-managed, cero Nicolify ownership):
  - `LiteLLM_VerificationToken` (virtual keys)
  - `LiteLLM_UserTable`, `LiteLLM_TeamTable` (spend tracking)
  - `LiteLLM_BudgetTable` (budget caps per key)
  - `LiteLLM_ModelTable` (models hot-swap cuando store_model_in_db=True ya activo)

### APIs LiteLLM Proxy

- `POST /v1/chat/completions` (OpenAI-compat, único consumer = backend Nicolify via LiteLLMService)
- `POST /key/generate`, `GET /key/info`, `POST /key/block` (admin endpoints — solo Streamlit con master key)
- `POST /model/new`, `GET /model/info`, `DELETE /model/delete` (admin endpoints S4 hot-swap)
- `GET /health/readiness` (Docker healthcheck)

### Settings extension points

- `Settings.LITELLM_BASE_URL` — endpoint del proxy (default Docker internal)
- `Settings.LITELLM_MASTER_KEY` — auth proxy admin
- `Settings.LITELLM_SALT_KEY` — encryption credentials (NO cambiar post-deploy)
- `Settings.LITELLM_PROXY_ENABLED` — toggle emergency rollback

### Admin Streamlit base

- `admin/registry.py` PageSpec patrón cementado
- `admin/pages/llm-virtual-keys.py` thin wrapper read-only S3 → S4 EXTEND CRUD
- `admin/modules/llm_virtual_keys.py` HTTP GET `/key/info` — S4 EXTEND POST `/key/generate` + DELETE

## Recomendación agentes S4

### S4 PR-1 db-registry-admin-ui (L scope ~12-15 archivos)

| Fase | Agente/skill | Entregable |
|---|---|---|
| Pre-flight | `nicolify-context-builder` (Haiku) | CONTEXT-BRIEF.md |
| Pre-design | `nicolify-architect` + `copilot-expert` + `backend-expert` (admin-panel skill) | CONTRACT.md con `llm_role_binding` table + `LLMConfigService.resolve` cache 60s + admin UI workflow |
| Implementation | `nicolify-backend` (auto-spawn auditor) — expectativa main thread takeover | IMPL-LOG.md + tests + commit |
| Audit | `nicolify-backend-auditor` | REVIEW.md PASS |
| Cierre | `/pm` | RESULT.md + current-state lineage |

### S4 PR-2 growthbook-per-tenant-override (M scope ~10 archivos)

Mismo workflow. Extra: research date-aware GrowthBook latest stable version + Docker svc spec + AI Configs producto dedicado.

## Riesgos S4

| Riesgo | Mitigación |
|---|---|
| Cache invalidation race condition (pod1 actualizado, pod2 stale post hot-swap) | Pub/sub Redis con timestamp + verify cache version on each request (CONTRACT spec) |
| LiteLLM Proxy svc no levantado en dev | Pre-S4 PR-1: `docker compose up litellm` + verify healthcheck OK + manual dispatch test |
| Sesión paralela PI-1 toca admin Streamlit (campaigns) | Regla M8: leer + extend. PI-1 PR-7 outbound NO toca admin LLM (separación clara) |
| Migration 117 `llm_role_binding` falla en prod-clone test | Test obligatorio `make migration-test` antes merge |
| Per-tenant override leak entre tenants (S4 PR-2) | Tests isolation explícitos + arch test (CONTRACT spec) |

## Estado verificable post-S3 (next session start)

```bash
# Allowlist target alcanzado
cd backend && .venv/bin/pytest tests/architecture/test_llm_routing_ssot.py -v
# 4/4 PASSED — KNOWN_LEGACY_LLM_FILES = set() (0 entries) + D-18 nuevo

cd backend && grep -rn "ModelTier" src/modules/copilot/
# 1 hit en docstring routing_policy.py:7 (comment histórico — cleanup S5 PR-2)

cd /home/chris/AISALESHT && find backend/src/modules/copilot/infrastructure/llm/
# find: 'No such file or directory' (eliminado S3 PR-1)

cat .env.example | grep -E "^AI_(MODEL|PROVIDER)_(NANO|FAST)|^LITELLM_"
# AI_MODEL_NANO=deepseek-v4-flash
# AI_MODEL_FAST=deepseek-v4-flash
# AI_PROVIDER_NANO=deepseek
# AI_PROVIDER_FAST=deepseek
# LITELLM_BASE_URL=http://visionarias_litellm:4000/v1
# LITELLM_MASTER_KEY=sk-litellm-master-dev
# LITELLM_SALT_KEY=sk-litellm-salt-dev
# LITELLM_PROXY_ENABLED=true

ls litellm_config.yaml
# litellm_config.yaml exists (SSoT 6 modelos + fallback chain)

ls backend/src/shared/infrastructure/llm/providers/litellm.py
# litellm.py exists (197 LOC)

docker compose config --services | grep litellm
# litellm (svc declared)
```

Verde = handoff S4 OK.

## Próximo paso

S4 PR-1 db-registry-admin-ui. Workflow standard: claim → architect CONTRACT → builder auto-loop con expectativa main thread takeover → close.
