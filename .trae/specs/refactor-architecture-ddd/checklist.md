# Checklist de Refactorización Arquitectura DDD

## Permisos y Configuración
- [ ] Permisos de carpeta `backend` configurados con `sudo` (propietario y modo 775).
- [ ] Nomenclatura de `PRODUCTION_ACCESS.md` corregida.
- [ ] Nomenclatura de `_base.py` (declarative) corregida.

## IAM Refactor
- [ ] `User` (ORM) movido a `src/modules/iam/infrastructure/models/user_model.py`.
- [ ] `User` (Pydantic) creado en `src/modules/iam/domain/user.py`.
- [ ] `UserRepository` actualizado para mapear ORM -> Dominio.
- [ ] Servicios dependientes de `User` actualizados y funcionando.

## Sales Refactor
- [ ] `Lead` (ORM) movido a `src/modules/sales/infrastructure/models/lead_model.py`.
- [ ] `Lead` (Pydantic) creado en `src/modules/sales/domain/lead.py`.
- [ ] `LeadRepository` actualizado para mapear ORM -> Dominio.
- [ ] Servicios dependientes de `Lead` actualizados y funcionando.

## Content Refactor
- [ ] `OfferGallery` (ORM) movido a `src/modules/content/infrastructure/models/offer_gallery_model.py`.
- [ ] `OfferGalleryImage` (Pydantic) creado en `src/modules/content/domain/offer_gallery.py`.
- [ ] `OfferGalleryRepository` actualizado para mapear ORM -> Dominio.
- [ ] Servicios dependientes de `OfferGallery` actualizados y funcionando.

## Verificación Final
- [ ] Todos los tests unitarios/integración pasan.
- [ ] `ruff check backend/src` no reporta errores.
- [ ] La estructura cumple con el estándar de `back-arch-auditor`.
