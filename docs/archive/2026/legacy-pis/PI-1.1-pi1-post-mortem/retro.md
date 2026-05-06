# PI-1.1-pi1-post-mortem — Retro

> Owner: PM. Cierre 2026-05-01. PI mini dedicado a hotfixes post-PI-1.

## Meta

| Campo | Valor |
|---|---|
| PI ID | PI-1.1-pi1-post-mortem |
| Inicio | 2026-04-30 |
| Cierre | 2026-05-01 (1 día execution Opus 4.7[1M]) |
| Sprints completados | S1-stabilization + S2-shared-observability (2 sprints) |
| PRs shipped | 2 (PR-1-pi1-bugs-hotfix scope-reducido + PR-2-shared-agent-observability) |
| Estado | DONE → archive |

## Origen

Manual gate Chris staging PI-1 ejecutado retroactivamente 2026-04-30 vía chrome-devtools MCP. PI-1 había sido archivado prematuramente sin gate. 4 bugs encontrados (#1+#2+#4+#6) + 3 cascade runtime descubiertos durante testing (#7+#8+#9).

## Outcome alcanzado vs hipótesis

### H1 — Bugs PI-1 son fixables sin reabrir PI completo
✅ **VALIDADA**. Mini-PI dedicado funcionó. Scope contenido a hotfixes específicos.

### H2 — Anti-duplication 5-layer enforcement previene mirror duplication recurrence
✅ **VALIDADA STRONGLY**. Test real en PR-2: architect Step 0 GATE catched PR.md outdated info ("FXResolver lines 116, 168" → real es 1 sitio único factory.py:78). Sin Step 0 GATE el error hubiera propagado al builder.

### H3 — Shared base + concrete subclass es estructura right-sized para growth (commercial_director PI-6, ManyChat WA, IG DM)
✅ **VALIDADA**. SalesAgentObservabilityContext = ~80 LOC. Future agente puede heredar mismo pattern <50 LOC.

### H4 — Sales agent observability emerge desbloquea visibilidad cascade bugs
✅ **VALIDADA**. PR-2 shipped → Bug #7 (brand adapter) + Bug #9 (LiteLLM) descubiertos durante smoke. Pre-PR-2 invisibles porque sin observability no había visibilidad ningún error.

## Bugs status final

| # | Severidad | Status |
|---|---|---|
| #1 slash CRM `/sales/contactos` 404 | CRÍTICO | ✅ FIXED PR-1 (FE+BE dual decorator) verified curl 401 |
| #2 sales_agent traces 0 globally | CRÍTICO | ✅ FIXED PR-2 verified Telegram smoke (+4 trace +2 llm_call) |
| #3 streamlit user_id confusion | NO BUG | descartado (UX clarity defer PI-3) |
| #4 ñ folder + sidebar orfana | CRÍTICO | ✅ FIXED PR-1 (FE rename + sidebar entry) |
| #5 max update depth FE | medio | NOT REPRODUCED — defer hasta repro window |
| #6 tenant switch non-persist Clerk | medio UX | RCA documented PR-1 RESULT — PR dedicado FE Clerk pendiente |
| #7 PersonalityProfileModel.model_dump | CRÍTICO | DISCOVERED runtime smoke PR-2 — bloquea sales_agent — PI-7 cascade-bugs-fix scope |
| #8 FXResolver no-arg crash | CRÍTICO | ✅ FIXED PR-2 (factory.py:78 FXResolver.default + arch ratchet enforced) |
| #9 LiteLLM container exited mount config | CRÍTICO | DISCOVERED runtime smoke PR-2 — bloquea TODOS LLM calls — PI-7 cascade-bugs-fix scope |

## Métricas

| Métrica | Target | Real |
|---|---|---|
| Bugs PI-1 originales fixed | #1+#2+#4 | ✅ 3/3 |
| Bugs cascading descubiertos documentados con owner | todos | ✅ 4/4 (#5+#6+#7+#9 con paths + severidad) |
| 5-layer anti-duplication primer test | PASS | ✅ PASSED en PR-2 |
| Real DB persistence test sales_agent | ≥1 row | ✅ 4 trace +2 llm_call smoke verified |
| Cero refactor cross-module pollution durante hotfix | 0 archivos copilot ajenos tocados | ✅ M8 verified |
| Cross-session collision PI-5 PR-2 | resolved sin conflict | ✅ hunks distintos (commit `d09799b9` vs `d80d15f5`) |

## Surface entregada

### PR-1-pi1-bugs-hotfix (S1-stabilization)
- FE Bug #1 trailing slash fix `use-contacts-query.ts:26`
- FE Bug #4 folder rename `campañas` → `campanas` + sidebar entry "Campañas"
- BE Bug #1 dual decorator `crm/api/contacts.py` (`""` + `"/"`) matching brand pattern — root cause real CF tunnel strip
- 6 BE módulos legacy con same anti-pattern documented as follow-up

### PR-2-shared-agent-observability (S2-shared-observability)
- `shared/agent_observability/recording/turn_envelope.py::BaseObservabilityContext` (NEW Template Method ABC)
- `shared/agent_observability/cost/fx_resolver.py::FXResolver.default()` (EXTEND classmethod)
- `copilot/observability/recording/turn_envelope.py` REFACTOR in-place (subclass + back-compat alias)
- `sales_agent/observability/recording/turn_envelope.py::SalesAgentObservabilityContext` (NEW subclass)
- Bug #2 wire `observe_turn` lifecycle en sales_agent orchestrator chat + outbound + pipeline
- Bug #8 fix factory.py:78 `FXResolver()` → `FXResolver.default()`
- 6 tests (base contract + FX factory + copilot regression + sales subclass + real DB persistence + arch ratchet)

### Process artifacts (commits separados)
- `.claude/rules/anti-duplication.md` (NEW universal rule #12)
- CLAUDE.md rule #12 entry
- PR.md template "Existing systems audit" MANDATORY block grep evidence
- prompts/02-builder-start.md template Step 0 GATE
- 3 auditor agents Cat 12/13 mirror detection
- skills copilot-expert + sales-agent-expert §0 anti-dup section

## Decisiones clave PI-1.1

10 decisiones documentadas (D-1 a D-10):
- D-1 PI-1 cerrado prematuramente sin manual gate
- D-2 Bug #2 deferred a PR-2 architect-driven post mirror duplication revert
- D-3 5-layer anti-duplication enforcement cementado universal
- D-4 Cross-session coordination handshake PI-5 PR-2 (regla M8 ratificada)
- D-5 FXResolver.default() classmethod elegida sobre helper module-level
- D-6 BaseObservabilityContext abstract base sobre Composition
- D-7 Anchor registry transient edit auto-cleanup
- D-8 5-layer enforcement primer test PASSED
- D-9 Bug #2 fix verified Telegram smoke real
- D-10 Bot error técnico durante smoke por Bug #7+#9 cascade — out-of-scope PR-2

## Lecciones globales (cementadas en process-learnings.md)

**L-PROC-DUPLICATION-PM-PROCESS** — 5 fallos PM cardinal cuando builder duplica:
1. PM marca "Existing systems audit" sin grep real
2. PM skipea architect por "scope hotfix"
3. Builder prompt sin Step 0 grep gate obligatorio
4. Auditor ve precedent existing pero misclasifica como "Strangler Fig"
5. PM no valida "¿es nueva infra o extensión?" en Walking Skeleton

Solución: 5-layer redundant enforcement (rule + template + builder gate + auditor cat + skills warning).

## Anti-pattern personal PM auto-flag

Cuando me siento "esto es solo un hotfix" → primer red flag. Hotfix no exime audit. Especialmente cuando observability/cost/pricing/llm-routing son scope. Skip architect en esos = repetir error.

## Pendientes deferred (handoff a PI-7-app-stability-restore)

PI-7 abre con scope claro:
- Bug #7 brand adapter PersonalityProfileModel.model_dump → bloquea sales_agent identity
- Bug #9 LiteLLM container exited mount conflict → bloquea todos LLM calls

Otros:
- Bug #5 max update depth FE → defer hasta repro
- Bug #6 Clerk tenant switch persist → PR dedicado FE Clerk session (no es PI-7 scope)

## Cierre

PI-1.1 closed 2026-05-01 con misión cumplida. Bugs PI-1 originales fixed. Process anti-duplication enforcement cementado. Cascade bugs descubiertos handoff a PI-7.

Move folder a `pis/archive/PI-1.1-pi1-post-mortem/`.
