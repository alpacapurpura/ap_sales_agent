# Learnings — F1 Provider pattern + discovery

**Fecha cierre:** 2026-04-25 · **Modelo:** Claude Opus 4.7 (1M context) · **Branch:** `development @ <commit>` (ver último `git log -1`)

---

## Resumen 3 líneas

- Discovery basado en convención (`src.modules.{name}.copilot_provider:provider`) + entry points externos como SoT del registry; legacy `_legacy_build_registry()` y flag `COPILOT_DISCOVERY_V2` retirados — discovery es la única fuente.
- Brand migrado deep (`brand/copilot_provider/{__init__,provider,module_data,tools,workflows,summary,context_inject}.py`); 9 módulos restantes con shim provider mínimo basado en `BaseCopilotProvider`; ratchet `copilot → módulo` shrunk de 28 a **22** y frozen.
- Aggregator de tool groups (`_build_tool_groups`) ya merge providers + transversales — F2/F3 publican brand_section/brand_voice via `BrandToolProvider.tool_groups()` sin tocar `copilot/tools/registry.py`.

---

## Decisiones clave

| Decisión | Razón | Alternativa descartada |
|---|---|---|
| **Brand pilot, no offer.** | F0 rec #7 explícita: brand tiene 8 imports (top), unblocks F3, módulo de mayor reuso. | Plan F1 §5.3 decía offer (19 tools); ROI de migrar 19 tools idénticos sin refactor real era bajo y no destrababa nada. |
| **Filesystem scan, no `pkgutil`.** | `assets/connections/iam/sales_agent` son namespace packages sin `__init__.py`; `pkgutil.iter_modules` los omite silenciosamente. | `pkgutil.walk_packages` (más lento + mismo problema con namespaces). Detectado a la primera corrida del golden snapshot — registry tenía 7 módulos en lugar de 9. |
| **Convention scan + entry points (no solo entry points).** | Backend usa `requirements*.txt`, no `pyproject.toml [project]` — entry points requieren editable install + reinstalación tras cada provider nuevo. Convention scan es zero-config para in-repo + entry points para distribución externa futura. | Entry points puro (plan original 02-architecture-target §2). Habría agregado packaging churn sin valor. |
| **Eliminar legacy fallback + flag `COPILOT_DISCOVERY_V2`.** | El flag mantenía 7 imports hardcoded en `module_registry.py` "por si discovery falla". Conservarlo bloqueaba shrink del ratchet y era frankenstein. Discovery probada estable (29/29 + 4421 tests). Rollback se hace via `git revert`. | Flag opcional default-true con legacy intacto (plan original F1 §5.2). Habría tapado el shrink y mantenido un branch muerto. |
| **`BaseCopilotProvider` ABC.** | Cada shim repetía 6 sub-port returns `None`. Base class centraliza defaults + docstrings (D102 ruff) y deja shim de 30 líneas → 25. | Per-file ruff ignore D102 sin base class. Funciona pero no DRY; cualquier provider nuevo redescubre el boilerplate. |
| **Provider-pattern exception en `test_ddd_boundaries`.** | Modules importan `copilot.domain.ports` — es la inversión de dependencia (copilot owns abstracción, módulos suplen concreción). Marcar como violación rompe el patrón. | Allowlist por entrada (10 entries nuevas). Diluye la señal del test; cualquier provider nuevo requeriría editar el allowlist. |
| **Contract test `test_social_proof_invariants` excluye `copilot_provider/`.** | Provider expone dict con keys `"testimonials"/"authority_items"/"team_members"` — coinciden con `LEGACY_JSON_KEYS` substring. Pero NO leen JSON columns: arman dict desde repos para consumer del copilot. False positive del substring scan. | Renombrar las keys (rompe `offer_section_tools.py:870-1254` que las consume vía `bundle.get(...)`). |

---

## Sorpresas / gotchas

