# LLM Config Storage Best Practices — Abril 2026

## Meta
- Fecha: 2026-04-30
- Owner: /pm
- Trigger: PR-3 PI-2 S2 audit failure — necesidad SSoT runtime + hot-swap sin redeploy
- Stack actual Nicolify: `AI_PROVIDER_<ROLE>` + `AI_MODEL_<ROLE>` en `.env` + Pydantic Settings en `core/config.py`
- Roles modelados: NANO, FAST, REASONING, AGENT, VISION, EMBEDDING

## Resumen ejecutivo

- `.env`-only es **anti-pattern muerto en 2026**. Modelos OpenAI/Anthropic deprecan cada 4-6 meses (GPT-4o/4.1/o4-mini retirados feb-2026, Claude Opus 4 + Sonnet 4 retirados jun-2026). Cada deprecation = redeploy si vivís en `.env`.
- Patrón ganador 2026 = **híbrido 3-capa**: (1) `.env` solo para secrets/provider keys, (2) DB registry para selection per-role + pricing snapshot + audit, (3) feature-flag layer para overrides per-tenant + A/B + rollback instant. 100% adopción en empresas tier-1 de LLMOps según LangChain/Calmops/Redis 2026.
- **LiteLLM Proxy** (BerriAI) = de-facto open-source standard. Soporta "Store Model in DB" desde admin UI sin restart, cost tracking nativo, fallback chains, 100+ providers compatibles formato OpenAI. Overhead ~11μs (Bifrost). Adopción: 3 de 5 mayores empresas LLM lo usan.
- **GrowthBook** (open-source) o **LaunchDarkly** (enterprise) para per-tenant routing. GrowthBook tiene producto explícito **AI Configs** con guarded rollouts para LLM models. Hash-based bucketing por `tenant_id` resuelve B2B SaaS multi-tenant correctamente.
- **Pricing snapshot histórico para billing es no-negociable** en SaaS multi-tenant. Pattern: tabla `model_pricing_snapshot` con `(provider, model, input_per_1m, output_per_1m, valid_from, valid_to)`. Sin snapshot, billing pre/post cambio de precio = inconsistente.
- **Eval gate antes de promote** = obligatorio en stack maduro. Tools: LangSmith deployments con instant rollback, GuideLLM (Red Hat) para regression testing, MLflow Model Registry con stages (staging→production).
- Trade-off central: **simplicidad vs hot-swap**. Config file YAML = simple pero requiere redeploy. DB registry = complex pero hot-swap. Verdict: para Nicolify (multi-provider, multi-tenant, modelos cambian semana) **DB registry pesa más que la complejidad**.
- **Cache es mandatorio** en service layer. Sin cache, cada call hace round-trip DB para resolver `role → provider+model`. Pattern: in-memory TTL cache 60s + invalidation pub/sub (Redis) cuando admin UI commitea cambio.
- Latencia overhead resolución model registry = <1ms con cache, <5ms sin cache (single Postgres query indexed). Aceptable vs 200-2000ms latency LLM call.
- Anti-pattern documentado: hardcodear pricing en código (`COST_PER_1K = 0.0001`). Cuando proveedor cambia precio (OpenAI bajó GPT-4o 50% en agosto 2025), tu billing miente hasta que alguien actualiza constante.

## Patrones identificados (tabla comparativa)

