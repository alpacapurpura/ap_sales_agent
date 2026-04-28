# Admin Migration Plan — sales_agent observability cutover

> **Generated 2026-04-28 in S00. Snapshot pre-S1 estado del Streamlit admin.**
>
> Plan para que `sales_audit.py` migre de `agent_trace_model` legacy → `sales_agent_trace_event` (event-sourced, S1) sin romper UI durante ventana dual-read.

---

## §1 · `sales_audit.py` shape actual

**File:** `backend/src/admin/modules/sales_audit.py` (179 LOC)
**Slug:** `auditoria` (PageSpec en `app.py:70`)
**Page wrapper:** `backend/src/admin/pages/auditoria.py` → llama `render_sales_audit_page()`

### Reads de `sales_agent` legacy

1. **Dropdown leads** — `AuditRepository.get_recent_users(tenant_id, limit=200)`:
   - JOIN `LeadModel` (CRM) + `MessageModel` o `AgentTrace` para `last_activity`.
2. **Timeline** — `AuditRepository.get_*_for_lead(...)`:
   - Lee `MessageModel`, `AgentTrace` (legacy), `LLMLogModel` (legacy).
3. **Sidebar "Ver Último Estado"** — query directo:
   ```python
   from src.modules.sales_agent.infrastructure.models.agent_trace_model import AgentTrace
   repo.db.query(AgentTrace).filter(AgentTrace.user_id == lead_id).order_by(...desc()).first()
   ```
4. **Sidebar "Ver Perfil"** — lee `lead.profile_data`, `lead.key_objections_history`, `lead.conversation_summary` (todo CRM, no sales_agent).
5. **"🗑️ Limpiar Conversación"** — `AuditRepository.clear_user_history(lead_id, tenant_id)`:
   - Borra: `MessageModel`, `AgentTrace`, `LLMLogModel`, `AgentStateCheckpoint` para el lead. Resetea scores en `LeadModel`.

### Dependencias rotas si `agent_trace_model` se borra hoy

- Sidebar "Ver Último Estado": rompe (import directo del modelo).
- Timeline: degrade — solo `MessageModel` queda; pierde nodos LangGraph + LLM logs.
- Dropdown leads: degrade — fallback a `MessageModel.last_activity` queda OK.
- Clear conversation: rompe (intenta borrar tabla inexistente).

---

## §2 · Migration path post-S1 (dual-read window)

### Fase A — S1 ship (semana 1)

S1 crea tablas nuevas + dual-write:
- `sales_agent_trace_event` (escrito por `SalesAgentCallbackHandler`).
- `sales_agent_llm_call` (escrito por callback handler).
- `sales_agent_routing_log`.

Legacy `@trace_node` + `LLMLogModel` siguen escribiendo en paralelo durante 4 semanas.

`sales_audit.py` durante esta fase **no cambia** — sigue leyendo legacy. Sin riesgo.

### Fase B — Dual-read en sales_audit.py (semana 1, mismo S1 sprint)

Patch `sales_audit.py` para leer **ambas fuentes**, deduplicando por `turn_id`:

```python
def render_timeline(repo: AuditRepository, lead_id: str, tenant_id: str) -> None:
    legacy = repo.get_legacy_trace_rows(lead_id, tenant_id)        # AgentTrace + LLMLogModel
    new = repo.get_event_sourced_rows(lead_id, tenant_id)          # sales_agent_trace_event + _llm_call

    if new and legacy:
        st.info(
            "Leyendo trazas event-sourced (preferido). "
            "Legacy mostrado como fallback."
        )
        rows = _merge_dedupe(new=new, legacy=legacy, key="turn_id")
    elif new:
        rows = new
    else:
        rows = legacy

    _render_rows(rows)
```

**Sidebar "Ver Último Estado":** durante dual-read, preferir `sales_agent_trace_event` `event_type='turn_end'` ordenado desc; fallback a `AgentTrace` legacy si no hay nuevo.

**Métricas dual-read:** S1 reconciliation worker compara escrituras legacy vs event-sourced. Diff <1% es criterio cutover (4 semanas observación).

### Fase C — Cutover (S6, post-4-semanas-verde)

`sales_audit.py` borra:
- Import directo `from src.modules.sales_agent.infrastructure.models.agent_trace_model import AgentTrace`.
- Branch `legacy` en dual-read.
- Cualquier query a `LLMLogModel`.

Solo queda lectura de `sales_agent_trace_event` + `sales_agent_llm_call`.

Migration drop tablas legacy (`agent_trace_model` + `LLMLogModel`) ejecutada en S6 (ver `phases/S6-fitness-tests-ratchet.md` step 9).

### Fase D — Arch test gate

`tests/architecture/test_admin_no_legacy_table_reads.py` (creado en S6):
- AST scan: `backend/src/admin/modules/sales_audit.py` no importa `AgentTrace` ni `LLMLogModel`.
- Falla CI si alguna page admin reintroduce import.

---

## §3 · Nuevas pages requeridas post-S1

S1+ habilita observability event-sourced cross-agent (`agent_kind` discriminator). Necesitamos pages dedicadas:

### `auditoria-v2` (S1, opcional — si dual-read en `auditoria` no alcanza)

Razón: dual-read en `auditoria` puede saturarse cuando ventana 4 sem termina y queremos mantener historial legacy lectura-only por compliance.

Decisión preliminar: **no crear `auditoria-v2`** — extender `auditoria` con dual-read es suficiente.

### `costo-sales` (S2)

Mirror de `costo-copilot`. Lee `sales_agent_llm_call` agregado por ciclo billing 25-25.

