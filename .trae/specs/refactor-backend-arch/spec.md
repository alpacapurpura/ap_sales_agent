# Backend Architecture Refactor Spec

## Why
The current backend structure has accumulated technical debt:
1.  **Misplaced AI Logic**: AI/LLM components (`LandingGenerator`, `OfferGenerator`, `SemanticRouter`) are in `src/services` (Infrastructure) instead of `src/core` (Cognitive Core).
2.  **Fragmented Logic**: Webhook handling is split between `src/api/routes.py` and specific routers (`whatsapp.py`), causing duplication and confusion.
3.  **Unintuitive Folder Structure**: Channel adapters are at the root `src/channels` instead of `src/services/channels` (Infrastructure).
4.  **Code Duplication**: `routes.py` re-implements logic found in routers.

Refactoring is needed to align with the "Domain-Driven" and "Clean Architecture" principles, ensuring all AI logic is centralized in `core` and features are self-contained.

## What Changes

### file_moves
- Move `src/services/landing_generator_service.py` -> `src/core/services/landing_generator.py`
- Move `src/services/offer_generator_service.py` -> `src/core/services/offer_generator.py`
- Move `src/services/image_analysis_service.py` -> `src/core/services/image_analysis.py`
- Move `src/services/semantic_router.py` -> `src/core/services/semantic_router.py`
- Move `src/services/chat_orchestrator.py` -> `src/core/services/chat_orchestrator.py`
- Move `src/channels/` -> `src/services/channels/`

### api_refactor
- **Consolidate Telegram Logic**:
  - Rename `src/api/routers/channels.py` to `src/api/routers/telegram.py`.
  - Move Telegram webhook logic from `src/api/routes.py` to `src/api/routers/telegram.py`.
  - Mount `telegram.py` at `/api/v1` to preserve paths (`/webhooks/telegram...` and `/channels/telegram...`).
- **Consolidate WhatsApp Logic**:
  - Update `src/api/routers/whatsapp.py` to include webhook logic from `src/api/routes.py`.
  - Change mount point to `/api/v1` (prefixing existing routes with `/whatsapp`) to allow defining `/webhooks/whatsapp` in the same file.
- **Deprecate `src/api/routes.py`**:
  - Remove logic. Keep it empty or remove it entirely if `main.py` is updated.

## Impact
- **Affected Specs**: `back-structure.md` (implicitly adhered to).
- **Affected Code**: `main.py`, `api/routers/*`, `services/*`, imports across the system.
- **Breaking Changes**: None externally (API paths preserved). Internal imports will change.

## ADDED Requirements
### Requirement: Centralized AI
The system SHALL store all LLM, Prompt, and Agent logic within `src/core`.

### Requirement: Feature Locality
All logic for a specific integration (e.g., Telegram) SHALL be contained within its specific Router and Service files, not scattered in generic `routes.py`.

## MODIFIED Requirements
### Requirement: API Structure
**Old**: Mixed routing in `routes.py` and `routers/`.
**New**: All routing in `routers/`. `main.py` includes routers directly.
