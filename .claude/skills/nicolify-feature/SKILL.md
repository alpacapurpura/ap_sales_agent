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

Before starting, verify agents exist:
- `.claude/agents/nicolify-architect.md`
- `.claude/agents/nicolify-backend.md`
- `.claude/agents/nicolify-agentic.md`
- `.claude/agents/nicolify-backend-auditor.md`
- `.claude/agents/nicolify-ux-designer.md`
- `.claude/agents/nicolify-frontend.md`

## Phase 1: Analysis (YOU — Interactive)

**You handle this phase directly. Do NOT delegate to a subagent.**

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
Before launching agents, ask the user:

> **¿Cómo quieres diseñar la UI?**
> - **A) Exploración creativa** — Proceso de Design Thinking con investigación, propuestas y debate (skill `ux-disruptivo`). Ideal para pantallas nuevas, rediseños, o features donde la UX importa mucho.
> - **B) Pantalla mecánica** — Spec rápido basado en CONTRACT.md (agente `nicolify-ux-designer`). Ideal para CRUDs, tablas, formularios estándar.

If the user chooses **A**: invoke the `ux-disruptivo` skill. The pipeline pauses here until the skill completes and produces a UI-SPEC.md. Then continue with Wave 1 (backend + frontend in parallel, skipping ux-designer agent).

If the user chooses **B** (or doesn't care): proceed with the standard Wave 1 below.

### Determine agents needed
- **Always:** nicolify-backend, nicolify-frontend
- **UX approach B (mechanical):** also nicolify-ux-designer
- **UX approach A (creative):** ux-disruptivo skill already produced UI-SPEC.md — skip ux-designer
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
# Backend tests
docker exec -it visionarias_brain_dev bash -c "cd /app && pytest src/modules/{module}/tests/ -v"

# Backend lint
docker exec -it visionarias_brain_dev bash -c "cd /app && ruff check src --fix"

# Frontend type check
docker exec -it visionarias_client_dev bash -c "npx tsc --noEmit"

# Frontend lint
docker exec -it visionarias_client_dev bash -c "npx next lint"

# Frontend build
docker exec -it visionarias_client_dev bash -c "npx next build"
```

If Playwright tests exist:
```bash
docker exec -it visionarias_client_dev bash -c "npx playwright test"
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
- Backend: [pass/fail]
- Frontend: [pass/fail]
- Lint: [pass/fail]

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
