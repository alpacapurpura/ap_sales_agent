# Backend Architecture Auditor (Visionarias Brain Edition)

This skill enforces the **Modular Monolith (DDD)** architecture for Visionarias Brain. It acts as a gatekeeper to ensure code quality, structural integrity, and adherence to domain-driven design principles.

## 🏗️ Architecture Standard

### 1. The "Must-Have" Structure
The project MUST adhere to this directory layout:

```
backend/src/
├── main.py              # Entry point (registers module routers)
├── config.py            # Global config
├── shared/              # Shared Kernel (Cross-cutting concerns)
│   ├── core/            # Base Agent logic, ABCs
│   ├── infrastructure/  # DB Base, LLM Providers, External Clients
│   └── utils/           # Common utilities
└── modules/             # Business Domains (Bounded Contexts)
    ├── iam/
    ├── sales/
    ├── communication/
    ├── offer/
    ├── marketing/
    ├── brand/
    ├── landing/
    ├── gallery/
    ├── integration/
    └── onboarding/
```

### 2. Module Anatomy (DDD Layers)
Every module in `src/modules/` MUST have these strict layers:

1.  **`domain/`**: **PURE PYTHON**.
    -   Contains Entities (Pydantic models), Value Objects, Domain Events, Repository Interfaces.
    -   **Strict Ban**: NO external infrastructure dependencies (SQLAlchemy, FastAPI).
2.  **`application/`**: **ORCHESTRATION**.
    -   Contains Use Cases, Services, Agent Graphs.
    -   Depends on `domain` and `shared`.
3.  **`infrastructure/`**: **IMPLEMENTATION**.
    -   Contains Repository Implementations, DB Models (SQLAlchemy), External Adapters.
    -   Depends on `domain` (implements interfaces).
4.  **`api/`**: **INTERFACE**.
    -   Contains FastAPI Routers, DTOs.
    -   Entry point for HTTP requests.

---

## 🕵️ Audit Checklist

Use this checklist to validate any code changes or new features.

### Phase 1: Structural Integrity
- [ ] **No Legacy Folders**: Verify `src/core`, `src/services`, `src/api/routers` (root) DO NOT exist.
- [ ] **Module Existence**: Ensure code belongs to a valid module in `src/modules`.
- [ ] **Shared Kernel**: Ensure `src/shared` contains only truly common code.

### Phase 2: Code Standards (Naming & Typing)
Refer to [CODE_STANDARDS.md](references/CODE_STANDARDS.md) for detailed rules.

- [ ] **Files/Dirs**: `snake_case`.
- [ ] **Classes/Types**: `PascalCase`.
- [ ] **Functions/Variables**: `snake_case`.
- [ ] **Constants**: `UPPER_CASE`.
- [ ] **Typing**: All public functions must be typed.

### Phase 3: Dependency Rules (DDD Strict)
- [ ] **Domain Purity**: `domain/` must NOT import `sqlalchemy`.
- [ ] **Infrastructure Isolation**: `infrastructure/` implements interfaces defined in `domain/`.
- [ ] **Cross-Module Limits**:
    -   **Strict Ban**: Importing `infrastructure/models.py` from another module.
    -   **Strict Ban**: SQL Joins between modules.
    -   **Allowed**: Calling `application/services` or using Domain Events.

### Phase 4: Database Isolation
- [ ] **No Cross-FKs**: `ForeignKey` must point to tables within the same module.
- [ ] **Tenant Filter**: All repositories must apply `_apply_tenant_filter`.

---

## 🛠️ Tools & Commands

### Ruff (Linter & Formatter)
Always run `ruff` to catch standard violations automatically.
```bash
# Option 1: Local
ruff check backend/src --fix

# Option 2: Docker
docker exec visionarias_brain_dev ruff check src --fix
```

## 📚 References
- [Audit Checklist](references/AUDIT_CHECKLIST.md): Full validation list.
- [Code Standards](references/CODE_STANDARDS.md): Naming and style guide.
- [Architecture Patterns](references/architecture-patterns.md): DDD & Clean Arch principles.
