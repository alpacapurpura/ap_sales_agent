# Checklist

- [x] Shared Kernel implemented and strictly separated (No business logic).
- [x] IAM Module refactored to DDD (Domain pure, Infra isolated).
- [x] Brand Module refactored to DDD.
- [x] Offer Module refactored to DDD.
- [x] Sales Module refactored to DDD.
- [x] Communication Module refactored to DDD.
- [x] Marketing Module refactored to DDD.
- [x] Gallery Module refactored to DDD.
- [x] Landing Module refactored to DDD.
- [ ] All Domain models are Pydantic only (No SQLAlchemy).
- [ ] All Infrastructure models inherit from SQLAlchemy Base.
- [ ] Repositories handle conversion between Domain and Infra models.
- [ ] Application services depend only on Domain and Repositories (Interfaces).
- [ ] Server starts without import errors.
