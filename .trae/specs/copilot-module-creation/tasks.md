# Tasks

- [x] Task 1: Create Copilot Module Structure
  - [x] Create directories: `api`, `application`, `domain`, `infrastructure`, `utils`.
  - [x] Create subdirectories: `application/agents`, `application/orchestrator`, `application/services`, `infrastructure/prompts`.
  - [x] Create `__init__.py` files for Python packages.

- [ ] Task 2: Move Web Extraction & Analysis Components
  - [ ] Move `sales_agent/application/agents/web_extractor` -> `copilot/application/agents/web_extractor`.
  - [ ] Move `sales_agent/application/services/web_extractor_adapter.py` -> `copilot/application/services/web_extractor_adapter.py`.
  - [ ] Move `sales_agent/application/services/file_parsing_service.py` -> `copilot/application/services/file_parsing_service.py`.
  - [ ] Move `sales_agent/application/services/image_analysis.py` -> `copilot/application/services/image_analysis.py`.
  - [ ] Move `sales_agent/infrastructure/prompts/brand_extraction` -> `copilot/infrastructure/prompts/brand_extraction`.

- [ ] Task 3: Update Imports & References
  - [ ] Update imports in `backend/src/modules/brand/application/extraction_service.py` to point to `copilot`.
  - [ ] Update imports in `backend/src/modules/brand/api/extraction.py` to point to `copilot`.
  - [ ] Verify if any other files reference the moved components.

- [ ] Task 4: Create Basic Copilot Orchestrator
  - [ ] Create `copilot/application/orchestrator/graph.py` (simple placeholder).
  - [ ] Create `copilot/application/orchestrator/state.py` (CopilotState).
  - [ ] Create `copilot/application/orchestrator/chat.py` (CopilotOrchestrator).

# Task Dependencies
- Task 2 depends on Task 1.
- Task 3 depends on Task 2.
- Task 4 depends on Task 1.
