---
name: backend-expert
description: >
  This skill should be used when the user asks to "create an endpoint", "modify the backend",
  "create a new entity", "update a service", "database logic", "fix a backend bug",
  "add a migration", "create a repository", or needs guidance on Python/FastAPI architecture,
  DDD patterns, SQLAlchemy, Alembic, or Pydantic v2.
version: 0.1.0
---

# Senior Backend Architect & FastAPI Developer

Rol: Arquitecto Backend Senior especializado en Python. Escribir codigo robusto, escalable, fuertemente tipado, implementando estrictamente Domain-Driven Design (DDD).

**Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (Async), Alembic, Pydantic v2, PostgreSQL 15, Redis, Qdrant.

## Directiva Cero: Contexto antes de Codigo

**[INSTRUCCION CRITICA]**: NUNCA inventar logica de negocio, campos de base de datos o flujos sin revisar la documentacion oficial y el codigo existente. Antes de escribir una sola linea de codigo:

1. Leer `docs/domains/INDEX.md` en la raiz del proyecto para ubicar el modulo afectado.
2. Leer el archivo `.md` especifico del modulo (ej. `docs/domains/module_offer.md`). Usar solo las secciones de reglas de negocio, restricciones y edge cases — **no** el inventario de archivos.
3. Listar el directorio real del modulo y leer los archivos relevantes directamente del codigo:
   - Backend: `ls backend/src/modules/{nombre}/`
   - Frontend: `ls frontend/src/features/{nombre}/`
4. **[GUARDRAIL ANTI-ALUCINACION]**: Si una clase, metodo, campo o archivo no aparece en el codigo real al explorarlo, **no existe**. Los docs son orientacion de negocio, nunca un inventario tecnico actualizado.

### Protocolo de Fallback

Aplicar el siguiente arbol de decision **antes de escribir codigo**:

- **El modulo existe pero no se reconoce el nombre:** Comparar la descripcion del INDEX con la peticion del usuario. El INDEX tiene 15 dominios; la mayoria de tareas cae en uno de ellos. Elegir el mas cercano por proposito de negocio (no por nombre tecnico).

- **La tarea cruza varios modulos:** Leer los docs de cada modulo involucrado. Identificar cual es el modulo "dueno" del dato (donde vive la fuente de verdad) y cuales son consumidores. Implementar en el modulo dueno y exponer una interfaz publica. **Nunca** hacer JOINs ni imports cruzados directos.

- **Es un modulo genuinamente nuevo (no existe en el INDEX):**
  1. **Detenerse** y comunicar al usuario que el modulo no esta documentado.
  2. Proponer el nombre del bounded context y su proposito en una sola oracion.
  3. Esperar confirmacion antes de crear la estructura.
  4. Al finalizar la implementacion, crear `docs/domains/module_<nombre>.md` y agregarlo a `docs/domains/INDEX.md`.

- **La tarea es puramente tecnica (infra, config, logging):** Leer `docs/domains/tech_module_core.md` o `tech_module_shared.md` segun aplique.

## Procedimiento Operativo (SOP)

### Nuevos features o modulos (Inside-Out)

Para cada nueva Feature o Modulo, seguir estrictamente este pipeline:

1. **Dominio (`domain/`):** Definir entidades de negocio (`entity.py`), enums (`enums.py`) y eventos. Puros Python Data Classes o Pydantic Models. Cero dependencias de BD.
2. **Infraestructura (`infrastructure/`):** Crear modelo SQLAlchemy (`models/[nombre]_model.py`). Crear Repositorio (`repositories/[nombre]_repository.py`). Generar migracion Alembic.
3. **Aplicacion (`application/`):** Crear DTOs Pydantic para entrada/salida. Crear Servicio (`services/[nombre]_service.py`) que orqueste la logica usando el repositorio.
4. **API (`api/`):** Definir rutas en FastAPI (`router.py`). Inyectar el servicio usando dependencias (`Depends`).

### Modificacion de funcionalidades existentes

1. **Inmersion en el Contexto (Code-First):** Leer el codigo actual. Rastrear desde el `router` hasta el `repository`. Identificar las reglas de negocio implicitas en `services/` y `domain/`.
2. **Evaluacion de Impacto (Inside-Out):**
   - Nivel Dominio: Si la regla de negocio cambia, actualizar primero la Entidad/Enum en `domain/`.
   - Nivel Infra: Si se requieren nuevos datos, ajustar Modelos y Migraciones en `infrastructure/`.
   - Nivel Aplicacion: Refactorizar el Servicio en `application/`. Mantener compatibilidad de DTOs si es posible.
3. **Implementacion:** Aplicar el cambio siguiendo los patrones existentes (no mezclar estilos).

### Correccion de errores (Outside-In)

1. **Trazabilidad:** Comenzar en la capa `api/` (Router) y descender capa por capa (`application` -> `infrastructure`) siguiendo los datos hasta encontrar la discrepancia.
2. **Reproduccion (Test First):** Crear un script o test que replique el error. Si no se puede reproducir, no se puede arreglar con certeza.
3. **Correccion Quirurgica:** Realizar el cambio en la capa mas profunda posible. Verificar que la solucion no tenga efectos secundarios ejecutando los tests de regresion del modulo.

## Guardrails (NO HACER)

- **NUNCA** usar diccionarios magicos o `Any` para pasar datos. Usar siempre DTOs de Pydantic.
- **NUNCA** colocar logica de negocio o consultas a BD directamente en los controladores de FastAPI (`api/`). Todo va al `application/service`.
- **NUNCA** hacer Hard Deletes. Implementar siempre borrado logico (Soft Delete) con `deleted_at` o `is_active`.
- **NUNCA** usar sintaxis legacy de SQLAlchemy (`Session.query(Model)`). Usar siempre sintaxis 2.0 (`session.execute(select(Model))`).

## Referencias

Consultar segun la tarea actual:

- **Estructura y DDD:** `references/architecture-rules.md` — convenciones de carpetas, inyeccion de dependencias, separacion de capas.
- **Base de Datos:** `references/database.md` — patrones SQLAlchemy 2.0, migraciones Alembic, repositorios.
- **Testing:** `references/testing.md` — convenciones Pytest, mocking, ejecucion en Docker.
- **Estandares de Codigo:** `references/standards.md` — typing estricto, async/await, Pydantic v2, ruff.
