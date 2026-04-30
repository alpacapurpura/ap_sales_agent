# Sprint S3 — copilot-llm-stack-convergence

## Meta

| Campo | Valor |
|---|---|
| Sprint ID | S3-copilot-llm-stack-convergence |
| PI padre | PI-2-copilot-improvement |
| Estado | done — PR-1 + PR-2 shipped 2026-04-30 |
| Inicio estimado | 2026-04-30+ |
| Cierre estimado | 2026-05-07 |
| Owner PM | /pm |

## Objetivo (1 línea)

Cerrar deuda PR-3 PI-2 S2 (capa LLM duplicada) + convergir copilot ModelTier→ModelRole único SSoT + introducir LiteLLM Proxy como motor multi-provider centralizado, dejando stack listo para hot-swap modelo en S4 sin más refactor.

## Pre-handoff (input desde S2)

- **Decisiones S2:** `../S2-copilot-cero-deuda-stack/handoff.md` (12 decisiones D-1..D-12 + 4 PR-2 D-MAIN + 7 PR-3 D-1..D-15).
- **Surface S2:** suggestion engine + 4 providers + endpoint /suggestions + LLM infra (DEUDA — capa duplicada PR-3).
- **Research base:**
  - `docs/pm-nico/research/2026-04-30-llm-landscape-chinese-models.md` (DeepSeek V4-Flash 4-15x cheaper NANO+FAST)
  - `docs/pm-nico/research/2026-04-30-llm-config-storage-best-practices.md` (hybrid 3-capa pattern)
- **SSoT doc:** `docs/domains/llm-routing.md` (creado 2026-04-30 process prevention)
- **Process prevention shipped:** CONTRACT template + PR template + nicolify-architect skill + arch fitness test guard
- **Riesgos abiertos:** ModelTier consumers en código aplicación (router/classifiers/llm_classifier, memory/rolling_summarizer, memory/title_generator, router/model_router, domain/routing_policy, hooks/copilot_events). Archivos `infrastructure/llm/` capa duplicada PR-3 deuda.

## Plan PRs (folders)

| PR | Folder | Descripción | Agentes/skills | Esfuerzo | Estado |
|---|---|---|---|---|---|
| PR-1 | `prs/PR-1-cleanup-modeltier-convergence/` | Eliminar capa duplicada PR-3 + convergir ModelTier consumers a ModelRole + activar DeepSeek V4-Flash NANO+FAST via .env. Mantener evals package + migration 114 + arch fitness test SSoT. | `nicolify-architect` → `nicolify-backend` → PM main thread takeover (builder truncate L-PROC) + `copilot-expert` + `sales-agent-expert` | M-L | **shipped** 2026-04-30 |
| PR-2 | `prs/PR-2-litellm-proxy-integration/` | Introducir LiteLLM Proxy (BerriAI) v1.83.10-stable como motor multi-provider centralizado. Docker svc visionarias_litellm + admin Streamlit virtual keys read-only + refactor router toggle-based + cost tracking dual-source. 18 D-decisions ejecutadas. | `nicolify-architect` → `nicolify-backend` (truncate) → PM main thread takeover + `copilot-expert` + `sales-agent-expert` | M | **shipped 2026-04-30** |

## Criterio éxito sprint

- [ ] `tests/architecture/test_llm_routing_ssot.py` 4 tests verde + 19 archivos KNOWN_LEGACY_LLM_FILES eliminados/migrados (allowlist shrinks to ≤5 archivos solo legacy realmente diferido)
- [ ] `grep -rn "TIER_METADATA\|ModelTier" backend/src/modules/copilot/` = 0 hits (excepto archivo origen marcado `@deprecated`)
- [ ] DeepSeek V4-Flash activo NANO + FAST: `SELECT DISTINCT model FROM copilot_llm_call WHERE created_at > NOW() - INTERVAL '5 minutes' AND tier_role IN ('NANO', 'FAST')` retorna `deepseek-v4-flash` post deploy
- [ ] LiteLLM Proxy Docker svc en `docker-compose.yml` healthcheck verde
- [ ] All copilot LLM consumers (classifier + summarizer + title generator) pasan por `settings.get_model(role)` + `settings.get_provider_for_role(role)` (no model_name hardcoded)
- [ ] Cero refactor necesario en sprint siguiente (verificable: handoff S3 NO lista deuda LLM routing)
- [ ] Todos los PRs tienen `RESULT.md` escrito
- [ ] `current-state/copilot.md` actualizado: cap "LLM stack convergencia ModelRole único + LiteLLM Proxy motor multi-provider"

## Out of scope

| Item | Razón | Sprint destino |
|---|---|---|
| DB registry runtime + admin UI hot-swap | Requiere LiteLLM Proxy primero (S3 PR-2) + GrowthBook integration | S4 |
| GrowthBook per-tenant override | Mismo, después DB registry | S4 |
| Eval gate pre-promote integration admin UI | Requiere admin UI primero | S5 |
| Embeddings migration Qwen3-Embedding-8B | Re-index Qdrant ventana mantenimiento | PI dedicado |
| Sales_agent voice swap | Q3 2026 + voice fidelity grader | PI futuro |
| Specialist (REASONING/HEAVY) tier swap | Eval gate goldens >100 + comparación blind | S5+ después gate framework wired |

## Decisiones tomadas durante sprint

(append-only)

| Fecha | Decisión | PR |
|---|---|---|

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| Eliminar `model_tier.py` rompe tests existentes con MagicMock | PR-1 RED tests primero — refactor + verde + delete file | PR-1 builder |
| LiteLLM Proxy adds latency overhead | Research 2026-04 indica <11μs overhead. Validar con benchmark inline pre-merge | PR-2 architect |
| Convergencia ModelTier→ModelRole pierde semantic granularity (HEAVY tier specifically) | Mapear: NANO→NANO, MINI→FAST, REASONING→REASONING, HEAVY→AGENT (ModelRole.AGENT cubre multi-step + heavy reasoning para agentic workflows) | PR-1 architect |
| Sesión paralela PI-1 toca `src/shared/infrastructure/llm/` | Regla M8: leer + extend. Probabilidad baja (campaigns no toca LLM routing). | Builder |

## Cierre

Llenar `learnings.md` + `handoff.md` antes próximo sprint. Verificar arch fitness test SSoT verde + allowlist shrunk + DeepSeek V4-Flash activo en queries `copilot_llm_call`.
