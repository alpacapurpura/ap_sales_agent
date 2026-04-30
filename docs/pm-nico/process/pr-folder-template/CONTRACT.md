# CONTRACT — PR-{N}-{slug}

> Owner: `nicolify-architect`. SSoT pre-implementación. Backend + frontend builders consumen este archivo en paralelo.

## Existing systems audit (NO NEW LAYER rule — architect-mandatory)

> **Regla** (origen PR-3 PI-2 S2 audit failure 2026-04-30): antes de proponer nueva capa de infraestructura (factory, registry, provider, config layer), DEBE haber este bloque verificado. Capa duplicada = deuda + drift + costo escala 1000+ tenants. Capa que duplica `core/` o `shared/` existente bloquea CONTRACT review.

### Audit cross-module ejecutado

```bash
# Comandos exactos que el architect ejecutó:
grep -rn "settings\.get_\|<keyword subsystem>" src/core/ src/shared/
grep -rn "from src.core.config\|from src.core.enums" src/modules/<target>/
find src/ -name "*.py" -path "*<subsystem>*"
```

### Sistemas existentes encontrados

| Sistema | Path | Enum/Config | Factory/Router | Providers/Adapters | Estado |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | active/deprecated/partial |

### Decisión por sistema

- **Sistema A (path)**: EXTEND/REPLACE/NEW + justificación
- **Sistema B (path)**: ... 

Si **NEW**: bloque obligatorio "Por qué los existentes no sirven" con código real referenciado (path:line) + criterio escala 1000+ tenants + cero deuda.

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
