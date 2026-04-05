# Estandares de Codigo y Buenas Practicas

## Python & Typing
- **Version**: Python 3.11+.
- **Typing**: Estricto. Usar `Optional`, `List`, `Dict` (o genericos nativos `list[]`, `dict[]`).
- **Retorno**: Todas las funciones deben tener type hints de retorno `->`.

## Linting & Formato
- **Herramienta**: `ruff`.
- **Comando Obligatorio**: Antes de hacer commit o finalizar una tarea, ejecutar nativo:
  ```bash
  cd backend && .venv/bin/ruff check src/ --fix --no-cache
  ```
  Esto corrige importaciones, formato y errores comunes automaticamente. NUNCA usar docker exec.

## Async/Await
- **I/O Bound**: Todo acceso a Base de Datos (SQLAlchemy Async), APIs externas (HTTPX) y archivos debe ser `async`.
- **FastAPI**: Definir endpoints con `async def`.

## Pydantic V2
- **Usar `BaseModel` de Pydantic V2.**
- **Preferir `model_validate` sobre `from_orm`.**
- **Configuracion mediante `model_config = ConfigDict(...)`.**

## Manejo de Errores
- **Usar `HTTPException` de FastAPI para errores controlados en la capa API.**
- **Definir excepciones de dominio personalizadas en `src/shared/domain/exceptions.py` si es necesario.**
- **Logs estructurados con `structlog`. No usar `print`.**

## Variables de Entorno
- **Gestion centralizada en `src/config.py` usando `pydantic-settings`.**
- **Nunca hardcodear credenciales o URLs.**
