# PI-1.1-pi1-post-mortem — Decisions log

> Append-only. Each decision = D-N entry with date + rationale + scope.

## D-1 (2026-05-01) — PI-1 cerrado prematuramente sin manual gate

PI-1 archivado 2026-04-30 sin Chris ejecutar staging manual gate. Manual gate ejecutado retroactivamente vía chrome-devtools MCP encontró 4 bugs (#1+#2+#4+#6) + 3 cascade runtime (#7+#8+#9). PI-1.1 mini-PI dedicado abierto para hotfixes + post-mortem.

**Aplica:** Manual gate Chris staging es REAL ship verdict, no formality. PI no se archivar antes de gate.

## D-2 (2026-05-01) — Bug #2 sales_agent observability deferred a PR-2 architect-driven

PR-1 hotfix abrió Bug #2 con builder agentic spawn directo. Builder creó mirror `turn_envelope.py` duplicando copilot existente. Chris flagged anti-pattern. REVERT commit 73ae51d2.

**Decisión:** Bug #2 reabre en PR-2-shared-agent-observability con architect Opus mandatory + 5-layer anti-duplication enforcement + lift-to-shared pattern.

**Aplica:** observability/cost/pricing/channel-format viven en `shared/agent_observability/`. Subsistemas cross-agent NUNCA mirror per-module.

## D-3 (2026-05-01) — 5-layer anti-duplication enforcement cementado

Process audit identificó 5 fallos PM cardinal cuando builder agentic duplicó turn_envelope. Cementing redundant enforcement layers:

1. PM PR.md template — "Existing systems audit" mandatory bloque grep evidence (paths + line numbers)
2. Builder Step 0 GATE — grep cross-codebase ANTES de Write nuevo file
3. Auditor Cat 12/13 — mirror detection scan (FAIL severity)
4. Architect mandatory cuando PR toca `shared/` o `*/observability/` o crea archivo donde pattern paralelo existe
5. Skills `copilot-expert` + `sales-agent-expert` warning + cross-link a `rules/anti-duplication.md` inventory

**Aplica:** universal #12 CLAUDE.md. Todo PR future testea contra estos 5 layers.

## D-4 (2026-05-01) — Cross-session coordination handshake PI-5 PR-2 cementada

Chris-mediated handshake con sesión PI-5 PR-2 (también modifica copilot/):
- Otra sesión informada que PR-2-shared-agent-observability tocará copilot observability
- Filosofía Chris ratificada: "mismo código sin temor, si tocan mismo archivo OK siempre que funciones distintas" (regla M8 cementada)
- WIP cross-session leíble bilateralmente vía PR-folders SSoT
- NO branch, NO pull, NO ambiente change
- Si commit propio rompe commit ajeno → STOP escalate Chris

**Aplica:** Sprint S2-shared-observability proceeds sin bloquearse por coordination overhead. Architect Step 0.4 sigue verificando overlap pero como info, no bloqueo.

## D-5 (2026-05-01) — `FXResolver.default()` factory classmethod elegida sobre helper

Bug #8 fix en PR-2 scope. 3 opciones consideradas:
- A) `FXResolver.default()` classmethod (1-line callers, test override directo) — **elegida**
- B) Module-level helper `build_fx_resolver()` — descartada (duplica per-consumer)
- C) Factory function en `shared/factories.py` — descartada (over-engineering 1 obj)

**Aplica:** Pattern para futuros default factory shared abstractions. Encapsula boilerplate `lambda: httpx.Client(timeout=10)` un solo lugar.

## D-6 (2026-05-01) — `BaseObservabilityContext` abstract base sobre Composition

3 patrones arquitectónicos considerados para shared observability:
- A) Abstract base class + 2 concrete subclasses copilot+sales_agent (herencia simple) — **elegida**
- B) Mirror per-module (estado pre-revert) — descartada (drift garantizado)
- C) Composition (delegate al shared) — descartada (over-engineering, herencia simple basta)

