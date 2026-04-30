# PR-1-cleanup-modeltier-convergence

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-1-cleanup-modeltier-convergence |
| Sprint padre | S3-copilot-llm-stack-convergence |
| PI padre | PI-2-copilot-improvement |
| Estado | in-progress (claimed 2026-04-30) |
| Tipo | refactor (cleanup deuda + convergencia SSoT) |
| Esfuerzo | M-L (~12-15 archivos, 30 tests, target ≤15 archivos cohesivos) |
| Owner PM | /pm |

## Problema (Chris-facing — deuda + costo escala)

PR-3 PI-2 S2 introdujo capa LLM routing duplicada (`copilot/infrastructure/llm/{model_config.py + provider_factory.py + providers/deepseek.py}`) paralela a sistema global ya existente (`core/config.py::Settings.get_model/get_provider_for_role` + `shared/infrastructure/llm/router.py + providers/`). Ambas capas coexisten = código orphan + drift + costo mantenimiento amplificado a 1000+ tenants.

Adicional deuda preexistente: `copilot/domain/model_tier.py::TIER_METADATA` hardcoded desincronizado del `.env` real (decía `gpt-5.4-nano`, .env tiene `gpt-4o-mini`). Drift silencioso porque ningún arch fitness test guard detectaba duplicación.

JTBD Chris: "Como founder pagando LLM bills crecientes con cada tenant nuevo, quiero un único sistema SSoT de routing LLM que me permita cambiar modelo en cualquier capa sin riesgo de drift ni código duplicado, escalable a 1000+ tenants."

## Outcome esperado

- 0 capa duplicada `copilot/infrastructure/llm/` (eliminada).
- 0 imports `ModelTier` o `TIER_METADATA` en código aplicación (excepto archivo origen marcado `@deprecated` o eliminado completamente).
- 1 SSoT: `ModelRole` + `Settings.get_model/get_provider_for_role` + `shared/infrastructure/llm/router.py`.
- DeepSeek V4-Flash activo NANO + FAST tiers (cost reduction 4-15x activado).
- Arch fitness test guard `test_llm_routing_ssot.py` 4/4 verde + allowlist shrunk a ≤5 archivos.

Métrica medible:
- `grep -rn "TIER_METADATA\|ModelTier" backend/src/modules/copilot/ | grep -v "@deprecated"` = 0
- `find backend/src/modules/copilot/infrastructure/llm/` = file not found (path eliminado)
- `SELECT DISTINCT model FROM copilot_llm_call WHERE created_at > NOW() - INTERVAL '7 days' AND tier_role='NANO'` post deploy retorna `deepseek-v4-flash` (no `gpt-4o-mini`).

## Walking skeleton (mínimo viable cohesivo)

1. **Refactor LLMClassifier** (`copilot/application/router/classifiers/llm_classifier.py`):
   - Recibir `role: ModelRole` en lugar de `tier: ModelTier`
   - Usar `settings.get_model(role)` + `settings.get_provider_for_role(role)` para construir LangChain ChatModel
   - Mapear: ModelTier.NANO → ModelRole.NANO; MINI → FAST; REASONING → REASONING; HEAVY → AGENT
2. **Refactor RollingSummarizer + TitleGenerator** (`copilot/application/memory/`):
   - Recibir `role: ModelRole` en lugar de `tier: ModelTier`
   - LLMProvider injection desde `shared/infrastructure/llm/router.py` (existente)
3. **Refactor model_router + routing_policy + classifiers/rule_classifier** (`copilot/application/router/` + `copilot/domain/`):
   - `RoutingDecision.tier: ModelTier` → `RoutingDecision.role: ModelRole`
   - `RoutingPolicy.default_tier` → `default_role`
   - Adapter en hooks `copilot_events.py` mantiene compatibilidad observability si tabla `routing_log` esperaba `tier` (alias o migration column rename).
