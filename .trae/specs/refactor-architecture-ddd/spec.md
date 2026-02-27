# Refactor Arquitectura Modular Monolith (DDD) Spec

## Por qué
El backend actual viola el principio de **Pureza del Dominio** en la Arquitectura DDD. Los modelos de dominio (`src/modules/*/domain/*.py`) dependen directamente de la librería de persistencia (SQLAlchemy), acoplando la lógica de negocio a la infraestructura. Además, existen archivos que no cumplen con la convención de nomenclatura `snake_case`, dificultando la búsqueda y mantenimiento del código.

## Qué Cambios
- **Corrección de Permisos**: Asegurar que el usuario y el entorno tengan control total sobre la carpeta `backend` mediante `sudo`.
- **Nomenclatura**:
    - Renombrar `backend/src/admin/PRODUCTION_ACCESS.md` a `backend/src/admin/production_access.md`.
    - Renombrar `backend/src/shared/infrastructure/db/_base.py` a `backend/src/shared/infrastructure/db/declarative.py`.
- **Refactorización de Módulos (IAM, Sales, Content)**:
    - **Separación de Modelos**:
        - Mover las clases ORM (SQLAlchemy) de `domain/` a `infrastructure/models/`.
        - Crear modelos Pydantic puros en `domain/` para representar las entidades de negocio.
    - **Adaptación de Repositorios**: Actualizar los repositorios para consultar los modelos ORM y devolver modelos de Dominio (Pydantic).

## Impacto
- **Archivos Afectados**:
    - `backend/src/modules/iam/domain/user.py` -> `infrastructure/models/user_model.py`
    - `backend/src/modules/sales/domain/lead.py` -> `infrastructure/models/lead_model.py`
    - `backend/src/modules/content/domain/offer_gallery.py` -> `infrastructure/models/offer_gallery_model.py`
    - Repositorios correspondientes (`UserRepository`, `LeadRepository`, `OfferGalleryRepository`).
- **Breaking Changes**: No en la API externa, pero sí en la estructura interna. Los servicios deberán importar los modelos de dominio en lugar de los ORM.

## Requerimientos AÑADIDOS
### Requerimiento: Separación Estricta de Capas
El sistema DEBE separar explícitamente los modelos de persistencia (SQLAlchemy) de los modelos de dominio (Pydantic/Dataclasses).
- **Dominio**: Solo python puro (Pydantic permitido). Sin imports de `sqlalchemy`.
- **Infraestructura**: Contiene los modelos ORM y conoce cómo mapearlos al dominio.

## Requerimientos MODIFICADOS
### Requerimiento: Nomenclatura de Archivos
Todos los archivos Python y Markdown deben usar `snake_case`.

## Requerimientos ELIMINADOS
### Requerimiento: Modelos Híbridos
Se ELIMINA la práctica de usar clases SQLAlchemy como modelos de dominio.
**Razón**: Viola la independencia de la infraestructura y dificulta los tests unitarios puros.
