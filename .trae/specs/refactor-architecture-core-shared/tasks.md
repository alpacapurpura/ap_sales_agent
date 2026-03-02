# Tasks

- [x] Task 1: Construcción de src/core (Infraestructura Transversal)
  - [x] SubTask 1.1: Crear directorio `src/core` y archivos base (`__init__.py`).
  - [x] SubTask 1.2: Mover `src/config.py` a `src/core/config.py`.
  - [x] SubTask 1.3: Crear `src/core/database.py` y consolidar lógica de DB (Engine, SessionLocal) extrayéndola de `sales_agent` o `shared` antiguo.
  - [x] SubTask 1.4: Crear `src/core/security.py`, `src/core/exceptions.py`, `src/core/logger.py`.
  - [x] SubTask 1.5: Actualizar importaciones de `src.config` a `src.core.config` en todo el proyecto.

- [x] Task 2: Construcción de src/shared/domain (Shared Kernel - Dominio)
  - [x] SubTask 2.1: Crear directorio `src/shared/domain`.
  - [x] SubTask 2.2: Reubicar `Base` (SQLAlchemy) a `src/shared/domain/base_entity.py` (buscar origen en `src/modules/sales_agent/infrastructure/db/base_model.py` o similar).
  - [x] SubTask 2.3: Crear `src/shared/domain/value_objects.py`.
  - [x] SubTask 2.4: Actualizar importaciones de `Base` en todos los modelos.

- [x] Task 3: Extracción de Links Compartidos (src/shared/links)
  - [x] SubTask 3.1: Crear directorio `src/shared/links`.
  - [x] SubTask 3.2: Mover `LinkService` y `ShareableLink` desde `src/modules/communication` a `src/shared/links`.
  - [x] SubTask 3.3: Mover schemas relacionados a `src/shared/links/schemas.py`.
  - [x] SubTask 3.4: Actualizar referencias a servicios de links.

- [x] Task 4: Revisión Exhaustiva y Extracción Módulo por Módulo
  - [x] SubTask 4.1: Revisar `src/modules/sales_agent` (Logger, Context, Crypto, LLM Factory) -> Mover a `core` o `shared`.
  - [x] SubTask 4.2: Revisar `src/modules/iam` (Dependencies, Auth Utils) -> Mover a `core/security` o `shared`.
  - [x] SubTask 4.3: Revisar `src/modules/communication` (Event Types, Availability) -> Validar si algo más es shared.
  - [x] SubTask 4.4: Revisar `src/modules/integration` (Channels, Webhooks) -> Extraer bases comunes a `shared/infrastructure`.
  - [x] SubTask 4.5: Revisar `src/modules/growth`, `brand`, `assets` -> Extraer utilidades genéricas.
  - [x] SubTask 4.6: Revisar `src/modules/copilot`, `onboarding` -> Extraer utilidades de archivos/imágenes a `core/utils`.

- [x] Task 5: Limpieza Final y Verificación
  - [x] SubTask 5.1: Eliminar directorios vacíos antiguos.
  - [x] SubTask 5.2: Verificar `alembic/env.py` para apuntar a las nuevas ubicaciones.
  - [x] SubTask 5.3: Linting final para asegurar reglas de dependencia (Core !=> Shared/Modules).
  - [x] SubTask 5.4: Ejecutar pruebas básicas (si existen) o verificar arranque de la aplicación.

- [x] Task 6: Corregir Violaciones Arquitectónicas Detectadas
  - [x] SubTask 6.1: Mover `PromptSource` a `src/core/enums.py` para romper ciclo Core -> Shared.
  - [x] SubTask 6.2: Eliminar dependencia de `Base` en `src/core/database.py`.
  - [x] SubTask 6.3: Mover `IncomingMessage` a `src/shared/domain/messages.py` para romper ciclo Shared -> Modules.
  - [x] SubTask 6.4: Devolver dependencias de IAM a su módulo para evitar Shared -> Modules.
  - [x] SubTask 6.5: Eliminar dependencias de `sales_agent` en `shared/llm`.