4. **Eliminar capa duplicada PR-3**:
   - DELETE `copilot/infrastructure/llm/model_config.py`
   - DELETE `copilot/infrastructure/llm/provider_factory.py`
   - DELETE `copilot/infrastructure/llm/providers/deepseek.py` (DeepSeek ya en `shared/infrastructure/llm/providers/_openai_compat.py`)
   - DELETE `copilot/infrastructure/llm/providers/__init__.py`
   - DELETE `copilot/infrastructure/llm/__init__.py`
   - DELETE `tests/modules/copilot/infrastructure/llm/test_model_config.py` (archivo + dirs vacíos)
   - DELETE `tests/architecture/test_pr3_no_sales_agent_imports.py` (ya no aplica si dir copilot/llm/ no existe; reemplazado por test_llm_routing_ssot.py general)
5. **Eliminar / deprecar ModelTier**:
   - Opción A: DELETE `copilot/domain/model_tier.py` completamente. Requiere todos consumers refactorizados.
   - Opción B: Marcar `@deprecated` con runtime warning + delegar a ModelRole mapping. Allowlist shrinks gradual.
   - **Decisión architect en CONTRACT.md**: probable A (cleanup completo) si surface manageable.
6. **Verificar `_openai_compat.py` soporta `deepseek-v4-flash`** modelo (vs `deepseek-reasoner` que ya soporta — probable solo agregar entry a registry interno). Si no soporta, agregar.
7. **Activar `.env` prod**:
   ```
   AI_MODEL_NANO=deepseek-v4-flash
   AI_PROVIDER_NANO=deepseek
   AI_MODEL_FAST=deepseek-v4-flash
   AI_PROVIDER_FAST=deepseek
   ```
   (Architect decide si ship en este PR vs PR-N+1 separado para habilitar eval gate antes — defer S5).
8. **Mantener de PR-3** (aporte real, NO eliminar):
   - `backend/src/modules/copilot/evals/` (golden_dataset + runner + scorers + 100 goldens)
   - `backend/alembic/versions/114_pricing_deepseek_v4_flash.py` (migration pricing)
   - `backend/tests/architecture/test_llm_routing_ssot.py` (arch guard SSoT — actualizar allowlist post-cleanup)
9. **Update arch fitness allowlist**: `KNOWN_LEGACY_LLM_FILES` shrinks a ≤5 archivos (solo lo realmente diferido — verify via test).

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A — Cleanup PR-3 + convergencia ModelTier→ModelRole + activar DeepSeek (mismo PR) | Cohesivo cierra deuda completa | Scope L (~15 archivos) — acerca límite truncate | **ELEGIDA** — único PR cumple cero deuda Chris |
| B — Solo cleanup PR-3 (DELETE), convergencia PR-N+1 | Más chico cada uno | Deja deuda ModelTier viva — viola SSoT | descartada |
| C — Solo convergencia ModelTier→ModelRole, cleanup PR-3 al final | ModelTier inviable mientras llm/ duplicado existe | Lógicamente imposible (Settings.get_model retorna AI_MODEL_NANO=gpt-4o-mini, ModelTier hardcoded gpt-5.4-nano = drift sigue) | descartada |

## Existing systems audit (NO NEW LAYER rule — architect-mandatory pre-CONTRACT)

> Esta sección se llenará completa por architect agent en CONTRACT.md. Pre-research PM:

```bash
# Audit cross-module obligatorio
grep -rn "settings\.get_\|ModelRole\|ModelTier" src/core/ src/shared/ src/modules/copilot/
grep -rn "from src.core.config\|from src.core.enums" src/modules/copilot/
find src/ -name "*.py" -path "*llm*" -o -path "*model_tier*"
```

**Sistemas conocidos previos research:**
- ✅ Sistema A (KEEP): `src/core/config.py + src/core/enums.py + src/shared/infrastructure/llm/router.py + providers/{openai, kimi, _openai_compat}.py`
- ❌ Sistema B (DELETE PR-3 deuda): `src/modules/copilot/infrastructure/llm/{model_config.py, provider_factory.py, providers/deepseek.py}`
- ⚠️ Sistema C legacy (REFACTOR/DELETE ModelTier): `src/modules/copilot/domain/model_tier.py + routing_policy.py + consumers en application/router/, application/memory/`

