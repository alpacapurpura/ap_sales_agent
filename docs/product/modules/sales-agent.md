---
module: sales-agent
last_audit: 2026-05-04
status: active                                  # active | maintenance | placeholder
links:
  capabilities_dir: "../capabilities/sales-agent/"
  stories_dir: "../stories/sales-agent/"
  domain_doc: "../../domains/module_sales-agent.md"
active_projects: []                              # auto-populated by /pm cuando hay PIs activos tocando este módulo
capability_registry_status: bootstrapped-2026-05-04
agentic_eval_suite_path: null                   # GAP: no agentic_evals/sales_agent/ — flagged CRÍTICO en gap-report-2026-05-04-group-c
---

# sales_agent — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Sales |
| Estado | activo (en mejora — PI-3) |
| Última actualización | 2026-04-29 (bootstrap) |
| Doc técnico | `docs/domains/module_sales_agent.md` |

## Qué hace por el user
AI SDR autónomo. Conversa con leads en canales conectados, pre-califica, maneja objeciones, agenda citas, envía links de pago, da seguimiento. Reemplaza función de un setter humano.

## Capacidades
> Auto-list generated from `docs/product/capabilities/sales-agent/`.
> See `docs/product/BACKLOG.md` "Capabilities snapshot" for current count + status.

## Capacidades operables desde copilot
- Activar / pausar agente (sólido)
- Ver últimas conversaciones (parcial)
- Ajustar voz vía Brand Studio communication-style (sólido)
- **Gap:** conversación natural con copilot sobre cómo ajustar comportamiento agente

## LLM routing
- **Dispatch único vía LiteLLM Proxy** (canonicalizado PI-12 S1, 2026-05-06). Ver `docs/domains/llm-routing.md` para SSoT técnica completa.
- Per-provider adapters legacy (`OpenAIService`, `KimiService`, `DeepSeekService`, `QwenService`, `GeminiService`, `_openai_compat`) eliminados físicamente (T-4 commit `429913a3`).
- El feature flag que toggleaba proxy vs adapters fue eliminado de `Settings` — no existe fallback ni reversión a per-provider direct (T-5 commits `28617716` + `560f14b5`).
- API keys de provider viven en `litellm_config.yaml` (env vars del proxy). Las columnas tenant `{openai,deepseek,kimi,dashscope}_api_key` están deprecadas Phase 1 (T-6a commits `f6e7ad0a` + `29b97eba`); DROP COLUMN final en T-6c post operational gate T-6b. `tenants.gemini_api_key` se preserva (uso paralelo Vertex AI).
- **Cost tracking runtime** vía `CostRecorderCustomLogger` (T-1 commit `5856be4d`) — captura `kwargs["response_cost"]` LiteLLM-native en cache TTL 60s, persiste vía LangChain callback handler en `sales_agent_llm_call.cost_usd`. `model_pricing_snapshot` queda como audit ledger histórico (no se invoca en runtime).
- Specialist routing por `ModelRole` semántico (NANO/FAST/REASONING/AGENT) declarado en `backend/src/modules/sales_agent/domain/model_tier.py::LLM_ROLE_BY_SITE`. Concrete provider+model resuelven por env vars `AI_PROVIDER_<ROLE>` + `AI_MODEL_<ROLE>`.

