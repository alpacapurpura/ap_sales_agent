# TP10 — Provider Pattern (F1)

**F# que valida:** F1 (provider pattern + discovery + `MODULE_REGISTRY` descentralizado).
**Tiempo estimado:** 1-2 hs.
**Pre-req hard:** TP0.

---

## Misión

Confirmar que el patrón "agregar tool/módulo nuevo sin tocar `copilot/`" realmente funciona:

1. Agregar un módulo dummy con su `copilot_provider/` se descubre en boot.
2. Tool nuevo aparece en LLM bound tools sin editar `copilot/application/tools/registry.py`.
3. Provider scan NO abre conexiones DB en module-load (heredado F4 gotcha).
4. Arch test `test_no_new_cross_module_imports` no se rompe agregando provider nuevo.
5. Remover el módulo dummy → tool desaparece sin restart.

---

## Research mandate

Queries:

- `"python entry_points plugin discovery 2026 best practices"` — confirmar entry_points sigue siendo el approach (vs setuptools deprecación).
- `"langchain tool registration dynamic 2026"` — validar bind_tools acepta lazy registration.
- `"DDD ports adapters provider pattern python 2026"` — validar el patrón sigue siendo la convención.

---

## Scenarios

### S10.1 — Discovery actual (baseline)

```python
from src.modules.copilot.application.providers.discovery import discover_providers
providers = discover_providers()
print([p.module_name for p in providers])
```

**Pass:** lista incluye `analytics`, `brand`, `offer`, `crm`, `landing`, `connections`, etc. (esperado per F1 learnings).

### S10.2 — Crear módulo dummy

Crear `backend/src/modules/_test_provider/`:
```
_test_provider/
├── __init__.py
├── domain/
│   └── __init__.py
└── copilot_provider/
    ├── __init__.py
    ├── tools.py          # define un tool dummy
    └── manifest.py        # define el provider
```

`copilot_provider/manifest.py`:
```python
from src.modules.copilot.domain.ports import CopilotProvider
from .tools import test_dummy_tool

class TestProviderManifest(CopilotProvider):
    module_name = "_test_provider"
    def tools(self):
        return [test_dummy_tool]
    def workflows(self):
        return ()
    def data_access(self):
        return None
```

`copilot_provider/tools.py`:
```python
from langchain_core.tools import tool

@tool
def test_dummy_tool(query: str) -> str:
    """Dummy tool for TP10. Returns input wrapped."""
    return f"[TEST_PROVIDER_OK] {query}"
```

### S10.3 — Re-discover encuentra el módulo

```python
providers = discover_providers()
test_module = next((p for p in providers if p.module_name == "_test_provider"), None)
assert test_module is not None
```

**Pass:** dummy aparece sin restart de boot (si discovery usa convention scan).

### S10.4 — Tool aparece en bound tools

Disparar turn forzando route donde test_dummy_tool aplique:
```
"llamá al tool _test_provider:test_dummy_tool con query='hello'"
```

```sql
SELECT name, data->'args' FROM copilot_trace_event
WHERE turn_id=:tid AND event_type='tool_call' AND name='test_dummy_tool';
```

**Pass:** tool_call con args correctos. Output preview = "[TEST_PROVIDER_OK] hello".

### S10.5 — NO conexiones DB en import time

Aislar el import:
```bash
.venv/bin/python -c "import src.modules._test_provider.copilot_provider.manifest as m; print('imported')"
```

Watch logs de Postgres:
```bash
docker logs visionarias_postgres --since 1m | grep -i connect
```

**Pass:** 0 nuevas conexiones DB durante el import. (Per F4 gotcha, providers que abren DB en import-time rompen tests).

### S10.6 — Arch tests siguen verde

```bash
.venv/bin/pytest tests/architecture/ -x -q
```

**Pass:** todos pass. Confirmar `_PROVIDER_CONTRACT_IMPORTS` permite el import desde `_test_provider/copilot_provider/` → `copilot.domain.ports`.

### S10.7 — Remove dummy → tool desaparece

`rm -rf src/modules/_test_provider/`.

Re-correr S10.1 → `_test_provider` no aparece.

Disparar turn que llame al tool → LLM no lo encuentra (or registry.py reflects).

**Pass:** sin restart, tool ya no está bound. (Si requiere restart, documentar — discovery puede ser eager-cached).

---

## Tools / queries

- Inspección directa imports + discovery.
- SQL: `copilot_trace_event` para verificar tool registration.

---

## Targets

| Métrica | Target | Hard fail |
|---|---|---|
| Discovery encuentra dummy | OK | 0 |
| Tool dispatchable | OK | tool_call falla |
| 0 DB conexiones en import | OK | 1+ |
| Arch tests verde | OK | 1+ violation |
| Remove → tool gone | OK (con/sin restart, doc) | tool persiste post-remove |

---

## Failure playbook

| Síntoma | Investigar | Root cause | Fix |
|---|---|---|---|
| Discovery no encuentra dummy | scan path | `discovery.py` glob | confirmar `_test_provider/copilot_provider/` matchea pattern |
| Tool no aparece bound | registry merge | `_build_tool_groups` | trace LLM bound_tools list |
| Import abre DB | side effect en módulo | import chain analysis | mover I/O a function-level |
| Arch test rompe | `KNOWN_CROSS_MODULE_IMPORTS` allowlist | `test_ddd_boundaries.py` | agregar provider con justificación |
| Remove no quita tool | discovery cacheada | rebuild cache o restart | documentar como expected |

---

## Lo que necesito de Chris

- [ ] Permiso para crear/borrar módulo `_test_provider/` temporalmente. Cleanup garantizado al cerrar TP.
