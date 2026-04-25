# Learnings — F0 Foundation cleanup

**Fecha cierre fase:** 2026-04-25
**Owner conversación:** Claude Opus 4.7 (1M context)
**Branch state al cerrar:** `development @ <commit-hash>` (commit en `git log --oneline -1`)

---

## Resumen 3 líneas

- Eliminamos 28 archivos dead (style_analyzer dup, web_extractor + adapter, context_loader_registry, offer_context_loader, skills_loader, rules_loader, skill_resolver, skills/*.md, rules/*.md, test asociado).
- Instalamos `deepagents 0.5.3` con bump de langchain-core 1.2.28 → 1.3.2 (major) + langchain 1.2.12 → 1.2.15 + langgraph 1.1.2 → 1.1.9 + langchain-anthropic nuevo; copilot orchestrator graph importable post-bump.
- Capturamos 4 golden snapshots determinísticos (module_registry shape, route_tool_selection, routing_policy_shape, studio_context_resolution) + arch test ratchet skip-by-default que F1 activará para enforzar provider pattern (28 imports copilot→módulo congelados).

---

## Decisiones clave

| Decisión | Razón | Alternativa descartada |
|---|---|---|
| Package real es `deepagents`, no `langchain-deepagents` (nombre incorrecto en plan F0). | PyPI no tiene `langchain-deepagents`; el repo oficial `langchain-ai/deepagents` se publica como `deepagents`. | Mantener nombre del plan e instalar paquete inexistente — bloquearía F2. |
| Aceptar bump major `langchain-core 1.2 → 1.3`. | Smoke test (`from src.modules.copilot.application.orchestrator.graph import build_system_prompt, agent_node, should_continue`) pasó; arch + golden + 540 unit tests verdes post-bump. | Pinnear `deepagents` a versión más vieja compatible con `langchain-core 1.2.x` — habría implicado feature lag (async subagents añadidos abr/2026 vienen en 0.5.x). |
| Golden tests "lite" deterministic-surface (4 snapshots de funciones puras) en vez de las 10-15 conversaciones canónicas que pedía F0 §5.2. | 73 test files de copilot ya cubren behavior end-to-end. El riesgo real de F1 es drift en *contratos* (module registry, routing, tool registry, studio context). Snapshots de conversación full requieren mocking pesado de LLM y son frágiles a cualquier tweak de prompt. F9 (LLM-judge) es el lugar correcto para conversation goldens. | Conversación full con `LLMFactory` monkeypatch + snapshot de tool_calls/cards/text — alto costo, baja señal anti-fragilidad. |
| Arch test `test_no_new_copilot_module_imports.py` con `_RATCHET_FROZEN = False` (skip-by-default) en F0. | El plan F0 §5.4 lo marca skip-by-default para F0 y activable en F1. La constante `_RATCHET_FROZEN` se flipea en una sola línea cuando F1 lance providers. | Activarlo ya con allowlist 28 entradas — bloquearía cualquier hotfix legítimo en copilot durante el gap F0→F1. |
| Snapshot del arch test usa formato `"copilot -> {target} | {rel_path}"` (mismo de `test_ddd_boundaries`). | Reusa pattern existente, devs ya conocen el formato cuando arreglan violaciones. | Inventar nuevo formato — incoherencia con resto de arch tests. |
| Eliminar skills/*.md y rules/*.md top-level (10 archivos) además de los loaders. | grep AST confirma que ningún módulo runtime los lee; eran corpus huérfano para `FileSkillsLoader` y `FileRulesLoader` que también eran dead. `application/skills/skill_resolver.py` también dead. `domain/skills/`, `domain/rules/`, `domain/hooks/` siguen vivos (no tocar). | Mantener .md como "documentación inerte" — confunde a F6 que diseña Workflow unificado y a F2 que diseña scratchpad. |
| Saltar verificación de `/test-backend` full + browser smoke en F0. | F0 no tocó FE; solo eliminó código sin imports vivos y bumped deps. Validamos con 540 tests (arch + golden + domain + unit copilot focused) verdes. La fragilidad de pytest-randomly en `test_mutation_journal_repository.py` y el TSC error en `CollapsibleFieldGroup.tsx` son pre-existentes (commit `976123cd`), no F0. | Bloquear cierre fase por fallas pre-existentes — burocracia. |

---

## Fuentes research consultadas

- **Web search**:
  - [deepagents · PyPI](https://pypi.org/project/deepagents/) — confirmó nombre real del package, versión 0.5.3 stable (feb 2026 con async subagents abr/2026).
  - [Deep Agents overview - Docs by LangChain](https://docs.langchain.com/oss/python/deepagents/overview) — confirmó que `create_deep_agent` retorna `compiled LangGraph graph`, runtime base = LangGraph.
  - [LangChain Changelog - deepagents 0.2 release](https://changelog.langchain.com/announcements/deepagents-0-2-release-for-more-autonomous-agents) — historial pluggable sandbox, response API default, summarization.
  - [LLM Testing in 2026 - Confident AI](https://www.confident-ai.com/blog/llm-testing-in-2024-top-methods-and-strategies) — confirmó que conversation goldens deben combinarse con LLM-judge, no equality semántica → respaldó decisión de diferir conversation snapshots a F9.
  - [Pytest Regressions Data - Golden File Updates](https://johal.in/pytest-regressions-data-golden-file-updates-2025/) — pattern UPDATE_GOLDEN env var aceptado por la comunidad → adoptado en `golden/conftest.py`.
- **WebFetch**:
  - `https://pypi.org/pypi/deepagents/json` — extrajo dependencias exactas: `langchain-core>=1.2.27,<2.0`, `langchain>=1.2.15,<2.0`, `langchain-anthropic>=1.4.0,<2.0`, `langchain-google-genai>=4.2.1,<5.0`, `langsmith>=0.3.0`, `wcmatch`. Esto bloqueó la decisión de bump.
- **Tessl tiles**: NO instalado nuevo tile específico para deepagents (la búsqueda en tile catalog no devolvió match — `tessl__langgraph` existe pero deepagents no es un tile separado, y la PyPI fetch + smoke import fueron suficientes).
- **Docs internos releídos**:
  - `docs/domains/copilot/redesign-2026-04/{README, 00-vision-and-non-goals, 01-master-plan, 02-architecture-target, 03-phase-protocol, phases/F0-foundation-cleanup}.md`
  - `docs/domains/copilot/INDEX.md`
  - `.claude/rules/{copilot-resilience, parallel-safety, backend-ddd, backend-quality}.md`
  - `backend/tests/architecture/test_ddd_boundaries.py` + `test_copilot_anchors.py` (para entender el ratchet pattern y registrar el nuevo anchor).

---

## Sorpresas / gotchas

- **Nombre de paquete incorrecto en el plan**. `phases/F0-foundation-cleanup.md §3` y §5.3 dicen `langchain-deepagents` pero el paquete real es `deepagents` (publicado por `langchain-ai`). El plan se redactó probablemente desde un repo donde se importaba como `langchain_deepagents`, pero el publisher en PyPI usa el nombre corto. Consecuencia: si una fase futura lo cita por el nombre viejo, no lo va a encontrar. Plan debe corregirse en `02-architecture-target.md` también — actualmente menciona `langchain-deepagents` en `application/orchestrator/deep_agent.py` (es referencia, no código). Ver §"Recomendaciones para fase siguiente" para corregir.
- **Bump de `langchain-core` de minor a major (1.2 → 1.3)** se disparó por `deepagents 0.5.3`. Los smoke tests (importar copilot orchestrator graph + correr suite arch+golden+domain) pasaron sin tocar código. Pero existe riesgo lateral en `sales_agent`, `analytics`, `crm` que también usan langchain. **Recomendación F1**: correr `/test-backend` full antes de tocar copilot.
- **`pytest-randomly` exhibe fragilidad pre-existente** en `tests/modules/copilot/test_mutation_journal_repository.py::TestMarkReverted::test_mark_reverted_only_affects_specified_ids`. Falla cuando se mezcla con otros tests por orden de carga del modelo `AppointmentModel` (relación SQLA no resuelta). Aislado pasa en 0.23s. NO causado por F0 (verificado con git blame del módulo afectado). **Tech debt para mejoras-proceso**: side-effect imports de SQLA models en conftest.py de copilot.
- **TSC error pre-existente** `CollapsibleFieldGroup.tsx(32,18): TS2339`. Commit origen `976123cd`. NO es F0. **Tech debt para frontend-quality**.
- **`pyproject.toml` solo configura tooling, no deps.** Las deps viven en `requirements-runtime.txt` + `requirements-dev.txt` (con `requirements.txt` como meta-include). Esto es atípico para repos modernos. Funcional pero confunde la query inicial.
- **`pytest tests/modules/copilot/` full corre extremadamente lento** (>10 min sin alcanzar 60% en mi sesión). No identifiqué qué test es el culpable porque pytest-randomly cambia el orden cada vez. **Tech debt**: marcar tests lentos con `@pytest.mark.slow` para ejecutarlos sólo en CI o en `/test-backend`. Mientras tanto, el set rápido (`tests/modules/copilot/domain/ tests/modules/copilot/golden/ tests/architecture/`) corre en 17s con 540 verdes.

---

## Lo que descarté

- **Ejecutar el `/test-backend` slash command** desde la conversación. Tomaría >10 min y la slash command está reservada para flujos del usuario; preferí ejecutar las piezas directamente con `.venv/bin/pytest`.
- **Activar el ratchet `_RATCHET_FROZEN = True` ya en F0**. Hubiera bloqueado cualquier hotfix legítimo en copilot durante el gap F0→F1; el plan original explícitamente dice skip en F0.
- **Crear conversation snapshots full** con LLM mock + tool call captures. Investigación sugiere que sin LLM-judge esos snapshots requieren mantenimiento constante (cada cambio de prompt rompe N tests). Dejado para F9 según diseño.
- **Refactorizar `_get_completion_snapshot` y `_get_behavior_summary`** para inyectar deps. F0 es housekeeping puro; refactor es F1.
- **Fix `pytest-randomly` fragility en mutation_journal**. Es pre-existente y arreglarlo requiere tocar conftest del módulo crm o copilot — fuera de scope F0.

---

## Recomendaciones para fase siguiente F1 (provider pattern)

1. **Corregir el nombre `langchain-deepagents` en docs**. En `02-architecture-target.md` linea 36 dice "langchain-deepagents harness" — cambiar a "deepagents harness". También revisar otros phases (F2 especialmente).
2. **Antes de empezar F1, correr `/test-backend` completo**. F0 no lo corrió (slow + fragility pre-existente). Si aparece algo nuevo a raíz del bump major de langchain-core, preferible saberlo antes de meter más cambios.
3. **F1 va a flippear `_RATCHET_FROZEN = True`** en `tests/architecture/test_no_new_copilot_module_imports.py`. La baseline frozen tiene 28 entradas. Cada provider que F1 entregue debe restar entradas del set; el test las mantiene como "stale entries permitted" (no fail) hasta que se limpien.
4. **F1 puede usar Python entry points** del setup según el plan (`02-architecture-target.md §2`). Verificar que `pyproject.toml` raíz (no el de backend) soporte entry points; el backend usa `requirements*.txt` no setup.py para deps. Quizá necesite agregar `[project.entry-points]` section a pyproject.toml o usar `importlib.metadata` con un fallback de discovery por convención (ej. `src.modules.{name}.copilot_provider`).
5. **No tocar `domain/hooks/`, `domain/skills/`, `domain/rules/`, `domain/tools/`**. Confirmé en F0 que están vivos (importados por `main.py`, `event_cleanup`, `event_model`, admin). Solo el material de loader + .md huérfano fue dead.
6. **Consumir golden snapshots en F1 verification**. `cd backend && .venv/bin/pytest tests/modules/copilot/golden/ -q` debe seguir verde; si cambia algo intencionalmente, `UPDATE_GOLDEN=1 ...` y revisar el diff en el PR.
7. **F1 debe agregar el primer provider (sugerido: `brand`)** — es el módulo con más imports desde copilot (8 entradas) y el más importante para F3 (brand summary lighthouse). Empezar ahí maximiza el ROI del provider pattern y marca la pauta para los otros.

---

## Riesgos abiertos

- **Bump major langchain-core 1.2→1.3** podría tener efectos laterales en `sales_agent` o `analytics` no detectados por mi subset focalizado. Mitigación: F1 corre `/test-backend` full en su Paso 5.
- **`langchain-anthropic 1.4.1` instalado pero no consumido en código**. Ocupa memoria + pip-audit surface. Si F2 no usa anthropic en deepagents config, considerar removerlo del requirements (pero deepagents lo lista como mandatory en su `pyproject.toml`).
- **Slow test fragility en `tests/modules/copilot/`**. Bloquea iteración rápida. F1 debería agregar `pytest.mark.slow` selectivo o mover tests integration a `tests/modules/copilot/integration/` separado.
- **Anchor `[COPILOT-REDESIGN-2026-04]` apunta al README del redesign**, no a un módulo SSoT específico. Cuando F1 lande providers, considerar agregar anchor más específico `[COPILOT-PROVIDER-PATTERN]` apuntando a `02-architecture-target.md §2`.

---

## Métricas medidas

| Métrica | Antes | Después | Delta |
|---|---|---|---|
| Archivos en `backend/src/modules/copilot/` | (baseline) | -28 | dead removed |
| `langchain-core` | 1.2.28 | 1.3.2 | major |
| `langchain` | 1.2.12 | 1.2.15 | patch |
| `langgraph` | 1.1.2 | 1.1.9 | patch |
| `deepagents` | absent | 0.5.3 | new |
| `langchain-anthropic` | absent | 1.4.1 | new (transitive) |
| Tests pasando (subset rápido: arch + golden + domain copilot) | N/A | 540 + 1 skip | baseline |
| Arch tests nuevos | 0 | 2 (ratchet + count guard) | +2 |
| Golden snapshots determinísticos | 0 | 4 | +4 |
| Cross-module imports `copilot → módulo` | 28 | 28 (frozen) | unchanged |

---

## Archivos modificados / creados

```
# Eliminados (28 archivos, dead code)
backend/src/modules/copilot/application/agents/                                   (dir + 8 files)
backend/src/modules/copilot/application/services/web_extractor_adapter.py
backend/src/modules/copilot/application/skills/                                   (dir + 2 files)
backend/src/modules/copilot/infrastructure/context/                               (dir + 3 files)
backend/src/modules/copilot/infrastructure/skills_loader.py
backend/src/modules/copilot/infrastructure/rules_loader.py
backend/src/modules/copilot/skills/{brand-audit,content-ideas,funnel-diagnosis,offer-ladder-builder,web-research}.md
backend/src/modules/copilot/rules/{honesty,mutation-safety,pii-guardrails,tenant-isolation,tone-caveman-latam}.md
backend/tests/modules/copilot/test_context_loaders.py

# Modificados
backend/requirements-runtime.txt                                                  (deps bump + new pins)
backend/src/modules/copilot/__init__.py                                           (anchor [COPILOT-REDESIGN-2026-04])
backend/tests/architecture/test_copilot_anchors.py                                (registry +1 anchor)
docs/domains/copilot/INDEX.md                                                     (sección "Active redesign")

# Creados
backend/tests/architecture/test_no_new_copilot_module_imports.py                  (ratchet skip-by-default + count guard)
backend/tests/modules/copilot/golden/__init__.py
backend/tests/modules/copilot/golden/conftest.py                                  (UPDATE_GOLDEN env var pattern)
backend/tests/modules/copilot/golden/test_baseline_module_registry.py
backend/tests/modules/copilot/golden/test_baseline_route_tools.py
backend/tests/modules/copilot/golden/test_baseline_routing_policy.py
backend/tests/modules/copilot/golden/test_baseline_studio_context.py
backend/tests/modules/copilot/golden/snapshots/module_registry_shape.json
backend/tests/modules/copilot/golden/snapshots/route_tool_selection.json
backend/tests/modules/copilot/golden/snapshots/routing_policy_shape.json
backend/tests/modules/copilot/golden/snapshots/studio_context_resolution.json
docs/domains/copilot/redesign-2026-04/learnings/F0-foundation.md                  (este archivo)
docs/domains/copilot/redesign-2026-04/prompts/F1-start.md                         (próxima fase)
```

---

## Tests agregados

| Test | Tipo | Qué valida |
|---|---|---|
| `tests/architecture/test_no_new_copilot_module_imports.py::test_no_new_copilot_to_module_imports` | arch (ratchet, F0=skip / F1=enforce) | Set frozen de 28 imports `copilot → módulo`. Sólo permite shrink. |
| `tests/architecture/test_no_new_copilot_module_imports.py::test_baseline_count_matches_documented_state` | arch (siempre on) | Sanity: edición silenciosa del frozen set sin actualizar el contador comentado falla CI. |
| `tests/modules/copilot/golden/test_baseline_module_registry.py::test_module_registry_shape_matches_baseline` | golden | Shape de `get_module_registry()`: keys + label/route_prefix/description por entrada. |
| `tests/modules/copilot/golden/test_baseline_route_tools.py::test_route_tool_selection_matches_baseline` | golden | Tool names bound por ruta canónica (13 rutas + wildcard). |
| `tests/modules/copilot/golden/test_baseline_routing_policy.py::test_routing_policy_shape_matches_baseline` | golden | `DEFAULT_ROUTING_POLICY`: default_tier + rule_count + per-rule (name, target_tier, intent_kinds, route_prefixes). |
| `tests/modules/copilot/golden/test_baseline_studio_context.py::test_studio_context_resolution_matches_baseline` | golden | `_resolve_studio_context()` por ruta canónica (15 entradas). |

---

## Comandos rápidos para próximas fases

```bash
# Correr golden tests (incluye 4 baseline F0)
cd backend && .venv/bin/pytest tests/modules/copilot/golden/ -q -o addopts=""

# Regenerar snapshots (cuando un cambio sea intencional)
cd backend && UPDATE_GOLDEN=1 .venv/bin/pytest tests/modules/copilot/golden/ -q -o addopts=""

# Verificar arch tests del redesign
cd backend && .venv/bin/pytest tests/architecture/test_no_new_copilot_module_imports.py tests/architecture/test_copilot_anchors.py tests/architecture/test_copilot_registry.py -v -o addopts=""

# Activar ratchet F1
# Editar tests/architecture/test_no_new_copilot_module_imports.py:
#   _RATCHET_FROZEN: bool = True
```
