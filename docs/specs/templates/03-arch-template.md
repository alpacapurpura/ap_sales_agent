# 03-arch-{be|fe|agentic}.md — Template

> Owner: `/architect-{be|fe|agentic}`. Documento técnico de UNA capa.
> Lo escribe el sub-architect correspondiente. El orchestrator `/architect` los reúne en `04-tickets.yaml`.

---
story_id: STORY_ID
surface: BE                                       # BE | FE | AGENTIC
sub_architect: /architect-be
arch_version: 1
last_modified: 2026-05-04T15:30Z
links:
  spec: "01-spec.md"
  ui_design: "02-design-ui.md"                    # solo si surface=FE
  agentic_design: "02-design-agentic.md"          # solo si surface=AGENTIC
  story_yaml: "../../../../../product/stories/{module}/{story-id}.yaml"
  domain_doc: "../../../../../domains/module_{module}.md"
  rules:
    - ".claude/rules/backend-ddd.md"
    - ".claude/rules/tenant-isolation.md"
    - ".claude/rules/backend-migrations.md"
---

## Decisión arquitectónica clave

[1 párrafo: qué se decidió, por qué (con tradeoffs).]

## Surface diff (BE)

### Endpoints nuevos / modificados

| Method | Path | Request DTO | Response DTO | Auth | Notas |
|---|---|---|---|---|---|
| POST | `/api/v1/{module}/{action}` | `RequestDTO` | `ResponseDTO` | clerk-jwt | tenant-scoped |

### DTOs

```python
# backend/src/modules/{m}/api/dtos.py
class RequestDTO(BaseModel):
    field_a: str
    field_b: int
    model_config = ConfigDict(...)

class ResponseDTO(BaseModel):
    id: UUID
    status: Literal["ok", "error"]
    model_config = ConfigDict(...)
```

### Domain entities / VOs

```python
# backend/src/modules/{m}/domain/{entity}.py
@dataclass(frozen=True)
class {Entity}:
    id: UUID
    tenant_id: UUID
    ...
```

### Migrations

```
alembic/versions/XXXX_{description}.py
- op.execute("CREATE TABLE IF NOT EXISTS ...")
- op.execute("ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...")
- op.execute("CREATE INDEX IF NOT EXISTS ...")
```

> **Verificación idempotencia:** correr migration 2x sin error.

### Servicios + Repos

| Componente | Path | Responsabilidad |
|---|---|---|
| `{Name}Service` | `application/services/` | Orquesta use case |
| `{Name}Repository` | `infrastructure/repositories/` | Persistencia |

### Eventos emitidos / consumidos

- Emite: `{Module}{Event}V1` → outbox pattern
- Consume: `{OtherModule}Event` → handler en `application/event_handlers/`

### Tests requeridos

- `tests/modules/{m}/test_{name}_service.py` — domain logic + happy/negative
- `tests/modules/{m}/test_{name}_endpoint.py` — contract test + tenant isolation
- `tests/modules/{m}/test_{name}_migration.py` — migration idempotency
- Coverage minimum: 60% del módulo (no debe bajar)

## Surface diff (FE)

### Routes nuevas / modificadas

| Path | Component | Type |
|---|---|---|
| `/[module]/[section]` | `{Section}Page.tsx` | Server Component |
| `/[module]/[section]/edit` | `{Section}EditClient.tsx` | Client Component |

### Features (FSD-Lite)

```
frontend/src/features/{module}/
├── api/use-{action}.ts              # React Query hook
├── components/{Component}.tsx
├── schemas/{action}-schema.ts        # Zod
├── hooks/use-{custom}.ts
├── types/{module}.types.ts
└── config/{module}.config.ts
```

### Stado / data flow

- React Query keys: `['{module}', '{action}', tenant_id]`
- Mutations: `use{Module}{Action}Mutation` con invalidate keys
- Auth: `useAuth()` Clerk; X-Tenant-ID auto-injected via `fetchClient`

### Tests requeridos

- Vitest unit: `tests/{module}/{component}.test.tsx`
- Vitest integration: `tests/{module}/{flow}.test.tsx`
- Playwright E2E: `e2e/regression/{module}-{story}.spec.ts`
- Coverage minimum: 20% all categories (no bajar)

## Surface diff (Agentic)

### Tool definitions

```python
# backend/src/modules/{module}/tools/{tool_name}.py
@tool
async def {tool_name}(
    tenant_id: UUID,
    {param}: {type},
) -> {ReturnDTO}:
    """{Docstring para LLM — describe función + inputs + outputs claramente.}"""
    ...
```

### Prompt slots affectados

| Slot | TTL | Content | Cache invalidation |
|---|---|---|---|
| 1 (system) | 1h | identity preamble | bump version |
| 2 (tools) | 5min | tool registry | new tool added |
| 3 (task) | not cached | task instructions | per session |
| 5 (brand voice) | 1h | tenant.brand_voice | tenant change |

### State machine LangGraph

```python
graph = StateGraph(AgentState)
graph.add_node("gather_context", gather_context_node)
graph.add_node("reason", reason_node)
graph.add_node("call_tool", call_tool_node)
graph.add_node("respond", respond_node)
graph.add_edge("gather_context", "reason")
graph.add_conditional_edges("reason", route_after_reason, {
    "call_tool": "call_tool",
    "respond": "respond",
})
```

### Agentic eval suite

- Path: `backend/tests/agentic_evals/{module}/{story_id}_eval.py`
- Runner: pytest con fixture `agentic_trial`
- Personas: `docs/specs/personas/{persona}.yaml`
- Rubrics: `docs/specs/rubrics/{rubric}.md`
- Trial policy: `trials_per_scenario=3`, `pass^k_threshold=0.5`
- Cost cap por trial: $0.50

### Observabilidad

- `copilot_trace_event` per turn con `tool_calls`, `tokens`, `latency`
- `copilot_llm_call` per LLM call con `cost_usd`, `model`, `cache_hit`
- PII: `sanitize_payload` ANTES de persistir
- LangSmith / langfuse traces (si configurado)

## Cross-cutting concerns

- **Tenant isolation:** confirmar `tenant_id` filter en cada query
- **Idempotency:** key strategy si aplica
- **Rate limiting:** N/min por tenant
- **Caching:** Redis keys + TTL si aplica
- **Backwards compatibility:** ¿existing data migra OK?

## Riesgos y mitigaciones

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Migration lenta en prod | high | Feature flag + chunked migration |
| Tool LLM costo alto | medium | Cap por session + tier pricing |

## Decisiones registradas

- **2026-05-04** — usar `idempotency-key` header vs natural key. Razón: requests con payload variable.
- ...

## Próximo paso (si soy /architect-X sub-arquitecto)

`done -> 03-arch-{surface}.md` (devuelvo referencia al orchestrator /architect).

## Próximo paso (si soy /architect orchestrator)

Reúno los 03-arch-* paralelos y produzco `04-tickets.yaml` con tickets ordenados, dependencias, owner_eligibility (qwen vs opus), acceptance criteria.
