# Lista de Verificación de Arquitectura Backend (DDD & Modular Monolith)

Esta lista debe completarse antes de aprobar cualquier cambio en el backend.

## 1. Integridad Estructural
- [ ] **Sin Carpetas Legacy**: Verificar que `src/core`, `src/services`, `src/routers` no existan en la raíz.
- [ ] **Módulos Definidos**: Confirmar que el código nuevo pertenezca a uno de los módulos: `iam`, `sales`, `communication`, `offer`, `marketing`, `brand`, `landing`, `gallery`, `integration`, `onboarding`.
- [ ] **Kernel Compartido**: Asegurar que `src/shared` solo contenga código verdaderamente transversal.

## 2. Reglas de Capas (DDD Estricto)
- [ ] **Dominio Puro**: `src/modules/{modulo}/domain/`
    - [ ] NO importa `sqlalchemy` ni `fastapi`.
    - [ ] NO hereda de `Base` (SQLAlchemy).
    - [ ] Usa `Pydantic` o clases Python puras.
- [ ] **Infraestructura Aislada**: `src/modules/{modulo}/infrastructure/`
    - [ ] Contiene modelos de base de datos (`models/`).
    - [ ] Contiene implementaciones de repositorios (`repositories/`).
- [ ] **Aplicación Orquestadora**: `src/modules/{modulo}/application/`
    - [ ] Contiene casos de uso y servicios.
    - [ ] Usa interfaces del dominio, no implementaciones directas.
- [ ] **Interfaz**: `src/modules/{modulo}/api/`
    - [ ] Contiene routers y DTOs.

## 3. Convenciones de Nombres (Estricto)
- [ ] **Archivos y Carpetas**: `snake_case` (e.g., `user_service.py`).
- [ ] **Clases y Tipos**: `PascalCase` (e.g., `UserRepository`).
- [ ] **Funciones y Variables**: `snake_case` (e.g., `get_user_by_id`).
- [ ] **Constantes**: `UPPER_CASE` (e.g., `MAX_RETRIES`).
- [ ] **Privados**: Prefijo `_` (e.g., `_validate_input`).

## 4. Aislamiento de Módulos
- [ ] **Sin Imports Cruzados de DB**: Un módulo NO importa modelos de `infrastructure/models.py` de otro módulo.
- [ ] **Sin Joins SQL**: No se realizan `JOIN` entre tablas de diferentes módulos.
- [ ] **Comunicación**: Se usa la capa de Servicio (Síncrono) o Eventos (Asíncrono) para interactuar entre módulos.

## 5. Calidad de Código
- [ ] **Linting**: Se ejecutó `ruff check` sin errores.
- [ ] **Typing**: Se usan type hints en todas las firmas de funciones.
