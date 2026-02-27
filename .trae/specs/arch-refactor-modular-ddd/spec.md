# Architecture Refactor Spec: Modular Monolith for Agentic Systems

## Why
The current architecture follows a Layered DDD approach (`src/api`, `src/core`, `src/services`), which was a good starting point. However, as the "Visionarias Brain" grows with multiple distinct agents (Sales, Onboarding, Web Extractor) and complex domains (Marketing, Admin), the layered approach creates high coupling:
- Logic for different agents is scattered across layers.
- "Core" and "Services" have ambiguous responsibilities (e.g., `src/core` has agent logic, but `src/services` has orchestrators).
- It is difficult to isolate the context (State, Tools, Prompts) of a single agent.

We need a **Modular Monolith** architecture (Vertical Slices) aligned with **Domain-Driven Design (DDD)** principles to ensure scalability, isolation of agent contexts, and maintainability.

## What Changes
We will define the **Target Architecture** in the documentation.
The goal is to move from a **Layered** structure to a **Modular** structure.

### New Structure Definition (`src/modules/`)
Each Bounded Context (e.g., `sales`, `onboarding`) will be a self-contained module with strict layering:

```text
src/
├── shared/                         # Shared Kernel
│   ├── domain/                     # Shared Entities (Tenant, User)
│   ├── infrastructure/             # Base implementations (DB, Auth, LLM Factory)
│   └── utils/                      # Common helpers
│
├── modules/                        # Vertical Slices (Bounded Contexts)
│   ├── sales/                      # Sales Agent Module
│   │   ├── domain/                 # Pure Logic: AgentState, Events, Protocols
│   │   ├── application/            # Orchestration: Graph, Nodes, Use Cases
│   │   ├── infrastructure/         # Implementation: Tools, Repositories, Prompts
│   │   └── api/                    # Interface: Routers
│   │
│   ├── onboarding/                 # Onboarding Agent Module
│   └── ...
```

## Impact
- **Documentation**:
  - Update `\home\chris\AISALESHT\.trae\skills\back-arch-auditor\references\back-structure.md`: Replace outdated layered structure with Modular Monolith structure.
  - Update `\home\chris\AISALESHT\.trae\skills\back-arch-auditor\references\visionarias-stack.md`: Update tech stack description to emphasize Modular DDD and Agentic patterns.
- **Codebase (Future)**: This spec only covers the *documentation update*. The actual code refactoring will be a subsequent execution phase based on these updated standards.

## ADDED Requirements
### Requirement: Architecture Documentation
The documentation SHALL describe the **Modular Monolith** pattern as the standard.
- **AgentState** SHALL be defined in the **Domain** layer of its module.
- **LangGraph Definitions** SHALL be in the **Application** layer of its module.
- **Tools** and **Repositories** SHALL be in the **Infrastructure** layer of its module.

## MODIFIED Requirements
### Requirement: Project Structure
- `src/core` (Cognitive Core) concept is **REMOVED** in favor of distributed `application` layers within modules.
- `src/services` (Infrastructure) is **RENAMED/SPLIT** into `src/shared/infrastructure` and `src/modules/*/infrastructure`.

## REMOVED Requirements
### Requirement: Layered Monolith
**Reason**: High coupling between distinct agent domains.
**Migration**: Adopt Vertical Slices.
