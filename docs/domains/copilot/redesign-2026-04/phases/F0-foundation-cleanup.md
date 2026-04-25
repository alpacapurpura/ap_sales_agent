# F0 — Foundation cleanup + baseline tests

**Pre-req:** ninguno.
**Sprints estimados:** 1.
**Bloquea:** F1 (provider pattern).
**Valor entregado:** dead code fuera del repo + golden snapshots de respuestas hoy + dependencia `langchain-deepagents` lista para F2.

---

## §1 Objetivo (claridad brutal)

Dejar el repo en estado "listo para rediseño" sin romper nada que funcione hoy. Eliminar lo confirmado dead, capturar baseline de comportamiento del copilot actual (para detectar regresiones en F1+), y dejar instalada la dep que F2 necesita.

**Esta fase NO refactoriza arquitectura.** Solo limpieza + instrumentación + baseline.

---

## §2 Pre-lectura obligatoria

Ver `03-phase-protocol.md` Paso 1.

Adicional para F0:

- `docs/domains/copilot/INDEX.md`
- `docs/domains/copilot/CONTRACT.md` + `CONTRACT-MULTIMODAL.md` (confirmar lo que está aprobado y NO se toca).
- `backend/src/modules/copilot/application/agents/style_analyzer/` (sospechoso dead).
- `backend/src/modules/copilot/application/agents/web_extractor/` (sospechoso dead).
- `backend/src/modules/copilot/infrastructure/context/context_loader_registry.py` (sospechoso dead).
- `backend/src/modules/copilot/infrastructure/context/offer_context_loader.py` (sospechoso dead).
- `backend/src/modules/copilot/skills/` + `infrastructure/skills_loader.py` (verificar uso real).
- `backend/src/modules/copilot/rules/` + `infrastructure/rules_loader.py` (verificar uso real).
- `backend/src/modules/copilot/domain/hooks/` + `infrastructure/in_memory_hook_registry.py` (verificar uso real).

---

## §3 Research mandate (abril 2026)

Queries WebSearch obligatorias:

- `langchain-deepagents pypi version April 2026 changelog`
- `langgraph compatibility deepagents 2026`
- `pytest snapshot testing LLM golden tests 2026 best practices`

Tessl tiles a verificar (usar skill `tessl-context`):

- `tessl__langgraph` — confirmar disponible y versión.
- Buscar tile relacionado a `deepagents`. Si no existe, confirmar como dep externa estándar.

Productos:

- Versión exacta `langchain-deepagents` a fijar en `pyproject.toml`.
- Compat verification con `langchain-core` y `langgraph` actuales del repo.

---

## §4 Lo que NO se toca (recordatorio crítico)

Ver `00-vision-and-non-goals.md §3`. Especialmente:

- Sidebar 3-state, multi-modal blocks, voice dual-mode, AssetsService, SSE v2, observability infra, context window builder, rolling summarizer, 4-tier router, `editable_fields`, `MODULE_REGISTRY`, `schema_introspection`, `navigation_map`, mutation_journal, anchor comments, tenant isolation.

---

## §5 Deliverables

### 5.1 Auditoría dead code

Para cada candidato sospechoso, ejecutar:

```bash
# en backend/
.venv/bin/python -c "import importlib; m=importlib.import_module('PATH'); print(m)"
# y rg para confirmar que NO hay imports vivos
rg "from src\.modules\.copilot\.application\.agents\.style_analyzer" backend/src/
rg "from src\.modules\.copilot\.application\.agents\.web_extractor" backend/src/
rg "context_loader_registry|offer_context_loader" backend/src/
rg "skills_loader|rules_loader" backend/src/
```

Para cada item:

- Si **0 imports vivos** + git log muestra última modificación > 60 días → eliminar (`git rm -r`).
- Si **imports en tests pero no en runtime** → eliminar tests + código.
- Si **imports activos pero comportamiento dudoso** → NO eliminar, dejar nota en learnings.

**Importante:** skills/rules/hooks pueden ser infraestructura embrionaria. Si están registrados pero nunca invocados por el graph → marcar como "frozen, decidir en F6".

### 5.2 Baseline golden tests del graph actual

Crear `backend/tests/modules/copilot/golden/`:

```
golden/
├── conftest.py                    # fixture de mock DB + mock LLM (deterministic)
├── snapshots/                     # golden outputs (.txt o .json)
└── test_baseline_conversations.py
```

Tests mínimos (10-15 conversaciones canónicas):