- **Namespace packages mezclados.** `assets/connections/iam/sales_agent` viven SIN `__init__.py` (Python 3 implicit namespace) mientras el resto SÍ los tiene. `pkgutil.iter_modules(pkg.__path__)` filtra los namespace packages cuando el paquete padre es regular. Workaround: filesystem scan vía `Path.iterdir()` + `(child / 'copilot_provider').is_dir()`. Reproduce: golden snapshot del registry mostró `convention=['analytics','brand','commercial_calendar','crm','landing','offer','social_proof']` faltando `connections`+`sales_agent`. Cualquier fase futura que use convention scan debe usar el mismo patrón filesystem (no `pkgutil`).

- **`_register_tool_groups` valida por `id()`, no por nombre.** Si un provider expone una lista que reusa un tool transversal (mismo `name` distinto objeto), `ToolNameCollisionError`. Para extender un grupo existente el tool DEBE ser el mismo objeto. F3 que publique `brand_voice` group con tool `clarify_brand_voice`: si reusa `clarify` tool transversal, debe importar el mismo `BaseTool` instance, no recrear.

- **`langchain-anthropic 1.4.1` instalado pero no usado.** Es transitive dep de `deepagents 0.5.3`. Evaluar después de F2 si deepagents config no lo invoca, considerar pin o exclusión.

- **Test flaky `test_tool_call_produces_tool_events` persiste.** F0 lo notó como pytest-randomly order-dep; se intentó con `-p no:randomly` y falla igual con suite full (4421 tests). Aislado en `TestStreamChatEventSequence` = 7/7 pasa. Hay state-leak persistente de algún test previo. **No bloqueante para F1** pero cualquier fase que toque `streaming` orchestrator debe correr aislado primero. Tech debt en `docs/mejoras-proceso/to-do.md`.

- **Plan F1 §5.5 mencionaba `test_offer_tools_migrated.py` — no aplica.** Cambié pilot a brand, así que el arch test específico es `test_brand_provider_is_deep_migrated`. Cualquier fase F# futura que migre offer's `offer_section_tools.py` (19 tools, ratchet entry `copilot -> brand | copilot/application/tools/offer_section_tools.py`) debe agregar test análogo.

---

## Hooks listos para próximas fases

- **`copilot/domain/ports.py::BaseCopilotProvider`** — base class con None defaults para todos los sub-ports. F2/F3/F6 que necesiten subclases nuevas heredan + override solo lo necesario.
- **`copilot/application/tools/registry.py::_build_tool_groups`** — merger de provider tool_groups + transversales con dedupe por `tool.name`. F3 expone `brand_section` group via `BrandToolProvider.tool_groups()` y aparece automáticamente sin tocar `_BASE_TOOL_GROUPS`.
- **`copilot/domain/ports.py::ProviderRoute`** — declarativo. Provider declara `routes()` y discovery agrega al ROUTE_TOOL_MAP — solo falta wire-up en `_match_route` (deferido por scope F1).
- **`brand/copilot_provider/summary.py::BrandSummaryProvider.summary()`** — devuelve None hoy. F3 implementa fetch de `brand_summary` table.
- **`brand/copilot_provider/context_inject.py::BrandContextInjector.inject_for()`** — devuelve None hoy. F3 implementa "lighthouse" injection.
- **Admin UI `/proveedores`** (Streamlit) — surface de health + tools per provider. F2 que falle silencioso aparece acá; F3 al publicar brand_voice group lo muestra automáticamente.
- **Arch tests fitness `test_copilot_provider_compliance.py`** — 6 invariants vivos. F# que migre un módulo más solo debe extender `test_brand_provider_is_deep_migrated` con su propio caso.
- **`test_no_new_copilot_module_imports.py::_RATCHET_FROZEN = True`** + 22 entradas frozen. F# que absorba más imports edita `KNOWN_COPILOT_TO_MODULE_IMPORTS` para shrink + bump `expected = 22` en `test_baseline_count_matches_documented_state`.

---

## Recomendaciones accionables para F2 (Deep Agents harness)

