# Social Proof — SSoT for Testimonials, Authority & Team

**Bounded context:** `backend/src/modules/social_proof/`
**API prefix:** `/api/v1/social-proof/`
**Frontend routes:** `/{tenantId}/brand-studio/{testimonials,authority,team}`
**Introduced:** 2026-04-20 (migration `054_create_social_proof`)

## Purpose

One tenant-scoped catalog per trust signal — **testimonials**, **authority items** and **team members** — reusable across every surface the tenant publishes: brand homepage, offer pages, landings, email sequences and the sales-agent KB. A single row lives in one of three specialised tables; where it is shown lives in the `social_proof_placements` link table (M:N). Editing the source row propagates everywhere; removing a placement only unpins it from that one surface.

Before this module, the same three concepts lived as JSONB arrays inside `tenants.config_json['brand_settings']` (`team`, `testimonials`, `authority_vault`), bound to the brand-homepage surface implicitly. Cross-surface reuse required copy/paste.

## Tables

| Table | Purpose | Notable columns |
|-------|---------|-----------------|
| `testimonials` | Customer quotes, videos, audio, reviews | `author_name`, `content`, `media_type`, `rating`, `language`, `tags[]` |
| `authority_items` | Premios, certificaciones, menciones, logos de cliente | `entity_name`, `authority_type`, `proof_url`, `logo_url` |
| `team_members` | Leadership, instructors, advisors | `name`, `role`, `is_primary_voice`, `work_whatsapp`, `gallery[]` |
| `social_proof_placements` | M:N link between source row and surface | `source_table`, `source_id`, `surface_type`, `surface_ref_id`, `sort_order`, `is_visible` |

All four tables have soft-delete (`deleted_at`), tenant scope on every query, and the link table has a partial unique index `(source_table, source_id, surface_type, COALESCE(surface_ref_id, '00000000-…'))` so the same row can't be placed twice on the same surface.

### Enum values

* `TestimonialMediaType` → `text | video | audio | image`
* `AuthorityType` → `certification | award | media_mention | published_work | client_logo | credential | partnership | speaking | podcast | other`
* `SourceTable` → `testimonial | authority_item | team_member`
* `SurfaceType` → `brand_homepage | offer | landing_page | email_sequence | sales_agent_kb`

`brand_homepage` and `sales_agent_kb` are tenant-wide (`surface_ref_id` must be `NULL`). The other three always target a concrete row.

## API endpoints

```
GET    /api/v1/social-proof/testimonials
POST   /api/v1/social-proof/testimonials
GET    /api/v1/social-proof/testimonials/{id}
PATCH  /api/v1/social-proof/testimonials/{id}
DELETE /api/v1/social-proof/testimonials/{id}
POST   /api/v1/social-proof/testimonials/{id}/clone
# Same shape for /authority and /team.

GET    /api/v1/social-proof/placements?source_table=&source_id=
POST   /api/v1/social-proof/placements
PATCH  /api/v1/social-proof/placements/{id}
DELETE /api/v1/social-proof/placements/{id}

GET    /api/v1/social-proof/placements/for-surface
       ?surface_type=&surface_ref_id=&include_brand=
       → { testimonials[], authority_items[], team_members[] }
```

Every endpoint declares `response_model=` and filters by `tenant_id` via `get_current_user`.

## Domain events

Published via `src.shared.domain.events.EventBus`, after-commit dispatch:

* `testimonial_created`, `testimonial_updated`, `testimonial_soft_deleted`
* `authority_item_created`, `authority_item_updated`, `authority_item_soft_deleted`
* `team_member_created`, `team_member_updated`, `team_member_soft_deleted`
* `placement_added`, `placement_removed`, `placement_reordered`

Subscribers live in other modules (Sales Agent KB cache, Landing Generator cache, Copilot embeddings) and never import from `social_proof/` directly.

## Cross-module integration (shared port)

`backend/src/shared/links/ports/social_proof.py` is the ONLY entry point other bounded contexts may touch. Available helpers:

* `resolve_for_surface(db, tenant_id, surface_type, surface_ref_id, include_brand=False)` — returns `ResolvedSocialProof`
* `list_tenant_testimonials(db, tenant_id)` / `list_tenant_authority_items` / `list_tenant_team_members`
* `resolve_sales_agent_context(db, tenant_id)` — pre-serialized dict for agent_identity.j2
* `resolve_offer_context(db, tenant_id, offer_id, include_brand=True)` — pre-serialized dict
* `resolve_landing_page_context(db, tenant_id, landing_page_id, include_brand=True)` — pre-serialized dict

