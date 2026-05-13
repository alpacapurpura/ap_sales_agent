"""Base entity re-export from luana-core (Pattern P6 migration prologue).

Unifies SQLAlchemy `declarative_base()` singleton across AISALESHT + luana-core
trees during Story 10 import rewrite. Without this stub, both
src/modules/iam/infrastructure/models/tenant_model.py (importing
src.shared.domain.base_entity.Base) AND luana_core_iam/infrastructure/models/tenant_model.py
(importing luana_core_platform.domain.base_entity.Base) would define
`class TenantModel(Base)` with `__tablename__ = "tenants"`, registering Table('tenants')
twice to distinct Base.metadata instances -> InvalidRequestError.

Migration-window scoped (auto-closes at T-7 shared/* rewrite final wave when
AISALESHT base_entity.py is deleted). See:
- docs/product/stories/luana-nicolify-migration/03-arch-be-addendum-2026-05-13.md §3
- .claude/rules/anti-duplication.md § Migration-window scoped exceptions
"""

from luana_core_platform.domain.base_entity import Base, BaseEntity

__all__ = ["Base", "BaseEntity"]
