"""Public fixtures surface for the eval simulator (Story B, T-3).

Exposes ``eval_tenant_seeded`` — the DB-seed fixture that materialises a
Story-A ``TenantContext`` (loaded from YAML) into real Postgres rows and
returns ``(tenant_id, TenantContext)`` for use in simulator runs.

Anti-duplication §0 note: the fixture reuses existing production ORM
models (``TenantModel``, ``PersonalityProfileModel``, ``ProductModel``,
``BuyerPersonaModel``, ``EvalSyntheticTenantModel``) and calls
``PersonalityCompiler.compile()`` from the brand domain — zero new
ORM classes or mirrors introduced.

Scope: story-local (Story B eval-foundation-simulator-homologation).
If a future story needs cross-story access to seeded fixtures, the /pm
must lift this to ``tests/agentic_evals/sales_agent/fixtures/`` — do NOT
inline-copy here (anti-duplication §0 + M8 rule).
"""

from tests.agentic_evals.sales_agent.simulator.fixtures.tenant_seeded import (
    eval_tenant_seeded,
)

__all__ = ["eval_tenant_seeded"]