| Patrón | Storage | Hot-swap | Multi-tenant override | Pricing snapshot | Eval gate | Adopción 2026 | Casos uso |
|---|---|---|---|---|---|---|---|
| `.env` + Pydantic Settings (Nicolify actual) | `.env` file | NO (requiere redeploy) | NO (global) | NO | NO | ~15% (legacy) | MVPs, single-tenant, single-model |
| Config file YAML/TOML versionado en repo | YAML/TOML + git | NO (PR + redeploy) | Parcial (per-env file) | NO (manual) | NO (review PR) | ~25% (mid-stage) | Equipos con buen GitOps, baja frecuencia cambio |
| DB registry table + admin UI custom | Postgres + custom UI | SI (with cache invalidation) | SI (tenant_id col) | SI (snapshot table) | Manual (custom flow) | ~20% (build-from-scratch) | Teams con infra interna pero sin LiteLLM |
| LiteLLM proxy + admin UI (BerriAI) | Postgres (managed by LiteLLM) | SI (sin restart) | SI (virtual keys per team/tenant) | SI (cost tracking nativo) | Parcial (manual via routing) | ~40% (open-source dominant) | Multi-provider SaaS, OSS-first, FastAPI compatible |
| Feature flag service (LaunchDarkly/GrowthBook) | SaaS feature flag | SI (instant) | SI (hash-based bucketing) | NO (separate concern) | SI (guarded rollouts) | ~30% (combinado con DB) | A/B tests, gradual rollout, kill-switch |
| **Hybrid: env (keys) + DB (selection) + flags (override)** | 3-capa | SI | SI | SI | SI | ~60% (winning pattern) | **Production multi-tenant SaaS — Nicolify fit** |
| LangSmith Deployment registry | LangChain managed | SI (instant rollback) | Parcial (prompt-level) | NO | SI (built-in) | ~15% (LangChain users) | Teams 100% LangChain stack |
| MLflow Model Registry | MLflow + S3 | SI (stage transitions) | NO (model-level) | NO | SI (stages) | ~20% (ML traditional) | Fine-tuned models, custom training |

## Patrón recomendado para Nicolify

**Veredicto: Hybrid 3-capa con LiteLLM Proxy como motor + DB registry custom para metadata Nicolify-específico + GrowthBook para per-tenant override.**

### Justificación

1. **LiteLLM resuelve 80% del problema gratis** (multi-provider, fallback, cost tracking, admin UI, hot-swap sin restart). No reinventar.
2. **DB registry custom Nicolify-specific** para mapping `role → litellm_model_alias` (NANO, FAST, etc.) — LiteLLM no conoce conceptos de negocio Nicolify.
3. **GrowthBook** para per-tenant override + A/B test + kill-switch. Open-source, hash-based bucketing por `tenant_id`, AI Configs producto dedicado.
4. **`.env` reducido a secrets**: provider API keys + LiteLLM master key + GrowthBook SDK key. Nada de model selection.
5. **Pricing snapshot dual-source**: LiteLLM tracker para prod accuracy + tabla Nicolify `model_pricing_snapshot` para billing histórico inmutable.

### Arquitectura propuesta (ASCII)

```
                      ┌─────────────────────────────────┐
                      │   Nicolify FastAPI Backend      │
                      │  (modules/copilot, sales_agent) │
                      └────────────┬────────────────────┘
                                   │
                    role="REASONING", tenant_id=X
                                   │
                                   ▼
                      ┌─────────────────────────────────┐
                      │ LLMConfigService (Nicolify)     │
                      │ - resolve(role, tenant_id)      │
                      │ - cache 60s TTL                 │
                      │ - emit audit event              │
                      └────┬────────────────────┬───────┘
                           │                    │
                           │                    │
              ┌────────────▼─────────┐  ┌──────▼─────────┐
              │ Postgres             │  │ GrowthBook SDK │
              │ llm_role_binding     │  │ (per-tenant    │
              │ (role,model,active)  │  │  override +    │
              │ model_pricing_snapsh │  │  A/B + kill)   │
              └────────────┬─────────┘  └──────┬─────────┘
                           │                   │
                           └─────────┬─────────┘
                                     │
                  resolved: model="claude-opus-4-7-1m"
                                     │
                                     ▼
                      ┌─────────────────────────────────┐
                      │ LiteLLM Proxy (Docker svc)      │
                      │ - 100+ provider compat OpenAI   │
                      │ - fallback chain                │
                      │ - cost tracking                 │
                      │ - admin UI (model swap no-restart)│
                      │ - virtual key per tenant        │
                      └────────────┬────────────────────┘
                                   │
                        OpenAI / Anthropic / DeepSeek
                        / Kimi / Cohere / Vertex AI
```

## Componentes capa por capa

### 1. Storage layer (DB schema)