1. **Antes de empezar:** correr `cd backend && .venv/bin/pytest tests/modules/copilot/golden/ tests/architecture/test_copilot_provider_compliance.py tests/architecture/test_no_new_copilot_module_imports.py -q -o addopts=""` (debe ser 17/17). Si falla → no agregar deepagents harness; investigar primero.
2. **El paquete real es `deepagents` 0.5.3** (no `langchain-deepagents`). Versión actual cumple. F2 puede importar: `from deepagents import create_deep_agent`. Retorna compiled LangGraph graph (LangGraph 1.1.9 ya instalado).
3. **No tocar `copilot/application/tools/registry.py::_BASE_TOOL_GROUPS`.** Si F2 introduce nuevos tools transversales (write_todos, scratchpad, pin_to_memory), agregarlos al `_BASE_TOOL_GROUPS` dict directamente; si son tools de un módulo, exponerlos via su provider's `ToolProvider.tool_groups()`.
4. **F2 puede agregar nuevos groups sin tocar discovery** — la aggregator pathway está activa. Verificar via `/admin/proveedores` page que el group nuevo aparezca.
5. **El `ProviderRoute.groups` aún no se consume en `_match_route`** — F2 no lo necesita pero F# que requiera "provider X declara que su tool group Y vive en route Z dinámicamente" debe agregar wire-up en `_match_route` o en una nueva fn `_aggregate_provider_routes()`. Hoy `ROUTE_TOOL_MAP` sigue siendo hardcoded.
6. **Si F2 introduce nuevos `[COPILOT-*]` anchors,** agregarlos a `tests/architecture/test_copilot_anchors.py::ANCHOR_REGISTRY` (límite es 25; usé 21 en F1 con `COPILOT-PROVIDER-PATTERN`).

---

## Riesgos abiertos

- **Test flaky persistente** (`test_tool_call_produces_tool_events`). F2 que toque streaming/orchestrator: correr aislado antes/después.
- **`offer_section_tools.py` (19 tools) sigue en `copilot/tools/`** con 5 imports a brand/scheduling/social_proof. Cualquier fase que mueva estas tools al provider correspondiente shrinks ratchet en 5 entradas más. Sugerencia: hacerlo en F-pos-3 cuando offer ladder builder se redibuje, no antes.
- **`copilot/infrastructure/persisters/{brand,buyer_persona,offer}_persister.py`** importan repos cross-module. Provider pattern para persisters = port `PersisterProvider`. Plan no lo cubrió en ninguna fase. Sugerencia: agendar como "F-pos-7 persister provider" después de F6 (workflow unification).
- **`copilot/application/services/offer_psychology_service.py`** importa avatar_repo + offer ports. Cross-module heavy. Considerar mover a `offer/copilot_provider/services/` cuando F# migre offer deep.

---

## Fuentes research útiles

- [deepagents · PyPI](https://pypi.org/project/deepagents/) — confirmó 0.5.3 stable + deps already installed (`langchain-core>=1.2.27`, `langchain>=1.2.15`, `langchain-anthropic>=1.4.0`).
- [Python Packaging — Creating and discovering plugins](https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/) — confirmó pattern entry_points + cuando convention-scan es preferible (in-repo zero-config).
- [LangChain Reference — BaseTool](https://reference.langchain.com/python/langchain-core/tools/base/BaseTool) — confirmó que `tools` arg de `create_deep_agent` acepta `list[BaseTool]` directo, sin wrapper. F2 podrá pasar `get_tools_for_route(...)` output directo.
- [importlib.metadata — Python docs](https://docs.python.org/3/library/importlib.metadata.html) — confirmó API estable Python 3.10+ (no necesitamos `importlib_metadata` backport).

Tessl tiles consultados: `tessl__fastapi`, `tessl__pytest-api-testing`, `pypi-langgraph` (versión actual cumple). No instalé tile nuevo — la combinación entry_points + convention scan no necesita doc curada.
