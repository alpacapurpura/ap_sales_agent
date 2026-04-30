# Sprint S4 — copilot-model-registry-runtime

## Meta

| Campo | Valor |
|---|---|
| Sprint ID | S4-copilot-model-registry-runtime |
| PI padre | PI-2-copilot-improvement |
| Estado | in-progress — S3 shipped 2026-04-30, PR-1 claimed |
| Inicio estimado | post S3 |
| Cierre estimado | S3+1 semana |
| Owner PM | /pm |

## Objetivo (1 línea)

Convertir LLM model selection en **runtime hot-swap (<60s sin deploy)** vía DB registry custom Nicolify-specific + admin Streamlit UI + GrowthBook per-tenant override + A/B + kill-switch, escalable a 1000+ tenants.

## Pre-handoff (input desde S3)

- LiteLLM Proxy live (motor multi-provider + cost tracking + virtual keys básico)
- ModelRole único SSoT (ModelTier eliminado)
- DeepSeek V4-Flash activo NANO+FAST via .env (cambio modelo aún requiere redeploy = problema escala)

## Plan PRs

| PR | Folder | Descripción | Esfuerzo | Estado |
|---|---|---|---|---|
| PR-1 | `prs/PR-1-db-registry-admin-ui/` | Tabla `llm_role_binding` SSoT runtime + admin Streamlit `/admin/llm-models` CRUD + `LLMConfigService.resolve(role, tenant_id)` con cache 60s + Redis pub/sub invalidation | L | not-started |
| PR-2 | `prs/PR-2-growthbook-per-tenant-override/` | Integrar GrowthBook OSS (self-hosted Docker) — feature flag `llm_model_override_<role>` con bucketing por `tenant_id`. Habilita A/B test, gradual rollout, kill-switch instant. | M | not-started |

## Criterio éxito

- [ ] Cambio modelo hot-swap admin UI → propagado a backend pods en <60s sin restart (medir latency)
- [ ] Per-tenant override: feature flag activo solo 10% tenants → resto sigue modelo default (verificable queries)
- [ ] Kill-switch: admin UI botón "Rollback" → MTTR <30s
- [ ] Audit trail: cada cambio admin UI → row en `llm_config_audit` con `(role, old_model, new_model, admin_user, timestamp)`
- [ ] Cero downtime detectable durante swap modelo (reqs siguen sirviéndose)
- [ ] Pricing snapshot sincronizado automático (LiteLLM → Nicolify table) sin drift

## Out of scope

| Item | Razón | Sprint destino |
|---|---|---|
| Eval gate integration admin UI | Requiere admin UI primero | S5 |
| ModelTier deprecation final cleanup | Allowlist shrunk en S3 + verificar 0 usage post deploy | S5 PR-2 |
| Embeddings + sales_agent voice | PI dedicados | futuro |

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Cache invalidation race condition (pod1 actualizado, pod2 stale) | Pub/sub Redis con timestamp + verify cache version on each request |
| Admin UI cambio sin eval gate = riesgo regresión calidad | S5 wire eval gate pre-promote — mientras tanto, admin UI shows warning "Eval gate not run" |
| GrowthBook self-hosted infra cost | Docker svc separado, ~256MB RAM, free OSS |
| Per-tenant override leak entre tenants | GrowthBook hash bucketing por tenant_id explicit + tenant isolation tests |