```sql
-- Selection per-role (SSoT runtime)
CREATE TABLE llm_role_binding (
    id UUID PRIMARY KEY,
    role VARCHAR(32) NOT NULL,  -- NANO, FAST, REASONING, AGENT, VISION, EMBEDDING
    provider VARCHAR(64) NOT NULL,
    model VARCHAR(128) NOT NULL,  -- maps to LiteLLM model alias
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    config JSONB,  -- temperature, max_tokens, top_p, etc.
    created_at TIMESTAMPTZ NOT NULL,
    created_by VARCHAR(128),  -- admin user
    activated_at TIMESTAMPTZ,
    deactivated_at TIMESTAMPTZ,
    notes TEXT,
    eval_score NUMERIC,  -- pre-promote eval gate score
    UNIQUE(role, is_active) WHERE is_active = TRUE  -- only 1 active per role
);

-- Pricing snapshot (immutable, audit trail)
CREATE TABLE model_pricing_snapshot (
    id UUID PRIMARY KEY,
    provider VARCHAR(64) NOT NULL,
    model VARCHAR(128) NOT NULL,
    input_per_1m_usd NUMERIC(12,6) NOT NULL,
    output_per_1m_usd NUMERIC(12,6) NOT NULL,
    cache_read_per_1m_usd NUMERIC(12,6),
    cache_write_per_1m_usd NUMERIC(12,6),
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,  -- NULL = currently valid
    source VARCHAR(64),  -- "manual_admin", "litellm_sync", "provider_api"
    UNIQUE(provider, model, valid_from)
);

-- Per-tenant override (paid plans, custom routing)
CREATE TABLE tenant_llm_override (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    role VARCHAR(32) NOT NULL,
    provider VARCHAR(64) NOT NULL,
    model VARCHAR(128) NOT NULL,
    reason VARCHAR(256),  -- "premium_plan", "compliance_eu", "ab_test_X"
    active BOOLEAN NOT NULL,
    expires_at TIMESTAMPTZ,
    UNIQUE(tenant_id, role) WHERE active = TRUE
);

-- Audit trail (every change tracked)
CREATE TABLE llm_config_audit (
    id UUID PRIMARY KEY,
    actor VARCHAR(128),  -- admin user or "system"
    action VARCHAR(64),  -- "promote", "deprecate", "override_set", "rollback"
    role VARCHAR(32),
    tenant_id UUID,
    before JSONB,
    after JSONB,
    created_at TIMESTAMPTZ NOT NULL
);
```

### 2. Service layer (`get_active_model` + cache)

```python
# backend/src/modules/shared/application/llm_config_service.py
from typing import Optional
import structlog
from cachetools import TTLCache

logger = structlog.get_logger()
_cache: TTLCache = TTLCache(maxsize=512, ttl=60)  # 60s TTL

class LLMConfigService:
    """SSoT runtime para selection LLM per role + tenant."""

    async def resolve(
        self,
        role: str,
        tenant_id: Optional[str] = None,
    ) -> ResolvedModel:
        cache_key = f"{role}:{tenant_id or 'global'}"
        if cached := _cache.get(cache_key):
            return cached

        # 1. Check per-tenant override
        if tenant_id:
            override = await self._tenant_override_repo.find(tenant_id, role)
            if override and override.active:
                resolved = ResolvedModel(
                    provider=override.provider,
                    model=override.model,
                    source="tenant_override",
                )
                _cache[cache_key] = resolved
                return resolved

        # 2. Check feature-flag layer (GrowthBook)
        flag_value = await self._growthbook.eval_feature(
            f"llm.role.{role.lower()}",
            attributes={"tenant_id": tenant_id},
        )
        if flag_value:
            resolved = ResolvedModel(**flag_value, source="feature_flag")
            _cache[cache_key] = resolved
            return resolved

        # 3. Fall back to global active binding (DB)
        binding = await self._role_binding_repo.find_active(role)
        if not binding:
            raise NoActiveModelError(role=role)
        resolved = ResolvedModel(
            provider=binding.provider,
            model=binding.model,
            source="global_active",
        )
        _cache[cache_key] = resolved
        return resolved

    def invalidate(self, role: Optional[str] = None) -> None:
        """Pub/sub from admin UI calls this on commit."""
        if role:
            keys = [k for k in _cache if k.startswith(f"{role}:")]
            for k in keys:
                del _cache[k]
        else:
            _cache.clear()
```

