# F5 — `ask_tenant_data` subgraph

**Pre-req:** F1 (provider repos enriquecidos), F2 (subagentes).
**Sprints estimados:** 2.
**Valor entregado:** salto cualitativo grande. Usuario pregunta "dame resumen del programa propósito-prosperidad para WhatsApp" o "cuántas personas escribieron esta semana" → obtiene respuesta directa.

---

## §1 Objetivo

Tool `ask_tenant_data(question, output_channel="chat")` que dispara subgraph (text-to-SQL agentic, descompuesto en nodos especializados):

```
intent_classifier (NANO) → entity_resolver (pg_trgm) → query_builder (MINI)
  → executor (repo del provider) → state_check → synthesizer (MINI, channel-aware)
```

NO toca SQL crudo. Usa repos del provider correspondiente (mantiene tenant_isolation + DDD).

---

## §2 Pre-lectura específica

- `02-architecture-target.md §6`.
- `learnings/F1-*.md` y `learnings/F2-*.md`.
- Repos existentes: `OfferRepository`, `CrmContactRepository`, `ConversationRepository`.

---

## §3 Research mandate (abril 2026)

Queries WebSearch:

- `text-to-SQL agentic LangGraph production 2026 entity resolution`
- `postgres pg_trgm fuzzy search LIKE similarity 2026 best practices`
- `LLM intent classification natural language queries Spanish 2026`
- `LangGraph subagent decomposed nodes data retrieval 2026`

Tessl tiles:

- `tessl__fastapi`, `tessl__langgraph`.

Productos:

- Patrón nodos descompuestos (input/output schema).
- Estrategia cache (Redis TTL 60s para queries frecuentes).
- pg_trgm threshold para fuzzy match (similarity > X).

---

## §4 Lo que NO se toca

- Repos existentes — solo se enriquecen con métodos `search()` adicionales, sin breaking.
- Tenant isolation.
- Channel formatter (es F7 — F5 puede preparar interface, F7 implementa).

---

## §5 Deliverables

### 5.1 Tool entry point

`backend/src/modules/copilot/application/tools/ask_tenant_data.py`:

```python
@tool
async def ask_tenant_data(question: str, output_channel: str = "chat") -> dict:
    """Answer natural-language questions about tenant's data."""
```

Spawn subagent `data_query` con isolation.

### 5.2 Subagent `data_query`

`backend/src/modules/copilot/application/subagents/data_query.py`:

Nodos:

#### intent_classifier
NANO. Output structured: `kind` ∈ {offer_lookup, lead_count, conversation_metric, revenue, mixed, unknown}.

#### entity_resolver
- Si kind requires entity (offer_lookup, conversation_metric for specific channel, etc.).
- Postgres `similarity(name, query) > 0.3` via pg_trgm extension.
- Migration adicional: `CREATE EXTENSION IF NOT EXISTS pg_trgm; CREATE INDEX ... USING gin (name gin_trgm_ops);`.

#### query_builder
MINI. Genera structured query plan (filters, since/until parseado en español: "esta semana"=current ISO week, "últimos 7 días", "marzo", "Q1", etc.).

#### executor
- Pickea repo correcto del provider activo (vía discovery F1).
- Ejemplo: `kind=offer_lookup` → `OfferRepository.search(...)`.
- Devuelve raw rows.

#### state_check
- Si entity inactive/archived/published_at null → flag.
- Para counts: si 0 results → propone próximo paso.

#### synthesizer
MINI. Channel-aware (F7 wires registry; F5 acepta channel param + structure básica).

### 5.3 Repos enrichment

Cada provider expone:

- `OfferRepository.search(name_like=None, status=None, since=None, limit=20)`.
- `CrmContactRepository.count_inbound(since, until, channel=None)`.
- `ConversationRepository.search(period, channel=None, status=None)`.

Tests por método.

### 5.4 Cache

Redis cache wrapper:

- Key: `ask:{tenant_id}:{hash(question)}:{channel}`.
- TTL 60s.
- Invalidate por tenant on relevant CRUD (best-effort).

### 5.5 Tests

- Unit por nodo (intent_classifier, entity_resolver, etc.).
- Integration: `ask_tenant_data("cuántas personas escribieron esta semana")` → respuesta con número correcto.
- Integration: `ask_tenant_data("resumen del programa propósito-prosperidad")` → fuzzy match offer + summary.
- Edge: query ambigua → state_check pide clarify.
- Edge: 0 resultados → respuesta sugerente.

---

## §6 Quality gates

- `/test-backend` verde.
- Migration pg_trgm idempotente verificada.
- Manual: 10 queries reales en español neutro responden coherente.
- LLM-judge sample: ≥85% accuracy sobre 50 queries (preliminar; medición real en F9).

---

## §7 Riesgos

| Riesgo | Mitigación |
|---|---|
| pg_trgm requiere migration que demora en prod | Idempotente + verificar en clone DB. |
| Intent classifier confunde categorías | Few-shot examples con casos reales. Telemetría. |
| Date parsing español falla edge cases | Lib `dateparser` + tests con casos LatAm ("ayer", "antier", "esta semana", "marzo", "Q1 2026"). |
| LLM genera SQL en lugar de usar repos | NO permitir SQL crudo. Repos como única vía. |

---

## §8 Definición de hecho

- [ ] Tool entry + subagent funcional.
- [ ] Nodos descompuestos con tests unit.
- [ ] Repos enriquecidos.
- [ ] pg_trgm migration aplicada.
- [ ] Cache Redis operativo.
- [ ] LLM-judge baseline >75%.
- [ ] `learnings/F5-ask-tenant-data.md` + `prompts/F6-start.md`.
