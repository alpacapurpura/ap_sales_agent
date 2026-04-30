# PR-2-pure-expansion-providers

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-2-pure-expansion-providers |
| Sprint padre | S2-copilot-cero-deuda-stack |
| PI padre | PI-2-copilot-improvement |
| Estado | shipped |
| Tipo | refactor + feature (BE pure expansion + 3 providers nuevos) |
| Esfuerzo | M |
| Owner PM | /pm |
| Claimed by session | 2026-04-30 sesión PI-2 S2 (módulo copilot) |
| Cerrado | 2026-04-30 — verdict PASS (PM main thread post builder truncation) |

## Problema (user-facing)

Sugerencias copilot hoy son **subproducto de heurísticas hardcoded** (último resto en `offer_section_tools.py`) + único provider real (`OfferSuggestionProvider`). Otros módulos (brand, sales, copilot transversal) NO tienen sugerencias dinámicas.

JTBD: "Cuando estoy en cualquier módulo (brand, offer, sales, copilot home) quiero ver smart-chips relevantes a ese módulo, no solo en offer-studio."

Plus deuda interna: `offer_section_tools.py` quedó híbrido S1 PR-2 (engine helper + static fallback). Cero deuda = cero static residual.

## Outcome esperado

- 3 providers nuevos registrados: `BrandSuggestionProvider`, `SalesAgentSuggestionProvider`, `CopilotSuggestionProvider`.
- `offer_section_tools.py` completamente engine-driven (0 `"suggestions": [...]` literales como datos hardcoded).
- Smart-chips funcionan en routes `/brand-studio`, `/sales`, `/` (copilot home), no solo `/offer-studio`.

Métrica: cobertura providers = 4/4 routes principales con chips dinámicos.

## Walking skeleton (mínimo viable cohesivo)

1. **`BrandSuggestionProvider`** (`backend/src/modules/copilot/application/suggestions/providers/brand.py`): heurísticas brand completion ratio, missing UVP, missing buyer_persona, voice_tone vacío. `applies_to_routes=("/brand-studio",)`. `provider_priority=10`.
2. **`SalesAgentSuggestionProvider`** (`.../providers/sales_agent.py`): heurísticas sales pipeline (no leads en últimas 24h, conversion rate <X%, agent paused). `applies_to_routes=("/sales",)`. `provider_priority=10`.
3. **`CopilotSuggestionProvider`** (`.../providers/copilot.py`): transversal, sin `applies_to_routes` (todos). Heurísticas onboarding (módulos vacíos cross-cutting, conversación nueva). `provider_priority=5` (lower priority — fallback).
4. **Pure expansion `offer_section_tools.py`**: eliminar `"suggestions": [hint]` line 163; refactor `_build_response_dict()` o equivalente para que `suggestions` field venga 100% de `_engine_suggestions_for_context()` (que ya llama engine). Si engine retorna `[]` → `suggestions: []` (graceful). Update tests dependientes.
5. **Registry update** (`registry.py` si aplica): registrar 3 nuevos providers en `get_default_engine()` en orden estable.

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A — 3 providers nuevos completos + pure expansion en mismo PR | Cohesivo: pure expansion sin providers extras = chips genéricas. Con providers, chips ricas en cada route. | PR un poco más grande pero sigue M | **ELEGIDA** |
| B — Solo pure expansion, providers nuevos PR separado | Más chico cada uno | Pure expansion sin providers = chips offer-only en otras routes (regresión user) | descartada — orfandad UX |
| C — Solo providers, pure expansion S3 | Closes part of debt | Deja deuda S1 #3 sin cerrar — viola "cero deuda" Chris | descartada — viola criterio |

## Validación técnica preliminar

- **Modules afectados:**
  - BE: `copilot/application/suggestions/providers/` (3 archivos nuevos), `copilot/application/suggestions/registry.py`, `copilot/application/tools/offer_section_tools.py` (refactor target).
  - Cross-module reads: brand repo, sales_agent repo, module_registry (helpers existentes — no cambian).
- **Blockers conocidos:** ninguno. Engine ya soporta múltiples providers + ranking. Pattern provider establecido en `OfferSuggestionProvider`.
- **Tiempo estimado:** 1 ejecución architect + 1 ejecución builder con auto-loop.
- **Alternativas técnicas:** ninguna.

## Decisiones diferidas (explícitas)

