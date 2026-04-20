"""tenant_profile bounded context.

First-class aggregate that owns the tenant's operational classification:
  - business_types (tuple[ExpertBusinessType, ...]) — drives preset filtering,
    format suitability, ladder hints, landing template defaults, and sales-agent
    grounding.

Migrated out of BrandIdentity (JSONB blob) in Sprint 2026-04-20 to establish
a typed SSoT and enable future tenant-wide fields (sector, stage, company_size).
"""
