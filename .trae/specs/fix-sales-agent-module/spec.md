# Sales Agent Module Repair Spec

## Why
The `sales_agent` module (formerly `agents`) was extracted from various locations and is currently non-functional due to mismatched state definitions, broken orchestrator logic, and missing integrations between the main graph and subgraphs. The `chat.py` orchestrator attempts to initialize `AgentState` with fields that do not exist in the current definition, causing runtime errors.

## What Changes
- **Update `AgentState`**: Expand `AgentState` in `application/orchestrator/state.py` to include all fields required by `chat.py` (tenant_config, history, user_profile, etc.).
- **Update `create_initial_state`**: Modify the factory function to accept and initialize these new fields.
- **Integrate Sales Subgraph**: Connect `application/orchestrator/graph.py` to the actual sales agent logic in `application/agents/sales/graph.py`.
- **Fix Imports**: Ensure all references in the module point to the correct internal paths.

## Impact
- **Affected Specs**: Sales Agent, Chat Orchestrator.
- **Affected Code**:
    - `backend/src/modules/sales_agent/application/orchestrator/state.py`
    - `backend/src/modules/sales_agent/application/orchestrator/graph.py`
    - `backend/src/modules/sales_agent/application/agents/sales/graph.py`

## ADDED Requirements
### Requirement: Comprehensive Agent State
The `AgentState` SHALL include:
- `tenant_config` (Dict)
- `history` (List[Dict])
- `user_profile` (Dict)
- `session_active` (bool)
- `active_enrollment` (Optional)
- `active_product` (Optional)
- `last_intent` (Optional[str])
- `launch_stage` (Optional[str])

### Requirement: Functional Orchestrator
The `sales_agent_node` in the orchestrator graph SHALL invoke the `sales_app` subgraph instead of returning a placeholder.

## MODIFIED Requirements
### Requirement: State Initialization
`create_initial_state` SHALL accept all context parameters provided by `ChatOrchestrator` in `chat.py`.

### Requirement: Sales Subgraph Integration
The sales subgraph SHALL be compiled and exposed correctly for the orchestrator to use.