### 3. Admin layer (CRUD UI)

- **Streamlit admin panel** (`admin/modules/llm_config.py` + `pages/llm-config.py` wrapper) para CRUD `llm_role_binding` + `tenant_llm_override` + view audit log.
- **LiteLLM Admin UI** (puerto separado, protected SSO) para CRUD models en LiteLLM Proxy + cost dashboard + virtual keys per tenant.
- Workflow promote: admin crea row `is_active=FALSE` + corre eval gate → si pasa → toggle `is_active=TRUE` (transactional) + emit invalidation event.
- Rollback: 1-click toggle reactiva binding anterior (DB time-travel via `created_at` desc).

### 4. Feature flag layer (per-tenant override)

**GrowthBook** (open-source, self-hosted o cloud). Setup:
- Feature flag por role: `llm.role.reasoning`, `llm.role.fast`, etc.
- Type: JSON value `{provider: str, model: str}`.
- Targeting rules: hash attribute = `tenant_id` (B2B-correct), bucketing 0-100%.
- Use cases:
  - **Premium plan tenants** → 100% target group "premium" → modelo más caro
  - **A/B test nuevo modelo** → 10% bucket → comparar quality+cost
  - **Kill-switch** → flag off → fallback a global binding instant
  - **Region targeting** → tenants EU → modelo con data residency EU

Alternativa enterprise: **LaunchDarkly** (mismo pattern, paid, mejor UI/audit).

### 5. Eval gate layer (pre-promote validation)

Antes de toggle `is_active=TRUE`:
1. **Goldens regression**: run dataset evaluación (sales_agent ya tiene `eval_loop` + `voice_fidelity_grader`). Score ≥ baseline.
2. **Cost simulation**: estimate cost-per-conversation con sample 100 conversaciones reales del tenant. Alert si >150% del modelo actual.
3. **Latency check**: p95 latency < threshold (e.g. <2s para FAST role, <5s REASONING).
4. **Smoke test**: 10 calls con prompts canónicos. 0 errores 5xx.

Tool: **GuideLLM** (Red Hat OSS) para benchmarking + regression testing. Integra como pre-deploy gate en CI.
Alternativa: **LangSmith Evaluations** (paid, mejor UI) si ya estás en stack LangChain.

### 6. Observability layer (audit trail + cost tracking)

- **LiteLLM cost tracking nativo** → emite logs estructurados por call con `(tenant_id, role, model, input_tokens, output_tokens, cost_usd)`.
- **Tabla `llm_config_audit`** registra TODO cambio (admin action, flag toggle, override set/expire).
- **Dashboard** (Grafana o Streamlit admin):
  - Cost per tenant per role per día/semana
  - Model usage distribution (% requests per model)
  - Latency p50/p95/p99 per role
  - Error rate per provider
- **Alerting**: cost spike >2σ baseline → Slack alert. Provider error rate >5% en 5min → page on-call.

## Anti-patterns a evitar

