# F6 — Workflow unificado

**Pre-req:** F1 cerrada. Paralelizable con F3/F7.
**Sprints estimados:** 2.
**Valor entregado:** un solo concepto `Workflow` reemplaza `guided` + `procedure` + `extraction_card_flow`. Cada provider declara workflows. Discovery los junta.

---

## §1 Objetivo

Fusionar 3 sistemas paralelos actuales en uno declarativo:

- `guided` (brand/offer setup)
- `procedure` (`brand_setup`, `offer_creation`, `first_setup`)
- `extraction_card_flow`

Resultado: clase única `Workflow`, estado en `copilot_conversations.workflow_state` (rename idempotente de `procedure_state`), registro vía provider, UI sidebar muestra progreso unificado.

---

## §2 Pre-lectura específica

- `02-architecture-target.md §3`.
- Código actual:
  - `copilot/application/guided/` (state, blocks).
  - `copilot/application/procedures/`.
  - `copilot/application/extraction_card_flow.py`.
- `learnings/F1-*.md` (provider API).

---

## §3 Research mandate (abril 2026)

Queries WebSearch:

- `LangGraph state machine workflow declarative 2026`
- `pydantic v2 state machine validation 2026`
- `adaptive clarify loop multi-step intake forms 2026`

Productos:

- Patrón state machine declarativo Python.
- Estrategia migración datos (`procedure_state` → `workflow_state`).

---

## §4 Lo que NO se toca

- UI sidebar 3-state.
- Card UI types existentes (extender params OK, romper NO).
- Tests existentes que cubren guided/procedure (deben seguir pasando con shim de compat hasta F8).

---

## §5 Deliverables

### 5.1 Domain

`backend/src/modules/copilot/domain/workflow.py`:

```python
@dataclass(frozen=True)
class WorkflowNode:
    id: str
    handler_ref: str                # "module.path:fn"
    next: str | "ConditionFn"
    timeout_s: int = 30

@dataclass(frozen=True)
class Workflow:
    id: str
    domain: str
    description_es: str
    trigger: WorkflowTrigger
    nodes: list[WorkflowNode]
    state_schema: type[BaseModel]
    ui_progress_kind: str
    max_clarify_questions: int = 5
```

### 5.2 Migration data

```sql
ALTER TABLE copilot_conversations
  RENAME COLUMN procedure_state TO workflow_state;
-- O si rename causa conflicto, columna nueva + backfill + drop.
```

Idempotente. Backfill verifica.

### 5.3 Provider workflows

Cada provider declara workflows en su `copilot_provider/workflows.py`:

- Brand: `setup_brand`.
- Offer: `setup_offer`, `design_offer_from_url`, `extract_to_offer_from_doc`.
- Landing, etc. (placeholder vacío si no aplica aún).

Discovery F1 los junta.

### 5.4 Adaptive clarify loop estandarizado

Componente `ClarifyLoopController`:

- State holds `pending_questions[]`, `answers{}`, `analysis_so_far{}`.
- Cada turn: LLM evalúa "suficiente?" → siguiente pregunta o "design_now".
- Cap `max_clarify_questions` (default 5).
- Reusable por todos los workflows.

### 5.5 UI

- Sidebar badge progreso unificado (`block_progress` o `plan_card` según `ui_progress_kind`).
- Eliminar lógica diferenciada FE entre guided/procedure/extraction.

### 5.6 Migration legacy → workflow

Backfill script:

- `procedure_state JSONB` → `workflow_state JSONB` (rename) + migrate `guided_state` (parte del old) a workflow_state con `id="setup_brand"` o `setup_offer`.
- `extraction_card_flow` instances → workflow `extract_to_*`.

Tests: 100% conversaciones legacy abren correctamente con workflow nuevo.

### 5.7 Feature flag

`WORKFLOW_V2_ENABLED` por tenant (override). Rollout gradual.

---

## §6 Quality gates

- `/test-backend` + `/test-frontend` verdes.
- Backfill corrido sin pérdida.
- Manual: completar setup_brand end-to-end con feature flag on.
- Smoke: extracción doc → workflow `extract_to_offer` ejecuta + clarify loop funciona.

---

## §7 Riesgos

| Riesgo | Mitigación |
|---|---|
| Backfill corrompe procedure_state legacy | Backup antes + dry-run en clone DB. |
| Clarify loop infinito | Cap duro + telemetría. |
| Tests existentes guided/procedure rompen | Shim de compat hasta F8. |

---

## §8 Definición de hecho

- [ ] Domain `Workflow` + tests.
- [ ] Migration rename + backfill.
- [ ] Workflows por provider (offer, brand min).
- [ ] ClarifyLoopController.
- [ ] UI unificada.
- [ ] Feature flag.
- [ ] `learnings/F6-workflow.md` + `prompts/F7-start.md`.
