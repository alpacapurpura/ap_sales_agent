# TP10 — Provider Pattern (F1)

**F# que valida:** F1 (provider pattern + discovery + `MODULE_REGISTRY` descentralizado).
**Tiempo estimado:** 1-2 hs.
**Pre-req hard:** TP0.

---

## Misión

Confirmar que el patrón "agregar tool/módulo nuevo sin tocar `copilot/`" realmente funciona end-to-end:

1. Agregar un módulo dummy con su `copilot_provider/` se descubre en boot (convention scan).
2. Tool nuevo aparece en LLM bound tools sin editar `copilot/application/tools/registry.py`.
3. Provider scan NO abre conexiones DB en module-load (heredado F4 gotcha).
4. Arch test `test_no_new_cross_module_imports` no se rompe agregando provider nuevo.
5. Remover el módulo dummy → tool desaparece (con/sin restart, documentar).
6. **Schema parity BE↔FE para cualquier card_kind / system prompt section / tool API que el provider exponga** (lección B18-TP9).

---

## Research mandate

Queries:

- `"python entry_points plugin discovery 2026 best practices importlib.metadata"` — confirmar entry_points sigue siendo el approach (vs setuptools deprecación).
- `"langchain bind_tools dynamic registration runtime 2026"` — validar bind_tools acepta runtime registration o requiere boot-time.
- `"DDD ports adapters provider pattern python 2026 plugin architecture"` — validar el patrón sigue siendo la convención.

---

## API real F1 (verificado 2026-04-26 vs codebase actual)

### Discovery

- Path: `src/modules/copilot/application/discovery.py` (NO `application/providers/discovery.py`).
- Signature: `discover_providers() -> dict[str, CopilotProvider]` keyed by `module_id`.
- Fuentes:
  - **Convention scan** sobre `src.modules.{name}.copilot_provider` con `provider` attribute top-level (`_PROVIDER_ATTR = "provider"`).
  - **Entry points** group `nicolify.copilot_providers`.
- **Gotcha crítico:** `_scan_convention()` SKIPea cualquier dir que `child.name.startswith((".", "_"))`. **Por eso el dummy NO puede llamarse `_test_provider/`** — quedaría invisible. Se llama `tp10_dummy/`.
- Cache: `@lru_cache(maxsize=1)`. Tests usan `reset_discovery()` para reload.

### CopilotProvider Protocol

`src/modules/copilot/domain/ports.py::CopilotProvider` (8 métodos):

```python
@runtime_checkable
class CopilotProvider(Protocol):
    @property
    def module_id(self) -> str: ...
    @property
    def label(self) -> str: ...
    def module_data(self) -> ModuleData | None: ...
    def routes(self) -> Sequence[ProviderRoute]: ...
    def tool_provider(self) -> ToolProvider | None: ...
    def workflow_provider(self) -> WorkflowProvider | None: ...
    def summary_provider(self) -> SummaryProvider | None: ...
    def context_injector(self) -> ContextInjector | None: ...
    def data_access(self) -> DataAccessProvider | None: ...
```

**Pattern recomendado:** subclasear `BaseCopilotProvider` (mismo file) que devuelve None / tuple vacía en todos los sub-ports — override solo lo que tu módulo expone.

### Tool registry merge

`src/modules/copilot/application/tools/registry.py::_build_tool_groups()`:

- Empieza con `_BASE_TOOL_GROUPS` (transversal owned por copilot).
- Itera `discover_providers().values()`, llama `provider.tool_provider().tool_groups()`, y MERGE en TOOL_GROUPS dedup por `tool.name`.
- Nuevos group names se insertan; existing extends.

### Route → group mapping

**`ROUTE_TOOL_MAP` es DICT ESTÁTICO** (registry.py:150). Provider.routes() NO se consume en runtime — solo en `discovery.health()` para health check (registry.py:203).

