# Tareas de Refactorización de Arquitectura DDD

## Dependencias
- [x] Task 1: Asegurar permisos correctos en la carpeta backend.
  - [x] SubTask 1.1: Ejecutar `sudo chown -R $USER:$USER backend` y `sudo chmod -R 775 backend` para tener control total sobre la carpeta y evitar problemas de permisos durante el refactor.
- [x] Task 2: Corregir Nomenclatura de Archivos y Directorios.
  - [x] SubTask 2.1: Renombrar `backend/src/admin/PRODUCTION_ACCESS.md` a `backend/src/admin/production_access.md`.
  - [x] SubTask 2.2: Renombrar `backend/src/shared/infrastructure/db/_base.py` a `backend/src/shared/infrastructure/db/declarative.py`.
  - [x] SubTask 2.3: Actualizar todos los imports de `src.shared.infrastructure.db._base` a `src.shared.infrastructure.db.declarative` usando `grep` y `sed` o `Read/Write`.
- [x] Task 3: Refactorización del Módulo IAM (Separación Dominio/Infraestructura).
  - [x] SubTask 3.1: Crear `backend/src/modules/iam/infrastructure/models/` y mover `backend/src/modules/iam/domain/user.py` (ORM) a `backend/src/modules/iam/infrastructure/models/user_model.py`.
  - [x] SubTask 3.2: Crear `backend/src/modules/iam/domain/user.py` (Pydantic) como entidad de dominio pura.
  - [x] SubTask 3.3: Actualizar `UserRepository` en `backend/src/modules/iam/infrastructure/user.py` para usar `UserModel` (ORM) y devolver `User` (Dominio).
  - [x] SubTask 3.4: Actualizar `UserService` y otros consumidores de `User` para usar el modelo de dominio.
- [x] Task 4: Refactorización del Módulo Sales (Separación Dominio/Infraestructura).
  - [x] SubTask 4.1: Crear `backend/src/modules/sales/infrastructure/models/` y mover `backend/src/modules/sales/domain/lead.py` (ORM) a `backend/src/modules/sales/infrastructure/models/lead_model.py`.
  - [x] SubTask 4.2: Crear `backend/src/modules/sales/domain/lead.py` (Pydantic) como entidad de dominio pura.
  - [x] SubTask 4.3: Actualizar `LeadRepository` en `backend/src/modules/sales/infrastructure/lead.py` para usar `LeadModel` (ORM) y devolver `Lead` (Dominio).
- [x] Task 5: Refactorización del Módulo Content (Separación Dominio/Infraestructura).
  - [x] SubTask 5.1: Crear `backend/src/modules/content/infrastructure/models/` y mover `backend/src/modules/content/domain/offer_gallery.py` (ORM) a `backend/src/modules/content/infrastructure/models/offer_gallery_model.py`.
  - [x] SubTask 5.2: Crear `backend/src/modules/content/domain/offer_gallery.py` (Pydantic) como entidad de dominio pura.
  - [x] SubTask 5.3: Actualizar `OfferGalleryRepository` en `backend/src/modules/content/infrastructure/offer_gallery_repository.py` para usar `OfferGalleryModel` (ORM) y devolver `OfferGalleryImage` (Dominio).
- [ ] Task 6: Verificación Final.
  - [ ] SubTask 6.1: Ejecutar `python -m unittest` o `pytest` (si disponible) para asegurar que no se rompió la lógica existente.
  - [ ] SubTask 6.2: Ejecutar `ruff check backend/src` para asegurar cumplimiento de estilo y validación de imports.
