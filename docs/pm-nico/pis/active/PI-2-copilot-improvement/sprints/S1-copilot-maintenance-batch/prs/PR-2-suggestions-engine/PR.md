# PR-2-suggestions-engine

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-2-suggestions-engine |
| Sprint padre | S1-copilot-maintenance-batch |
| PI padre | PI-2-copilot-improvement |
| Estado | in-progress |
| Tipo | refactor + feature |
| Esfuerzo | L |
| Owner PM | /pm |
| Claimed by session | sesión 2026-04-29 main thread (Opus 4.7) |
| Inicio | 2026-04-29 (architect spawn) |

## Problema (user-facing)

User en copilot recibe "sugerencias" hardcoded en `application/tools/offer_section_tools.py` que no aprovechan contexto real (módulo actual, tenant state, history). Resultado: sugerencias genéricas que el user ignora. Limita la propuesta de valor copilot-first ("interfaz primaria que descubre lo que puedo hacer").

JTBD: "como user de Nicolify, quiero que el copilot me sugiera la próxima acción concreta basada en lo que YO necesito ahora, no recetas genéricas".

## Outcome esperado

- Motor real de suggestions: `SuggestionEngine` que recibe context (route + tenant state + recent actions) y devuelve N sugerencias rankeadas
- Provider pattern: cada módulo registra `SuggestionProvider` (offer, brand, copilot, etc.). Engine compone resultados
- Adapter consume `SuggestionEngine` desde tools transversales (reemplaza `offer_section_tools.py` hardcoded)
- Métrica observable: `copilot_suggestion_shown` + `copilot_suggestion_accepted` (eventos para futura optimización)

## Walking skeleton (mínimo viable cohesivo)

1. `domain/suggestion.py`: `Suggestion` value-object (id, label, action, score, source_module, metadata)
2. `application/suggestions/engine.py`: `SuggestionEngine` con registry + `get_suggestions(context) -> list[Suggestion]`
3. `application/suggestions/providers/`: interface `SuggestionProvider` + 1 provider concreto inicial (`OfferSectionProvider` que reemplaza hardcoded hint actual)
4. `application/suggestions/registry.py`: bootstrap registra providers
5. Refactor `offer_section_tools.py`: consume `SuggestionEngine.get_suggestions(context)` en lugar de hint hardcoded
6. Eventos observabilidad: `SuggestionShownEvent`, `SuggestionAcceptedEvent` (best-effort write)
7. Tests: engine standalone + provider offer + integración tool wiring

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A: Registry + Provider pattern (módulos opt-in) | Extensible cero refactor (cada módulo agrega provider). DDD-friendly | LOC mayor inicial | ELEGIDA |
| B: LangGraph subagent dedicado para suggestions | Reutiliza infraestructura agentic, suggestions con LLM | Latencia + costo + scope creep enorme | descartada — postpone si motor estático no alcanza |
| C: Hardcoded refactor a config YAML | Trivial | No resuelve problema de fondo (sigue genérico) | descartada |

## Validación técnica preliminar (Technical Sanity Check)

- Modules afectados: `modules/copilot/{domain,application/suggestions,application/tools/offer_section_tools.py}`
- Blockers conocidos: provider para módulos no-copilot (offer, brand) requiere import boundary check — copilot puede importar otros (es infra-like, regla `backend-ddd.md` excepción explícita)
- Tiempo estimado: 1 sesión architect + 2 sesión builder (provider + tool refactor + tests) + 1 sesión auditor
- Alternativas técnicas: usar `pluggy` lib (descartado — registry manual es ~50 LOC sin dep nueva)

## Decisiones diferidas (explícitas)

- ¿Score ranking con LLM o heurística simple? → Architect decide en CONTRACT (default heurística por simplicidad; LLM postpone PI-2 S2+)
- ¿Persistencia de suggestions accepted para fine-tuning futuro? → Sí pero best-effort (no romper turn). Tabla `copilot_suggestion_event` o reusar `copilot_trace_event`
- ¿Más providers en este PR (brand, copilot) o solo offer? → Solo offer en este PR, otros PR siguiente

