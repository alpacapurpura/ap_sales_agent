# Prompt — Architect kickoff (PR-1 + PR-3 compartido)

> **Architect Opus 1 ejecución cubre PR-1 + PR-3** (decisión D5 PI-11). Acoplamiento técnico: singleton fixture design (PR-1) + arch fitness test que reflexiona sobre ese fixture (PR-3).
>
> **Prerequisito:** ejecutar `prompts/00-context-prep.md` para AMBOS PRs primero (Haiku produce CONTEXT-BRIEF.md cada uno). Architect lee los briefs — NO re-lee 30-50k de docs.

## Spawn pattern

```
Agent({
  description: "Architect PR-1 + PR-3 (PI-11 hardening)",
  subagent_type: "nicolify-architect",
  model: "opus",
  prompt: <BLOQUE FIJO + BLOQUE VARIABLE abajo>
})
```

## Prompt body

```
[BLOQUE FIJO — cacheable, byte-idéntico entre invocaciones]

Sos `nicolify-architect` (Opus 4.7[1M]). Trabajo: producir CONTRACT.md PR-1 + CONTRACT.md PR-3 cross-linked.

Step 0 OBLIGATORIO antes de cualquier acción:
  date -u +%Y-%m-%d   # captura today
  date -u +%Y         # captura {current_year} para WebSearch

NUNCA hardcodees fechas en CONTRACT. Usa fecha capturada Step 0 para citas + research notes.

Reglas duras:
- NO escribas código de implementación. Solo schemas + interfaces + decisiones arquitectónicas.
- CONTRACTs deben ser ÚNICOS consumidos en paralelo por builders distintos según surface.
- SQLA 2.0 async + Pydantic v2 + structlog. Migrations idempotentes.
- Si detectás gap funcional en PR.md → flag § Open questions for PM y NO inventes solución.

Surface ownership:
- modules/copilot/, modules/sales_agent/ → nicolify-agentic + nicolify-agentic-auditor
- modules/{brand,offer,landing,assets,analytics,advertising,social_media,scheduling,connections,iam,crm,core,shared}/ → nicolify-backend + nicolify-backend-auditor
- frontend/src/** → nicolify-frontend + nicolify-frontend-auditor
- .claude/rules/, tests/architecture/ → nicolify-backend (PR-3)

Skills domain a invocar antes de diseñar:
- backend-expert (toda surface backend)
- copilot-expert + sales-agent-expert + tessl__langgraph (para análisis singleton fixture cobertura agentic)
- tessl__pytest-api-testing (singleton fixture pattern)

State-of-the-art research (DATE-AWARE):
- WebFetch canonical URLs:
  · pytest fixture autouse: https://docs.pytest.org/en/stable/how-to/fixtures.html#autouse-fixtures-fixtures-you-don-t-have-to-request
  · pytest pytester / polluter detection: https://docs.pytest.org/en/stable/how-to/writing_plugins.html#testing-plugins
  · LangGraph state isolation: https://docs.langchain.com/oss/python/langgraph/persistence
- WebSearch: "pytest test pollution detection {current_year}", "langgraph compilation cache reset {current_year}", "deepagents global state isolation {current_year}"
- Cita en § Research Notes: URL + accessed {YYYY-MM-DD desde Step 0}

Output: 2 CONTRACTs (uno PR-1, uno PR-3) cross-linked.

Última línea de tu respuesta MUST ser:
<!-- @pm: CONTRACT.md PR-1 + CONTRACT.md PR-3 ready (cross-linked). Próximo paso: ejecutar PR-1/prompts/02-builder-start.md (business) + PR-1/prompts/02-builder-start-agentic.md (agentic) + PR-3/prompts/02-builder-start.md (en paralelo) -->

Reportar a Chris brief < 300 palabras: qué decidiste para singleton fixture exhaustivo, polluter hunt methodology, EventBus migration strategy, arch fitness test design, open questions si hay.

[BLOQUE VARIABLE — específico de esta invocación]

PR-1 folder: docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-1-fix-broken-tests-and-arch-snapshots
PR-3 folder: docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-3-anti-default-flip-enforcement
Surfaces: business + agentic + arch fitness (PR-3 only)

Lectura obligatoria (en orden):
1. PR-1/CONTEXT-BRIEF.md (Haiku Pre-flight)
2. PR-1/PR.md — scope completo expandido (XL)
3. PR-3/CONTEXT-BRIEF.md (Haiku Pre-flight)
4. PR-3/PR.md — scope rule + arch fitness
5. docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/PI.md — § Decisión arquitectónica clave (D1-D7)
6. backend/src/shared/domain_events/legacy_event_bus.py + outbox/application/event_bus_adapter.py
7. backend/tests/conftest.py (versión actual + stash extension scope)
8. backend/src/core/config.py — flags USE_OUTBOX_PATTERN_*
9. CLAUDE.md — project constraints
10. .claude/rules/anti-duplication.md (inventario shared abstractions)

Decisiones tomadas (PI-11 § Decisión):
D1: outbox `True` permanente (escala 1000 clientes multi-worker)
D2: tests migran a adapter_bus mock o outbox table probe (NO monkeypatch False)
D3: LegacyEventBus.publish runtime warning + deprecation gradual
D4: polluter hunt sin band-aid `@pytest.mark.flaky` final
D5: architect 1 ejecución PR-1 + PR-3 cross-linked
D6: PR-4 = PM directo
D7: stash apply en builder PR-1 Phase 1 Step 1

CONTRACT.md PR-1 debe incluir secciones:
- § 0 Context Summary (date, surface mapping, decisions consumed D1-D7)
- § 1 Singleton inventory (lista exhaustiva esperada de class-level singletons via grep `_instance =`; builder valida + extiende; lista mínima: LLMFactory, ChatOrchestrator, SemanticRouter)
- § 2 Singleton fixture design (autouse pre-test + post-test reset, comments per-singleton, cleanup hooks)
- § 3 EventBus migration strategy (probe adapter_bus vs query outbox table — cuándo cada uno)
- § 4 Snapshot helpers outbox-aware design (`_chat_flow_snapshot_helpers.py` API)
- § 5 LegacyEventBus deprecation runtime warning impl pattern
- § 6 Polluter hunt methodology (bisección orden + JSON diff + sospechosos primarios)
- § 7 litellm.py kimi clamp design (REVISAR stash fix; mirror clamp adapter legacy)
- § 8 Tests EventBus mock migration list (lista TODOS tests que mockean path legacy + estrategia migration cada uno)
- § 9 Stash apply checklist (16 archivos del stash + REVISAR cada vs scope nuevo D2)
- § 10 Open questions for PM
- § 11 Surface mapping (business vs agentic file ownership exclusivo)
- § 12 Research Notes
- § 13 Cross-link to PR-3 CONTRACT (referencias arch fitness test design)

CONTRACT.md PR-3 debe incluir secciones:
- § 0 Context Summary (date, dependencies on PR-1 design — singleton fixture + EventBus migration)
- § 1 Rule design `.claude/rules/anti-default-flip-audit.md` (workflow obligatorio + ejemplos + anti-patterns)
- § 2 Arch fitness test design `tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py`:
  · Detection logic (ast walk para mock targets `EventBus.publish`, `LegacyEventBus.publish`)
  · Bypass list (tests internos LegacyEventBus capability)
  · Failure message diagnostic
  · Performance budget (no slow O(n²))
- § 3 Integration con regla anti-duplication.md (referencia cross)
- § 4 Cross-link to PR-1 CONTRACT
- § 5 Open questions for PM
- § 6 Research Notes

Output:
- {pr-1_folder}/CONTRACT.md
- {pr-3_folder}/CONTRACT.md
```

## Cómo usar

1. Reemplazar `{current_year}` (Step 0 lo captura).
2. Spawn vía Agent tool con `model: "opus"`.
3. Architect produce ambos CONTRACTs en una respuesta.
4. PM revisa briefs + cross-links + decide si CONTRACTs ready o re-spawn.
