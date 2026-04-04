---
module: Landing
status: active
---

# Landing

Genera landing pages automaticamente a partir de una Offer existente. No permite crear landings vacias.

## Domain Concepts

- **Archetype**: Plantilla estructural que define el layout y campos del content. El codigo define 6: THE_SQUEEZE, THE_EVENT, THE_FLASH_OFFER, THE_TRANSFORMER, THE_VELVET_ROPE, THE_BROCHURE.
- **LandingPageConfig**: Contenedor polimorfico — el campo `content` es un Union de 6 modelos tipados (uno por archetype) + `Dict[str, Any]` para datos crudos de Puck Editor.

## Architecture Decisions

- **JSONB hibrido**: Metadatos relacionales (`id`, `offer_id`, `slug`) + campo `config` JSONB para la estructura visual completa. Permite que Puck Editor cambie estructura sin migraciones.
- **Born-from-Offer**: Toda landing nace mapeando campos de la Offer (`headline_promise` -> `headline`, `primary_outcome` -> `subheadline`, `marketing_pain_points` -> `bullets`).

## Business Rules

- Una landing siempre requiere una `offer_id` existente — no hay creacion standalone.
- El `slug` se genera desde el titulo de la oferta; colisiones se resuelven con sufijo aleatorio.
- El validator `validate_content_matches_archetype` verifica que el tipo de `content` coincida con el `archetype` seleccionado (actualmente es soft — no lanza error).

## Edge Cases

- **Desync Offer-Landing**: Cambios en la Offer NO se propagan automaticamente a la landing para proteger ediciones manuales del usuario. Requiere "Regenerar" explicito.
- **Hydration mismatch**: Puck Editor carga componentes dinamicos — usar `client-only` o `useEffect` para inicializar y evitar errores de hidratacion en Next.js.

## CRITICAL — Do Not Violate

- Nunca asumir 3 archetypes — son **6** (`enums.py`). Cada uno tiene su modelo de content tipado en `content.py`.
- El campo `content` acepta `Dict[str, Any]` como fallback para datos raw de Puck — no forzar tipado estricto en ese caso.