## Out of scope

- Cards UI nuevas para mostrar suggestions con botón "aceptar" (BE-only este PR; FE cards = PR FE separado en S1 PR-4 opcional o S2)
- LLM-powered ranking (heurística estática este PR)
- Providers para módulos brand, sales_agent, analytics (solo offer este PR)
- ML feedback loop (suggestions accepted → reranker)

## Copilot-first checklist

- [x] ¿Operable conversacional desde copilot? **SÍ** — el motor ALIMENTA copilot. Es infra del copilot mismo
- [x] ¿Qué tools nuevos requiere? Ninguno externo. Reemplaza interno `offer_section_tools` hardcoded
- [ ] ¿Cards/UI nueva? FE cards de aceptación = PR siguiente (este es BE motor)
- [x] Si NO copilot → razón documentada: aplica copilot-first, motor BE habilita suggestions visibles en cards copilot

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt pre-coce | Entregable esperado |
|---|---|---|---|
| Pre-design | `nicolify-architect` + `copilot-expert` | `prompts/01-architect-start.md` | `CONTRACT.md` |
| Implementation | `nicolify-backend` + `copilot-expert` (`nicolify-agentic` solo si architect decide LLM ranking, default no) | `prompts/02-builder-start.md` | code + tests + IMPL-LOG.md |
| Audit | `nicolify-backend-auditor` + `copilot-expert` | `prompts/03-auditor-start.md` | `REVIEW.md` |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/copilot.md` update |

## Surface impactada

| Tipo | Path / nombre | Cambio |
|---|---|---|
| Domain | `modules/copilot/domain/suggestion.py` | nuevo (value object) |
| Application | `modules/copilot/application/suggestions/engine.py` | nuevo |
| Application | `modules/copilot/application/suggestions/providers/{base,offer_section}.py` | nuevos |
| Application | `modules/copilot/application/suggestions/registry.py` | nuevo |
| Application | `modules/copilot/application/tools/offer_section_tools.py` | refactor (consume engine) |
| Eventos | `modules/copilot/domain/events.py` | + `SuggestionShownEvent`, `SuggestionAcceptedEvent` |
| Observabilidad | `modules/copilot/observability/` | hook eventos a trace event recorder |
| Tests | `backend/tests/modules/copilot/suggestions/` (nueva carpeta) | engine + providers + tool wire |
| current-state/ | `current-state/copilot.md` | append capability "Suggestion engine + provider registry" + lineage |

## Tests requeridos (TDD)

- `test_engine_register_provider.py` — registra provider, retrieve via `get_suggestions(context)`
- `test_engine_score_ranking.py` — múltiples providers, score desc orden
- `test_offer_section_provider.py` — context offer_studio → suggestions específicas tipo "agregar testimonios"
- `test_offer_section_tools_consumes_engine.py` — refactor preserva contrato externo tool
- `test_suggestion_event_recorded.py` — engine.get → emite `SuggestionShownEvent` (best-effort, no rompe turn si falla)

## Aceptación

- [ ] Tests verdes (5 nuevos + tests `offer_section_tools` existentes intactos)
- [ ] Lint/type check verdes
- [ ] No imports cruzados ilegales (copilot puede importar otros, OK)
- [ ] `IMPL-LOG.md` completo
- [ ] `REVIEW.md` PASS
- [ ] `RESULT.md` escrito por PM
- [ ] `current-state/copilot.md` actualizado
- [ ] Decisiones registradas en `decisions.md` PI-2

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Provider para módulos no-copilot rompe boundary DDD | Copilot tiene excepción explícita en regla (infra-like). Verify arch test no lo bloquea |
| Tool refactor rompe contrato externo (consumers downstream) | Mantener signature pública tool, cambiar solo implementación interna |
| Eventos observabilidad rompen turn copilot si DB cae | `try/except + structlog warning` (regla `copilot-observability.md`) |
| Scope creep LangGraph subagent | Architect veta en CONTRACT — heurística estática este PR |
| Provider offer requiere lectura de offer state (cross-module) | OK, copilot tiene excepción. Read-only, sin mutación |