**→ F1 promise BREAK identificado TP10:** provider puede registrar tool_groups pero el tool NO queda bindable a LLM si ningún `ROUTE_TOOL_MAP[prefix]` o `ALWAYS_AVAILABLE_GROUPS` contiene ese group name. Editar ROUTE_TOOL_MAP requiere tocar `copilot/application/tools/registry.py` → viola la promesa "agregar tool sin tocar copilot/".

**Fix arquitectónico TP10 propuesto (TDD):**
- Renombrar `ROUTE_TOOL_MAP` estático a `_BASE_ROUTE_TOOL_MAP`.
- Implementar `_build_route_tool_map()` análogo a `_build_tool_groups()`: merge `provider.routes()` ProviderRoute entries en el map.
- `ROUTE_TOOL_MAP = _build_route_tool_map()` al import.
- Test regresión: provider con `routes() → (ProviderRoute("*", ("tp10_dummy",)),)` expone tool en `get_tools_for_route("/cualquiera")`.

---

## Scenarios

### S10.1 — Discovery actual (baseline)

```python
from src.modules.copilot.application.discovery import discover_providers
providers = discover_providers()
print(sorted(providers.keys()))
# Esperado: ['analytics', 'brand', 'commercial_calendar', 'connections', 'crm', 'landing', 'offer', 'sales_agent', 'social_proof']
```

**Pass:** lista incluye los 9 módulos in-repo (entry_points = []).

### S10.2 — Crear módulo dummy `tp10_dummy/`

Crear `backend/src/modules/tp10_dummy/`:
```
tp10_dummy/
├── __init__.py            # vacío
└── copilot_provider/
    ├── __init__.py        # re-export provider
    ├── tools.py           # @tool test_dummy_tool + DummyToolProvider
    └── provider.py        # TP10DummyProvider + provider singleton
```

`copilot_provider/__init__.py`:
```python
from src.modules.tp10_dummy.copilot_provider.provider import provider
__all__ = ["provider"]
```

`copilot_provider/tools.py`:
```python
from collections.abc import Mapping, Sequence
from typing import Any
from langchain_core.tools import tool


@tool
def test_dummy_tool(query: str) -> str:
    """TP10 dummy tool. Returns input wrapped to verify dispatch end-to-end."""
    return f"[TEST_PROVIDER_OK] {query}"


class TP10DummyToolProvider:
    def tool_groups(self) -> Mapping[str, Sequence[Any]]:
        return {"tp10_dummy": [test_dummy_tool]}

    def tools(self) -> Sequence[Any]:
        return (test_dummy_tool,)
```

`copilot_provider/provider.py`:
```python
from collections.abc import Sequence

from src.modules.copilot.domain.ports import (
    BaseCopilotProvider,
    ModuleData,
    ProviderRoute,
    ToolProvider,
)
from src.modules.tp10_dummy.copilot_provider.tools import TP10DummyToolProvider


class TP10DummyProvider(BaseCopilotProvider):
    """TP10 dummy provider — validates F1 plug-and-play e2e."""

    @property
    def module_id(self) -> str:
        return "tp10_dummy"

    @property
    def label(self) -> str:
        return "TP10 Dummy"

    def module_data(self) -> ModuleData | None:
        return ModuleData(
            module_id="tp10_dummy",
            label="TP10 Dummy",
            description="TP10 provider pattern verification dummy.",
            route_prefix="tp10-dummy",
        )

    def routes(self) -> Sequence[ProviderRoute]:
        return (ProviderRoute(prefix="*", groups=("tp10_dummy",)),)

    def tool_provider(self) -> ToolProvider | None:
        return TP10DummyToolProvider()


provider = TP10DummyProvider()
```

### S10.3 — Re-discover encuentra `tp10_dummy`