- Greeting simple en /brand-studio.
- Pregunta directa sin tools ("¿qué hace el copilot?").
- `propose_field_updates` único campo.
- `propose_field_updates` 3 campos.
- `get_module_data("brand")`.
- `get_module_data("offer")`.
- `get_funnel_metrics(period="7d")`.
- Trigger `extract_from_url` (mock ARQ dispatch).
- Trigger guided start_guided.
- Search knowledge_base con scope "all".
- Navigation tool → `/offer-studio/promise`.
- Conversation con 5 turnos (multi-turn context).

**Cada snapshot captura:**

- Lista de tool calls realizados (orden + args).
- Card kinds emitidos (`proposal`, `clarify_card`, etc.).
- Routing tier seleccionado.
- Texto final del assistant (semantic-similar OK, exact NO requerido — usar `pytest-approval-tests` o similar).

LLM mock: usar `LLMFactory.get_service()` con monkeypatch que devuelve respuestas fixtured deterministic. NO golpear OpenAI real en tests.

### 5.3 Instalación langchain-deepagents

```bash
cd backend
.venv/bin/pip install "langchain-deepagents==X.Y.Z"  # versión confirmada en research
# actualizar pyproject.toml + lock
```

**Smoke test (no funcional aún, solo importable):**

```python
def test_deepagents_importable():
    from langchain_deepagents import create_deep_agent  # noqa
```

Si `langchain-deepagents` requiere bump de `langchain-core` o `langgraph` → verificar compat con resto del código antes de aceptar.

### 5.4 Arch test prep para F1

Crear `backend/tests/architecture/test_no_new_copilot_module_imports.py` (skip-by-default, activable F1):

```python
# Captura el set actual de imports copilot ← módulos.
# F1 lo activa flipping `_RATCHET_FROZEN = True`.
```

Esto **no enforce nada en F0**, solo deja la base lista para F1.

### 5.5 Documentación

- Anchor comment nuevo en `backend/src/modules/copilot/__init__.py`:
  ```python
  # [COPILOT-REDESIGN-2026-04] → docs/domains/copilot/redesign-2026-04/README.md
  ```
- Update `docs/domains/copilot/INDEX.md` con link a `redesign-2026-04/`.

---

## §6 Quality gates

```bash
# Backend
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
cd backend && .venv/bin/ruff format --check src/ tests/
cd backend && .venv/bin/pytest -x -q --tb=short
cd backend && .venv/bin/pytest tests/architecture/ -x -q
cd backend && .venv/bin/pytest tests/modules/copilot/golden/ -x -q  # nuevos golden

# Confirmar imports limpios
cd backend && .venv/bin/python -c "from src.modules.copilot import *"

# Frontend (smoke)
cd frontend && npx tsc --noEmit
```

Adicional manual:

- Iniciar `/dev-up`, abrir browser, mandar 3 mensajes al copilot, confirmar SSE v2 + audio + history sidebar funcionan.

---

## §7 Riesgos específicos F0

| Riesgo | Mitigación |
|---|---|
| `langchain-deepagents` requiere bump grande de langchain-core | Si el bump rompe otros usos (sales_agent), aplazar dep a F2 y dejar nota. |
| Eliminar dead code rompe tests obscure | Correr suite completa antes de borrar definitivamente. |
| Golden tests muy frágiles (false positives) | Usar similarity threshold semántico, no exact match. Documentar threshold elegido. |
| Skills/rules/hooks resultan estar en uso latente | Si grep encuentra **cualquier** uso en runtime path, NO eliminar. |

---

## §8 Definición de hecho

- [ ] Dead code confirmado eliminado (con justificación 0-imports).
- [ ] Skills/rules/hooks loaders: estado documentado (vivos/frozen).
- [ ] `langchain-deepagents` instalado, versión fijada, smoke test verde.
- [ ] ≥10 golden tests baseline pasando.
- [ ] Anchor comment + INDEX.md actualizado.
- [ ] `/test-backend` verde.
- [ ] `/test-frontend` verde (smoke).
- [ ] Verificación manual en browser de que §3 (no tocar) sigue funcionando.
- [ ] `learnings/F0-foundation.md` completo.
- [ ] `prompts/F1-start.md` generado.
- [ ] Commit en `development`, push.

---

## §9 Notas para próxima fase F1

Al cerrar, en learnings dejar listo:

- Lista exacta de archivos eliminados (para que F1 no se confunda buscándolos).
- Versión `langchain-deepagents` fijada.
- Comando para correr golden tests rápido.
- Cualquier sorpresa sobre el estado actual del código relevante para provider pattern.
