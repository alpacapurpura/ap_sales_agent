# F1 — Provider pattern + discovery

**Pre-req:** F0 cerrada (dead code limpio, golden tests baseline, `langchain-deepagents` instalado).
**Sprints estimados:** 2.
**Bloquea:** F2, F3, F5, F6, F7 (todos dependen del provider para registrarse).
**Valor entregado:** extender el copilot dejó de requerir editar `copilot/`. Cada módulo expone su `copilot_provider/`.

---

## §1 Objetivo

Convertir el `MODULE_REGISTRY` y `ROUTE_TOOL_MAP` hardcodeados en un **registry runtime** poblado por discovery via Python entry points. Cada módulo (`brand`, `offer`, `landing`, `analytics`, `crm`, `connections`) expone un `copilot_provider/` con sus tools. Migrar **offer** como módulo piloto end-to-end.

Resto de módulos: solo migra los puntos de entrada al patrón nuevo (su provider devuelve los tools existentes sin re-escritura). Refactor profundo de cada provider llega en fases siguientes según corresponda.

---

## §2 Pre-lectura específica

- `phases/F0-*.md` + `learnings/F0-foundation.md`.
- `02-architecture-target.md §2` (Ports).
- Código actual:
  - `backend/src/modules/copilot/domain/module_registry.py`
  - `backend/src/modules/copilot/application/tools/registry.py`
  - `backend/src/modules/copilot/application/tools/offer_section_tools.py` (18 tools, módulo piloto)
  - `backend/src/modules/copilot/application/tools/offer_ladder_tools.py`
- `.claude/rules/backend-ddd.md` (cross-module imports).
- `pyproject.toml` actual (entry points existentes).

---

## §3 Research mandate (abril 2026)

Queries WebSearch:

- `python entry_points plugin discovery best practices 2026 importlib.metadata`
- `pydantic v2 protocol runtime_checkable plugin pattern 2026`
- `LangChain tool registry dynamic loading 2026`
- `python entry_points pyproject.toml `

Tessl tiles:

- `tessl__fastapi`, `tessl__pytest-api-testing`.
- Buscar tile relacionado con plugin systems / entry points.

Productos:

- Confirmación: `importlib.metadata.entry_points(group=...)` API estable Python 3.12+.
- Decisión: lazy load (entry point loaded on first use) vs eager (loaded at startup). Recomendación inicial: **lazy con cache**.
- Patrón para health-check de providers en startup (logging + Sentry).

---

## §4 Lo que NO se toca

- `MODULE_REGISTRY` conceptualmente: el patrón sigue. Solo cambia el populating.
- `schema_introspection.py`, `editable_fields` ports, `navigation_map.py`.
- Tools transversales en `copilot/tools/` (navigation, web_research, propose_field_updates, etc.).
- Tests existentes copilot.
- Sales agent. Si el provider pattern necesita changes en `shared/`, asegurar que sales_agent siga compilando + tests verdes.

---

## §5 Deliverables

### 5.1 Ports

`backend/src/modules/copilot/domain/ports.py` con `CopilotProvider`, `ToolProvider`, `WorkflowProvider`, `SummaryProvider`, `ContextInjector` (ver `02-architecture-target.md §2`).

Tests unitarios de los Protocols (instance check sobre stubs).

### 5.2 Discovery service

`backend/src/modules/copilot/application/discovery.py`:

```python
def discover_providers() -> dict[str, CopilotProvider]:
    """Itera entry points group=nicolify.copilot_providers, lazy load + cache."""
```

Comportamiento:

- Cache singleton.
- Logs: provider cargado / fallido (Sentry tag).
- Health-check al startup: cada provider responde a `module_id` y al menos un sub-port.
- Si discovery falla → fallback al `MODULE_REGISTRY` legacy (feature flag `COPILOT_DISCOVERY_V2` env, default `False` durante F1 y `True` antes de cerrar fase).

### 5.3 Migración offer (piloto)

Crear `backend/src/modules/offer/copilot_provider/`:

```
copilot_provider/
├── __init__.py            # exporta `provider: CopilotProvider`
├── tools.py               # mueve offer_section_tools (18) + offer_ladder_tools
├── workflows.py           # placeholder vacío (F6 lo poblará)
├── summary.py             # placeholder None (F-future)
└── context_inject.py      # placeholder None (F3 maneja brand)
```

Los tools NO se re-escriben. Solo se mueven y se exponen via provider. El comportamiento queda idéntico.

`pyproject.toml`:

```toml
[project.entry-points."nicolify.copilot_providers"]
offer = "src.modules.offer.copilot_provider:provider"
```

`backend/src/modules/copilot/application/tools/registry.py`:

- Reemplaza imports hardcoded de `offer_section_tools` + `offer_ladder_tools` por consumo del provider via discovery.
- `ROUTE_TOOL_MAP` para `offer-studio` deriva del provider (provider expone qué routes consume).

### 5.4 Migración resto de módulos (mínima)

Para `brand`, `landing`, `analytics`, `crm`, `connections`:

- Crear `copilot_provider/__init__.py` que devuelve provider con `tool_provider()` que delega al import existente en `copilot/tools/{name}_tools.py`.
- Estos tools quedan en su path actual hasta fase específica que los migre.
- Solo se mueve el **registro** al provider, no el código de tool.

Después de F1, el dispatch del registry pasa por providers, pero los tools viven aún en `copilot/tools/{module}_tools.py` (excepto offer ya migrado).

### 5.5 Arch tests

- `test_no_new_copilot_module_imports.py` — activar `_RATCHET_FROZEN = True`. Capturar baseline (los imports legacy pre-F1) + bloquear nuevos.
- `test_every_module_has_copilot_provider.py` — todos los módulos en `MODULE_REGISTRY` tienen `copilot_provider/` registrado.
- `test_provider_protocol_compliance.py` — cada provider implementa `CopilotProvider` Protocol (runtime_checkable).
- `test_offer_tools_migrated.py` — confirma que `offer_section_tools.py` ya no existe en `copilot/tools/`.

### 5.6 Admin observability

Página Streamlit nueva `/admin/copilot/providers` (usar registry pattern de admin-panel rule):

- Lista providers cargados.
- Tools que cada uno expone.
- Workflows registrados (vacío en F1).
- Health-check status (last error si hubo).

---

## §6 Quality gates

- `/test-backend` verde (incluyendo `tests/architecture/`).
- `/test-frontend` verde.
- Golden tests F0 verdes (críticos — confirman 0 regresión comportamiento).
- Manual: arrancar `/dev-up`, conversación full en `/offer-studio/*` — todos los tools de offer responden idéntico a pre-F1.

---

## §7 Riesgos específicos

| Riesgo | Mitigación |
|---|---|
| Discovery falla al startup → copilot caído | Feature flag + fallback. Test de fallback explícito. |
| Imports circulares al crear `copilot_provider/` en módulo | Lazy imports dentro de `__init__.py` del provider. |
| Sales agent rompe por cambios en `shared/` | Correr `pytest tests/modules/sales_agent/` antes de cerrar. |
| Performance: discovery costoso en cada turn | Cache singleton + warm-up en startup. Medir overhead. |

---

## §8 Definición de hecho

- [ ] Ports definidos + tests Protocol compliance.
- [ ] Discovery + cache + fallback + feature flag.
- [ ] Offer migrado fully a provider (18+1 tools).
- [ ] Resto de módulos con shim provider mínimo.
- [ ] Arch tests fitness pasando.
- [ ] Admin Streamlit `/admin/copilot/providers` operativo.
- [ ] Golden tests F0 verdes (sin regresión).
- [ ] Documentación: anchor comments en código + update `docs/domains/copilot/INDEX.md`.
- [ ] `learnings/F1-provider-pattern.md` completo.
- [ ] `prompts/F2-start.md` generado.

---

## §9 Notas para fase siguiente F2

Al cerrar, dejar listo en learnings:

- API exacta del discovery (cómo F2 va a registrar tools transversales sin entry point).
- Hooks donde F2 inyecta el deep agent harness.
- Si `langchain-deepagents` introduce algún choque con `langchain-core` actual.
