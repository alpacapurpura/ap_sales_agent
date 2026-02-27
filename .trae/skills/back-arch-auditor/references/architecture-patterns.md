# Architecture Patterns: Clean Architecture & DDD

This reference guides the implementation of Clean Architecture and Domain-Driven Design (DDD) principles within the Visionarias Brain backend.

## Clean Architecture Principles

1.  **Dependency Rule**: Dependencies point **inward**.
    -   `api` (Outer) -> `application` (Inner) -> `domain` (Core).
    -   `infrastructure` (Outer) implements interfaces defined in `domain`.
2.  **Independence**:
    -   The Core Domain should not depend on frameworks (FastAPI), database (SQLAlchemy), or external agencies.
    -   Entities should be plain Python objects (Pydantic/Dataclasses).

## Domain-Driven Design (DDD)

### Tactical Patterns

#### 1. Entities (`src/modules/{name}/domain/entities.py`)
Objects defined by their identity, not just their attributes. They encapsulate business behavior.

```python
# src/modules/iam/domain/entities.py
class User(BaseModel):
    id: str
    email: EmailStr
    is_active: bool

    def activate(self):
        self.is_active = True
```

#### 2. Value Objects
Objects defined by their attributes. Immutable.

```python
# src/modules/sales/domain/value_objects.py
class Money(BaseModel):
    amount: Decimal
    currency: str
    model_config = ConfigDict(frozen=True)  # Immutable
```

#### 3. Repositories (Interfaces)
Define the contract for data access in the Domain layer (`src/modules/{name}/domain/interfaces.py`), implement in Infrastructure (`src/modules/{name}/infrastructure/repositories/`).

```python
# src/modules/iam/domain/interfaces.py
class IUserRepository(ABC):
    @abstractmethod
    async def get(self, id: str) -> Optional[User]: ...
```

#### 4. Domain Services (`src/modules/{name}/application/services/`)
Logic that doesn't naturally fit into a single Entity.

## Directory Mapping

| Pattern Concept | Visionarias Path |
| :--- | :--- |
| **Entities** | `src/modules/{name}/domain/entities.py` |
| **Use Cases** | `src/modules/{name}/application/services/` |
| **Interface Adapters** | `src/modules/{name}/api/` (Controllers) |
| **Frameworks & Drivers** | `src/modules/{name}/infrastructure/` (DB), `src/main.py` (App) |

## Common Refactoring Targets

### Anemic Domain Models
**Problem**: Domain objects are just data holders (DTOs) and all logic is in Services.
**Fix**: Move behavior into the Domain Model.

```python
# BEFORE (Anemic)
def activate_user(user: User):
    user.status = "active"
    user.activated_at = now()

# AFTER (Rich Model)
# User.activate() handles its own state transition invariants.
```

### Leaky Abstractions
**Problem**: Database details (SQLAlchemy models) leaking into the API or Business Logic.
**Fix**: Use Mappers (`model_validate`) to convert DB Models -> Domain Models before returning from Repositories.

### Fat Controllers (Routers)
**Problem**: API Routers containing business logic.
**Fix**: Extract logic to a Service or Use Case class. The Router should only parse requests and format responses.
