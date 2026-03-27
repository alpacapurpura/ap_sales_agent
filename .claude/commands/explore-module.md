Explore the DDD structure of a backend module.

Arguments: $ARGUMENTS (module name, e.g. "brand", "offer", "copilot")

Steps:
1. Show directory tree: `find backend/src/modules/$ARGUMENTS -type f -name "*.py" | head -50`
2. Read the domain layer: list models, value objects, repository interfaces in `domain/`
3. Read the API layer: list routes and DTOs in `api/`
4. Read the application layer: list services/use cases in `application/`
5. Summarize: models, endpoints, services, and dependencies
