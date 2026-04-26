# TP5 — Workflows Runtime Unification (F6)

**F# que valida:** F6 (`Workflow` declarative + `WorkflowEngine` + dual-read fallback `procedure_state ↔ workflow_state`).
**Tiempo estimado:** 2 hs.
**Pre-req hard:** TP0 + TP4 + tenant test con brand vacío + offer vacío (para correr setup completos).

---

## Misión

Confirmar que:

1. Pilot workflows (`setup_brand_minimal`, `design_offer_from_url`) corren end-to-end sin crash.
2. State persiste en `workflow_state` JSONB (con dual-read fallback `procedure_state` para conv legacy).
3. Coexistencia 4 sistemas (guided + procedure + extraction_card_flow + Workflow nuevo) no se pisan.
4. Reanudar conv interrumpida levanta del nodo correcto.
5. UX consistente entre los 2 pilots (mismo render de cards, mismo timing, mismo wording de errores).

---

## Research mandate

Queries:

- `"langgraph multi-step workflow state persistence resume 2026"` — confirmar patrón JSONB + dual-read sigue siendo aceptado.
- `"agent workflow declarative vs imperative tradeoffs 2026"` — ver si la decisión F6 sigue siendo defensible.
- `"workflow engine python lazy handler resolution 2026"` — confirmar `importlib` lazy sigue siendo el approach (vs eager imports).

---

## Scenarios

### S5.1 — `setup_brand_minimal` happy path

Tenant fresco. Disparar workflow desde UI o API:
```
"ayudame a configurar mi marca desde cero"
```

Expected:
- LLM detecta intent → workflow `setup_brand_minimal` se inicia.
- Cards aparecen secuencialmente: probe → ask_next_section → finalize_summary.
- Al cerrar, `brand_identity` table tiene mínimo viable populated.
- `workflow_state` JSONB con `workflow_id='setup_brand_minimal'` + `current_node` updated.

```sql
SELECT workflow_state FROM copilot_conversations WHERE id=:cid;
SELECT * FROM brand_identity WHERE tenant_id=:uuid;
```

**Pass:** brand_identity con `name` + `voice_tone` + `narrative` mínimos. workflow_state con `is_complete=true` o equivalent.

### S5.2 — `design_offer_from_url` happy path

```
"diseñá una oferta inspirada en https://example.com/landing-curso"
```

Expected: workflow inicia → fetch_url → extract → propose offer fields → user accepts → offer creado.

**Pass:** new offer row + workflow_state completo.

### S5.3 — Reanudar workflow interrumpido

S5.1 in-flight. Cerrar conversation. Re-abrir 30 min después: `"sigamos con la marca"`.

**Pass:** workflow resume desde `current_node` exacto donde quedó. NO reinicia.

### S5.4 — Coexistencia con guided runner

Conv NUEVA (post-F6). Disparar guided flow (legacy `procedure_state`).

```sql
SELECT procedure_state, workflow_state FROM copilot_conversations WHERE id=:cid;
```

**Pass:** uno de los dos populated, NO ambos al mismo tiempo (a menos que F12 cutover esté activo).

### S5.5 — Coexistencia con extraction_card_flow

Pegar doc PDF como adjunto. Extraction job dispara.

**Pass:** `procedure_state.active_extraction_job` populated. Workflow_state NO interfiere.

### S5.6 — UX consistency entre pilots

Browser flow Chrome DevTools:
- S5.1 + S5.2 lado a lado.
- Comparar: tiempo entre cards, wording errores, render visual.

**Pass:** diferencias <20% en timing, wording sigue mismo template, render idéntico.

### S5.7 — Workflow falla → graceful

Force fail en handler (mock retorna `NodeOutput(error="db down")`).

**Pass:** workflow para, error message visible al user, NO crash silencioso. trace muestra `error` event.

---

## Tools / queries

- DeepEval: `tests/quality/deepeval/test_tp5_workflows.py` con `ConversationCompletenessMetric`.
- Chrome DevTools MCP para S5.6.
- SQL: `copilot_conversations.workflow_state`, `brand_identity`, `offers`.

---

## Targets

| Métrica | Target | Hard fail |
|---|---|---|
| Setup brand completion rate | ≥70% (sample 5 runs) | <40% |
| Design offer completion rate | ≥70% | <40% |
| Resume from interruption | OK | reinicia |
| Coexistence sin pisarse | OK | data corruption |
| UX consistency entre pilots | <20% diff | >50% diff |
| Latencia per nodo | ≤2s p50 | >8s |

---

## Failure playbook

| Síntoma | Investigar | Root cause | Fix |
|---|---|---|---|
| Workflow no inicia | LLM no llama tool | tool description vague | refinar `application/tools/workflows/` |
| State no persiste | repo update_workflow_state | `conversation_repository.py` | unit test path |
| Resume desde nodo wrong | dual-read fallback prefieren wrong | `get_workflow_state(..., fallback_to_procedure=True)` | F12 cutover acelera |
| Coexistencia rompe | escritor a ambas columnas | confirmar handler dual-write o single | depende de F12a estado |
| Card no aparece | block_adapters | `chat.py::_handle_tool_end_v2` | trace → ¿card_emitted event? |

---

## Lo que necesito de Chris

- [ ] Tenant fresco (sin brand, sin offer) — para correr S5.1 y S5.2 sin contaminación.
- [ ] URL real para S5.2 (landing de competidor o referencia).
