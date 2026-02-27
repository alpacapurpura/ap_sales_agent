# Visionarias Backend Tech Stack & Architecture

## Core Technology Stack

-   **Framework**: FastAPI (Async)
-   **Orchestration**: LangGraph (Agentic Flows, Domain-Driven)
-   **Database**: PostgreSQL 15 + SQLAlchemy (Async) + Alembic
-   **Vector Store**: Qdrant (Partitioned by `tenant_id`)
-   **Validation**: Pydantic V2 (Strict ConfigDict)
-   **Task Queue**: Redis 7 (Celery/Arq optional)

## Project Structure (Modular Monolith)

The project follows a **Modular Monolith** architecture, where each business capability (Sales, Onboarding, Admin) is a self-contained module (Vertical Slice).

### 1. Modules (Bounded Contexts)
Located in `src/modules/{context_name}`. Each module contains:
-   **Domain Layer**: Pure logic, Entities, and `AgentState` definitions. No external dependencies.
-   **Application Layer**: Orchestration logic, LangGraph workflows (`graph.py`, `nodes.py`), and Use Cases.
-   **Infrastructure Layer**: Database repositories, LLM adapters, and Tool implementations.
-   **Interface Layer**: API Routers and Webhook handlers.

### 2. Shared Kernel (`src/shared`)
Common code shared across modules:
-   **Domain**: `Tenant`, `User` entities.
-   **Infrastructure**: `BaseRepository`, `DB Session`, `Auth Middleware`.

## Agentic DDD Patterns

To ensure scalability and maintainability of AI Agents, we apply strict DDD patterns:

### The Agent as an Aggregate Root
-   **AgentState**: Acts as the transactional boundary. It is defined as a Pydantic Model or TypedDict in the **Domain Layer**.
-   **Graph**: The `StateGraph` (in Application Layer) enforces valid state transitions.
-   **Nodes**: Pure functions (Domain Services) that take state and return updates.

### Domain Purity in Agents
-   **Nodes must be Deterministic**: Avoid direct DB/API calls inside nodes if possible.
-   **Dependency Injection**: Inject services/tools into nodes via the `config` parameter or a Service Locator pattern.
-   **Ubiquitous Language**: Use business terms (e.g., `qualify_lead`, `close_deal`) for node names, not technical terms (`llm_node`, `process_text`).

## Multi-Tenancy (Critical Security Rule)

Visionarias Brain is a multi-tenant system. Every data access must be scoped to a `tenant_id`.

-   **Database Access**:
    -   ALL Repositories must inherit from `BaseRepository`.
    -   ALL queries must use `_apply_tenant_filter(query, model)`.
    -   **Never** use raw SQL or unfiltered queries in shared tables.
-   **Vector Store**:
    -   Qdrant collections are partitioned by payload `tenant_id`.
    -   Always filter vector search by `tenant_id`.

## Database Patterns

### Repository Pattern
All database interaction happens through Repositories located in the **Infrastructure Layer** of each module.

```python
# GOOD (Module-Specific Repository)
# src/modules/sales/infrastructure/repositories.py
class SalesLeadRepository(BaseRepository):
    def get_qualified_leads(self) -> List[Lead]:
        return self.db.query(Lead).filter(Lead.status == 'qualified').all()
```

### Sync vs Async
-   **Goal**: Full Async.
-   **Rule**: Use `AsyncSession` for all new modules. Legacy sync code should be migrated incrementally.
