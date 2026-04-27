# Phase 3 — Research Checklist

**Objetivo:** confirmar best practices vigentes para reporting + PII en LLM observability.

**Tiempo estimado:** 20-30 min.

---

## 1. Postgres MV vs continuous aggregate (2026)

**Por qué importa:** decisión MV plain vs TimescaleDB continuous aggregate.

**Verificar:**
- WebSearch → "postgres materialized view refresh concurrently performance 2026"
- WebSearch → "timescaledb continuous aggregate vs materialized view 2026"
- Confirmar que para volumen actual (<5M calls/mes) MV plain con `REFRESH CONCURRENTLY` hourly es suficiente.

**Si volumen mayor proyectado:** considerar adoptar TimescaleDB. Anotar en `learnings.md`.

---

## 2. Microsoft Presidio Spanish recognizers status (2026)

**Por qué importa:** PII redaction depende de Presidio NER para español.

**Verificar:**
- WebFetch → https://microsoft.github.io/presidio/
- WebSearch → "presidio-analyzer spanish recognizer 2026"
- WebSearch → "presidio LATAM phone number recognizer"
- Confirmar:
  - Presidio v2.x soporta `nlp_engine` con spaCy `es_core_news_md` o `es_dep_news_trf`.
  - Recognizers built-in para EMAIL, PHONE, CREDIT_CARD funcionan en español.
  - Si falta recognizer para DNI/CURP/RUC LatAm → custom recognizer pattern.

**Decisión:** si Presidio sincrónico es < 100ms → usar en recorder. Si es > 100ms → solo regex sincrónico + Presidio en worker async.

---

## 3. Streamlit data viz patterns 2026

**Por qué importa:** dashboard usable.

**Verificar:**
- Leer páginas existentes en `backend/src/admin/modules/` que ya usan Plotly/charts (ej. `copilot_routing.py`, `copilot_quality.py`) — imitar pattern.
- WebSearch → "streamlit st.dataframe vs st.data_editor 2026" (decidir cuál para tabla con sort/filter).
- WebSearch → "streamlit plotly stacked bar chart cost analysis 2026".

**Criterio:** elegir pattern compatible con stack actual del admin.

---

## 4. Frankfurter API (re-verificar)

Si no se confirmó en Fase 1 (caso edge) → verificar ahora antes de FX flow.

---

## 5. Verificar `tenant_billing_config` poblada

```sql
SELECT COUNT(*), COUNT(*) FILTER (WHERE flat_fee_amount IS NOT NULL) FROM tenant_billing_config;
```

Si tabla vacía → necesitamos task de bootstrap en Fase 3 que crea config default por tenant existente. Anotar en plan/learnings.

---

## 6. Verificar `copilot_llm_call` poblada

```sql
SELECT COUNT(*), MIN(created_at), MAX(created_at) FROM copilot_llm_call;
SELECT tenant_id, COUNT(*), SUM(cost_usd) FROM copilot_llm_call GROUP BY tenant_id ORDER BY 3 DESC;
```

Para que el dashboard muestre data real durante development. Si volumen muy bajo → considerar seed con script de smoke pre-lanzamiento.

---

## 7. Verificar fecha + sesiones paralelas

```bash
date
git status --short
```

Sesiones paralelas en archivos del admin (`backend/src/admin/`)? Si sí → coordinar.

---

## Output del research

Bloque al inicio de `learnings.md`:

```markdown
## Research findings (executed YYYY-MM-DD)

### Postgres MV vs TimescaleDB
- Decisión: ...
- Razón: ...

### Presidio Spanish recognizers
- Status: ...
- Latencia medida (si aplica): ...
- Decisión: [sincrónico / async-only] ...

### Streamlit viz pattern
- Pattern elegido: ...

### Frankfurter API
- Status: ...

### tenant_billing_config bootstrap
- Tenants existentes: N
- Acción: [poblar todos con default / dejar opcional] ...

### copilot_llm_call data volume
- Rows: N
- Tenants con data: N
- Suficiente para dashboard real: [sí/no]

### Sesiones paralelas
- backend/src/admin/: ...

### Cambios al diseño respecto a ARCHITECTURE.md
- (vacío si nada)
```
