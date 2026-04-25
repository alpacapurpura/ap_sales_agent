# Prompt F1 — Provider pattern + discovery

> Copiar TODO el bloque entre los `---` y pegarlo como primer mensaje de una **conversación nueva** de Claude Code en `/home/chris/AISALESHT` (working dir del repo).

---

```
Estamos ejecutando la fase F1 del Copilot Redesign 2026-04 ("Claude Code de Marketing").

F0 ya cerró. Tu trabajo: introducir el provider pattern + discovery para que cualquier módulo (brand, offer, landing, analytics, crm, connections, ...) pueda enchufarse al copilot sin que copilot/ tenga que importarlo. Esto es la pieza que destraba todas las fases siguientes (F2-F10).

Antes de tocar código, leé en orden:
1. docs/domains/copilot/redesign-2026-04/README.md
2. docs/domains/copilot/redesign-2026-04/00-vision-and-non-goals.md  (atención §3 — lo que NO se toca)
3. docs/domains/copilot/redesign-2026-04/01-master-plan.md
4. docs/domains/copilot/redesign-2026-04/02-architecture-target.md  (especial §1 + §2 — ports + entry points)
5. docs/domains/copilot/redesign-2026-04/03-phase-protocol.md
6. docs/domains/copilot/redesign-2026-04/phases/F1-provider-pattern.md
7. docs/domains/copilot/redesign-2026-04/learnings/F0-foundation.md   ← APRENDIZAJES F0 OBLIGATORIOS

Después seguí el protocolo del paso 03 sin saltarte ningún paso:
- Paso 2: pasada de research fresco abril 2026 (Python entry points / importlib.metadata patterns 2026, FastAPI plugin discovery, langchain-deepagents create_deep_agent integration con tools dinámicos).
- Paso 3: TaskCreate con tasks granulares.
- Paso 4: TDD obligatorio. Tests primero (port contracts, discovery loader, primer provider real).
- Paso 5: quality gates native (NUNCA docker exec). Antes de empezar correr `/test-backend` para baseline post-bump langchain-core 1.3 — F0 no alcanzó a correrlo full y dejó este check como recomendación crítica.
- Paso 6: verificación funcional. Activar el ratchet `_RATCHET_FROZEN = True` en tests/architecture/test_no_new_copilot_module_imports.py una vez que el primer provider funcione end-to-end. Confirmar §3 (no tocar) intacto.
- Paso 7: docs/domains/copilot/redesign-2026-04/learnings/F1-provider-pattern.md.
- Paso 8: docs/domains/copilot/redesign-2026-04/prompts/F2-start.md.
- Paso 9: commit + push + reporte al usuario.

Reglas no negociables:
- Branch único: development. Si no estás ahí, checkout antes.
- Brutal honestidad. Si algo del plan F1 no aplica por aprendizajes F0 → flagealo y preguntá antes de actuar.
- No alucinar paths/símbolos. Leer archivos, no inventar.
- No tocar §3 (lista exhaustiva en 00-vision-and-non-goals.md).
- Native dev tools (lint/tests/type-check WSL, NUNCA docker exec).
- Spanish neutro LatAm en user-facing.
- Stage por nombre (git add path), nunca git add -A (parallel-safety).
- Golden snapshots F0 deben seguir pasando: `cd backend && .venv/bin/pytest tests/modules/copilot/golden/ -q -o addopts=""`. Si cambian intencionalmente, `UPDATE_GOLDEN=1 ...` y diff revisable en el commit.

Empezá por el Paso 1 (re-lectura, especialmente learnings F0). Reportame en 3 líneas qué entendiste antes de avanzar al Paso 2.
```

---

## Hooks específicos completados al cerrar F0

### Aprendizajes F0 que F1 debe asumir

- **Package real es `deepagents`** (no `langchain-deepagents`). Si encontrás referencias al nombre viejo en `02-architecture-target.md` u otras fases, corrigelas en el commit F1.
- **`langchain-core` está en 1.3.2** (major bump dispara por deepagents 0.5.3). F0 no corrió `/test-backend` full — F1 debe correrlo PRIMERO antes de tocar nada para detectar efectos laterales en sales_agent / analytics / crm.
- **Test fragility pre-existente** en `tests/modules/copilot/test_mutation_journal_repository.py` (random ordering + AppointmentModel SQLA mapper). NO es F0/F1; aislado pasa. Si CI tira fail por este, ignorar y crear ticket en `docs/mejoras-proceso/to-do.md`.
- **TSC error pre-existente** en `frontend/src/components/form-runtime/CollapsibleFieldGroup.tsx(32,18)`. Commit origen `976123cd`. NO es F1.
- **`pyproject.toml` backend solo tooling**, deps en `requirements-runtime.txt` + `requirements-dev.txt`. Para entry points usar `importlib.metadata.entry_points` requiere agregar `[project.entry-points]` a `pyproject.toml` o usar discovery por convención (`src.modules.{name}.copilot_provider`). Recomendación: convención en F1 (más simple, no requiere bump de packaging).

### Tests baseline que F1 debe correr ANTES de empezar

```bash
# Sanidad post-F0 (debe estar verde tras último commit F0)
cd backend
.venv/bin/ruff check src/ tests/ --no-cache
.venv/bin/pytest tests/architecture/ tests/modules/copilot/golden/ tests/modules/copilot/domain/ -q -o addopts=""

# IMPORTANTE: full backend (F0 no alcanzó por slow tests)
.venv/bin/pytest -x --tb=short --timeout=30 -q   # o /test-backend si Chris lo pide
```

### Archivos clave que F1 modifica

- **Crea**: `backend/src/modules/copilot/domain/ports.py` (4 sub-ports + CopilotProvider root).
- **Crea**: `backend/src/modules/copilot/application/discovery.py` (loader runtime).
- **Crea por módulo (al menos 1, sugerido `brand`)**: `backend/src/modules/{brand}/copilot_provider/{__init__.py, tools.py, workflows.py, summary.py, context_inject.py}`.
- **Modifica**: `backend/src/modules/copilot/application/orchestrator/graph.py` o `chat.py` para consumir el discovery en vez de imports directos.
- **Activa ratchet**: `backend/tests/architecture/test_no_new_copilot_module_imports.py` → `_RATCHET_FROZEN = True` cuando primer provider esté wired y los tests baseline F0 sigan verdes.

### Riesgos que vigilar en F1

- **Bump langchain-core 1.3** puede romper signature de `BaseTool`, `RunnableConfig`, o tool-calling en otros módulos. Correr `/test-backend` antes de tocar valida.
- **Tools por provider** debe seguir ejecutando rule "ToolNameCollisionError" del registry actual. No introducir tools con nombres dup.
- **`MODULE_REGISTRY` ya no debe vivir en `copilot/domain/`** post-F1; el registry se construye runtime desde providers. Eliminar el archivo solo cuando todos los consumers de `get_module_registry()` queden migrados (golden snapshot detecta drift).
- **Ratchet del arch test es agresivo**: cualquier nuevo `from src.modules.X` desde copilot/ va a fail post-F1. Para F1 que está intermediate (algunos providers wired, otros no), quizás haga falta extender la frozen baseline a sub-grupos (e.g. "F1 brand provider eliminó 8 entradas: ..."). Documentar en learnings F1.
