# PR-2-litellm-proxy-integration

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-2-litellm-proxy-integration |
| Sprint padre | S3-copilot-llm-stack-convergence |
| PI padre | PI-2-copilot-improvement |
| Estado | ready (depends on PR-1) |
| Tipo | infra (introducir motor multi-provider centralizado) |
| Esfuerzo | M (~10 archivos, Docker svc + router refactor) |
| Owner PM | /pm |

## Problema

Stack actual `shared/infrastructure/llm/router.py` + `providers/{openai, kimi, _openai_compat}.py` mantiene cada provider como adapter custom. Cada nuevo provider = nuevo archivo + tests + maintenance. Adopción 2026 (research base): **LiteLLM Proxy de BerriAI** = OSS standard 40% adoption empresas LLMOps tier-1, 100+ providers nativos format OpenAI compatible, fallback chain automático, cost tracking nativo, virtual keys per-tenant, admin UI hot-swap sin restart, overhead <11μs.

JTBD Chris: "Como founder con stack multi-provider creciendo, no quiero mantener N adapters custom + N rate-limiters + N fallback chains. Quiero un motor único que hable con cualquier provider OpenAI-format."

## Outcome esperado

- LiteLLM Proxy en `docker-compose.yml` como svc dedicado (`visionarias_litellm`).
- `shared/infrastructure/llm/router.py` refactor: dispatch único via LiteLLM (unified OpenAI-format API endpoint).
- `providers/{openai, kimi, _openai_compat}.py` simplificados o eliminados (LiteLLM resuelve nativamente).
- Cost tracking automático via LiteLLM + sync con `model_pricing_snapshot` table.
- Virtual keys per-tenant configurables (cap budget, model allowlist, rate limit).

Métricas medibles:
- Latencia overhead p99 < 50ms (research: ~11μs proxy + retry semantics).
- Stack soporta agregar provider nuevo (ej: Anthropic Claude, Cohere, MiniMax) sin código nuevo (LiteLLM nativamente).
- Multi-provider fallback chain configurable via `litellm_config.yaml`.

## Walking skeleton (mínimo viable cohesivo)

1. **Docker compose svc** `visionarias_litellm`:
   - Image `ghcr.io/berriai/litellm:main-stable`
   - Port 4000 (API) + 4001 (admin UI)
   - Postgres connection (LiteLLM usa DB para hot-swap config + virtual keys + cost tracking)
   - Volume mount `litellm_config.yaml`
2. **`litellm_config.yaml`** initial:
   - Models: openai/gpt-4o-mini, openai/gpt-4o, deepseek/deepseek-v4-flash, deepseek/deepseek-reasoner, moonshot/kimi-k2.6
   - API keys via env (referenced from secrets)
   - Fallback chains: deepseek-v4-flash → openai/gpt-4o-mini (transparent retry on provider outage)
3. **Refactor `shared/infrastructure/llm/router.py`**:
   - Single endpoint: `LITELLM_BASE_URL=http://visionarias_litellm:4000/v1`
   - Use `openai.AsyncOpenAI(base_url=LITELLM_BASE_URL)` para todo provider routing
   - Settings.get_model resolve role → litellm_model_alias (e.g., NANO → "nano-default" → litellm dispatches to active model)
4. **Eliminar adapter providers redundantes**:
   - Marcar `providers/{openai, kimi, _openai_compat}.py` `@deprecated` o eliminar si test surfaces lo permiten
   - Mantener solo `LiteLLMProvider` adapter (`providers/litellm.py` nuevo) que implementa `LLMProvider` Protocol
5. **Cost tracking sync**:
   - Worker periódico (5min) sincroniza `litellm_pricing` table → `model_pricing_snapshot` Nicolify (preserva billing histórico immutable)
6. **Virtual keys per-tenant** (preparation S4):
   - Admin Streamlit `/admin/llm-virtual-keys` CRUD básico (UPDATE litellm.virtual_keys table)
   - Per-tenant key opcional (default = system key)
7. **Migration `116_litellm_pricing_sync_marker`** idempotente (audit table sync runs).

## Existing systems audit (architect-mandatory)

```bash
# Verificar antes proponer
grep -rn "router\.py\|llm.*adapter\|llm.*provider" src/shared/infrastructure/
grep -rn "AsyncOpenAI\|ChatOpenAI" src/  # quien instancia clients direct
docker ps | grep litellm  # ¿ya existe svc?
```

**Sistemas conocidos:**
- ✅ Sistema A (REPLACE): `shared/infrastructure/llm/router.py + providers/openai.py + kimi.py + _openai_compat.py` → reemplazar dispatch interno por delegación a LiteLLM Proxy. Mantener interface `LLMProvider` Protocol externa.
- 🆕 Sistema B (NEW infra layer justificada): LiteLLM Proxy svc Docker. Justificación: OSS estándar industry, NO se puede extender sistema A para cubrir 100+ providers + fallback chain + cost tracking + admin UI sin reinventar LiteLLM.

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A — Introducir LiteLLM Proxy + refactor router central | OSS standard 40% adoption, multi-provider gratis, admin UI hot-swap | Nuevo svc Docker, learning curve config YAML | **ELEGIDA** |
| B — Mantener adapters custom + agregar más providers manual | Sin nuevo svc | No escala — cada provider = N días dev. Anti-pattern documentado research | descartada |
| C — Usar LangChain unified ChatModel interface | Soporta multi-provider | LangChain runtime overhead + lock-in framework + worse multi-tenant | descartada |
| D — Build proxy custom Nicolify | Control total | 6+ semanas dev, mantenimiento eternal, NIH syndrome | descartada |

