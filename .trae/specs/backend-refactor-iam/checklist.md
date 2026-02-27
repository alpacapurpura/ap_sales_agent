# Checklist

- [ ] `User` domain entity is pure Python/Pydantic.
- [ ] `Tenant` domain entity is pure Python/Pydantic.
- [ ] Infrastructure models inherit from `src.shared.infrastructure.db.base_model.Base`.
- [ ] Repositories return Domain Entities, not SQLAlchemy models.
- [ ] Services depend on Repositories (DI).
- [ ] API returns correct DTOs.
- [ ] No circular imports.