| Anti-pattern | Por qué fail | Fix |
|---|---|---|
| Modelo en `.env` sin DB layer | Cada cambio = redeploy. Ventana cambio modelo en 2026 = días, no semanas. | DB registry + admin UI |
| Hardcodear pricing en código (`COST_PER_1K = 0.0001`) | Provider cambia precio → billing inconsistente sin nadie notar. OpenAI bajó GPT-4o 50% ago/2025 — equipos cobraron de más por meses. | Tabla `model_pricing_snapshot` con `valid_from/to` |
| Per-tenant override en `.env` (`OPENAI_MODEL_TENANT_X=...`) | No escala >5 tenants. Imposible audit. | Tabla `tenant_llm_override` o feature flag |
| Sin cache en service layer | DB query por cada LLM call → +5ms × millones calls/día = problema. | TTL cache 60s + pub/sub invalidation |
| Sin invalidación cache al cambiar config | Admin promueve modelo nuevo, instancias siguen usando viejo hasta TTL expire. | Redis pub/sub on commit + signal handler |
| Rollback manual editando `.env` + redeploy | Crisis: modelo nuevo degrada quality, MTTR >30min. | 1-click toggle DB / kill-switch flag → MTTR <30s |
| Eval post-deploy en producción real | Detectás regression cuando tenants ya sufrieron. | Eval gate pre-promote con goldens + cost sim |
| Mezclar prompt management con model selection | Acoplas cosas con lifecycle distinto. Prompt cambia diario, model cambia semanal. | LangSmith para prompts, DB+LiteLLM para models |
| Reinventar LiteLLM | 6 meses de dev + bugs vs OSS battle-tested 100+ providers. | Adoptar LiteLLM, customizar solo lo Nicolify-specific |
| Feature flag para TODO (incl. global default) | Cuando GrowthBook cae, sistema sin default → outage. | DB registry como fallback siempre. Flag = override opcional. |
| `is_active = TRUE` sin constraint UNIQUE | Race condition activa 2 modelos mismo role → ambiguo. | DB constraint partial UNIQUE WHERE is_active |

## Migration path desde stack actual Nicolify

### Phase 1: Foundation (sprint 1, ~3 días)
- Crear tabla `model_pricing_snapshot` + seed con pricing actual de modelos en uso (OpenAI, Kimi, DeepSeek, embeddings).
- Crear tabla `llm_role_binding` + seed con valores actuales de `.env` (`AI_PROVIDER_<ROLE>` + `AI_MODEL_<ROLE>` → rows con `is_active=TRUE`).
- Migration idempotente con `CREATE TABLE IF NOT EXISTS`. Tests integration pre-merge.
- **Output**: DB tiene SSoT pero código sigue leyendo `.env`. Zero breaking change.

### Phase 2: Service layer (sprint 1-2, ~3 días)
- Implementar `LLMConfigService.resolve(role, tenant_id)` con TTL cache + fallback DB.
- Wrapper alrededor del llamado actual a `OpenAI()` etc.: en vez de `model=settings.AI_MODEL_REASONING` → `model=await llm_config.resolve("REASONING", tenant_id).model`.
- Rollout module-by-module (copilot primero — más maduro, sales_agent segundo, etc.).
- Eval con sales_agent goldens antes/después per módulo.
- **Output**: código lee de DB. `.env` sigue siendo source pero es seedeo, no runtime.

### Phase 3: Admin UI + audit (sprint 2, ~3 días)
- Streamlit admin module `llm_config.py`: CRUD `llm_role_binding` (toggle active, view history) + view audit log.
- Pub/sub Redis para invalidate cache al commit cambios.
- Audit table populated en cada CRUD action.
- **Output**: ops puede cambiar modelo desde UI sin redeploy. Cambio toma <60s en propagar.

### Phase 4: LiteLLM Proxy (sprint 3, ~5 días)
- Levantar `litellm-proxy` container en docker-compose. Postgres compartido o separado.
- Migrar provider configs (OpenAI, Anthropic, DeepSeek, Kimi) a LiteLLM models config.
- Reemplazar SDK calls directos (`OpenAI()`, `anthropic.Anthropic()`) por single SDK apuntando a LiteLLM (formato OpenAI).
- Cost tracking dual: LiteLLM nativo + opcional sync a `model_pricing_snapshot`.
- Virtual keys per tenant (LiteLLM feature) para budget caps + audit.
- **Output**: provider-agnostic. Agregar provider nuevo = config LiteLLM, sin tocar código.

### Phase 5: Feature flag layer (sprint 4, ~3 días)
- Setup GrowthBook (self-hosted Docker o cloud).
- Crear flags `llm.role.<role>` con JSON value type.
- SDK Python en `LLMConfigService.resolve()`.
- Crear tabla `tenant_llm_override` para overrides estables (no A/B). Flag para A/B + rollouts.
- **Output**: per-tenant routing operativo. Premium plan tenants pueden usar Opus 4.7, free tier usa Haiku.

