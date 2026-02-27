# Core Directory Restructuring Plan

This plan organizes `backend/src/core` into a clean, feature-driven architecture suitable for complex Agentic Systems (2026 standards).

## 1. Directory Structure

We will transition from a flat/mixed structure to a modular one:

```
backend/src/core/
├── agents/                  # Autonomous Agents (Features)
│   ├── orchestrator/        # The Main "Brain" (Root Graph)
│   │   ├── graph.py         # Was agent.py
│   │   ├── nodes.py         # Was nodes.py (generic parts)
│   │   ├── state.py         # Was state.py (Global AgentState)
│   │   └── prompts.py       # (New)
│   ├── sales/               # Sales Swarm (Sub-graph)
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   ├── prompts.py
│   │   └── state.py         # (If specific state needed)
│   └── onboarding/          # Onboarding Agent
│       ├── graph.py
│       ├── nodes.py
│       ├── nodes_research.py
│       ├── state.py
│       └── prompts.py
├── domain/                  # Shared Business Logic & Schemas
│   ├── offer/               # Offer Domain
│   │   └── schema.py
│   └── schema.py            # Global Types (User, Tenant)
├── services/                # Infrastructure Services
│   ├── llm/                 # LLM Factory & Providers
│   │   ├── factory.py
│   │   └── ...
│   ├── tools/               # External Tool Integrations
│   │   └── research.py
│   └── tracing.py           # Observability
└── config.py                # Core Configuration
```

## 2. Execution Steps

### Phase 1: Create Directories
1. Create `backend/src/core/agents/orchestrator`.
2. Create `backend/src/core/domain`.
3. Create `backend/src/core/services`.

### Phase 2: Move Files (Refactoring)
1. **Orchestrator**:
   - Move `src/core/agent.py` -> `src/core/agents/orchestrator/graph.py`
   - Move `src/core/nodes.py` -> `src/core/agents/orchestrator/nodes.py`
   - Move `src/core/state.py` -> `src/core/agents/orchestrator/state.py`

2. **Domain**:
   - Move `src/core/schema.py` -> `src/core/domain/schema.py`
   - Move `src/core/offer/` -> `src/core/domain/offer/`

3. **Services**:
   - Move `src/core/llm/` -> `src/core/services/llm/`
   - Move `src/core/tools/` -> `src/core/services/tools/`
   - Move `src/core/tracing.py` -> `src/core/services/tracing.py`

4. **Agents**:
   - Move `src/core/onboarding/` -> `src/core/agents/onboarding/`
   - Move `src/core/sales/` -> `src/core/agents/sales/`

### Phase 3: Update Imports (The Heavy Lifting)
We will need to scan and update imports in all moved files and their consumers.
- `from src.core.state` -> `from src.core.agents.orchestrator.state`
- `from src.core.nodes` -> `from src.core.agents.orchestrator.nodes`
- `from src.core.schema` -> `from src.core.domain.schema`
- `from src.core.llm` -> `from src.core.services.llm`
- `from src.core.tools` -> `from src.core.services.tools`
- `from src.core.tracing` -> `from src.core.services.tracing`

### Phase 4: Cleanup
- Remove empty directories in `src/core`.
- Verify `__init__.py` files exist where needed.

## 3. Verification
- Run `python -m compileall backend/src/core` to ensure no syntax errors or broken imports in python files.
