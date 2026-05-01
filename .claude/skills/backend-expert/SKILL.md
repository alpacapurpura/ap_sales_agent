---
name: backend-expert
description: "Implements FastAPI endpoints, creates SQLAlchemy 2.0 async models, generates idempotent Alembic migrations, structures bounded contexts following DDD (domain→infrastructure→application→api), and produces typed Pydantic v2 DTOs. Runs inside Docker (visionarias_brain_dev). Use when: 'create an endpoint', 'modify the backend', 'create a new entity', 'update a service', 'database logic', 'fix a backend bug', 'add a migration', 'create a repository', 'agrega un campo', 'nueva ruta API', 'corrige el servicio', or any Python/FastAPI/SQLAlchemy/Alembic task."
---

# SOP — Flujo de Trabajo

Antes de escribir codigo, ubicar el modulo destino:

1. **Ubicacion:** Leer `docs/domains/INDEX.md` → identificar bounded context. Leer el doc del modulo (reglas de negocio, restricciones, edge cases — no inventario de archivos).
2. **Explorar codigo:** `ls backend/src/modules/{nombre}/` y leer archivos clave (router, service, models).
3. Seguir el procedimiento segun el tipo de tarea:

> **⚠️ Si vas a tocar `backend/src/modules/analytics/` (cualquier provider, ETL pipeline, scheduler, workers, o `metric_catalog.py`):**
>
> 1. Leer `.claude/rules/etl-extraction-contract.md` ANTES de empezar.
> 2. Consultar `docs/etl/extraction-contract.md` para entender qué dice el contrato del provider/canal que vas a tocar.
> 3. Después de implementar, los 3 pasos finales son OBLIGATORIOS:
>    - Actualizar `backend/src/modules/analytics/domain/extraction_contract.py` para reflejar el cambio.
>    - `make extraction-contract` para regenerar `docs/etl/extraction-contract.md`.
>    - `cd backend && .venv/bin/pytest tests/architecture/test_extraction_contract.py -x -q`.
> 4. El commit final incluye SIEMPRE: el código del provider/pipeline + la entrada del contrato + el Markdown regenerado, en un solo commit.
>
> El test arquitectural falla si saltas estos pasos. No es opcional.

### Nuevos features (Inside-Out)

0. **Tests (TDD):** Para CADA capa, escribir test que falla (RED) antes de implementar. Orden: domain → infra → app. Ver `references/testing.md`.
1. **`domain/`:** Entidades (`entity.py`), enums, eventos. Puros Python — cero dependencias de BD.
2. **`infrastructure/`:** Modelo SQLAlchemy (`models/`), Repositorio (`repositories/`), migracion Alembic.
3. **`application/`:** DTOs Pydantic entrada/salida, Servicio que orqueste logica via repositorio.
4. **`api/`:** Rutas FastAPI (`router.py`), inyeccion con `Depends`.

### Modificaciones (Code-First)

0. **Tests primero:** Si hay tests, actualizarlos para reflejar el cambio (RED). Si NO hay tests, escribir tests del comportamiento actual primero.
1. Leer codigo actual: rastrear router → service → repository. Identificar reglas implicitas.
2. Evaluar impacto por capas: dominio primero, luego infra, luego aplicacion.
3. Implementar siguiendo patrones existentes — no mezclar estilos.

### Bugs (Outside-In)

1. Trazar desde `api/` descendiendo capa por capa hasta la discrepancia.
2. Escribir test de regresión que reproduce el bug (DEBE fallar RED). NO corregir hasta tener test rojo.
3. Corregir en la capa mas profunda posible. Verificar con tests de regresion.

### Quality runtime checklist OBLIGATORIO

Antes de commit Y antes de spawn auditor, leer [runtime-quality-checklist.md](backend-expert/references/runtime-quality-checklist.md). Cubre anti-patterns que mypy + ruff + pytest NO catch: FastAPI Annotated dep type alias, override fixture sin Depends, 501 stubs Response param, datetime query parsing, SQLA legacy Column handling, multi-tenant test fixture pattern.

## Ubicacion de modulos

- **Modulo no reconocido:** Comparar proposito de negocio en INDEX (15 dominios). Elegir por funcion, no por nombre.
- **Tarea cross-modulo:** Implementar en el modulo "dueno" del dato. Exponer interfaz publica. Sin JOINs ni imports cruzados directos.
- **Modulo nuevo:** Detenerse → proponer nombre y proposito → esperar confirmacion → crear estructura + doc en `docs/domains/`.
- **Tarea tecnica (infra/config):** Consultar `docs/domains/tech_module_core.md` o `tech_module_shared.md`.

## Referencias (leer solo cuando aplique)

- **Estructura y DDD:** `references/architecture-rules.md`
- **Base de Datos y migraciones:** `references/database.md`
- **Testing:** `references/testing.md`
- **Estandares de codigo:** `references/standards.md`

## Patrones de referencia rapida

**SQLAlchemy 2.0 (correcto vs prohibido):**
```python
# CORRECTO
result = await session.execute(select(Lead).where(Lead.tenant_id == tenant_id))
leads = result.scalars().all()

# PROHIBIDO — sintaxis legacy
leads = session.query(Lead).filter_by(tenant_id=tenant_id).all()
```

**Pydantic v2 DTO tipado:**
```python
class LeadCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    email: EmailStr
    tenant_id: UUID
```

**Alembic migracion idempotente (raw SQL obligatorio):**
```python
def upgrade():
    op.execute("CREATE TABLE IF NOT EXISTS leads (id UUID PRIMARY KEY, name VARCHAR NOT NULL)")
    op.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS email VARCHAR")
    op.execute("CREATE INDEX IF NOT EXISTS ix_leads_tenant ON leads (tenant_id)")
```

## Constraints (CRITICAL — read last)

- **Anti-alucinacion:** Si una clase, metodo, campo o archivo no aparece en el codigo real al explorarlo, **no existe**. Los docs son orientacion de negocio, nunca inventario tecnico.
- **Sin `Any` ni dicts magicos** — siempre DTOs Pydantic tipados.
- **Sin logica de negocio en `api/`** — todo va al `application/service`.
- **Sin Hard Deletes** — siempre soft delete con `deleted_at` o `is_active`.
- **SQLAlchemy 2.0 only** — `session.execute(select(Model))`, nunca `Session.query(Model)`.
- **Fitness tests:** New code must pass `cd backend && .venv/bin/pytest tests/architecture/ -v`. These enforce DDD boundaries (no cross-module imports), API contracts (response_model= required), and conventions (no hard deletes, SA 2.0). Run `make arch-test` to verify. NEVER use docker exec for lint/tests.

## Project invariants (read on demand)

- `references/runtime-quality-checklist.md` — **OBLIGATORIO leer antes commit y antes spawn auditor**. FastAPI Annotated deps, override fixture pattern, 501 stubs JSONResponse, datetime query, SQLA legacy Column handling, tenant isolation, JSONB shape (origen S4 PI-1 PR-10)
- `references/backend-quality.md` — Ruff 70+ rules, arch fitness gates, naming conventions
- `references/master-data.md` — TenantLocale VO, currency+timezone, no hardcoded
- `references/currency-handling.md` — currency from data source, formatMoney patterns
- `references/architectural-fitness.md` — ratchet pattern, common fixes
- `references/admin-panel.md` — Streamlit registry-based, contract+smoke tests
