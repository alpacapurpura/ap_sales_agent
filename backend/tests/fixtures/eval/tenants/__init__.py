"""Eval tenant seed fixtures package.

Contains:
- loader.py: load_eval_tenant(slug) → TenantContext
- dialect_catalog.yaml: BCP-47 dialect definitions (SSoT, migrates to sales_agent/ post-dialect-configuration story)
- test_*.py: baseline test files (some RED until T-3 adds content YAMLs)
- {tenant_slug}/: per-tenant YAML seed files (added in T-3)
"""
