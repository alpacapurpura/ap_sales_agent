# Software Design & Engineering Best Practices

## Clean Code
### Naming
- **Meaningful**: Variables and functions should be self-documenting. Avoid abbreviations (e.g., `calculate_user_retention` vs `calc_usr_ret`).
- **Context**: Use domain terminology.

### Functions
- **Small**: Functions should do one thing and do it well (Single Responsibility Principle).
- **Arguments**: Limit arguments to 3 or fewer. Use objects/dataclasses for complex inputs.
- **Side Effects**: Avoid side effects unless explicitly intended (e.g., I/O).

### Error Handling
- **Exceptions**: Use custom exceptions for domain-specific errors. Catch specific exceptions, not broad `Exception`.
- **Feedback**: Provide actionable error messages.

## SOLID Principles
### Single Responsibility (SRP)
- Each class/module/agent node should have only one reason to change.
- Separate business logic from infrastructure/persistence.

### Open/Closed (OCP)
- Software entities should be open for extension but closed for modification.
- Use interfaces/abstract base classes (ABCs) to define contracts.
- Implement new behavior by adding new classes, not modifying existing ones.

### Liskov Substitution (LSP)
- Subtypes must be substitutable for their base types.
- Ensure derived classes fulfill the contract of the base class.

### Interface Segregation (ISP)
- Clients should not be forced to depend on methods they do not use.
- Prefer smaller, specific interfaces over large, general-purpose ones.

### Dependency Inversion (DIP)
- Depend on abstractions, not concretions.
- Use dependency injection to decouple components (e.g., inject `DatabaseService` into `UserService`).

## Gang of Four (GoF) Patterns relevant to Agents
### Behavioral Patterns
- **Strategy**: Define a family of algorithms (e.g., different search strategies or LLM models) and make them interchangeable.
- **State**: Allow an object to alter its behavior when its internal state changes (Core to LangGraph).
- **Observer**: Define a one-to-many dependency so that when one object changes state, all its dependents are notified (e.g., Logging, Monitoring).
- **Command**: Encapsulate a request as an object (e.g., Tool calls).

### Structural Patterns
- **Adapter**: Convert the interface of a class into another interface clients expect (e.g., wrapping external APIs for agent tools).
- **Decorator**: Attach additional responsibilities to an object dynamically (e.g., adding logging/retry logic to tools).
- **Facade**: Provide a unified interface to a set of interfaces in a subsystem (e.g., simplify complex library usage for the agent).

### Creational Patterns
- **Factory Method**: Define an interface for creating an object, but let subclasses decide which class to instantiate (e.g., creating different types of agents).
- **Singleton**: Ensure a class has only one instance (e.g., Global configuration, DB connection pool - *use with caution*).

## Python Specifics
- **Type Hinting**: Use strict type hints (`mypy`, `pydantic`) for robustness.
- **Docstrings**: Use Google or NumPy style docstrings for all public methods/classes.
- **Context Managers**: Use `with` statements for resource management (files, network connections).
