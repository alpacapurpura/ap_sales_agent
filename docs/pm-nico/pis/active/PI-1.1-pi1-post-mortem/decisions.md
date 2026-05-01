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