**Decisión preliminar (architect refina):**
- A: EXTEND (agregar entry deepseek-v4-flash a `_openai_compat.py` registry si no está)
- B: DELETE entero
- C: REFACTOR consumers + DELETE archivo origen (Opción A walking skeleton step 5)

## Validación técnica preliminar

- **Modules afectados:**
  - `src/modules/copilot/domain/` (model_tier.py DELETE, routing_policy.py REFACTOR, ports.py touch ligero)
  - `src/modules/copilot/application/router/` (model_router + classifiers REFACTOR)
  - `src/modules/copilot/application/memory/` (rolling_summarizer + title_generator REFACTOR)
  - `src/modules/copilot/infrastructure/llm/` DELETE entero
  - `src/modules/copilot/infrastructure/repositories/routing_log_repository.py` (column rename si tabla almacena `tier`)
  - `src/modules/copilot/infrastructure/models/routing_log_model.py` (mismo)
  - `src/shared/infrastructure/llm/providers/_openai_compat.py` (verificar/agregar deepseek-v4-flash)
  - `backend/.env` + `backend/.env.example` (set AI_MODEL_NANO + AI_PROVIDER_NANO=deepseek si Chris autoriza activación post eval gate diferido o now)
- **Blockers conocidos:** ninguno bloqueante. Arch fitness test SSoT ya shipped (Bloque A) detecta regresión.
- **Tiempo estimado:** 1 ejecución architect + 1 ejecución builder con auto-loop. Probable main thread takeover (PR scope ~15 archivos = límite).
- **Alternativas técnicas:** ninguna — convergencia obligatoria por SSoT rule.

## Decisiones diferidas (explícitas)

- **Activación DeepSeek V4-Flash en `.env` prod**: defer a post eval gate S5 si Chris quiere safety check antes. Si Chris quiere agresivo (research valida 95%+ calidad), activar en este PR.
- **Migration column rename `routing_log.tier → role`**: si tabla existing tiene rows, migration con DEFAULT mapping + DROP column antiguo en S5+ (deprecation timeline).

## Out of scope

- LiteLLM Proxy intro (eso es PR-2 S3)
- DB registry runtime (S4)
- GrowthBook (S4)
- Eval gate pre-promote (S5)
- Embeddings + sales_agent voice (PI dedicados)

## Copilot-first checklist

