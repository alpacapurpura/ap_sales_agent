# F9 — Quality + Observability

**Pre-req:** F2-F8 cerradas.
**Sprints estimados:** 1.
**Valor entregado:** detectas degradación antes que el user. Confianza para evolucionar el copilot sin romper.

---

## §1 Objetivo

1. Golden tests semánticos para 20 conversaciones canónicas, corren weekly en CI.
2. Trace recorder completo: todos los nodes emiten `node_enter`/`node_exit`.
3. Admin Streamlit dashboard `/copilot/quality` con LLM-as-judge eval.
4. Eval framework por workflow (KPIs: completion rate, accept rate, satisfaction proxy).

---

## §2 Pre-lectura específica

- Trace recorder existing (`copilot/application/observability/trace_recorder.py`).
- Admin panel rule (`.claude/rules/admin-panel.md`).

---

## §3 Research mandate (abril 2026)

Queries WebSearch:

- `LLM-as-judge eval framework 2026 best practices`
- `LangChain evaluation patterns deep agents 2026`
- `golden tests semantic similarity LLM regression 2026`

Productos:

- LLM-judge prompt template.
- Threshold de similarity semántico para golden tests.

---

## §4 Deliverables

### 4.1 Golden tests semánticos

`backend/tests/quality/golden/`:

- 20 conversaciones canónicas extendidas (8 categorías):
  - URL contextual, Q&A simple, Q&A complejo, design offer, audit funnel, brand setup, multi-channel synth, error recovery.
- Cada test: input fijado, output evaluado por LLM-judge contra rúbrica.
- Threshold ≥85% similarity semántica.

### 4.2 Trace events completos

Cada node del deep agent + cada node de subagent emite `node_enter` + `node_exit` con preview I/O.

### 4.3 Admin dashboard

Página `/admin/copilot/quality`:

- Sample 50 conversaciones random últimos 7 días.
- LLM-judge auto-eval (utility, accuracy, brand_coherence, tone) sobre sample.
- Distribución scores.
- Top errores / abandons.
- Filter por workflow_id.

### 4.4 Eval framework workflows

Por workflow:

- Completion rate (% finished / started).
- Avg turns to completion.
- Accept rate (% propose_field_updates accepted).
- Abandon points (donde el user para).

Telemetry tabla nueva `copilot_workflow_metric`.

### 4.5 Weekly cron

GitHub Actions o ARQ scheduled:

- Corre golden semánticos.
- Sample 20 conversaciones reales (anonimizadas) → LLM-judge.
- Reporte a Slack / email.

---

## §5 Quality gates

- 20 golden semánticos verdes.
- Dashboard operativo con data real.
- Weekly cron triggered una vez sin error.

---

## §6 Definición de hecho

- [ ] Golden tests semánticos en CI.
- [ ] Trace events completos.
- [ ] Admin dashboard.
- [ ] Eval framework + tabla.
- [ ] Weekly cron.
- [ ] `learnings/F9-quality.md` + `prompts/F10-start.md`.
