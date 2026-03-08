# Conversion Command Center Spec

## Why

The current dashboard is passive and disconnected from the business reality. The user needs an actionable "Command Center" that reflects the **Full-Funnel Lifecycle Framework** (AARRR + Bowtie). This dashboard must visualize the flow from "Hot Opportunity" (Nutrition) to "Conversion" (First Sale) to "Expansion" (LTV), centering all sales logic within the CRM to prioritize the human relationship and Lifetime Value.

## What Changes

### Backend (CRM Centric Transaction Engine)

* **New Entity**: `Sale` (in `src/modules/crm`).

  * **Purpose**: Tracks monetary transactions linked to a Customer, enabling LTV calculation and Cohort Analysis.

  * **Key Fields**:

    * `id`, `tenant_id`, `customer_id` (FK to CustomerProfile).

    * `offer_id` (FK to Product/Offer) - **CRITICAL**: Links to the specific value proposition sold.

    * `transaction_id` (External ID, e.g., Shopify Order ID, Stripe Charge ID).

    * `amount`, `currency` (ISO 4217).

    * `status` (COMPLETED, REFUNDED, PENDING, FAILED).

    * `stage` (CONVERSION vs EXPANSION) - **Logic**:

      * If `Customer.total_sales_count == 0` -> `CONVERSION` (Acquisition).

      * If `Customer.total_sales_count > 0` -> `EXPANSION` (Retention/Upsell).

    * `source` (SHOPIFY, MANUAL, STRIPE, API).

    * `payment_method` (CREDIT\_CARD, WIRE, CASH).

    * `metadata` (UTMs, coupons, affiliate\_id).

    * `occurred_at` (When the sale actually happened).

* **New Repository**: `SaleRepository` in `crm`.

* **New Repository**: `AppointmentRepository` in `scheduling`.

* **New Dashboard API**: `src/modules/crm/api/dashboard.py`.

  * **Aggregator Role**: Pulls data from `LeadRepository`, `AppointmentRepository`, and `SaleRepository`.

  * **Reasoning**: The "Closer Studio" is fundamentally a view of the CRM (Customer Relationship Management). It is not just for an "AI Agent", but for the human business owner to manage relationships. Placing it in `crm` centralizes the "Truth" of the customer journey.

### Frontend (The 3-Lane Methodology View)

* **New Component**: `ConversionCommandCenter` (replaces old widgets).

* **Lane 1: "Nutrición & Oportunidad" (Stages 2-3 -> 4)**

  * Displays **High-Intent Leads** (MQLs ready for conversion).

  * **Metrics**: Total Pipeline Value (Sum of potential offers).

  * **Action**: "Spy Chat" / "Intervene".

* **Lane 2: "Conversión & Cierre" (Stage 4)**

  * Displays **Appointments**.

  * **Controls**: Toggle \[Today] | \[Tomorrow] | \[Week].

  * **Context**: Shows "First Time" vs "Upsell" opportunity based on customer history.

  * **Action**: "Launch Meeting".

* **Lane 3: "Crecimiento & LTV" (Stages 4, 5, 6)**

  * Displays **Real-time Sales Ticker**.

  * **Controls**: Default \[Last 30 Days]. Switchable to \[Today], \[This Week], \[All Time].

  * **Visual**: Distinguishes between **New Business** (Conversion) and **Expansion** (Upsell/Recurring) with badges.

  * **Goal**: Daily Revenue Goal progress bar.

## Impact

* **Affected Specs**: CRM, Sales Agent, Dashboard.

* **Affected Code**:

  * `backend/src/modules/crm/*` (Adding Sales and Dashboard logic).

  * `backend/src/modules/sales_agent/api/dashboard.py` (Deprecated/Removed).

  * `frontend/src/features/sales/components/dashboard/*`.

## ADDED Requirements

### Requirement: CRM-Based Sales Tracking with Lifecycle Logic

The system SHALL record sales within the CRM module to link revenue directly to Customers.

* **Fields**: Must include `offer_id` to link to the Offer module, `transaction_id` for traceability, and `stage` for lifecycle tracking.

* **Logic**: System must automatically determine `stage` (CONVERSION vs EXPANSION) based on customer's purchase history at the moment of creation.

### Requirement: Methodology-Aligned Dashboard

The dashboard SHALL visualize the 3 key phases of the daily workflow:

1. **Prioritization**: Who is hottest? (Lane 1)
2. **Execution**: Who am I meeting? (Lane 2) - Supports Today/Week views.
3. **Motivation**: How much have I won? (Lane 3) - Supports 30-day rolling view.

## REMOVED Requirements

* **Separate Sales Module**: All sales logic is moved to `crm` module.

* **Sales Agent Dashboard**: The aggregation logic is moved to `crm/api/dashboard.py` to reflect that the "Closer Studio" is a CRM view, not just an agent function.