**Aplica:** Pattern para futuros agentes shared (commercial_director PI-6, ManyChat WA, IG DM, etc.). Subclass new agent <50 LOC.

## D-7 (2026-05-01) — Anchor registry edit deferred (auto-cleanup post-revert)

`backend/tests/architecture/test_sales_agent_anchors.py` recibió edit transient agregando `SALES-AGENT-TURN-RUNNER-PR1-HOTFIX` anchor. Tras revert WIP, anchor no aplica. Edit se revirtió `git checkout --`.

**Aplica:** anchor registry maintenance happens at builder commit boundary, no en transit.

## D-8 (2026-05-01) — 5-layer anti-duplication enforcement primer test PASSED en PR-2

PR-2-shared-agent-observability fue primer PR del nuevo proceso (commits `b0700be9` + `3e84bb93`). Resultado:

- Layer 1 (PR.md mandatory grep evidence) **catched PR.md outdated info**: PR.md decía "FXResolver() at lines 116, 168" — architect Opus ejecutando Step 0 grep CORRIGIÓ a "factory.py:78" (1 sitio único)
- Layer 2 (builder Step 0 GATE) — IMPL-LOG-agentic § "Step 0 grep findings" sección obligatoria documentada
- Layer 3 (auditor Cat 13 mirror detection) — REVIEW-agentic verdict PASS confirmó class distinct + 3 overrides + 2 fields = NOT byte-mirror per anti-duplication semantics
- Layer 4 (architect mandatory) — CONTRACT.md producido por architect Opus ANTES builder (747 lines, 9 secciones)
- Layer 5 (skills warning) — todos 5 mandatory invocados (copilot-expert + sales-agent-expert + tessl__langgraph + tessl__graceful-degradation + tessl__pytest-api-testing)

**Aplica:** proceso anti-duplicación funciona end-to-end. Sin Step 0 GATE, error PR.md hubiera propagado al builder. Layer 1 trabajó como diseñado.

## D-9 (2026-05-01) — Bug #2 fix verificado smoke real Telegram Chris-mediated

2026-05-01 14:15 UTC — Chris mandó "holaaaa" al `visionarias_bot` Telegram:

| Tabla | Pre | Post | Delta |
|---|---|---|---|
| `sales_agent_trace_event` | 0 | 4 | +4 ✅ |
| `sales_agent_llm_call` | 0 | 2 | +2 ✅ |
| `sales_agent_routing_log` | 0 | 0 | 0 (no routing decisions este turn — normal) |
| `messages` visionarias | 69 | 70 | +1 ✅ |

4 trace events: turn_start ok + 2 llm_call error + turn_end error. Lifecycle envelope funciona correctamente, captura turn_start ANTES del fallo LLM + cost tracking incluso en errors.

**Aplica:** Bug #2 (sales_agent traces 0 globalmente) FIX VERIFIED end-to-end. Sales agent observability LIVE.

## D-10 (2026-05-01) — Bot respondió error técnico durante smoke por Bug #7+#9 (out-of-scope PR-2)

Bot respondió "Lo siento, ocurrió un error técnico interno" en lugar de mensaje normal porque:

- **Bug #7** `PersonalityProfileModel.model_dump` brand_data_adapter.py:46 SQLA ORM treated as Pydantic → knowledge_builder.build_identity falla → agent_identity inválida
- **Bug #9** LiteLLM container exited (mount config.yaml dir/file conflict) → `visionarias_litellm:4000` DNS unreachable → APIConnectionError todos LLM calls

Estos 2 bugs son scope SEPARADO PR-2 — fueron descubiertos durante smoke runtime cuando el observability stack DESBLOQUEÓ visibilidad de los stack faltantes.

**Aplica:** Bug #2 fix demonstrated correct INCLUSO bajo error LLM downstream — best-effort observability captura errors (4 trace rows incluyendo turn_end status='error'). Esos 2 bugs siguen pendientes en PRs separados:
- Bug #7 → backend negocio brand module — abrir PR dedicado
- Bug #9 → infra LiteLLM container restart + mount fix — abrir PR dedicado infra