```python
from src.modules.copilot.application.discovery import discover_providers, reset_discovery
reset_discovery()
providers = discover_providers()
assert "tp10_dummy" in providers
p = providers["tp10_dummy"]
assert p.label == "TP10 Dummy"
assert len(p.routes()) == 1
tp = p.tool_provider()
assert tp is not None
assert "tp10_dummy" in tp.tool_groups()
```

**Pass:** provider visible + tool_groups reportado.

### S10.4 — Tool aparece en TOOL_GROUPS + bound a LLM (F1 promise full)

Tras fix arquitectónico `_build_route_tool_map`:

```python
from src.modules.copilot.application.tools.registry import (
    TOOL_GROUPS, ROUTE_TOOL_MAP, get_tools_for_route, get_tools_for_context,
)
# Reload registry tras nuevo provider:
import importlib, src.modules.copilot.application.tools.registry as reg
importlib.reload(reg)

assert "tp10_dummy" in reg.TOOL_GROUPS
assert "tp10_dummy" in reg.ROUTE_TOOL_MAP["*"]
tools_global = reg.get_tools_for_route("/copilot")
assert any(t.name == "test_dummy_tool" for t in tools_global)
```

Luego turn live (Kimi K2.6 Sprint 0 routing):

```bash
TOKEN=$(.venv/bin/python scripts/get_clerk_test_token.py)
curl -sS -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: c67c9845-6cf7-4aee-beba-7e177e84d167" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: text/event-stream" \
  -d '{"message":"Llamá al tool test_dummy_tool con query=\"hello\" y devolveme el resultado exacto","conversation_id":null,"client_context":{"current_route":"/copilot"}}'
```

```sql
SELECT name, status, data->>'output_preview' AS output, data->'args' AS args
FROM copilot_trace_event
WHERE event_type='tool_call' AND name='test_dummy_tool'
ORDER BY created_at DESC LIMIT 1;
```

**Pass:** row con `name='test_dummy_tool'`, `status='success'`, output_preview contiene `[TEST_PROVIDER_OK] hello`. Probar **2 phrasings** (lección sample-variance TP9):

- Phrasing A: imperativo explícito ("llamá al tool ... con query='hello'").
- Phrasing B: descripción natural ("usá el dummy tool y devolveme la respuesta wrappeada").

### S10.5 — NO conexiones DB en import-time

Watch:
```bash
docker logs visionarias_postgres --since 1s -f &
sleep 1
.venv/bin/python -c "import src.modules.tp10_dummy.copilot_provider.provider as m; print('imported:', m.provider.module_id)"
```

**Pass:** 0 nuevas líneas `connection received`/`authenticated` durante el import. (Per F4 gotcha).

### S10.6 — Arch tests verde

```bash
.venv/bin/pytest tests/architecture/ -x -q --tb=short
```

**Pass:** todos los tests arch pasan con `tp10_dummy/` presente. Validar:

- `test_ddd_boundaries` — el provider importa solo `copilot.domain.ports` (allowed por convention) + `langchain_core.tools` (external).
- `test_no_new_cross_module_imports` — `copilot/` NO importa `tp10_dummy/` directamente (discovery resuelve runtime).

### S10.7 — Remove dummy → tool desaparece

```bash
rm -rf backend/src/modules/tp10_dummy/
.venv/bin/python -c "
from src.modules.copilot.application.discovery import discover_providers, reset_discovery
reset_discovery()
import src.modules.copilot.application.tools.registry as reg
import importlib; importlib.reload(reg)
assert 'tp10_dummy' not in discover_providers()
assert 'tp10_dummy' not in reg.TOOL_GROUPS
print('CLEANED')
"
```

Re-trigger turn → tool no firea (LLM no lo encuentra; si lo nombra explícito, error de tool not found).

**Pass:** registry limpio. **Documentar** si requiere restart de api_dev (probable: `lru_cache` en discovery + module-level `TOOL_GROUPS = _build_tool_groups()` se ejecuta UNA vez por proceso).

### S10.8 — Schema parity BE↔FE para outputs cross-stack del dummy