The arch test `tests/architecture/test_social_proof_invariants.py::test_social_proof_module_only_consumes_shared_or_iam` prevents `social_proof/` from importing other modules, and the pre-serialized helpers ensure consumers never need to import `SurfaceType` or the resolver classes.

## Frontend

| Layer | Files |
|-------|-------|
| API clients | `src/lib/api/{testimonial,authority-item,team-member,placement}.ts` |
| Hooks | `src/features/brand-studio/hooks/use-{testimonials,testimonial,authority-items,authority-item,team-members,team-member,placements,social-proof-for-surface}.ts` |
| Schemas | `src/features/brand-studio/schemas/{testimonial-item,authority-item,team-member-item}.schema.ts` |
| Landing pages | `src/features/brand-studio/pages/{Testimonials,Authority,Team}LandingPage.tsx` |
| Detail pages | `src/features/brand-studio/pages/{Testimonial,AuthorityItem,TeamMember}DetailPage.tsx` |
| Instance pickers | `src/features/brand-studio/components/{Testimonial,AuthorityItem,TeamMember}InstancePicker.tsx` |
| Offer reuse | `src/features/offer-studio/components/social-proof/{OfferSocialProofPicker,AddFromBrandVaultModal}.tsx` |

Routing:

```
/{tenantId}/brand-studio/testimonials           → Landing (picker + welcome)
/{tenantId}/brand-studio/testimonials/instance/{id}/{fieldId?}
# Same for /authority and /team.
```

The static routes take precedence over the legacy `[section]/[[...fieldId]]` catch-all dispatcher, which no longer registers entries for these three slugs.

## Architecture fitness tests (ratchet)

Backend (`backend/tests/architecture/test_social_proof_invariants.py`):

1. Every repo query filters by `tenant_id`
2. `domain/` layer imports no framework code and no outer layers
3. `social_proof/` imports only from `src.core`, `src.shared`, `src.modules.iam`
4. Enum value sets stay frozen (`test_enum_value_set_is_frozen`)
5. Every mutation in an application service emits a DomainEvent
6. The shared port declares all four public helpers
7. No file in the module reads the legacy `brand_settings.{team,testimonials,authority_vault}` paths
8. Every HTTP endpoint declares `response_model=`

Frontend (`frontend/src/__tests__/architecture/test-no-legacy-social-proof.test.ts`):

9. No file imports `testimonialsSchema`, `authoritySchema`, `teamSchema` or `TestimonialItem` — the legacy array-wrapper symbols that were removed during the SSoT migration.

## Migration & rollout

* `alembic/versions/054_create_social_proof.py` creates the 4 tables + indexes + partial unique index and backfills rows from `tenants.config_json['brand_settings']` with enum normalization (Spanish free-text → canonical `AuthorityType` values). Idempotent: re-running the migration produces identical rowcounts.
* Dry-run against a cloned DB verified rowcounts (14 testimonials / 11 authority items / 14 team members / 39 placements for the current tenant set).
* The legacy JSONB keys stay in place during the migration window so the existing Brand Studio AI extraction pipeline keeps functioning. Removing them is a follow-up sprint that migrates `extraction_orchestrator` to post to the new REST API.

## Open follow-ups

* **Extraction pipeline migration** — `backend/src/modules/brand/application/extraction_orchestrator.py` still writes its AI-extracted testimonials/team/authority into `brand_settings` JSONB. It should POST to `/api/v1/social-proof/*` instead and emit domain events on completion.
* **InstructorsSelector migration** — `frontend/src/features/offer-studio/components/editor/sections/instructors/InstructorsManager.tsx` still pulls `settings.team` from Brand Settings and opens the legacy `TeamManager` dialog. Migrate to `useTeamMembers()` and deep-link to `/brand-studio/team` for global management.
* **Clone-per-row UX** — the `/clone` endpoint is wired on the backend; the frontend currently only offers "Link" from `AddFromBrandVaultModal`. Add a per-row menu ("Customize this one") that clones the source and places the clone on the current surface in a single mutation.
* **Landing Generator integration** — `LandingPage.content` still embeds testimonial snapshots inline. A future rendering layer should call `resolve_landing_page_context()` and merge dynamic social proof into the content at render time.
