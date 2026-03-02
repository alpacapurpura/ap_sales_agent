# Copilot Module Creation Spec

## Why
The system requires a clear separation between the "Sales Agent" (customer-facing) and the "Copilot" (user-facing assistant). Currently, internal tools like web extraction, file parsing, and brand analysis reside in `sales_agent`, violating the separation of concerns. The `copilot` module will house all logic related to assisting the user in configuring and using the system.

## What Changes
- Create `backend/src/modules/copilot` with Agentic-DDD structure.
- Move non-sales capabilities from `sales_agent` to `copilot`:
    - **Agents**: `web_extractor`
    - **Services**: `web_extractor_adapter.py`, `file_parsing_service.py`, `image_analysis.py`
    - **Prompts**: `brand_extraction` folder
- Update imports in `sales_agent` (if any) to reference the new locations in `copilot` or refactor as needed.
- Ensure `copilot` has its own Orchestrator and Agent definitions for internal tasks.

## Impact
- **Modules**: `sales_agent` (files removed), `copilot` (new module).
- **Code**: Imports across the system referencing the moved services must be updated.

## ADDED Requirements
### Requirement: Copilot Module Structure
The `copilot` module SHALL follow the Agentic-DDD structure:
- `api/`: Endpoints for user interaction.
- `application/`: Orchestration and Agents (Web Extractor, Brand Analyst).
- `domain/`: Entities for internal tasks (e.g., `ExtractionTask`, `AnalysisResult`).
- `infrastructure/`: Implementations (LLM, Prompts).

## MOVED Requirements
### Requirement: Web Extraction & Analysis
- **Source**: `sales_agent/application/agents/web_extractor`, `sales_agent/application/services/*`
- **Destination**: `copilot/application/agents/web_extractor`, `copilot/application/services/*`
- **Reason**: These are tools for the user to gather info, not strictly for the sales conversation loop.

### Requirement: Brand Extraction Prompts
- **Source**: `sales_agent/infrastructure/prompts/brand_extraction`
- **Destination**: `copilot/infrastructure/prompts/brand_extraction`
- **Reason**: Brand extraction is a setup/configuration task assisted by the Copilot.