Para TP10 el dummy expone solo un tool simple → output `ToolMessage` content cadena → consumido por chat orchestrator → renderizado FE como bubble texto. **No** introduce nueva card_kind ni nuevo system prompt section, así que la parity check se reduce a:

- Verificar que el tool result (`ToolMessage(content="[TEST_PROVIDER_OK] hello")`) navega del backend al stream SSE como `text` block sin schema gaps.
- **Si en futura iteración el dummy emitiera card_kind nueva → arch test BE↔FE parity necesario** (lección B18-TP9).

**Pass:** SSE stream del turn S10.4 contiene `text` block con `[TEST_PROVIDER_OK] hello` en algún punto antes del done.

---

## Tools / queries

- Inspección directa: `discover_providers()`, `TOOL_GROUPS`, `ROUTE_TOOL_MAP`.
- SQL: `copilot_trace_event WHERE name='test_dummy_tool'`.
- Postgres logs: `docker logs visionarias_postgres --since Ns | grep -i connect`.
- Arch tests: `.venv/bin/pytest tests/architecture/ -x -q`.

---

## Targets

| Métrica | Target | Hard fail |
|---|---|---|
| Discovery encuentra dummy | OK | 0 |
| Tool dispatchable end-to-end | tool_call status=success + output preview correcto | tool_call no firea o status=error |
| 0 DB conexiones en import | OK | 1+ |
| Arch tests verde | 100% pass | 1+ violation |
| Remove → tool gone | OK (con/sin restart, doc) | tool persiste post-remove |
| Schema parity (S10.8) | SSE stream coherente | gap silencioso |
| Routes merge wired post-fix | ROUTE_TOOL_MAP[*] include "tp10_dummy" sin editar registry.py | hardcoded edit needed |

---

## Failure playbook

| Síntoma | Investigar | Root cause | Fix |
|---|---|---|---|
| Discovery no encuentra dummy | path + name | `_scan_convention` glob | confirmar dir matchea pattern + NO leading underscore |
| Tool en TOOL_GROUPS pero no bound | route binding | `ROUTE_TOOL_MAP` estático | **fix arquitectónico TP10:** wire `provider.routes()` en `_build_route_tool_map` |
| Import abre DB | side effect en módulo | import chain analysis | mover I/O a function-level |
| Arch test rompe | `KNOWN_CROSS_MODULE_IMPORTS` allowlist | `test_ddd_boundaries.py` | agregar provider con justificación o asegurarse import solo de `copilot.domain.ports` |
| Remove no quita tool | discovery cacheada (`lru_cache`) | `reset_discovery` + `importlib.reload(registry)` | documentar como expected (eager-cached registry) |
| Tool not found en LLM tras restart | container env stale | docker compose recreate | `docker compose up -d --force-recreate api_dev` |

---

## Lo que necesito de Chris

- [x] Permiso para crear/borrar módulo `tp10_dummy/` temporalmente. Cleanup garantizado al cerrar TP.
- [x] Permiso para fix arquitectónico `_build_route_tool_map` si S10.4 confirma F1 promise rota.

---

## Antipatrones

- ❌ Llamar al dummy `_test_provider/` o `_anything/` — convention scan SKIPea leading underscore. Naming valid: lowercase letters + digits, sin prefix `_`.
- ❌ Editar `ROUTE_TOOL_MAP` estático para hacer pasar S10.4. El TP existe para validar que NO hace falta tocar `copilot/`. El fix correcto wire dynamic merge.
- ❌ Mockear LLM en S10.4. Tool dispatch = real Kimi K2.6 turn — Sprint 0 routing live.
- ❌ Cleanup parcial (solo borrar el dir sin reset_discovery + reload registry). El test S10.7 verifica todo el ciclo.
- ❌ Embedder PlanCard / cards / system prompt sections en el dummy. TP10 valida tool dispatch puro — extender scope distrae.