- `PageSpec(slug="costo-sales", title="Costo Sales Agent", icon="💵")`
- `pages/costo-sales.py` thin wrapper.
- `modules/costo_sales.py::render_costo_sales()`.

Implementation reusa `BillingCycleService` (movido a shared en S0/S1) parametrizado con `agent_kind='sales_agent'`.

### `costo-agentes` (S2, alternativa unificada)

Mirror unificado: ambos copilot + sales en una sola page. Lee `mv_daily_llm_cost_per_tenant_v2` (cross-agent MV de S2).

- `PageSpec(slug="costo-agentes", title="Costo Agentes (cross)", icon="📊")`
- Page deprecará `costo-copilot` post-cutover (rename suave: `costo-copilot` queda alias por 1 release).

**Decisión:** S2 implementa `costo-agentes` cross-agent. `costo-copilot` se mantiene durante 1 release y se borra cuando dashboards externos migren.

### `sales-routing` (S4, posterior)

Mirror de `copilot-routing`. Muestra distribución provider/model + tier para sales_agent_routing_log.

- `PageSpec(slug="sales-routing", title="Routing Sales Agent", icon="🧭")`

Defer a S4 cierre.

### `sales-quality` (S10)

Dashboard de eval loop sales (judge multi-rubric + goldens).

- `PageSpec(slug="sales-quality", title="Calidad Sales Agent", icon="🎓")`

Defer a S10.

---

## §4 · `_shared.py` extensions

`backend/src/admin/modules/_shared.py` actualmente expone:
- `render_tenant_selector(key, allow_all)` — selector.
- (helpers SQL, flags).

Extensions requeridas post-S1+:

### `render_agent_kind_selector(key="agent_kind") -> str`

Selector `copilot` vs `sales_agent` para pages cross-agent (`costo-agentes`, futuras).

```python
def render_agent_kind_selector(key: str = "agent_kind", *, default: str = "sales_agent") -> str:
    return st.selectbox(
        "Agente",
        options=["sales_agent", "copilot"],
        index=0 if default == "sales_agent" else 1,
        key=key,
    )
```

### `query_cross_agent_costs(tenant_id, cycle_start) -> dict[str, dict]`

Helper común para `costo-agentes`:

```python
def query_cross_agent_costs(
    tenant_id: UUID, cycle_start: date
) -> dict[str, dict]:
    """Returns {'copilot': {...}, 'sales_agent': {...}} con cost_usd/calls/turns."""
```

### `render_dual_read_banner(legacy_count: int, new_count: int)`

UI helper común para dual-read window (reutilizable en `auditoria` y futuras):

```python
def render_dual_read_banner(legacy_count: int, new_count: int) -> None:
    if new_count > 0 and legacy_count > 0:
        st.info(
            f"Dual-read window — leyendo nuevo ({new_count}) + legacy ({legacy_count}). "
            "Cutover programado al cerrar ventana de 4 semanas."
        )
    elif legacy_count > 0 and new_count == 0:
        st.warning(
            "Solo legacy disponible para este lead. "
            "Trazas anteriores a S1 cutover."
        )
```

---

## §5 · Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| Dual-read query lenta (timeline largo) | Index en `sales_agent_trace_event(tenant_id, lead_id, started_at)`. EXPLAIN ANALYZE en S1. |
| Cutover prematuro borra trazas legacy y rompe queries históricas | Mantener `agent_trace_model` 90d post-cutover (read-only) antes de DROP. Migration drop S6 sólo si `last_legacy_write` >30 días atrás. |
| `clear_user_history` no borra event-sourced rows | S1 extender `AuditRepository.clear_user_history` para borrar `sales_agent_trace_event` + `sales_agent_llm_call` también. |
| Sidebar "Ver Último Estado" rompe en dual-read si new tabla vacía para lead histórico | Branch fallback: si new vacío → leer legacy. Test cubre ambos casos. |
| Admin smoke test rompe post-S1 si conftest no mockea nuevas tablas | Editar `tests/admin/conftest.py` cuando se agreguen repos nuevos (regla `admin-panel.md`). |

---

## §6 · Action items checklist

S1:
- [ ] Crear `sales_agent_trace_event` + `_llm_call` + `_routing_log` (Alembic idempotente).
- [ ] `SalesAgentCallbackHandler` heredando `BaseAgentCallbackHandler` (S0).
- [ ] Dual-write 4 semanas.
- [ ] Reconciliation worker.
- [ ] `sales_audit.py` dual-read patch.
- [ ] Extender `AuditRepository` con `get_event_sourced_rows()` + dual `clear_user_history`.
- [ ] Extender `tests/admin/conftest.py` con mocks de tablas nuevas.

S2:
- [ ] `mv_daily_llm_cost_per_tenant_v2` cross-agent MV.
- [ ] `costo-agentes` page + `_shared.render_agent_kind_selector`.

S6:
- [ ] Cutover dual-read en `sales_audit.py` (drop branch legacy).
- [ ] Migration drop `agent_trace_model` + `LLMLogModel` (idempotente, post 30d gracia).
- [ ] `tests/architecture/test_admin_no_legacy_table_reads.py`.
- [ ] `tests/architecture/test_no_legacy_agent_trace_reads.py`.

S4 / S10:
- [ ] `sales-routing` page (S4).
- [ ] `sales-quality` page (S10).

---

## Anchor

Cualquier cambio al admin panel relacionado a sales_agent → revisar este doc + `.claude/rules/admin-panel.md`. Si la realidad diverge → actualizar §1-4.
