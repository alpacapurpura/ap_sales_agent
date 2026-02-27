# Refactor Sales Studio to Closer Studio Spec

## Why
Currently, Sales Studio and Marketing Studio operate in silos with duplicate identity data (`CustomerProfile` vs `LeadModel`). This causes data inconsistencies and hinders a unified view of the customer. The goal is to transform "Sales Studio" into a streamlined "Closer Studio" focused on velocity and context, while using "Marketing Studio" as the single source of truth for identity.

## What Changes
- **Database Schema**:
  - `LeadModel` (Sales) will now have a Foreign Key `customer_id` pointing to `CustomerProfile` (Marketing).
  - Remove redundant identity fields from `LeadModel` (`full_name`, `email`, `phone`, `social_handle`, `timezone`).
  - `LeadModel` retains sales-specific context: `stage`, `probability`, `temperature`, `ai_memory`, `score`.
- **Backend Logic**:
  - Lead Creation Flow: Incoming leads (e.g., via Webhook) first find/create a `CustomerProfile`, then create a `LeadModel` linked to it.
  - Data Migration: Existing leads must be migrated to create/link `CustomerProfile` records.
- **Frontend Architecture**:
  - Refactor `frontend/src/features/sales` to use Atomic Design (Atoms, Molecules, Organisms).
  - Implement "Closer's Cockpit":
    - **Pipeline Board**: Simplified Kanban (New, In Conversation, Closing, Won/Lost).
    - **Lead Command Center**: Detailed view with Identity (Read-only from Marketing), Sales Context (Editable), and Action Panel (Chat/Calendar).
  - **Mock-First Development**: Develop UI against strict TypeScript interfaces and mock data covering 5 scenarios (Empty, Partial, Full, Extreme, Error) before backend integration.

## Impact
- **Affected Specs**: Sales Module, Marketing Module (Consumer).
- **Affected Code**:
  - Backend: `src/modules/sales/infrastructure/models/lead_model.py`, `src/modules/sales/domain/lead.py`, `src/modules/sales/services/lead_service.py`.
  - Frontend: `src/features/sales/*`.
- **Breaking Changes**:
  - `LeadModel` schema change requires database migration.
  - API endpoints for Leads will return a nested `customer` object instead of flat identity fields.

## ADDED Requirements
### Requirement: Unified Identity
The system SHALL store all personal identity data (Name, Email, Phone, Socials) in `CustomerProfile`.
The system SHALL link every `LeadModel` to a `CustomerProfile` via `customer_id`.

#### Scenario: New Lead via Webhook
- **WHEN** a new lead comes in from a channel (e.g., WhatsApp)
- **THEN** the system checks if a `CustomerProfile` exists for that phone number.
- **IF** yes, it links the new `LeadModel` to the existing `CustomerProfile`.
- **IF** no, it creates a new `CustomerProfile` and then links the `LeadModel`.

### Requirement: Atomic Frontend Design
The Frontend SHALL be organized into Atoms, Molecules, and Organisms within `features/sales/components`.

#### Scenario: Component Usage
- **WHEN** a developer needs a lead status badge
- **THEN** they import `TemperatureBadge` from `features/sales/components/atoms`.

## MODIFIED Requirements
### Requirement: Lead Model
`LeadModel` table SHALL NOT contain `full_name`, `email`, `phone`, `social_handle`.
`LeadModel` API responses SHALL include `customer` data joined from `CustomerProfile`.

## REMOVED Requirements
### Requirement: Standalone Lead Identity
**Reason**: Duplication with Marketing Studio.
**Migration**: Run a migration script to extract identity data from `LeadModel` to `CustomerProfile` and set `customer_id`.
