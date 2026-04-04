---
module: Offer
status: active
---

# Offer

Estructura productos y servicios con polimorfismo (un curso tiene curriculum, un servicio tiene sesiones, un producto fisico tiene envio). Es el nucleo del Offer Ladder del negocio.

## Domain Concepts

- **Dualidad Offer/Product**: En codigo de negocio se usa `Offer`. La tabla SQL se llama `products` (legacy). En migraciones buscar `products`.
- **Polimorfismo**: Columna `archetype` (enum `OfferArchetype`) + columna JSONB `specific_details`. El mapping `ARCHETYPE_TO_DETAILS_MAPPING` instancia la subclase Pydantic correcta (`ProductDetails`, `ProgramDetails`, `ServiceDetails`, `SubscriptionDetails`, `EventDetails`).
- **Archetypes** (en espanol): `producto`, `programa`, `servicio`, `membresia`, `experiencia`.

## Architecture Decisions

- **Discriminador + JSONB**: Evita N tablas relacionales. `archetype` determina que clase de detalles parsear de `specific_details`. Pydantic es la unica barrera de validacion (la DB no valida estructura interna del JSONB).
- **Pricing como lista JSONB**: `pricing_options` es una lista de `PricingStructure` (pago unico, cuotas, suscripcion). Permite multiples opciones de pago sin tablas extra.

## Business Rules

- `archetype` determina el `delivery_model` por defecto via `ARCHETYPE_DEFAULT_DELIVERY` si no se especifica uno.
- El `model_validator` en `Offer` valida que `specific_details` sea instancia de la clase esperada segun `archetype`. Mismatch -> `ValueError`.
- `deliverables` y `marketing_pain_points` se inyectan en el prompt del Sales Agent. Mas de ~20 elementos saturan la ventana de contexto del LLM.

## Edge Cases

- **Mutacion de ofertas activas**: Editar precio/promesa mientras el Sales Agent la ofrece causa inconsistencias (bot dice $300, link cobra $500). Para cambios drasticos, archivar y crear v2.
- **JSONB corrupto via SQL directo**: Si se inyectan datos malformados en `specific_details` saltando Pydantic, la API falla con `ValidationError` al leer.

## CRITICAL -- Do Not Violate

- El campo es `archetype`, no `type`. El mapping es `ARCHETYPE_TO_DETAILS_MAPPING`, no `OFFER_TYPE_TO_DETAILS_MAPPING`.
- Los valores del enum `OfferArchetype` estan en espanol: `producto`, `programa`, `servicio`, `membresia`, `experiencia`.
- Toda query filtra por `tenant_id`.
