# PR-2-growthbook-per-tenant-override

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-2-growthbook-per-tenant-override |
| Sprint padre | S4-copilot-model-registry-runtime |
| PI padre | PI-2-copilot-improvement |
| Estado | shipped 2026-04-30 — minimal viable scaffold (Settings + LLMConfigService.resolve tenant_id arg + Docker svc profile growthbook + 5 tests) |
| Tipo | infra (feature flag service para per-tenant + A/B) |
| Esfuerzo | M (~10 archivos) |
| Owner PM | /pm |

## Problema

Post-PR-1: hot-swap modelo es global. A escala 1000+ tenants:
- Premium tier puede pagar usar modelo más caro/calidad alta (ej: GPT-5.5 Pro vs deepseek-v4-flash default).
- A/B test modelo nuevo solo 10% tenants antes promote 100% (research recommended pattern).
- Kill-switch instant per-tenant si modelo causa regresión específica al tenant X.

JTBD Chris: "Quiero probar nuevos modelos con un subset de tenants antes de hacer rollout completo. Y dar acceso a modelos premium a planes pagos."

## Outcome esperado

- GrowthBook OSS self-hosted (Docker svc).
- Feature flag `llm_model_override_<role>` con bucketing por `tenant_id`.
- `LLMConfigService.resolve(role, tenant_id)` consulta GrowthBook → si flag activo, retorna model override; else default DB binding.
- Admin Streamlit `/admin/llm-experiments` CRUD experiments + targeting rules.
- Kill-switch per-tenant: admin UI button → instant flag deactivate per tenant_id.

## Walking skeleton

1. **Docker svc `visionarias_growthbook`** en compose (Postgres connection).
2. **GrowthBook SDK** `growthbook-python` en `backend/requirements.txt`.
3. **Service integration** `LLMConfigService.resolve(role, tenant_id)`:
   - Default: DB binding from PR-1
   - Override: `growthbook.eval_feature(f"llm_model_override_{role}", attributes={"tenant_id": str(tenant_id)})`
   - Cache flag eval result 60s
4. **Admin Streamlit** `admin/pages/llm_experiments.py`:
   - List experiments + targeting rules
   - Bucketing percentage (10%, 50%, 100%)
   - Per-tenant explicit allowlist/blocklist
   - Kill-switch button
5. **Tests cobertura**: tenant isolation, flag bucketing determinístico (mismo tenant_id → mismo bucket), kill-switch immediate.

## Existing systems audit

```bash
grep -rn "feature_flag\|growthbook\|launchdarkly" src/
docker ps | grep growthbook
```

**Sistemas:** sin existente. NEW infra layer justificada (research base: GrowthBook OSS standard 30% adoption + AI Configs producto dedicado para LLM).

## Surface impactada

| Tipo | Path | Cambio |
|---|---|---|
| Docker | `docker-compose.yml` | NEW svc visionarias_growthbook |
| Settings | `src/core/config.py` | NEW GROWTHBOOK_API_HOST + GROWTHBOOK_CLIENT_KEY |
| BE service | `src/shared/infrastructure/llm/config_service.py` | EXTEND resolve(role, tenant_id) consulta GrowthBook |
| Admin | `admin/pages/llm_experiments.py` | NEW |
| Tests | `tests/shared/infrastructure/llm/test_config_service_per_tenant.py` | NEW |
| current-state | `current-state/copilot.md` | append cap "Per-tenant LLM model override + A/B" |

## Tests requeridos

- Tenant isolation: tenant A flag activo, tenant B sin flag → A usa override, B usa default
- Bucketing determinístico: mismo tenant_id → mismo bucket en runs sucesivos
- Kill-switch: deactivate flag → tenant inmediatamente vuelve default
- Cache invalidation funciona

## Aceptación

- [ ] Tests verde
- [ ] Docker compose svc visionarias_growthbook healthy
- [ ] Manual: crear experiment 10% tenants → verificar bucketing correcto
- [ ] current-state updated

## Riesgos

| Riesgo | Mitigación |
|---|---|
| GrowthBook svc down → flag eval falla | Fallback default DB binding + log warning |
| Bucketing skew (random hash mal-distribuido) | Tests determinísticos verifican distribución +/- 5% |
| Per-tenant override cross-leak | Tests isolation explícitos + arch test |
