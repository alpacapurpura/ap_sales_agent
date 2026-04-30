# Handoff — S2-copilot-cero-deuda-stack → próximo sprint

> Owner: `/pm`. Producido al cerrar sprint. Input para sprint siguiente o cierre PI.

## Estado cierre

| Campo | Valor |
|---|---|
| Sprint | S2-copilot-cero-deuda-stack |
| Cierre | 2026-04-30 |
| PRs shipped | 3/3 (PR-1 fe-swap-suggestions-api PASS · PR-2 pure-expansion-providers PASS · PR-3 llm-cost-optimization PASS PARTIAL) |
| Verdicts | PR-1 BE+FE PASS (1 iter cada uno) · PR-2 PASS (1 iter PM main thread) · PR-3 PASS PARTIAL (wiring DEFERRED PR-4) |
| Commits totales sprint | 7 (research + 3 architects + 3 builders + 3 cierres = 10 — algunos consolidados) |

## Surface entregada al PI

### Backend infra
- **Suggestion engine API endpoints** (PR-1): `POST /copilot/suggestions` (engine + breakdown + latency_ms) + `POST /copilot/suggestions/accept` (event SuggestionAccepted producer). 5 Pydantic v2 DTOs.
- **3 nuevos suggestion providers** (PR-2): `BrandSuggestionProvider` (7 reglas, route brand-studio, priority=10), `SalesAgentSuggestionProvider` (5 reglas, route sales, priority=10, §3 read-only via port), `CopilotSuggestionProvider` (5 reglas transversal, priority=5).
- **SalesAgentObservabilityPort** (PR-2): nuevo port `shared/links/ports/sales_agent.py` + adapter en `sales_agent/application/services/observability_adapter.py` (read-only enrollments + messages, PII-stripped DTO).
- **BrandDataPort extension** (PR-2): 2 abstract methods nuevos additive (`get_buyer_persona_count`, `get_active_personality_profile_present`) + adapter impl.
- **Pure expansion `offer_section_tools.py`** (PR-2): 0 static `"suggestions": [hint]` literales hardcoded post-refactor (cierra deuda S1 PR-2 D-9).
- **LLM cost optimization infra** (PR-3 PARTIAL): `model_config.py` env override layer, `DeepSeekLLMProvider` adapter, `provider_factory` con fallback chain, eval gate framework completo (golden_dataset + runner + scorers + 100 goldens).
- **Migration alembic 114** (PR-3): pricing snapshot deepseek-v4-flash idempotente.

### API endpoints nuevos
- `POST /api/v1/copilot/suggestions` (response_model SuggestionsResponse)
- `POST /api/v1/copilot/suggestions/accept` (response_model SuggestionAcceptResponse)

### Frontend
- **Voice transcription endpoint estable** (PR-1): `voice-api.ts` migra `/voice/transcribe` (410 Gone) → `/voice/upload-and-transcribe` con D-9 shape adapter.
- **Smart-chips dinámicas live** (PR-1): `useSuggestions` rewrite React Query hook, `useSuggestionAccept` mutation fire-and-forget, drop `ROUTE_SUGGESTIONS` static map en SuggestedChips + SuggestedActions.

### Tests agregados
- 16 BE PR-1 (8 unit + 5 unit accept + 3 integration)
- 21 FE PR-1 (use-suggestions, use-suggestion-accept, voice-api, SuggestedChips)
- 54 BE PR-2 (3 providers + registry + engine integration + tools refactor + brand adapter + sales_agent adapter)
- 6 BE PR-3 smoke (5 model_config + 1 arch sales_agent isolation)
- **Total nuevos: 97 tests** (todos verde)

### current-state/copilot.md updates
- Cap: Smart-chips dinámicas FE consume engine + producer event (PR-1)
- Cap: Voice transcription endpoint estable (legacy retired live) (PR-1)
- Cap: 4 suggestion providers — multi-route smart-chips (PR-2)
- Cap: SalesAgentObservabilityPort cross-module read-only (PR-2)
- Cap: offer_section_tools pure expansion (cero deuda S1 PR-2) (PR-2)
- Cap: BrandDataPort extension additive (PR-2)
- Cap: LLM stack DeepSeek V4-Flash infra ready (wiring PR-4 pendiente) (PR-3 PARTIAL)

