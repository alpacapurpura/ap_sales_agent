---
module: CRM
status: active
---

# CRM

Centraliza la identidad de personas (CDP) y gestiona su ciclo de vida comercial. Es la fuente de verdad para resolver "quien es este contacto" across canales.

## Domain Concepts

- **CustomerProfile (WHO)**: Golden Record unificado. Sobrevive a multiples ventas y canales. 1:N con Identities, 1:N con Leads.
- **CustomerIdentity (HOW)**: Punto de contacto resoluble — `(type, value)` ej. `(TELEGRAM, 123456)`. Permite que la misma persona en distintos canales converja en un solo Profile.
- **Lead (CONTEXT)**: Oportunidad de venta efimera. Estado del funnel, temperatura, objeciones de *esta* venta. Nunca duplicar datos demograficos aqui — usar `customer_id` -> `CustomerProfile`.

## Architecture Decisions

- **CDP 3-entity split**: Separar WHO/HOW/CONTEXT permite identity resolution sin contaminar el contexto de venta. Un Profile persiste; un Lead es desechable.
- **Servicios especializados**: Ademas de `IdentityService` y `LeadService`, el modulo incluye `NpsService` (encuestas de satisfaccion), `ReferralService` (referidos), `LifecycleService` (transiciones automaticas de stage), `InactivityService` (deteccion de inactividad) e `IgProfileEnricher` (enriquecimiento desde Instagram).

## Business Rules

- **Golden Rule**: Nunca duplicar datos demograficos en `Lead`. El Lead apunta a `customer_id`.
- La conversion vs expansion se detecta automaticamente por historial de ventas.
- `lifecycle_stage = CHURNED` para churn — nunca hard delete de CustomerProfile.
- `Lead` usa `is_blacklisted` para bloqueos, `deleted_at` para borrado logico.

## Edge Cases

- **Race condition en creacion**: Dos mensajes simultaneos del mismo usuario nuevo pueden crear dos Profiles. Depende de DB constraints (unique index) como mitigacion.
- **Falsos positivos de fusion**: Dos personas comparten telefono (linea fija, error de input) -> se fusionan incorrectamente. Validar propiedad del canal si es posible.
- **N+1 en historial**: Cargar Profile con todos sus Leads y Sales puede ser pesado — usar `joinedload` con cuidado.

## CRITICAL — Do Not Violate

- Identity resolution DEBE filtrar por `tenant_id`. Un mismo email puede existir en dos tenants como personas distintas.
- Toda consulta de CustomerProfile, Identity y Lead DEBE incluir `tenant_id` — sin excepciones.
