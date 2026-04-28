# S6.5 · Legacy drop + admin cutover

## Objetivo

Cierre formal de la ventana dual-write S1 (4 semanas, cumple 2026-05-26).
Drop tablas legacy `agent_trace_model` + `LLMLogModel`. Cutover de
`sales_audit.py` (drop branch dual-read). Activar arch tests que bloquean
re-introducción de los nombres.

## Trigger

**Reloj**: 2026-05-26 (4 semanas desde S1 close 2026-04-28).

**Pre-condición de ejecución**:

1. Reconciliation worker S1 reportó **diff < 1%** durante las últimas
   2 semanas consecutivas (verificar `reconciliation_runs` table).
2. `sales_agent_trace_event` + `sales_agent_llm_call` poblados continuamente.
3. `sales_audit.py` dual-read funciona (banner UI muestra ambos counts).

Si alguna falla → diferir 2 semanas + investigar drift.

## Dependencias

S6 cerrado (ratchet + sweeps + 6 arch tests fundacionales).

## Criterios de éxito

1. ✅ Migración Alembic idempotente que dropea `agent_traces` + `llm_logs`
   (raw SQL `DROP TABLE IF EXISTS`).
2. ✅ `sales_audit.py` borra:
   - import directo de `AgentTrace`,
   - branch `legacy` en dual-read,
   - cualquier query a `LLMLogModel`.
3. ✅ `AuditRepository.clear_user_history` borra solo `MessageModel` +
   `sales_agent_trace_event` + `sales_agent_llm_call` + `AgentStateCheckpoint`.
4. ✅ `tests/architecture/test_no_legacy_agent_trace_reads.py` activo
   sin allowlist — AST scan bloquea cualquier import de `agent_trace_model`
   o `llm_log_model`.
5. ✅ `tests/architecture/test_admin_no_legacy_table_reads.py` activo sin
   allowlist — `sales_audit.py` no importa AgentTrace/LLMLog.
6. ✅ `tests/architecture/test_no_future_annotations_in_langgraph_files.py`
   activo — bloquea `from __future__ import annotations` en
   `*/orchestrator/graph.py` files (cierra watchpoint S1).
7. ✅ Reconciliation worker `dual_write_reconciliation_task` desregistrado
   de `WorkerSettings.functions` + `SchedulerSettings.cron_jobs`.
8. ✅ Files `agent_trace_model.py` + `llm_log_model.py` borrados.
9. ✅ `infrastructure/monitoring/tracing.py` (decorator `@trace_node`) borrado.
10. ✅ Docs corregidos: `agent_log_model` → `LLMLogModel` references.
11. ✅ `make arch-test` global verde. Admin smoke verde.
12. ✅ Migration aplicada en clone DB + idempotent re-run = 0 cambios.

## Research mandate

### Queries WebSearch

1. `Alembic drop table production safe rollback strategy 2026` — best
   practices para drop irreversible.
2. `Postgres DROP TABLE active connections lock contention 2026`.

### Lectura obligatoria

- `audit/admin-migration-plan.md` §2 Fase C (cutover).
- `learnings/S1-sales-agent-observability-parity.md` (dual-write contract).
- `tests/architecture/test_no_new_copilot_module_imports.py` (pattern para
  los nuevos tests de bloqueo).
- `.claude/rules/backend-migrations.md` (idempotency + clone test).

### Hallazgos research

> COMPLETAR.

---

## Diseño

### Migration drop legacy

```sql
-- Alembic migration <NNN>_drop_legacy_agent_trace.py
-- Idempotente: el drop hace nothing si la tabla ya fue removida.

DROP TABLE IF EXISTS agent_traces CASCADE;
DROP TABLE IF EXISTS llm_logs CASCADE;
```

NOTA: `CASCADE` solo si `agent_traces`/`llm_logs` tienen FKs incoming
(verificar con `\d+` antes). Si no, omitir.

### Arch test pattern (sin allowlist)

```python
# tests/architecture/test_no_legacy_agent_trace_reads.py
FORBIDDEN_IMPORTS = (
    "src.modules.sales_agent.infrastructure.models.agent_trace_model",
    "src.modules.sales_agent.infrastructure.models.llm_log_model",
)

def test_no_imports_of_legacy_models() -> None:
    violations = []
    for py in REPO.rglob("*.py"):
        tree = ast.parse(py.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in FORBIDDEN_IMPORTS:
                violations.append(f"{py.relative_to(REPO)}:{node.lineno}")
    assert not violations, ...
```

