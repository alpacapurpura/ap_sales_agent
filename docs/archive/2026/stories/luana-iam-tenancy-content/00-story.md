# Story 3 — IAM + Tenancy + Content lift

> **Outcome:** luana-platform-migration · **Sequence:** 3/14

## What

Lift 6 modules a packages Luana:

| Module | Destino |
|---|---|
| `iam` | `luana-core-iam` (Clerk integration brand-agnostic) |
| `tenant_profile` | `luana-core-tenant-profile` (settings, locale, currency, plan_tiers) |
| `tenant_domains` | `luana-core-tenant-domains` (Cloudflare Custom Hostnames) |
| `commercial_calendar` | `luana-core-commercial-calendar` |
| `social_proof` | `luana-core-social-proof` |
| `assets` | `luana-core-assets` |

## Multi-Clerk consideration (per ADR-001 §2.5)

`luana-core-iam` es **engine brand-agnostic**. Cada brand wirea SU Clerk app via env config. Smoke test: 2 brand apps con Clerk apps distintos, ambos validan JWT correctamente.

## Acceptance

- 6 packages publicados v0.0.3-alpha
- Smoke test: stub `nicolify` consume `luana-core-iam` con Clerk app real
- Arch fitness: cero brand-aware code en `core-iam`

## Effort: 8-12 tickets, ~3 días
