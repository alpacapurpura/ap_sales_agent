# Tasks

- [x] Task 1: Preparar directorios destino
    - [ ] Crear directorio `src/modules/offer/application` si no existe.
    - [ ] Crear directorio `src/modules/offer/domain/offer` si es necesario para mantener estructura, o aplanar.
    - [ ] Verificar estructura de `src/modules/communication`.

- [x] Task 2: Mover archivos a módulo Offer
    - [ ] Mover `src/modules/content/domain/offer_gallery.py` -> `src/modules/offer/domain/offer_gallery.py`
    - [ ] Mover `src/modules/content/api/dto/offer_gallery.py` -> `src/modules/offer/api/dto/offer_gallery.py`
    - [ ] Mover `src/modules/content/application/offer_generator.py` -> `src/modules/offer/application/offer_generator.py`
    - [ ] Mover `src/modules/content/api/offer_ai.py` -> `src/modules/offer/api/offer_ai.py`
    - [ ] Mover `src/modules/content/domain/offer/offer_ai_schemas.py` -> `src/modules/offer/domain/offer_ai_schemas.py`
    - [ ] Mover `src/modules/content/api/definitions.py` -> `src/modules/offer/api/definitions.py`
    - [ ] Mover infraestructura relacionada (repositorios, modelos) si existen en `content`.

- [x] Task 3: Mover archivos a módulo Communication
    - [ ] Mover `src/modules/content/domain/link.py` -> `src/modules/communication/domain/link.py`
    - [ ] Mover `src/modules/content/api/public_links.py` -> `src/modules/communication/api/public_links.py`
    - [ ] Mover `src/modules/content/api/dto/public_links.py` -> `src/modules/communication/api/dto/public_links.py`
    - [ ] Mover `src/modules/content/application/link_service.py` -> `src/modules/communication/application/services/link_service.py`

- [x] Task 4: Renombrar módulo Content a Landing
    - [ ] Renombrar carpeta `src/modules/content` a `src/modules/landing`.

- [x] Task 5: Actualizar Imports (Refactor masivo)
    - [ ] Actualizar referencias a `src.modules.content.domain.offer_gallery` -> `src.modules.offer.domain.offer_gallery`
    - [ ] Actualizar referencias a `src.modules.content.application.offer_generator` -> `src.modules.offer.application.offer_generator`
    - [ ] Actualizar referencias a `src.modules.content.api.offer_ai` -> `src.modules.offer.api.offer_ai`
    - [ ] Actualizar referencias a `src.modules.content.api.definitions` -> `src.modules.offer.api.definitions`
    - [ ] Actualizar referencias a `src.modules.content.api.public_links` -> `src.modules.communication.api.public_links`
    - [ ] Actualizar referencias a `src.modules.content.application.link_service` -> `src.modules.communication.application.services.link_service`
    - [ ] Actualizar referencias a `src.modules.content.domain.link` -> `src.modules.communication.domain.link`
    - [ ] Actualizar referencias a `src.modules.content` -> `src.modules.landing` (para el resto de archivos).

- [x] Task 6: Verificación
    - [ ] Verificar que no queden referencias rotas a `src.modules.content`.
    - [ ] Ejecutar `ruff check` para validar imports.
