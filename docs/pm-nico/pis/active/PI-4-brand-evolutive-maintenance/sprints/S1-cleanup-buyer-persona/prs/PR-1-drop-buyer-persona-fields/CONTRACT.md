# CONTRACT — PR-{N}-{slug}

> Owner: `nicolify-architect`. SSoT pre-implementación. Backend + frontend builders consumen este archivo en paralelo.

## Domain entities (nuevas o modificadas)

```python
# Pydantic v2 / SQLAlchemy 2.0
class X(BaseModel):
    ...
```

## API endpoints

| Method | Path | Request body | Response model | Status codes |
|---|---|---|---|---|
| POST | /api/v1/{m}/x | XCreate | XResponse | 201, 400, 409 |

## DB schema

```sql
-- migrations/{timestamp}_xxx.py (idempotente, raw SQL IF NOT EXISTS)
CREATE TABLE IF NOT EXISTS x (...);
CREATE INDEX IF NOT EXISTS ... ;
```

## Eventos / outbox

| Event name | Payload | Producer | Consumer |
|---|---|---|---|
| ... | ... | ... | ... |

## Retry / idempotency policy

- Idempotency key: ...
- Retry: ... (exponential backoff, max N)
- Circuit breaker: ... (umbral fallos, ventana, recovery)

## Tenant isolation

- Cada query filtra por `tenant_id`. Repos exigen param required.
- Migración crea índice compuesto `(tenant_id, ...)` cuando aplique.

## Observability

- structlog: ... (campos clave: tenant_id, agent_kind, operation)
- Trace events emitted: ... (si aplica)

## Open questions for PM

- {Cosas que architect detectó y necesitan decisión PM antes de implementar}

---

<!-- @pm: CONTRACT.md ready. Próximo paso: ejecutar prompts/02-builder-start.md o ejecutar /pm "PR-N architect done" para review. -->