## Estado calidad funcional
| Capacidad | Estado | Notas |
|---|---|---|
| Conversación core | sólido | Redesign 2026-04 finalizado |
| Voz marca | sólido | SSoT en `personality_profiles.system_instruction` |
| Tools (scheduler, payment) | sólido | |
| **Observabilidad traces persistence** | **live** | PR-2 (PI-1.1, S2, commit `d80d15f5`, 2026-05-01) — wire `observe_turn` lifecycle around `agent_app.ainvoke`. Pre-PR: 0 rows globalmente. Post-PR: traces reales persistidos (smoke verified +4 trace_event +2 llm_call) |
| Cost tracking sales_agent | live | PR-2 — captura cost_usd + fx_rate también en errors (best-effort) |
| Routing decisions auditables | live | PR-1 PI-7 (commit `d8226cf9`, 2026-05-01) — LLM functional, schema populated |
| **Eval simulator dual-LLM** | **live** | Story B PI-12 sub-épica eval-foundation-* (2026-05-08, Migration 125 + 10 tickets). Dual-LLM harness in-process bajo `backend/tests/agentic_evals/sales_agent/simulator/` con public API minimal 7 nombres. Cost-bucket separation via NEW tables `eval_simulator_{llm_call,trace_event}` + `eval_synthetic_tenants` (paridad campaigns precedent). Schema versioning + frozen golden v1 + termination policy registry forward-compat. Unblocks Stories C/D/E/F/G/H/I (personas runtime + goldens curation + voice fidelity grader + pass^k tracking + cost cap CI gate + adversarial jailbreak suite). |
| **Personas-as-simulators (Story C)** | **developed (pending audit)** | Story C `sales-agent-personas-instrumented-runtime` (2026-05-08, 9 tickets). 15 archetype-aware personas YAML (5 archetypes × 3 dialects: AR/MX/CO/PE/419) en `docs/specs/personas/archetype-aware/` + 5 _legacy preserved. ActorProfile schema v1→v2 con identity migrators (SCHEMA_MIGRATIONS registry). Customer Prompt V2 sub-slot pain/objection rotation turn-by-turn (additive — V1 byte-equal preserved). customer_node V1/V2 dispatch + extends eval_metadata con persona_kind/schema_version/archetype (Story B 6 invariants preserved). Scenarios 5 (qualification × 5 × 3 trials) + 6 (nurture 8-15 turns × 5) skip-with-escalation pendientes qualify_lead/tag_lead_status toolkit — test cement listo. Scenario 4 adversarial extiende Story B fixture con prompt-injection-via-traits (REUSE FORBIDDEN_LEAK_STRINGS). Story B H9 surface frozen 7 names + H10 frozen golden v1 byte-equal preservados. |
| Multi-canal | parcial | IG/FB OK, WhatsApp pendiente |
| Prompt cache | sólido | Per-tenant key |
| LLM call functional | **live** | PR-1 PI-7 (commits `1bdcfdc9`+`d8226cf9`, 2026-05-01) — Bug #9 LiteLLM restored (LITELLM_ENVIRONMENT propagation + memory 1536M) + Bug #7 brand_data_adapter ORM→DTO. Smoke real Chris-mediated 16:09 UTC: turn_end status='ok', 4 LLM calls (gpt-4o-mini + deepseek-reasoner) |
| Cost tracking accuracy | **degraded** | `cost_usd=0` post-fix por pricing resolution provider mapping (deepseek tagged como openai). Backlog PR follow-up |

## Conexiones cross-módulo
- **Lee de:** crm, brand, offer, connections, scheduling
- **Lo lee:** copilot, connections

## Dolor user / oportunidades detectadas
_Pendiente captura._

## PIs históricos
| PI | Cambio | Fecha cierre |
|---|---|---|
| sales-agent-redesign-s12 | Redesign completo, 12 sprints | 2026-04 |
| PI-1.1-pi1-post-mortem S2 PR-2 | Lift `BaseObservabilityContext` + Bug #2 traces persistence + Bug #8 FXResolver.default | 2026-05-01 |
| PI-7-app-stability-restore S1 PR-1 | Bug #7 brand_data_adapter ORM→DTO + Bug #9 LiteLLM env propagation + memory OOM fix → sales_agent restored functional end-to-end | 2026-05-01 |

## Decisiones producto vinculadas
| Fecha | Decisión | Razón |
|---|---|---|
| 2026-04-28 | Voz vive en personality_profile compilado, slot 5 BRAND_VOICE | SSoT + cache per-tenant + sin fine-tune |
| 2026-04 | Tier pricing semantic routing | Optimizar costo (Kimi 200k context tier) |
