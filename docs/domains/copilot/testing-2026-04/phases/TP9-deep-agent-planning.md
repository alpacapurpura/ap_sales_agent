# TP9 — Deep Agent Harness + Planning (F2)

**F# que valida:** F2 (`langchain-deepagents` harness + `write_todos` tool + scratchpad + subagentes).
**Tiempo estimado:** 3 hs.
**Pre-req hard:** TP0 + TP1.

---

## Misión

Confirmar que:

1. `write_todos` tool emite `plan_card` con todos visibles en UI cuando tarea es multi-step.
2. Scratchpad (read_file/write_file/edit_file/ls/glob/grep) funciona dentro del turn sin cross-conversation leak.
3. Subagentes (`audit_inspector`, `url_analyzer`, `data_query`) corren aislados y devuelven a parent agent.
4. Tareas chicas NO disparan write_todos (no over-engineering).
5. Spanish neutro LatAm respetado en plan_card content (regla 11).

---

## Research mandate

Queries:

- `"langchain deepagents 2026 latest version changelog"` — verificar version + bugs known.
- `"agent planning visible plan card UX 2026 patterns"` — best practices render plan UI.
- `"subagent isolation context window 2026 langchain"` — confirmar isolation pattern sigue siendo el correcto.

---

## Scenarios

### S9.1 — Tarea chica NO dispara write_todos

Prompt: `"hola, ¿cómo estás?"`.

```sql
SELECT name FROM copilot_trace_event
WHERE turn_id=:tid AND event_type='tool_call' AND name='write_todos';
```

**Pass:** 0 rows. write_todos NO se llama.

### S9.2 — Tarea grande SÍ dispara write_todos

Prompt: `"audita mi marca completa, revisá brand identity + offers + connections + leads, dame 5 recomendaciones priorizadas"`.

**Pass:** 1+ rows write_todos. plan_card emitido (event `card_emitted` con `card_kind='plan_card'`).

### S9.3 — plan_card render en UI

Browser flow Chrome DevTools:
- Disparar S9.2.
- Esperar plan_card aparecer.
- Screenshot DOM.

Heurística:
- Cada todo visible.
- Status (pending / in_progress / completed) cambia visiblemente.
- No flash-of-empty.

**Pass:** 5+ todos visibles + status updates en tiempo real.

### S9.4 — Scratchpad funciona

Prompt forzado: `"escribí un draft largo en tu scratchpad y después léelo"`.

```sql
SELECT name FROM copilot_trace_event
WHERE turn_id=:tid AND event_type='tool_call' AND name IN ('write_file','read_file');
```

**Pass:** ≥2 rows (write + read).

### S9.5 — Scratchpad NO cross-conversation

Conv A: agent escribe `notes.md`.
Conv B (nuevo conv id): agent intenta `read_file('notes.md')` → no encuentra (filesystem aislado por turn).

**Pass:** Conv B `read_file` returns "file not found".

### S9.6 — Subagent `audit_inspector` corre

Prompt: `"hacele un audit rápido a mi sección de identity"`.

**Pass:** trace muestra `task` tool call + subagent invoked + report devuelto al main agent.

### S9.7 — Subagent `url_analyzer` corre con URL

Prompt: `"analizá esta URL como inspiración: https://stripe.com/payments"`.

**Pass:** url_analyzer subagent corre + persiste inspiration. Diferente a `fetch_url` directo (TP3) — éste es subagent dispatch.

### S9.8 — plan_card spanish neutro

S9.2 plan_card payload:
```python
import re
VOSEO = re.compile(r'\b(querés|tenés|podés|sabés|hacés|venís|decís|mirá|dejá|poné|usá|hacé|elegí|seleccioná|arrancá|empezá|agregá|configurá|revisá|escribí|guardá)\b')
for todo in plan_card.payload.todos:
    assert not VOSEO.search(todo.content)
    assert not VOSEO.search(todo.active_form)
```

**Pass:** 0 voseo en plan_card content.

### S9.9 — Latencia HEAVY + planning

Medir total turn latencia para S9.2 (audit completo):

**Pass:** p50 ≤8s, p95 ≤20s. Hard fail >30s.

### S9.10 — Cost HEAVY tier

S9.2 cost calc (HEAVY model = Opus pricing):

**Pass:** ≤$0.05 per turn (target `03-metrics-and-targets.md`).

---

## Tools / queries

- DeepEval `TaskCompletionMetric` para multi-step.
- Chrome DevTools MCP para S9.3.
- SQL: `copilot_trace_event` con filtros tool_call.

---

## Targets

| Métrica | Target | Hard fail |
|---|---|---|
| write_todos para multi-step | 100% (S9.2) | 0% |
| write_todos NO para tarea chica | 100% (S9.1) | 1+ false positives |
| plan_card render OK | OK | flash-of-empty |
| Scratchpad isolation | OK cross-conv | leak detected |
| Subagent invocations | OK | crash bubbleado |
| plan_card neutro | 0 voseo | ≥1 voseo |
| HEAVY p50 latencia | ≤8s | >30s |
| HEAVY cost | ≤$0.05 | >$0.20 |

---

## Failure playbook

| Síntoma | Investigar | Root cause | Fix |
|---|---|---|---|
| write_todos siempre disparado (over-eager) | LLM prompt en deep_agent suffix | `_DEEP_AGENT_SUFFIX_ES` | refinar "tareas chicas: respondé sin write_todos" |
| plan_card no renderea | block_append missing | `_maybe_emit_plan_card` | check trace muestra card_emitted |
| Scratchpad cross-leak | StateBackend mal configurado | `deep_agent.py::create_deep_agent` config | force fresh state per turn |
| Subagent crash | llm timeout | `astream_events` timeout | bumpar `COPILOT_STREAM_TIMEOUT_SECONDS` |
| voseo en plan_card | LLM ignoró regla | suffix prompt | bumpear strength + `[COPILOT-NEUTRO]` anchor |

---

## Lo que necesito de Chris

- [ ] Tenant test con datos suficientes para audit (brand + 1+ offers + 1+ connections).
- [ ] Confirmar `langchain-deepagents` version pinneada (`pip show deepagents`).