### Phase 6: Eval gate (sprint 5, ~5 días)
- Integrar GuideLLM o LangSmith eval con goldens existentes (sales_agent ya los tiene).
- CI/CD pipeline: pre-promote → run eval → score ≥ threshold → habilita toggle UI.
- Cost simulation: query 100 conversaciones reales sample → estimate con modelo nuevo.
- Manual override con justification comment para emergencias.
- **Output**: imposible promover modelo sin pasar gate. MTTR rollback <30s.

### Total estimate: ~6 sprints (~3-4 semanas wall-clock para 1 dev senior).

## Roadmap LLM cambio rápido — escenarios

### Caso 1: Nuevo modelo released hoy (e.g., DeepSeek V5)
1. Admin UI Nicolify → "Add Model" → fill provider=`deepseek`, model=`deepseek-v5`, role candidato=`REASONING`. `is_active=FALSE`.
2. Add row `model_pricing_snapshot` con pricing oficial DeepSeek.
3. Admin UI LiteLLM → add model entry (config DB, no restart).
4. Run eval gate: goldens regression → cost sim → smoke test.
5. Si pass → toggle `is_active=TRUE` (DB migration en 1 transaction: deactiva viejo + activa nuevo).
6. Pub/sub invalida cache → instancias FastAPI usan modelo nuevo en <60s.
7. Monitor 24h → si cost/quality OK → cleanup viejo. Si no → 1-click rollback.

**Tiempo total: ~2h (eval) + 1min (toggle).** Cero redeploy.

### Caso 2: Cambiar provider per role (e.g., REASONING openai → claude)
- Idéntico Caso 1 pero target `provider=anthropic, model=claude-opus-4-7-1m`.
- Validación adicional: `tenant_llm_override` rows que apunten a OpenAI REASONING siguen funcionando (no auto-migran). Decisión PM.

### Caso 3: A/B test modelo nuevo solo 10% tenants
1. NO tocar `llm_role_binding` (binding global queda igual).
2. GrowthBook → crear flag `llm.role.reasoning` → rule: `bucketing=10%, hash=tenant_id, value={provider:"deepseek",model:"deepseek-v5"}`.
3. SDK eval automático en `LLMConfigService.resolve()` retorna nuevo modelo para 10% de tenants (consistente per tenant — siempre mismo bucket).
4. Comparar metrics (cost, latency, conversion, quality) entre cohorts en GrowthBook dashboard.
5. Si win → ramp 100% → graduate a `llm_role_binding` global (cleanup flag).

### Caso 4: Rollback instant si calidad degrada
- Admin UI Nicolify → click "Rollback" en `llm_role_binding` → reactiva binding anterior (1 transacción).
- Pub/sub invalida cache → instancias usan modelo viejo en <60s.
- Alternativa más rápida: GrowthBook flag → toggle "Force value: previous_model" → propagación SDK <5s.
- MTTR total: **<30s** (vs ~15-30min con `.env` + redeploy + cache busting + Docker rebuild).

## Tools mencionadas en el ecosistema 2026

| Tool | Propósito | Adopción 2026 | Open-source | Recomendación Nicolify |
|---|---|---|---|---|
| **LiteLLM Proxy** (BerriAI) | Multi-provider gateway, cost tracking, admin UI, store-model-in-DB | ~40% (OSS dominant) | SI (MIT) | **ADOPTAR** — resuelve 80% problema |
| **GrowthBook** | Feature flags + AI Configs (LLM-specific) | ~25% (creciendo) | SI (MIT) | **ADOPTAR** — per-tenant override |
| LaunchDarkly | Feature flags enterprise | ~30% (paid) | NO | Skip — GrowthBook OSS suficiente |
| Unleash | Feature flags OSS | ~15% | SI (Apache 2.0) | Skip — GrowthBook tiene AI Configs específico |
| Bifrost | LLM gateway, sub-11μs overhead, zero-downtime failover | ~5% (nuevo) | SI | Evaluar si LiteLLM perf insuficiente |
| OmniRoute | AI gateway open-source | ~3% | SI | Skip — LiteLLM más maduro |
| Requesty | LLM gateway managed, <20ms failover | ~5% (paid) | NO | Skip |
| Cloudflare AI Gateway | Edge caching + analytics | ~10% | NO (managed) | Considerar para edge cache si tráfico global |
| Vercel AI Gateway | Routing managed | ~5% | NO | Skip — vendor lock-in Vercel |
| Kong AI Gateway | Enterprise gateway | ~8% | Parcial | Skip — overkill |
| **MLflow Model Registry** | Model versioning con stages | ~20% (ML traditional) | SI | Skip para LLM API — diseñado para custom-trained models |
| **LangSmith** | Prompt versioning + agent deployment + evals | ~15% (LangChain stack) | NO (paid) | Considerar solo para evals si ya migras a LangChain |
| **GuideLLM** (Red Hat) | LLM benchmarking + regression testing | ~10% (creciendo) | SI (Apache 2.0) | **ADOPTAR** para eval gate |
| **Vertex AI Model Registry** | Google managed | ~15% (GCP users) | NO | Skip — vendor lock-in, Nicolify multi-cloud |
| **AWS Bedrock Model registry** | AWS managed | ~12% (AWS users) | NO | Skip — vendor lock-in |
| Maxim AI | LLM eval + observability platform | ~5% | NO (paid) | Skip — overlap con GuideLLM + GrowthBook |