- **Caching agresivo per-tenant providers** (Redis 5min): si latencia engine >10ms p99 post-3-providers → habilitar. Defer hasta data prod.
- **Provider priority weights**: actuales (offer 0, brand 10, sales 10, copilot 5) — tunear post métricas adopción real.

## Out of scope

- LLM-based ranking — backlog (mismo defer que PR-1 risk).
- Tabla persistencia dedicada — `copilot_trace_event` sigue.
- Analytics provider (route `/growth-studio`) — backlog. No bloquea S2.
- Connections provider (route `/connections`) — backlog.

## Copilot-first checklist

- [x] ¿Operable conversacional desde copilot? — **sí indirecto** (chips habilitan exploración rápida)
- [x] ¿Qué tools nuevos requiere? — ninguno (providers son backend-only)
- [x] ¿Cards/UI nueva? — no (FE consume mismo endpoint PR-1)
- [x] Si NO copilot → razón documentada — N/A

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt pre-coce | Entregable esperado |
|---|---|---|---|
| Pre-design | `nicolify-architect` + `copilot-expert` + `brand-expert` + `sales-agent-expert` | `prompts/01-architect-start.md` | `CONTRACT.md` (heurísticas per provider, data joins, fallbacks) |
| Implementation | `nicolify-backend` + `copilot-expert` | `prompts/02-builder-start.md` | `IMPL-LOG.md` + tests + commit |
| Audit | `nicolify-backend-auditor` (auto-spawn) | `prompts/03-auditor-start.md` | `REVIEW.md` |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/copilot.md` lineage |

## Surface impactada

| Tipo | Path / nombre | Cambio |
|---|---|---|
| BE provider | `copilot/application/suggestions/providers/brand.py` | nuevo |
| BE provider | `copilot/application/suggestions/providers/sales_agent.py` | nuevo |
| BE provider | `copilot/application/suggestions/providers/copilot.py` | nuevo |
| BE registry | `copilot/application/suggestions/registry.py` | modificado (registrar 3) |
| BE tool | `copilot/application/tools/offer_section_tools.py` | refactor (drop static suggestions[]) |
| current-state/ | `current-state/copilot.md` | append cap "3 providers nuevos + pure expansion offer_section_tools" |

## Tests requeridos (TDD)

- `tests/modules/copilot/application/suggestions/providers/test_brand_provider.py`: brand_completion <30% → "completar marca" chip; UVP vacío → chip; voice_tone vacío → chip; tenant isolation
- `tests/modules/copilot/application/suggestions/providers/test_sales_agent_provider.py`: no_leads_24h chip; conv_rate < threshold chip; agent_paused chip; tenant isolation
- `tests/modules/copilot/application/suggestions/providers/test_copilot_provider.py`: onboarding empty chip; cross-module gap chip; tenant isolation
- `tests/modules/copilot/application/suggestions/test_registry.py`: get_default_engine returns 4 providers (offer + brand + sales_agent + copilot) en orden priority
- `tests/modules/copilot/application/tools/test_offer_section_tools.py`: refactor — verificar engine-driven path. `_build_response()` con engine [] → suggestions [] graceful
- `tests/modules/copilot/application/suggestions/test_engine_integration.py`: engine con 4 providers retorna chips ranked respetando provider_priority + cap 5 total

## Aceptación

- [ ] Tests verdes (BE)
- [ ] Lint/type check verdes
- [ ] `IMPL-LOG.md` completo
- [ ] `REVIEW.md` PASS (sin findings críticos)
- [ ] `RESULT.md` escrito por PM
- [ ] `current-state/copilot.md` actualizado con lineage
- [ ] Decisiones registradas en `decisions.md` PI-2
- [ ] grep verifica: `grep -n '"suggestions": \[' offer_section_tools.py` → 0 hits hardcoded literales
- [ ] Verificación manual: dev up + curl `POST /copilot/suggestions` con route=`brand-studio` → chips brand visibles

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Brand/SalesAgent providers latencia >10ms p99 (data joins) | Engine SLA <10ms p99 budget — providers async + soft TTL cache 5min per tenant+route si supera (defer evaluar prod) |
| Heurísticas brand/sales mal calibradas (chips irrelevantes) | 6 heurísticas mínimas per provider validadas con `brand-expert` + `sales-agent-expert` skills |
| Refactor `offer_section_tools.py` rompe tools existentes (1523 LOC) | Tests pre-existentes deben mantenerse verdes; baseline test pre-refactor |
| Sesión paralela toca `offer_section_tools.py` | Regla M8: leer cambios ajenos + extend (no replace bloque entero) |
