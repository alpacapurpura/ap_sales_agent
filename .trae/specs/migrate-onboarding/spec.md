# Migrate Onboarding Module Spec

## Why
The `backend/src/modules/onboarding` module is an anomaly in the domain architecture. Its functionality (analyzing chat history to extract brand voice/style) belongs to the `Brand` domain (Identity/Voice) and the `Copilot` domain (AI Configuration Assistant), as defined in `docs/domains/INDEX.md`. Moving it ensures strict domain adherence.

## What Changes
- **Move Agent Logic to Copilot**:
  - `onboarding/application/agents/*` -> `copilot/application/agents/style_analyzer/`
  - `onboarding/application/tools/*` -> `copilot/application/tools/`
  - This centralizes all AI configuration assistants in `Copilot`.

- **Move API Endpoint to Brand**:
  - `onboarding/api/onboarding.py` -> `brand/api/style.py`
  - This places the "Style Extraction" capability within the `Brand` domain, which owns the "Tone of Voice" and "Identity".

- **Update Entry Point**:
  - Update `backend/src/main.py` to remove `onboarding` router and include `brand.api.style` router (likely via `brand.api.router` or directly).

- **Cleanup**:
  - Delete `backend/src/modules/onboarding`.

## Impact
- **Affected Specs**: Brand, Copilot.
- **Affected Code**:
  - `backend/src/main.py`
  - `backend/src/modules/brand/api/style.py` (New)
  - `backend/src/modules/copilot/application/agents/style_analyzer/*` (New)

## ADDED Requirements
### Requirement: Style Analysis in Brand
The system SHALL expose an endpoint to analyze communication style within the `Brand` module.

### Requirement: Style Analyzer Agent in Copilot
The system SHALL host the Style Analyzer LangGraph agent within the `Copilot` module.

## REMOVED Requirements
### Requirement: Onboarding Module
**Reason**: Merged into Brand and Copilot.
**Migration**: Move files.
