---
name: backend-expert
description: Experto en desarrollo backend (FastAPI, SQLAlchemy, Servicios) para la API del Dashboard Cliente. Usar para tareas de endpoints, lógica de negocio, base de datos y corrección de bugs en la API. NO usar para lógica agéntica compleja (LangGraph) ni panel Superadmin.
---

# Backend Functional Expert

Guía para el desarrollo y mantenimiento del backend funcional (API REST, DB, Servicios) del sistema Visionarias Brain.

## 🚀 Inicio Rápido

### Comandos Frecuentes

```bash
# Validar y corregir código (OBLIGATORIO antes de entregar)
ruff check backend/src --fix

# Ejecutar tests
docker exec -t visionarias_brain pytest

# Crear migración de DB (RECORDAR: Editar archivo generado para hacerlo defensivo/idempotente)
cd backend && alembic revision --autogenerate -m "mensaje" && alembic upgrade head
```

## 📚 Referencias

- **Arquitectura**: Estructura de carpetas, capas y flujo de datos. Ver [architecture.md](references/architecture.md).
- **Base de Datos**: Modelos, Repositorios y **Pipeline de Migraciones**. Ver [database.md](references/database.md).
- **Estándares**: Typing, Linting (Ruff), Pydantic V2 y Async. Ver [standards.md](references/standards.md).
- **Testing**: Estrategia de pruebas y ejecución en Docker. Ver [testing.md](references/testing.md).

## 🛑 Límites del Skill

1.  **Superadmin (`src/admin`)**: ⛔ **ÁREA RESTRINGIDA**. No modificar salvo petición explícita de administración de sistema.
2.  **Lógica Agéntica (`src/core/nodes.py`, `agent.py`)**: Usar el skill `agentic-system-architect` para flujos complejos de IA.
3.  **Frontend**: Usar el skill `frontend-expert`.

## Stack Tecnológico Principal

- **Framework**: FastAPI
- **DB**: PostgreSQL + SQLAlchemy (Async) + Alembic
- **Validación**: Pydantic V2
- **Vector Store**: Qdrant
