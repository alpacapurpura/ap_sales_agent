# Offer Structure & Functional Specification

## Why

The user needs a clear understanding of how to extend the "OfferType" system and a detailed functional document of the current implementation to analyze UX, identify redundancies, and plan future types.

## What Changes

* **Documentation**: Creation of a comprehensive functional document `docs/functional/offer-structure.md`.

* **Guide**: Inclusion of a "How-to" guide for adding new OfferTypes in the developer documentation.

## Impact

* **Affected specs**: None (Purely documentation).

* **Affected code**: None (Documentation only).

## Functional Document: Offer Structure

### 1. Architecture Overview

The system uses a **Polymorphic Architecture** on both Backend and Frontend.

* **Backend**: `Offer` entity has a `type` (Enum) and a `specific_details` (JSONB) field. The structure of `specific_details` is enforced by Pydantic models mapped to the `OfferType`.

* **Frontend**: A "Builder" pattern where `OfferType` determines a list of `Sections`. Each `Section` corresponds to a specific Form Component.

### 2. How to Create a New OfferType

To add a new OfferType (e.g., `HYBRID_MASTERMIND`), follow these steps:

#### Backend

1. **Enum**: Add `HYBRID_MASTERMIND` to `OfferType` in `backend/src/core/domain/offer_enums.py`.
2. **Schema**:

   * If existing details models (`ProgramDetails`, `ServiceDetails`, etc.) fit, use one.

   * If not, define `HybridMastermindDetails(BaseModel)` in `backend/src/core/domain/offer/schema.py`.
3. **Mapping**: Update `OFFER_TYPE_TO_DETAILS_MAPPING` in `schema.py` to link `HYBRID_MASTERMIND` -> `HybridMastermindDetails`.

#### Frontend

1. **Enum**: Add to `OfferType` in TypeScript types.
2. **Config**: Update `OFFER_BUILDER_CONFIG` in `frontend/src/features/offer-studio/config/offer-builder-config.ts`.

   ```typescript
   [OfferType.HYBRID_MASTERMIND]: ['identity', 'strategy', 'program_details', 'pricing', 'closing']
   ```
3. **Forms**: If a new section is needed, create the form component and register it in `SECTION_REGISTRY`.

### 3. Detailed Form Catalog

#### A. Common Forms (All Offers)

**1. Identity Form (`identity`)**

* **Logic**: Always the first step. Defines the "Soul" of the offer.

* **Fields**:

  * `public_name` (Text, Req): "Nombre Público". Name shown to customers.

  * `type` (Read-only Badge): Displays current OfferType.

  * `delivery_model` (Read-only Badge): Displays Delivery Model (DIY/DWY/DFY).

**2. Pricing Form (`pricing`)**

* **Logic**: Handles financial models.

* **Fields**:

  * `pricing_options` (List):

    * `total_amount` (Number, Req): Price value.

    * `currency` (Select, Req): USD/EUR/MXN.

    * `plan_type` (Select): One-time vs Subscription.

    * `number_of_installments` (Number): Split payments.

#### B. Specific Details Forms (Polymorphic)

**3. Program Details (`program_details`)**

* **Used By**: `COHORT_BASED_COURSE`, `HYBRID_MENTORSHIP`, `GROUP_COACHING`, `CHALLENGE`.

* **Logic**:

  * If `structure_type` is `FIXED_DATE_COHORT`, `start_date` is mandatory.

  * Recommendations for `interaction_type` appear based on `structure_type`.

* **Fields**:

  * `structure_type` (Select, Req): "Tipo de Estructura" (Cohorte/Evergreen/Reto).

  * `is_application_required` (Switch): "Requiere Aplicación". Gates checkout.

  * `duration_weeks` (Number): "Duración (Semanas/Días)".

  * `interaction_type` (Select): "Dinámica de Interacción" (Live/Hybrid/Async).

  * `community_platform` (Select): "Plataforma de Comunidad" (Circle/Slack/Discord).

  * `start_date` (Date+Time): "Fecha de Inicio". Mandatory for Cohorts.

  * `registration_end_date` (Date+Time, Opt): "Cierre de Inscripciones".

  * `end_date` (Date, Opt): "Fecha de Fin".

**4. Product Details (`product_details`)**

* **Used By**: `EBOOK`, `MERCH`, `TRIPWIRE`, `SELF_PACED_COURSE`.

* **Logic**:

  * If `fulfillment_type` is `PHYSICAL`, shows Shipping fields.

* **Fields**:

  * `fulfillment_type` (Select, Req): "Tipo de Entrega" (Digital/Physical).

  * `format` (Select): "Formato Digital" (PDF/Video/Audio).

  * `access_url` (URL): "URL de Acceso". Download link.

  * `requires_shipping` (Switch): "Requiere Envío". Visible only if Physical.

  * `stock_quantity` (Number): "Stock". Visible only if Physical.

  * `sku_inventory_code` (Text): "SKU Interno".

**5. Service Details (`service_details`)**

* **Used By**: `AGENCY`, `CONSULTING`, `FREELANCE`.

* **Fields**:

  * `category` (Select): Service type (Advisory/Agency).

  * `deliverables_list` (List<String>): "Entregables".

  * `turnaround_time_days` (Number): "Tiempo de Entrega (Días)".

  * `booking_url` (URL): "Link de Agenda". Critical for Advisory.

  * `revision_rounds` (Number): "Rondas de Cambios".

**6. Event Details (`event_details`)**

* **Used By**: `RETREAT`, `MASTERMIND`, `WORKSHOP`.

* **Logic**:

  * Validates `end_date` > `start_date`.

* **Fields**:

  * `start_date` / `end_date` (DateTime): Event timing.

  * `location_type` (Select): Virtual/Physical.

  * `venue_name` (Text): "Lugar/Hotel". Required if Physical.

  * `venue_address` (Text): Address for Maps.

  * `virtual_meeting_url` (URL): Zoom link. Required if Virtual.

### 4. UX Analysis & Optimization Proposals

**Redundancies Identified:**

1. **Date Pickers**: `ProgramDetails` and `EventDetails` both implement complex date logic. Could be unified into a `ScheduleComponent`.
2. **Instructors**: Currently a separate form (`instructors`), but often intrinsically linked to `Identity` in user mental model.

**Complexity Evaluation:**

* **High Complexity**: `ProgramDetails` is the heaviest form due to the conditional logic between `structure_type` -> `interaction_type` -> `dates`.

* **Risk**: The separation of `Pricing` from `Details` can cause friction (e.g., defining a "Membership" price without setting "Subscription Details" first).

**Optimization Proposals:**

1. **Unified Schedule Builder**: Extract the session scheduler from `ProgramDetails` and make it available for `EventDetails` (Workshops often have schedules too).
2. **Smart Defaults**: Pre-fill `structure_type` based on the `OfferType` selected in creation (e.g., `COHORT` type should default structure to `FIXED_DATE`).

