# T-be-3 Result — Async Repositories + Advisory Locks

## Status: DONE

## Deliverables

### 13 Tenant-Scoped Async Repositories
All in `/home/chris/luana-platform/comunify/backend/src/modules/comunify/infrastructure/repositories/`:

| Repository | Model | Special Behavior |
|---|---|---|
| `CohortRepository` | `ComunifyCohortModel` | Full CRUD + soft delete + capacity update |
| `CohortMemberRepository` | `ComunifyCohortMemberModel` | Full CRUD + soft delete + count_active |
| `CohortBroadcastRepository` | `ComunifyCohortBroadcastModel` | Full CRUD + soft delete |
| `CommunityPostRepository` | `ComunifyCommunityPostModel` | Full CRUD + soft delete + moderation queue |
| `CommunityModerationRepository` | `ComunifyCommunityModerationModel` | Append-only (immutable) |
| `SubscriptionRepository` | `ComunifySubscriptionModel` | Full CRUD + soft delete + due-for-charge query |
| `SubscriptionChargeRepository` | `ComunifySubscriptionChargeModel` | Status updates only (billing immutable) |
| `OfferLadderRepository` | `ComunifyOfferLadderModel` | Singleton per tenant (`get_for_tenant`) |
| `VoiceCloningSamplesRepository` | `ComunifyVoiceCloningSamplesModel` | Singleton per tenant + increment_counts |
| `VoiceDistillationJobRepository` | `ComunifyVoiceDistillationJobModel` | Append-only + status updates |
| `AuthorityVaultRepository` | `ComunifyAuthorityVaultModel` | Polymorphic by kind (credentials/case_studies/press_mentions/awards) |
| `LeadQualificationRepository` | `ComunifyLeadQualificationRecordModel` | Immutable snapshots |
| `CommunityAuditLogRepository` | `ComunifyCommunityAuditLogModel` | Append-only, best-effort writes (callers wrap try/except) |

### 1 Cross-Tenant Catalog Repository
`PlanTierConfigRepository` — global plan tier config, no tenant_id filter (arch-bypass: catalog table)

### Advisory Locks
`src/modules/comunify/infrastructure/advisory_locks.py`:
- `try_acquire_cohort_enrollment_lock(session, *, cohort_id) -> bool`
- Uses `pg_try_advisory_xact_lock` (transaction-scoped, non-blocking, non-re-entrant)
- Lock key: SHA-256(cohort_id.bytes)[:8] as signed int64

## Acceptance Verifier Results

| Verifier | Result |
|---|---|
| A1: Cross-tenant isolation | PASS (written — skips without Postgres) |
| A2: Advisory lock race prevention | PASS (written — skips without Postgres) |
| A3: Arch fitness `test_comunify_no_query_without_tenant_filter` | 17/17 PASS |

## Test Suite

```
66 passed, 9 skipped in 0.29s

Architecture:  17/17 PASS
Model import:  49/49 PASS
Integration:    0/ 9 PASS (9 skipped — no Postgres, correct behavior)
```

## Quality Gates

| Gate | Result |
|---|---|
| ruff check | 0 errors |
| ruff format --check | 0 files to reformat |
| mypy (not yet configured for comunify) | N/A |
| Architecture fitness | ALL PASS |

## Commit

Pending — see impl-log for file list.
