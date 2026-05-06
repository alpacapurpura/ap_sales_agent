# S2-shared-observability — Handoff

> Sprint cierre 2026-05-01. Único PR (PR-2) shipped. PI-1.1 estado: scope reducido cumplido — decision Chris pendiente: cerrar PI-1.1 o continuar con sub-PRs deferred (#7 brand, #9 infra).

## Decisiones tomadas en este sprint

| # | Decisión | Aplicación |
|---|---|---|
| D-8 | 5-layer anti-duplication enforcement primer test PASSED | Proceso cementado funciona. Layer 1 catched PR.md outdated FXResolver line numbers |
| D-9 | Bug #2 fix verificado smoke real Telegram | Sales agent observability LIVE. 4 trace events + 2 llm_call post-message verified |
| D-10 | Bot error técnico durante smoke por Bug #7+#9 cascade — out-of-scope PR-2 | Bugs deferred a PRs separados (brand backend negocio + infra LiteLLM) |

## Surface entregada

### Shared NEW

- `shared/agent_observability/recording/turn_envelope.py::BaseObservabilityContext` (Template Method ABC)
- `shared/agent_observability/cost/fx_resolver.py::FXResolver.default()` (classmethod EXTEND)

### Copilot REFACTOR in-place

- `copilot/observability/recording/turn_envelope.py` — class becomes subclass + back-compat alias
- `copilot/application/orchestrator/chat.py` — FXResolver.default()

### Sales agent NEW + Bug #2/#8 fix

- `sales_agent/observability/recording/turn_envelope.py::SalesAgentObservabilityContext` (NEW subclass)
- `sales_agent/observability/recording/factory.py:78` — Bug #8 FXResolver.default()
- `sales_agent/application/orchestrator/{chat,outbound_orchestrator,conversation_pipeline}.py` — Bug #2 wire `observe_turn` lifecycle

### Tests

- 6 NEW test files (base contract + FX factory + copilot inheritance regression + sales subclass behavior + real DB persistence + arch ratchet anti-duplication-envelope)
- All gates green (369/369 obs tests + 20/20 PR arch)

## Métricas sprint

| Métrica | Target | Real |
|---|---|---|
| Architect Opus produces CONTRACT.md grep evidence | sí | ✅ 747 lines, 9 secciones |
| Builder Step 0 GATE documented | sí | ✅ IMPL-LOG-agentic § "Step 0 grep findings" |
| Auditor Cat 13 mirror detection PASS | sí | ✅ verdict PASS iter 1 |
| Bug #2 traces persisten post-Telegram message real | ≥3 rows | ✅ 4 trace + 2 llm_call |
| `FXResolver()` no-arg en codebase post-PR | 0 | ✅ enforced via arch test |
| Mirror `turn_envelope.py` per-module | 1 (sales NEW with distinct class) | ✅ no byte-mirror, 3 overrides + 2 fields |
| Cross-session M8 verified | no overlap | ✅ hunks distintos vs PI-5 PR-2 |

## Hipótesis sprint validadas

**H1: Anti-duplication 5-layer enforcement previene mirror recurrence.**
✅ VALIDADA. Architect ejecutando Step 0 GATE catched PR.md outdated info. Builder NO mirror creado. Auditor Cat 13 verified.

**H2: Shared base + concrete subclass es estructura right-sized para growth.**
✅ VALIDADA. SalesAgentObservabilityContext = ~80 LOC. Future agente (commercial_director PI-6, ManyChat WA, IG DM) puede heredar mismo pattern <50 LOC.

## Bloqueadores discovered

| Bug | Severidad | Owner futuro |
|---|---|---|
| **#7 PersonalityProfileModel.model_dump** brand_data_adapter | CRÍTICO bloquea agent identity build | PR dedicado backend negocio (módulo brand) |
| **#9 LiteLLM container exited mount config.yaml** | CRÍTICO bloquea TODOS LLM calls runtime | PR dedicado infra (docker compose mount fix + restart) |
| #5 Maximum update depth FE | a investigar | TBD post-reproduce |
| #6 Tenant switch non-persist Clerk publicMetadata | medio UX | PR dedicado FE Clerk session |

## Recomendaciones sprint siguiente

### Opción A — Cerrar PI-1.1 ahora con scope reducido

Justificación: PI-1.1 misión era post-mortem PI-1 hotfixes. Bugs #1+#4 (PR-1) + #2+#8 (PR-2) shipped. Bugs descubiertos cascading (#7+#9+#5+#6) son scope SEPARADO de "post-mortem PI-1" — son discovery propios.

Acciones:
- Escribir `retro.md` PI-1.1
- Move folder a `pis/archive/PI-1.1-pi1-post-mortem/`
- Abrir issues separados para #7+#9+#5+#6 con owner asignado
- Roadmap append "Done" PI-1.1

### Opción B — PI-1.1 mantener active con sprint S3 que cubre #7+#9

Justificación: bugs descubiertos vía PI-1.1 testing. Cohesión thematic con PI-1.1 (post-mortem PI-1).

Acciones:
- Sprint S3-cascade-bugs con PR-3 (Bug #7) + PR-4 (Bug #9)
- Architect mandatory para cada (ahora regla)
- Posible scope creep — riesgo

### Opción C (recomendada PM) — Cerrar PI-1.1 + abrir nuevos PRs en sus PIs naturales

Justificación: cleanest. PI-1.1 cumplió misión (hotfixes PI-1). Bugs descubiertos cascading van a PIs naturales:

- **Bug #7** brand adapter → opening en PI sin nombre yet (brand-evolutive-maintenance ya existe activo? — verificar)
- **Bug #9** LiteLLM infra → opening en infra-related PI o crear PI nuevo "infra-stability"
- **Bug #5** FE max update depth → defer hasta repro
- **Bug #6** Clerk tenant switch FE → PI tenant-management nuevo o PI iam-stability

Acciones:
- Cerrar PI-1.1 con retro.md
- Notificar Chris bugs descubiertos para que decida PI homes
- PM no inventa PIs — Chris owns roadmap decisions

## Skills consultados durante sprint (anti-skill-routing-violation evidence)

- copilot-expert (architect + builder + auditor)
- sales-agent-expert (architect + builder + auditor)
- tessl__langgraph (architect + builder + auditor)
- tessl__graceful-degradation (architect + builder)
- tessl__pytest-api-testing (builder)

## Cierre sprint

S2-shared-observability **CLOSED 2026-05-01**.
- Único PR shipped: PR-2-shared-agent-observability ✅
- Sprint hipótesis validadas (2/2)
- Bloqueadores cascading descubiertos documentados
- Decisión PI continuation pendiente Chris (Opción A/B/C arriba)
