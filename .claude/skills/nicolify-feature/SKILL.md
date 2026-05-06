---
name: nicolify-feature-deprecated
description: "DEPRECATED skill (post pm-redesign 2026-05-06 Wave 3). Replaced by 3-conversation flow (Discovery+Ready / Autonomous Build / Review+Merge) orchestrated by /pm + /po-ux + /architect + /dev-team + /auditor. NEVER invoke this skill — its monolithic 4-phase orchestrator is incompatible with the new context-isolated 3-conversation paradigm. For new full-stack features, follow: idea → /pm validates → /po-ux or /po (spec) → /architect (ready package) → /dev-team (autonomous build) → /auditor (review+merge). See docs/process/pm-redesign-2026-05.md."
---

# Nicolify Feature Pipeline — DEPRECATED (Wave 3 pm-redesign 2026-05-06)

> **🛑 DEPRECATED.** Do NOT invoke this skill.
>
> **Replaced by 3-conversation flow** orchestrated by:
> - `/pm` — director, owner BACKLOG.{yaml,md} + outcomes/ + stories/
> - `/po-ux` (UI std) or `/po` (service) or `/po + /ux-agentico` (agentic) — spec
> - `/architect` — ready package (03-arch + 04-validators + 05-guidelines + 06-tickets)
> - `/dev-team` — autonomous build Conv 2 (opencode + Sonnet iterating vs validators)
> - `/auditor` — review+merge Conv 3 (CHECKPOINTS.md C1-C5)
>
> **Why deprecated:** the monolithic 4-phase orchestrator with 6 hardcoded subagents is incompatible with:
> - Context isolation between Conversations (each Conv has its own model + scope)
> - 7-state vocabulary (idea/validated/ready/building/review/done/parked/dropped)
> - WIP caps (validated≤10, ready≤5, building≤3, review≤2)
> - Autonomous build mode (opencode + Sonnet iterating against `04-validators.yaml` without supervision)
> - Story folder structure flat at `docs/product/stories/{story-id}/`
>
> **For history:** legacy content preserved below for reference. Active workflow → see `docs/process/pm-redesign-2026-05.md`.

## Replacement workflow

```
Conv 1 — DISCOVERY + READY  (Chris + /pm + /po-ux + /architect)
  Chris idea → /pm validates (OST) → state=validated →
  /po-ux (UI std) o /po (service) o /po + /ux-agentico (agentic) → 01-spec.md ratificada →
  /architect spawna /architect-{be,fe,agentic} → ready package →
  state=validated → ready

Conv 2 — AUTONOMOUS BUILD   (opencode + Sonnet iterando vs validators)
  /dev-team toma 06-tickets.yaml ticket-por-ticket →
  loop: implement → run validators → fix → repeat hasta GREEN o cap_reached →
  state=ready → building → review

Conv 3 — REVIEW + MERGE     (/auditor + /pm merge)
  /auditor spawna auditor-{be,fe,agentic} → CHECKPOINTS.md C1-C5 →
  /pm aplica merge → scenarios migran a capability → archive story →
  state=review → done
```

## Legacy reference (DO NOT invoke)

> The original nicolify-feature skill orchestrated 6 agents through 4 phases (Analysis, Architecture, Backend+Agentic+Auditor parallel, UX+Frontend) with user checkpoints. This forced a single conversation context to handle all phases, causing token bloat and scope drift. The new 3-conversation paradigm uses context isolation to keep each phase efficient.

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
  prompt="Implement backend from CONTRACT.md at [path]. Module: [module]. Follow TDD + Inside-Out DDD: for each layer, write failing tests FIRST (RED), then implement until tests pass (GREEN). Coverage must increase.",
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
  prompt="Implement frontend from CONTRACT.md at [path]. Follow TDD: write hook/component tests FIRST (RED), then implement (GREEN). Start with types and API layer. When UI-SPEC.md appears, write component tests then implement. Module: [module].",
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

**Los tests deben existir desde Phase 3 (TDD).** Esta fase verifica cobertura e integración.
Si algún módulo carece de tests, escribirlos AHORA antes de continuar.

Run all tests natively in WSL (NEVER use docker exec for lint/tests):

```bash
# Backend lint
cd backend && .venv/bin/ruff check src/ --fix --no-cache

# Backend format check
cd backend && .venv/bin/ruff format --check src/

# Architectural fitness (DDD boundaries, API contracts, conventions)
cd backend && .venv/bin/pytest tests/architecture/ -v

# Backend tests with coverage
cd backend && .venv/bin/pytest --cov=src/modules --cov=src/shared --cov-report=term -x -q --tb=short

# Backend security audit
cd backend && .venv/bin/pip-audit --strict --desc

# Frontend type check
cd frontend && npx tsc --noEmit

# Frontend lint
cd frontend && npx eslint src/

# Frontend tests with coverage
cd frontend && npx vitest run --coverage

# Frontend security audit
cd frontend && npm audit --audit-level=high

# E2E Smoke (obligatorio si el feature tiene UI nueva — nativo, NUNCA Docker)
cd frontend && npx playwright test --project=smoke
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
| Arch fitness | PASS/FAIL | — |
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
