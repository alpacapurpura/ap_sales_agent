# Docs Structure Setup Spec

## Why

To enable "Agent-First Documentation" and provide a clear structure for documenting business logic, rules, and edge cases for each domain module. This will help future agents understand the context before coding.

## What Changes

* Create a new directory `docs/domains/` in the project root.

* Create `docs/domains/INDEX.md` as a "Context Router" mapping domains to their documentation files.

* Create individual Markdown files for each identified domain module with a standardized template.

## Impact

* **Affected specs**: None (New documentation capability).

* **Affected code**: None (Documentation only).

## ADDED Requirements

### Requirement: Documentation Structure

The system SHALL have a dedicated `docs/domains/` directory containing:

* An `INDEX.md` file that serves as a directory and instruction for agents.

* Individual markdown files for each business domain (`module_*.md`).

### Requirement: Domain File Template

Each domain file SHALL follow this structure:

* **Frontmatter**:

  ```yaml
  module: [name]
  status: active
  core_files: []
  ```

* **Sections**:

  1. Propósito del Negocio (El "Por Qué")
  2. Reglas de Negocio Estrictas (Business Rules)
  3. Mapa de Código (Rutas relativas a Front y Back)
  4. Casos Borde Conocidos (Edge Cases)

## Identified Domains

Based on `backend/src/modules/` and `frontend/src/features/`:

1. Offer (`module_offer.md`)
2. Brand (`module_brand.md`)
3. Sales (`module_sales.md`)
4. Marketing (`module_marketing.md`)
5. Landing (`module_landing.md`)
6. IAM (`module_iam.md`)
7. Communication (`module_communication.md`)
8. Gallery (`module_gallery.md`)
9. Integration (`module_integration.md`)
10. Onboarding (`module_onboarding.md`)

