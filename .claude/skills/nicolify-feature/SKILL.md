---
name: nicolify-feature
description: Full-stack feature development pipeline for Nicolify. Orchestrates 6 specialized agents (architect, backend, agentic, backend-auditor, ux-designer, frontend) through 4 phases with user checkpoints. Use when building new features, adding CRUD endpoints, creating new UI screens, or implementing cross-stack functionality.
triggers:
  - "nueva funcionalidad"
  - "nuevo feature"
  - "implementa feature"
  - "crea feature"
  - "build feature"
  - "nicolify-feature"
  - "full-stack feature"
  - "crear módulo"
  - "agregar funcionalidad"
---

# Nicolify Feature Pipeline

You are the orchestrator for Nicolify's full-stack feature development. You coordinate 6 specialized agents through 4 phases, with user approval checkpoints between phases.

## Prerequisites

Before starting, verify all agents in `.claude/agents/nicolify-*.md` exist (architect, backend, agentic, backend-auditor, ux-designer, frontend).

## Phase 1: Analysis (YOU — Interactive)

1. Read `docs/domains/INDEX.md` to understand available modules
2. Interview the user to clarify:
   - What is the feature? (user story or description)
   - Which module(s) does it affect?
   - What entities/data are involved?
   - What UI does the user need?
   - Are there AI/agentic components? (LangGraph, RAG, etc.)
3. Read the relevant module doc (`docs/domains/module_*.md`)
4. Produce a `REQUIREMENTS.md` with:
   - Feature description
   - Affected modules
   - Entities to create/modify
   - API endpoints needed
   - UI screens needed
   - Whether agentic development is needed (yes/no)
   - Acceptance criteria

### Checkpoint 1
Show REQUIREMENTS.md to the user. Ask for approval using `AskUserQuestion`:
- "Are these requirements correct? Any changes needed?"
- Wait for user confirmation before proceeding.

---

## Phase 2: Architecture (Subagent — Sequential)

Spawn the architect agent:

```
Agent(
  subagent_type="nicolify-architect",
  prompt="Read REQUIREMENTS.md and produce CONTRACT.md following your design rules. Feature: [description]. Module: [module]. Requirements file: [path]",
  description="Design API contract"
)
```

Wait for CONTRACT.md to be produced.

### Checkpoint 2
Read CONTRACT.md and present a summary to the user:
- Models to be created
- API endpoints
- TypeScript types
- Ask: "Does this contract look correct?"
- Wait for approval.

---

## Phase 3: Implementation (Subagents — Parallel Waves)

### UX Approach Decision
Before launching agents, ask the user to choose a UI design approach:

> **A) Creative exploration** — Design Thinking process with research, proposals, and debate (skill `ux-disruptivo`). Best for new screens, redesigns, or UX-critical features.
> **B) Mechanical screen** — Quick spec from CONTRACT.md (agent `nicolify-ux-designer`). Best for CRUDs, tables, and standard forms.

- **If A:** invoke the `ux-disruptivo` skill. Pause until it completes and produces `UI-SPEC.md`. Then proceed to Wave 1 skipping the ux-designer agent.
- **If B (or no preference):** proceed with the standard Wave 1 below.

### Determine agents needed
- **Always:** nicolify-backend, nicolify-frontend
- **UX approach B:** also nicolify-ux-designer
- **UX approach A:** ux-disruptivo already produced UI-SPEC.md — skip ux-designer
- **Conditional:** nicolify-agentic (only if REQUIREMENTS.md flags agentic=yes)

### Wave 1: Parallel implementation
Launch these agents IN PARALLEL (single message, multiple Agent tool calls):

```
Agent(
  subagent_type="nicolify-backend",
  prompt="Implement backend from CONTRACT.md at [path]. Module: [module]. Follow Inside-Out DDD pattern. Run tests when done.",
  description="Implement backend",
  run_in_background=true
)

Agent(
  subagent_type="nicolify-ux-designer",
  prompt="Design UI from CONTRACT.md at [path]. Module: [module]. Check available Shadcn components. Produce UI-SPEC.md.",
  description="Design UX/UI",
  run_in_background=true
)

Agent(
  subagent_type="nicolify-frontend",
  prompt="Implement frontend from CONTRACT.md at [path]. Start with types and API layer. When UI-SPEC.md appears, implement components. Module: [module].",
  description="Implement frontend",
  run_in_background=true
)

# CONDITIONAL: Only if agentic development is needed
Agent(
  subagent_type="nicolify-agentic",
  prompt="Implement agentic workflow from CONTRACT.md at [path]. Module: [module]. Follow existing LangGraph patterns.",
  description="Implement agentic",
  run_in_background=true
)
```

### Wave 2: Backend Audit (after backend completes)
When the backend agent completes:

```
Agent(
  subagent_type="nicolify-backend-auditor",
  prompt="Audit backend implementation for [feature]. Check recent commits and files in backend/src/modules/[module]/. Read CONTRACT.md for spec compliance. Produce REVIEW.md.",
  description="Audit backend code"
)
```

### Wave 3: Fix audit findings (if FAIL found)
Read REVIEW.md. If any FAIL findings:

```
Agent(
  subagent_type="nicolify-backend",
  prompt="Fix these audit findings from REVIEW.md at [path]. Apply only the FAIL items. Run tests after fixes.",
  description="Fix audit findings"
)
```

### Checkpoint 3
Summarize implementation results to the user:
- Files created/modified (backend + frontend)
- Audit results (PASS/WARN/FAIL counts)
- Any deviations from CONTRACT.md
- Ask: "Implementation complete. Ready for testing?"

---

## Phase 4: Testing (YOU — Direct Execution)

Run tests inside Docker:

```bash
# Backend lint
docker exec -it visionarias_brain_dev bash -c "cd /app && ruff check src --fix"

# Backend tests with coverage
docker exec -it visionarias_brain_dev bash -c "cd /app && pytest --cov=src/modules --cov=src/shared --cov-report=term -x -q --tb=short"

# Frontend type check
docker exec -it visionarias_client_dev bash -c "npx tsc --noEmit"

# Frontend lint
docker exec -it visionarias_client_dev bash -c "npx next lint"

# Frontend tests with coverage
docker exec -it visionarias_client_dev bash -c "npx vitest run --coverage"

# E2E Smoke (obligatorio si el feature tiene UI nueva)
make e2e-smoke
```

### Final Output
Present results:
```
## Feature Complete: [Feature Name]

**Files Created:**
- [list of new files]

**Files Modified:**
- [list of modified files]

**Test Results:**
| Step | Result | Coverage |
|---|---|---|
| Backend lint | PASS/FAIL | — |
| Backend tests | X passed | XX% (min 60%) |
| Frontend types | PASS/FAIL | — |
| Frontend lint | PASS/FAIL | — |
| Frontend tests | X passed | XX% (min 20%) |
| E2E Smoke | X passed | — |

**Audit:** [PASS/WARN/FAIL with summary]

**Artifacts:**
- REQUIREMENTS.md
- CONTRACT.md
- UI-SPEC.md
- REVIEW.md
```

---

## Error Handling

- If an agent fails, read its output to understand why
- If a backend agent fails on migration: check existing tables, verify idempotency
- If frontend agent fails on types: verify CONTRACT.md TypeScript section is complete
- If auditor finds FAIL: always run Wave 3 fixes before proceeding
- If tests fail: investigate, fix in the appropriate agent (backend or frontend), re-run
