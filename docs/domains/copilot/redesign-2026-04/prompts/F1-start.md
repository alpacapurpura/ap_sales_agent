# Prompt F1 — Provider pattern + discovery

> Copiar TODO el bloque entre los `---` y pegarlo como primer mensaje de una **conversación nueva** de Claude Code en `/home/chris/AISALESHT` (working dir del repo).

---

```
Estamos ejecutando la fase F1 del Copilot Redesign 2026-04 ("Claude Code de Marketing").

Objetivo único de esta fase: introducir provider pattern + discovery para que cualquier módulo (brand, offer, landing, analytics, crm, connections, ...) pueda enchufarse al copilot sin que copilot/ tenga que importarlo. Esta es la pieza que destraba F2-F10.

Antes de escribir código, leé en orden (sin saltarte ninguno):
1. docs/domains/copilot/redesign-2026-04/README.md
2. docs/domains/copilot/redesign-2026-04/00-vision-and-non-goals.md  (atención §3 — lista exhaustiva de lo que NO se toca)
3. docs/domains/copilot/redesign-2026-04/01-master-plan.md
4. docs/domains/copilot/redesign-2026-04/02-architecture-target.md  (especial §1 + §2 — ports + entry points)
5. docs/domains/copilot/redesign-2026-04/03-phase-protocol.md
6. docs/domains/copilot/redesign-2026-04/phases/F1-provider-pattern.md
7. docs/domains/copilot/redesign-2026-04/learnings/F0-foundation.md  ← APRENDIZAJES F0 OBLIGATORIOS

Después seguí los 9 pasos del protocolo (03-phase-protocol.md). Énfasis especial:

- **Paso 2 — Research fresco abril 2026 (no skip).**
  - WebSearch (mínimo 2 queries, anotar fuentes en learnings):
    - "python entry points plugin discovery FastAPI 2026 best practices"
    - "deepagents create_deep_agent dynamic tools per request 2026"
    - "langchain BaseTool runtime registration langgraph 1.x patterns"
  - Tessl tiles (skill `tessl-context`, equivalente Context7 para docs versionadas):
    - Verificar `tessl__langgraph` versión instalada vs latest. Si está vieja, actualizar.
    - Buscar tile `deepagents` — si no hay, leer pyproject de la lib + README oficial vía WebFetch.
    - Verificar `tessl__fastapi` para patterns Annotated/Depends actuales.
  - Si el research sugiere que el plan cambió → ajustar plan ANTES de codear y dejar nota corta en learnings.

- **Foco — no scope creep.** F1 entrega UNA cosa: provider pattern funcionando con AL MENOS un módulo real (brand sugerido — 8 imports, máximo ROI + bloqueante de F3). Ideas tangenciales atractivas → recomendaciones para F# siguiente, no código.

- **Paso 4 — TDD obligatorio.**
  - Test contracts de los 4 sub-ports + CopilotProvider root antes de implementarlos.
  - Test discovery loader antes del loader real.
  - Test integración del primer provider antes de wirearlo.
  - Golden snapshots F0 deben seguir pasando: `cd backend && .venv/bin/pytest tests/modules/copilot/golden/ -q -o addopts=""`. Si cambian intencionalmente, `UPDATE_GOLDEN=1` y diff revisable en el commit.

- **Paso 5 — Quality gates native (NUNCA `docker exec`).**
  - **CRÍTICO antes de tocar nada**: F0 no alcanzó a correr `/test-backend` full por slow tests. Hubo bump major `langchain-core 1.2 → 1.3`. Correr el suite full ahora para detectar efectos laterales en sales_agent / analytics / crm ANTES de meter más cambios.
  - Después de cada bloque: `ruff check + format + pytest tests/architecture/ tests/modules/copilot/golden/`.

- **Paso 6 — Activar el ratchet.**
  - Cuando primer provider esté wired y golden snapshots sigan verdes, flippear `_RATCHET_FROZEN = True` en `backend/tests/architecture/test_no_new_copilot_module_imports.py`.
  - Cada provider absorbido = entry removido del frozen set (sólo shrink permitido).
  - Confirmar §3 (no tocar) intacto: smoke browser o trace inspection si tocaste algo cerca de UI / SSE / cards.

- **Paso 7 — Lecciones aprendidas: ÚTILES, no plantilla rellenada.**
  - Solo lo que F2 va a consultar: decisión clave (con razón + alternativa), gotchas reales de versión, hook listo (path + cómo activar), riesgo abierto (qué puede romper).
  - Prohibido: lista exhaustiva de archivos (vive en `git diff`), métricas inventadas, secciones con "N/A".
  - Si una sección del template `learnings/_template.md` no aplica → eliminarla.
  - Criterio: ¿F2 sería más torpe sin esta nota? Si no, sobra.

- **Paso 8 — Generar `prompts/F2-start.md`** desde `prompts/_template.md`, completando los hooks específicos al final con aprendizajes F1.

- **Paso 9 — Commit + push.**
  - Conventional commit: `feat(copilot-redesign-f1): provider pattern + discovery + first provider`.
  - Stage por nombre (nunca `git add -A`).
  - Push a `development`.
  - Reportar al usuario: 3 líneas + paths a `learnings/F1-provider-pattern.md` y `prompts/F2-start.md`.

Reglas no negociables:
- Branch único: `development`. Si no estás ahí, checkout antes.
- Brutal honestidad. Si el plan F1 no aplica por aprendizajes F0 → flagear y preguntar antes de actuar.
- No alucinar paths/símbolos. Leer archivos, no inventar.
- No tocar §3 (00-vision-and-non-goals.md). Si parece necesario → parar, preguntar.
- Native dev tools (lint/tests/type-check WSL, NUNCA `docker exec`).
- Spanish neutro LatAm en todo lo user-facing (`.claude/rules/spanish-text.md`).
- Stage por nombre (`git add path/file`), nunca `git add -A` (parallel-safety).

Empezá por el Paso 1 (re-lectura, especialmente learnings F0). Reportá en 3 líneas qué entendiste antes de avanzar al Paso 2.
```