## Decisiones cross-PR (para decisions.md PI-2)

Ya appendeadas a `decisions.md`. Ver entradas 2026-04-30 (4 entradas: S2 inicio, PR-1, PR-2, PR-3 PARTIAL).

## Riesgos abiertos al sprint siguiente

| Riesgo | Mitigación propuesta | Sprint destino |
|---|---|---|
| Wiring upstream LLMClassifier+RollingSummarizer NO ejecutado — env flags `COPILOT_TIER_*_PROVIDER=deepseek` NO toman efecto runtime | PR-4-llm-wiring-runtime: encontrar LLMProvider factory upstream + injection + tests T-2..T-8 (~50 LOC + 24 tests + .env) | S3 PR-1 |
| 6 `# type: ignore[...]` defensivos en PR-2 providers (port retorna `object`) | Backlog refinar tipos port methods | Backlog cleanup |
| 4 `# ruff: noqa: ANN401` file-level PR-3 (LLM SDK dynamically typed) | Justificado — no acción requerida | n/a |
| Sales_agent voice swap pendiente Q3 2026 | rule sales-agent-brand-voice + voice fidelity grader | PI futuro Q3 |
| Embeddings migration (Qwen3-Embedding-8B) requires Qdrant re-index ventana mantenimiento | PR dedicado con rollback plan | PI futuro |
| Specialist (REASONING + HEAVY) tier swap calidad-crítico | Eval gate goldens >100 + comparación blind | S4+ o PI futuro |

## Skills/agentes recomendados S3

- Si S3 incluye **wiring upstream PR-4** (CRÍTICO): `nicolify-architect` (verificar LLMProvider factory location) + `nicolify-backend` + `nicolify-backend-auditor` + `copilot-expert`
- Si S3 incluye **multicanal Bloque A Telegram bridge**: `nicolify-architect` + `nicolify-backend` + `copilot-expert` + `manychat-expert` (pattern reference) + `nicolify-backend-auditor`
- Si S3 incluye **discovery formal Bloque C**: PM solo + `Explore` agent (research patrones agentic copilot 2026)

**Sugerencia PM:** S3 = S3-copilot-llm-wiring-runtime con PR-1 wiring (cierra deuda PR-3 PARTIAL) + PR-2 multicanal Telegram bridge (Bloque A inicio). Cohesivo cumple cero deuda + abre nueva capacidad cliente-facing.

## Pase a producción

Sprint S2 acumula:
- 1 migración nueva (`114_pricing_deepseek_v4_flash`)
- 97 tests nuevos
- 2 endpoints API nuevos (suggestions + suggestions/accept)
- Cross-stack: BE 26 archivos + FE 11 archivos
- Total commits: ~7

**Recomendación PM**: pase a producción factible POST S3 PR-1 wiring runtime. Razón: ship PR-1+PR-2 ahora aporta smart-chips live (user-facing). Ship PR-3 wiring activa cost reduction (financial impact). Pasar las 3 juntas reduce ventanas deploy.

Pre-requisitos pase prod S2:
- `/test-all` pase
- Migration prod-clone test (`114`)
- `make ci-parity` antes `git push origin main`
- Smoke E2E voice + suggestions + accept event tracking post-deploy

Auto-spawn agent PASE-PRODUCCION → POST PR-3 wiring shipped (no antes).

## Próximo sprint sugerencia

**Opción A (recomendada PM):** S3-copilot-llm-wiring-runtime
- PR-1 wiring upstream LLMClassifier+RollingSummarizer factory (cierra deuda PR-3 PARTIAL) — esfuerzo S/M
- PR-2 (opcional) Telegram bridge MVP Bloque A (multicanal) — esfuerzo M

**Opción B:** Cerrar PI-2, abrir PI-3 dedicado multicanal (Bloque A) + PR técnico LLM wiring como PI-2 sub-task.

**Opción C:** S3-copilot-discovery-formal Bloque C (entrevistas users + research patrones agentic 2026 Replit/Cursor/Claude Projects).

PM recomienda **A** (cohesivo + cierra deuda visible + abre multicanal). Después decidir B vs C según métricas adopción smart-chips post pase prod.