## Validación técnica preliminar

- **Modules afectados:**
  - `src/shared/infrastructure/llm/router.py` (REFACTOR)
  - `src/shared/infrastructure/llm/providers/` (DEPRECATE adapters individuales, NEW `litellm.py`)
  - `src/core/config.py` (add `LITELLM_BASE_URL` Setting)
  - `docker-compose.yml` + `docker-compose.dev.yml` (NEW svc)
  - `litellm_config.yaml` NEW
  - `backend/alembic/versions/116_*` migration sync marker
- **Blockers conocidos:** ninguno bloqueante. Postgres ya en stack (LiteLLM usa Postgres connection).
- **Tiempo estimado:** 1 architect + 1 builder con auto-loop. Probable main thread takeover si scope crece.
- **Dependencias:** PR-1 S3 shipped (cleanup convergencia ModelTier→ModelRole) — sin esto, refactor inconsistente.

## Decisiones diferidas (explícitas)

- **DB registry custom + admin UI Streamlit** runtime hot-swap = S4 PR-1.
- **Virtual keys per-tenant CRUD UI completo** = S4 (admin UI introduces it). PR-2 S3 solo prep básico.
- **GrowthBook integration** = S4 PR-2.

## Out of scope

- DB registry custom (S4)
- GrowthBook (S4)
- Eval gate pre-promote (S5)
- Embeddings + sales_agent voice

## Copilot-first checklist

- [x] ¿Operable conversacional copilot? — no (infra)
- [x] Tools nuevos — ninguno
- [x] Cards/UI — admin Streamlit `/admin/llm-virtual-keys` (admin-only)

## Agentes / skills recomendados

| Fase | Agente/skill | Entregable |
|---|---|---|
| Pre-design | `nicolify-architect` + `copilot-expert` | CONTRACT.md con LiteLLM Proxy config + refactor plan |
| Implementation | `nicolify-backend` + `copilot-expert` | IMPL-LOG.md + tests + commit |
| Audit | `nicolify-backend-auditor` (auto-spawn) | REVIEW.md PASS verificación overhead p99 + multi-provider funcional |
| Cierre | `/pm` | RESULT.md + current-state/copilot.md lineage |

## Surface impactada

| Tipo | Path | Cambio |
|---|---|---|
| Docker | `docker-compose.yml` + `docker-compose.dev.yml` | NEW svc visionarias_litellm |
| Config | `litellm_config.yaml` | NEW |
| Settings | `src/core/config.py` | NEW field LITELLM_BASE_URL |
| Refactor | `src/shared/infrastructure/llm/router.py` | dispatch via LiteLLM endpoint |
| NEW provider | `src/shared/infrastructure/llm/providers/litellm.py` | LLMProvider Protocol impl |
| Deprecate | `providers/openai.py + kimi.py + _openai_compat.py` | @deprecated o DELETE post-verificación |
| Migration | `alembic/versions/116_litellm_pricing_sync_marker.py` | NEW idempotente |
| Worker | `src/workers/litellm_pricing_sync_task.py` | NEW (5min sync) |
| Admin | `admin/pages/llm_virtual_keys.py` | NEW Streamlit basic CRUD |
| Tests | `tests/shared/infrastructure/llm/test_litellm_router.py` | NEW |
| current-state | `current-state/copilot.md` | append cap "LiteLLM Proxy motor multi-provider" |

## Tests requeridos (TDD)

- `test_litellm_router.py` — dispatch correcto per role, fallback chain transparent, cost tracking sync
- `test_litellm_provider.py` — LLMProvider Protocol compliance + retry/timeout
- Integration test Docker compose — svc visionarias_litellm starts + health endpoint OK + dispatch a openai mock works
- Migration test idempotente
- Arch fitness: `test_llm_routing_ssot.py` allowlist update post-refactor (providers individuales pueden quedar legacy o eliminados)

## Aceptación

- [ ] Tests verde
- [ ] Lint/type check verde
- [ ] IMPL-LOG.md completo
- [ ] REVIEW.md PASS
- [ ] RESULT.md
- [ ] current-state/copilot.md updated
- [ ] Decisiones registradas
- [ ] Docker compose up: `docker compose ps` muestra `visionarias_litellm` healthy
- [ ] Dispatch verificado: query LLM via Settings.get_model retorna response correctly via LiteLLM
- [ ] Latencia overhead medido p99 < 50ms
- [ ] `litellm_config.yaml` versioned in repo

## Riesgos

| Riesgo | Mitigación |
|---|---|
| LiteLLM Proxy single point of failure | Docker compose restart policy + health check + fallback chain config | 
| Latencia overhead > spec (>50ms p99) | Benchmark inline pre-merge + revertir si breach |
| LiteLLM config YAML sintaxis invalid bloque deploy | CI validate `litellm_config.yaml` schema pre-merge |
| Dependencia DB Postgres LiteLLM conflicta con migrations Nicolify | LiteLLM usa schema separado o tablas prefijo `litellm_*` (config) |
| Cost tracking sync drift | Worker idempotente + audit table runs |