---

## Hooks específicos para F1 (completados al cerrar F0)

### Aprendizajes F0 que F1 debe asumir

- **Package real es `deepagents`** (no `langchain-deepagents`). Si encontrás referencias al nombre viejo en `02-architecture-target.md` u otras fases, corregirlas en el commit F1.
- **`langchain-core 1.3.2`, `langchain 1.2.15`, `langgraph 1.1.9`, `langchain-anthropic 1.4.1`** instalados. F0 no corrió `/test-backend` full — F1 debe correrlo PRIMERO antes de tocar nada para detectar efectos laterales en sales_agent / analytics / crm.
- **`pyproject.toml` backend solo tooling**, deps en `requirements-runtime.txt`. Para discovery preferir convención (`src.modules.{name}.copilot_provider`) en vez de `[project.entry-points]` (más simple, no requiere bump packaging).
- **No tocar `domain/hooks/`, `domain/skills/`, `domain/rules/`, `domain/tools/`** — confirmados vivos en F0 (importados por main.py, event_cleanup, event_model, admin). Solo loaders + .md huérfanos eran dead.
- **Pre-existentes ignorables (NO arreglar en F1):**
  - `tests/modules/copilot/test_mutation_journal_repository.py` random-order fragility (aislado pasa).
  - TSC error `frontend/src/components/form-runtime/CollapsibleFieldGroup.tsx(32,18)` (commit `976123cd`).

### Tests baseline que F1 debe correr ANTES de empezar

```bash
cd backend
# Sanidad post-F0 (debe estar verde)
.venv/bin/ruff check src/ tests/ --no-cache
.venv/bin/pytest tests/architecture/ tests/modules/copilot/golden/ tests/modules/copilot/domain/ -q -o addopts=""

# CRÍTICO: full suite (F0 no lo alcanzó por slow tests)
.venv/bin/pytest -x --tb=short --timeout=30 -q
# o /test-backend si Chris lo pide
```

### Archivos clave que F1 modifica

- **Crea**: `backend/src/modules/copilot/domain/ports.py` (4 sub-ports + CopilotProvider root).
- **Crea**: `backend/src/modules/copilot/application/discovery.py` (loader runtime con convención `src.modules.{name}.copilot_provider`).
- **Crea por módulo (sugerido `brand` primero)**: `backend/src/modules/{brand}/copilot_provider/{__init__.py, tools.py, workflows.py, summary.py, context_inject.py}`.
- **Modifica**: `backend/src/modules/copilot/application/orchestrator/{graph.py, chat.py}` para consumir discovery en vez de imports directos.
- **Activa ratchet**: `backend/tests/architecture/test_no_new_copilot_module_imports.py` → `_RATCHET_FROZEN = True` cuando primer provider funcione end-to-end.

### Riesgos que vigilar en F1

- **Bump langchain-core 1.3** puede romper signature de `BaseTool`, `RunnableConfig`, o tool-calling en otros módulos no-copilot. El `/test-backend` baseline lo detecta.
- **`MODULE_REGISTRY` en `copilot/domain/`** queda obsoleto post-providers. NO eliminar el archivo hasta que TODOS los consumers de `get_module_registry()` queden migrados (golden snapshot `module_registry_shape.json` detecta drift).
- **Tools por provider** debe seguir respetando `ToolNameCollisionError`. No dup de nombres entre providers.
- **Ratchet agresivo**: post-flip, cualquier nuevo `from src.modules.X` desde copilot/ falla CI. Si F1 está en estado intermedio (algunos providers wired, otros no), documentar en learnings F1 cómo restar entradas del frozen set por wave.