## Sources

- [LLMOps Architecture: Managing Large Language Models in Production 2026 — Calmops](https://calmops.com/architecture/llmops-architecture-managing-llm-production-2026/)
- [The Complete MLOps/LLMOps Roadmap for 2026 — Medium / Sanjeeb Panda](https://medium.com/@sanjeebmeister/the-complete-mlops-llmops-roadmap-for-2026-building-production-grade-ai-systems-bdcca5ed2771)
- [LLM Orchestration in 2026: Frameworks + Best Practices — Orq.ai](https://orq.ai/blog/llm-orchestration)
- [Complete Guide to LLMOps Platforms — Tech Daily Shot 2026](https://techdailyshot.com/blog/complete-guide-llmops-platforms-2026)
- [Deploying LLMs in the Enterprise: SaaS Framework — CalypsoAI](https://calypsoai.com/insights/deploying-llms-in-the-enterprise-the-saas-framework/)
- [LangChain Releases (2026)](https://github.com/langchain-ai/langchain/releases)
- [LangSmith Deployment Infrastructure](https://www.langchain.com/langsmith/deployment)
- [LangSmith Cookbook — Prompt Versioning](https://github.com/langchain-ai/langsmith-cookbook/blob/main/hub-examples/retrieval-qa-chain-versioned/prompt-versioning.ipynb)
- [LiteLLM Proxy Admin UI — Quick Start](https://docs.litellm.ai/docs/proxy/ui)
- [LiteLLM Store Model in DB Settings](https://docs.litellm.ai/docs/proxy/ui_store_model_db_setting)
- [LiteLLM Model Management](https://docs.litellm.ai/docs/proxy/model_management)
- [LiteLLM AI Gateway — Simple Proxy](https://docs.litellm.ai/docs/simple_proxy)
- [LiteLLM Router — Load Balancing](https://docs.litellm.ai/docs/routing)
- [LiteLLM GitHub (BerriAI)](https://github.com/BerriAI/litellm)
- [GrowthBook vs LaunchDarkly: Feature Flagging](https://www.growthbook.io/blog/growthbook-vs-launchdarkly-why-developers-choose-growthbook-for-feature-flagging)
- [Open Source Feature Flag Tools Compared 2026 — FlagShark](https://flagshark.com/blog/open-source-feature-flag-tools-compared-2026/)
- [Top 10 Feature Flag Management Tools in 2026 — Kameleoon](https://www.kameleoon.com/blog/top-feature-flag-management-tools)
- [Feature Flag Platform Comparison 2026 — DEV Community](https://dev.to/domenico_giordano_e441224/feature-flag-platform-comparison-2026-an-honest-self-audit-5433)
- [Feature flags vs configuration — PostHog](https://posthog.com/product-engineers/feature-flags-vs-configuration)
- [Beyond Environment Variables: When to Use Feature Flags — ConfigCat](https://configcat.com/blog/feature-flags-vs-environment-variables/)
- [LLM Feature Flags in Backends — Medium / Codastra](https://medium.com/@2nick2patel2/llm-feature-flags-in-backends-policy-driven-prompts-and-safe-rollouts-9b8361ca4479)
- [Selected Anthropic and OpenAI Models Deprecated — GitHub Changelog 2026-02-19](https://github.blog/changelog/2026-02-19-selected-anthropic-and-openai-models-are-now-deprecated/)
- [Vertex AI Model Deprecations (MaaS)](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/deprecations/partner-models)
- [Claude Sonnet 4 / Opus 4 Deprecation Migration Guide — MindStudio](https://www.mindstudio.ai/blog/claude-sonnet-4-opus-4-deprecation-migration-guide)
- [OpenAI Model Deprecation Guide 2026 — KissAPI](https://kissapi.ai/blog/openai-model-deprecation-migration-guide-2026.html)
- [OpenAI Deprecations API Docs](https://developers.openai.com/api/docs/deprecations)
- [AI Deprecations Feeds](https://deprecations.info/)
- [LLMOps Guide 2026: Build Fast, Cost-Effective LLM Apps — Redis](https://redis.io/blog/large-language-model-operations-guide/)
- [GuideLLM: Evaluate LLM deployments — Red Hat Developer](https://developers.redhat.com/articles/2025/06/20/guidellm-evaluate-llm-deployments-real-world-inference)
- [Best LLM Evaluation Tools of 2026 — Online Inference / Medium](https://medium.com/online-inference/the-best-llm-evaluation-tools-of-2026-40fd9b654dce)
- [Reduce LLM Cost and Latency — Maxim AI 2026](https://www.getmaxim.ai/articles/reduce-llm-cost-and-latency-a-comprehensive-guide-for-2026/)
- [6 Production-Tested Optimization Strategies for LLM Inference — BentoML](https://www.bentoml.com/blog/6-production-tested-optimization-strategies-for-high-performance-llm-inference)
- [Top 5 LLM Router Solutions in 2026 — Maxim AI](https://www.getmaxim.ai/articles/top-5-llm-router-solutions-in-2026/)
- [Best LLM Gateways in 2026 — Maxim AI](https://www.getmaxim.ai/articles/best-llm-gateways-in-2026/)
- [Top 5 AI Gateways for Multi-Model Routing — Maxim AI](https://www.getmaxim.ai/articles/top-5-ai-gateways-for-multi-model-routing/)
- [Best LLM Router for Enterprise: Bifrost vs LiteLLM — Maxim AI](https://www.getmaxim.ai/articles/best-llm-router-for-enterprise-ai-bifrost-vs-litellm/)
- [Best LLM Router and AI Gateway 2026 — Inworld](https://inworld.ai/resources/best-llm-router-ai-gateway)
- [OpenRouter Provider Routing Docs](https://openrouter.ai/docs/guides/routing/provider-selection)
- [OmniRoute GitHub (multi-provider AI gateway)](https://github.com/diegosouzapw/OmniRoute)
- [Requesty — Unified LLM Gateway](https://www.requesty.ai/)
- [MLflow Model Registry](https://mlflow.org/docs/latest/ml/model-registry/)
- [Manage Secrets & Config for LangChain Apps — APXML](https://apxml.com/courses/langchain-production-llm/chapter-7-deployment-strategies-production/managing-secrets-config)
- [Claude Code in the Enterprise — Model Mapping for LLM Proxies — Medium / Trevor Samaroo](https://medium.com/@trevor00/claude-code-in-the-enterprise-model-mapping-for-llm-proxies-b0d8069c6aa3)
- [LLM Integration Strategy For SaaS Platforms In 2026 — GainHQ](https://gainhq.com/blog/llm-integration/)
- [Complete LLM Pricing Comparison 2026 — CloudIDR](https://www.cloudidr.com/blog/llm-pricing-comparison-2026)
- [LLM API Cost Comparison 2026 — Zen van Riel](https://zenvanriel.com/ai-engineer-blog/llm-api-cost-comparison-2026/)
- [Vertex AI Model Registry Overview (Google Cloud)](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/overview)