- [x] ¿Operable conversacional desde copilot? — no (infra LLM layer transparente al user)
- [x] ¿Qué tools nuevos requiere? — ninguno
- [x] ¿Cards/UI nueva? — no
- [x] Si NO copilot → razón documentada — refactor infra cero impacto user-facing

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt pre-coce | Entregable esperado |
|---|---|---|---|
| Pre-design | `nicolify-architect` + `copilot-expert` + `sales-agent-expert` (verify NO touch §3) | `prompts/01-architect-start.md` | `CONTRACT.md` con audit cross-module + plan refactor + tests TDD lista cerrada |
| Implementation | `nicolify-backend` + `copilot-expert` | `prompts/02-builder-start.md` | `IMPL-LOG.md` + tests RED→GREEN + commit |
| Audit | `nicolify-backend-auditor` (auto-spawn) | `prompts/03-auditor-start.md` | `REVIEW.md` con verificación allowlist shrunk + arch fitness test SSoT verde |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/copilot.md` lineage |

## Surface impactada

| Tipo | Path / nombre | Cambio |
|---|---|---|
| BE refactor | `copilot/application/router/classifiers/llm_classifier.py` | ModelTier→ModelRole + Settings.get_model |
| BE refactor | `copilot/application/router/model_router.py` | ModelTier→ModelRole |
| BE refactor | `copilot/application/router/classifiers/rule_classifier.py` | ModelTier→ModelRole |
| BE refactor | `copilot/application/memory/rolling_summarizer.py` | LLMProvider injection desde shared, ModelRole.NANO |
| BE refactor | `copilot/application/memory/title_generator.py` | mismo |
| BE delete | `copilot/domain/model_tier.py` | DELETE archivo (Opción A) |
| BE refactor | `copilot/domain/routing_policy.py` | ModelTier→ModelRole |
| BE refactor | `copilot/domain/hooks/copilot_events.py` | ClassifierType.tier→role |
| BE refactor | `copilot/domain/skills/skill_metadata.py` | ModelTier→ModelRole |
| BE refactor | `copilot/domain/ports.py` | LLMProvider Protocol — quitar tier param o renombrar role |
| BE delete | `copilot/infrastructure/llm/` | DELETE entero |
| BE delete | `tests/modules/copilot/infrastructure/llm/` | DELETE dir |
| BE delete | `tests/architecture/test_pr3_no_sales_agent_imports.py` | DELETE (reemplazado por test_llm_routing_ssot) |
| BE migration | `alembic/versions/115_routing_log_tier_to_role.py` | rename column si tabla existing |
| BE config | `_openai_compat.py` | verificar/agregar deepseek-v4-flash entry |
| Env | `backend/.env` + `.env.example` | (opcional) AI_MODEL_NANO=deepseek-v4-flash + AI_PROVIDER_NANO=deepseek |
| Tests | refactor existing tests del classifier/summarizer/router | ModelTier→ModelRole |
| Arch fitness | `test_llm_routing_ssot.py` | KNOWN_LEGACY_LLM_FILES shrink (allowlist update) |
| current-state/ | `current-state/copilot.md` | append cap "LLM stack convergencia ModelRole único + cleanup PR-3" |

Total estimado: **~15 archivos** (target ≤15 cohesivo, no splittear).

## Tests requeridos (TDD)

- Refactor existing tests:
  - `tests/modules/copilot/application/router/test_llm_classifier.py` — usar ModelRole
  - `tests/modules/copilot/application/router/test_model_router.py` — RoutingDecision.role
  - `tests/modules/copilot/application/memory/test_rolling_summarizer.py` — LLMProvider injection
  - `tests/modules/copilot/application/memory/test_title_generator.py` — mismo
  - `tests/modules/copilot/domain/test_routing_policy.py` — default_role
- Tests nuevos integración:
  - `tests/modules/copilot/test_llm_classifier_settings_integration.py` — verificar usar settings.get_model + get_provider_for_role
- Arch fitness:
  - `test_llm_routing_ssot.py::test_no_new_modeltier_imports` PASS post-cleanup (allowlist shrunk)
  - `test_llm_routing_ssot.py::test_no_new_llm_factory_layers` PASS (copilot/infrastructure/llm/ DELETED)
- Migration test idempotente: si rename column → re-run upgrade head no-op.

## Aceptación

- [ ] Tests verde (refactor + nuevos)
- [ ] Lint/type check verde (ruff + mypy strict)
- [ ] `IMPL-LOG.md` completo
- [ ] `REVIEW.md` PASS
- [ ] `RESULT.md` escrito por PM
- [ ] `current-state/copilot.md` actualizado
- [ ] Decisiones registradas en `decisions.md` PI-2
- [ ] Verificación grep: `grep -rn "TIER_METADATA\|ModelTier" backend/src/modules/copilot/` = 0 hits
- [ ] Verificación path: `find backend/src/modules/copilot/infrastructure/llm/` = no such directory
- [ ] Arch fitness SSoT 4/4 verde + allowlist shrunk a ≤5 entries
- [ ] Si DeepSeek V4-Flash activado: query `copilot_llm_call.model` post deploy retorna nuevo modelo

## Riesgos

| Riesgo | Mitigación |
|---|---|
| ModelTier→ModelRole semantic mismatch (HEAVY=AGENT no exacto) | Architect decide mapping en CONTRACT con tabla equivalencias justificada |
| Refactor tests rompe baseline pre-existing | Baseline tests pre-refactor primero (snapshot comportamiento), refactor green después |
| `_openai_compat.py` no soporta `deepseek-v4-flash` | PR-1 bloque-mid: extender registry interno + tests |
| Sesión paralela toca `shared/infrastructure/llm/` | Probable cero (campaigns no toca LLM) — regla M8 si pasa |
| Migration column rename rompe rows existing | DEFAULT mapping en migration + tests data preserved |