```python
# tests/architecture/test_admin_no_legacy_table_reads.py
ADMIN_PATH = REPO / "backend" / "src" / "admin" / "modules" / "sales_audit.py"

def test_admin_does_not_import_legacy_models() -> None:
    src = ADMIN_PATH.read_text()
    forbidden_strings = ("AgentTrace", "LLMLog", "agent_trace_model", "llm_log_model")
    for forb in forbidden_strings:
        assert forb not in src, f"sales_audit.py reintrodujo legacy: {forb}"
```

```python
# tests/architecture/test_no_future_annotations_in_langgraph_files.py
LANGRAPH_FILES = (
    REPO / "src/modules/sales_agent/application/orchestrator/graph.py",
    # extender con copilot/orchestrator/graph.py si copilot también
    # introspecta runtime
)

def test_no_future_annotations_in_introspected_files() -> None:
    for path in LANGRAPH_FILES:
        src = path.read_text()
        assert "from __future__ import annotations" not in src, (
            f"{path.relative_to(REPO)}: __future__ annotations rompe LangGraph "
            "runtime introspection (ver learnings/S1)."
        )
```

## Plan TDD

1. RED: arch tests escritos contra el estado actual (post-S1 dual-read).
   Esperado: `test_no_legacy_agent_trace_reads` falla porque
   `sales_audit.py` aún importa `AgentTrace`. Confirma que el test
   detecta la condición.
2. Implementar cutover en `sales_audit.py` (drop import + branch legacy).
3. Re-correr → GREEN.
4. Migration drop tablas → aplicar → verificar idempotente en clone.
5. Borrar `agent_trace_model.py` + `llm_log_model.py` + `tracing.py`.
6. Re-correr arch tests + admin smoke + sales_agent tests.

## Implementación step-by-step

1. Verificar pre-condición reconciliation drift < 1%.
2. Crear arch test `test_no_legacy_agent_trace_reads.py` (RED).
3. Crear arch test `test_admin_no_legacy_table_reads.py` (RED).
4. Crear arch test `test_no_future_annotations_in_langgraph_files.py` (RED si aplica).
5. Cutover `sales_audit.py`: borrar dual-read branch, dejar solo lectura
   event-sourced. Smoke admin manual.
6. Borrar `infrastructure/monitoring/tracing.py` + `@trace_node` decorator.
7. Crear migración Alembic idempotente drop tablas.
8. Aplicar en clone DB + verificar idempotency.
9. Aplicar en dev.
10. Borrar files Python legacy (`agent_trace_model.py`, `llm_log_model.py`).
11. Desregistrar `dual_write_reconciliation_task` de workers settings.
12. Quality gates verdes.
13. Update tech debt log: FIXED entries para todas las deudas que estaban
    DEFERRED-cutover-window.

## Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| Drift cross-tenant > 1% al cumplir 4 sem | Diferir cutover 2 semanas + investigar. NO ejecutar drop. |
| Migration drop falla por FK incoming no documentada | Usar `CASCADE`. Pre-check con `\d+ agent_traces` en clone. |
| Admin smoke rompe post-cutover | Test admin smoke en CI debe verde antes de merge. Rollback fácil (Alembic downgrade NO recrea data — pero el cutover de admin sí es revertible). |
| Tenants enterprise con compliance exigen retention legacy | Mantener export pre-drop a S3/cold storage si emerge requirement. Documentar antes del drop. |

## Tech debt closure

Cierra estas entradas FIXED (con commit hash) en `05-tech-debt-log.md`:

- `[HIGH] Sales_agent sin retention policy` (S1) — retention worker S2 + drop legacy completa el ciclo.
- `[HIGH] Streamlit sales_audit.py lee tabla legacy` (S0) — cutover.
- `[LOW] agent_log_model mencionado en docs no existe` (S1) — cleanup docs.
- `[LOW] from __future__ import annotations rompe LangGraph` (S1) — arch test cierra el watchpoint.
- `[HIGH] Drop tablas legacy agent_trace_model + LLMLogModel` (S6) — cierra.
