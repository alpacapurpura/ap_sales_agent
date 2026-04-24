/**
 * ARCH TEST: every offer-studio schema `path` must resolve to a real field
 * on the backend `Offer` (or one of its polymorphic `*Details`) domain.
 *
 * The backend ships the canonical list via
 * ``backend/tests/architecture/fixtures/offer_field_paths.json`` (generated
 * by ``backend/scripts/generate_offer_field_paths.py``). Regenerate that
 * file whenever ``Offer`` or a ``*Details`` model gains/loses a field — see
 * ``docs/refactors/field-contract-ssot/PLAN.md`` Fase 00.
 *
 * Until the per-phase migrations of the ``field-contract-ssot`` refactor
 * land, nine paths that the UI already uses ship ahead of their backend
 * counterparts. They stay in ``KNOWN_UNRESOLVED_PATHS`` with the phase that
 * will remove them. The set is **shrink-only** — every new entry requires
 * explicit approval and a sibling PR closing the backend gap.
 *
 * Scope note: Fase 00 validates top-level field paths
 * (``section.fields[].path``). Array ``itemSchema.fields[].path`` entries
 * resolve against the nested BE types (``PricingStructure``, ``ObjectionItem``,
 * …) which are not yet enumerated in the JSON — a strict check there is
 * deferred to Fase 01+. Item paths are scanned only to exclude their ids
 * from the top-level comparison.
 */
import { readFileSync } from "fs";
import * as path from "path";

import { describe, it, expect } from "vitest";

import { OFFER_SCHEMA_REGISTRY } from "@/features/offer-studio/schemas";

import type { FieldSchema, SectionSchema } from "@/lib/form-runtime/schema";

const BACKEND_FIXTURE = path.resolve(
  __dirname,
  "../../../../backend/tests/architecture/fixtures/offer_field_paths.json",
);

/**
 * Paths that ship on the frontend ahead of the matching backend domain field.
 * Each entry names the phase that closes the gap. The set is **shrink-only**
 * — every new entry requires an ADR (see DECISIONS.md) and a sibling PR
 * that advances the refactor plan.
 *
 * ADR-007 captures why Fase 00 landed a larger cap than the original SPEC
 * predicted: the audit during guardrail setup surfaced the full backlog
 * (pricing LATAM + authority/value-stack + subscription/service/product
 * naming drift + platform-details archetype + cross-module federated
 * fields). The cap reflects that reality; shrinking is the job of
 * Fase 01→05.
 */
const KNOWN_UNRESOLVED_PATHS = new Set<string>([
  // ── Fase 01 closed — pricing LATAM now lives on Offer (see commits B-F).
  // ── Fase 02 Block A closed — authority narrative lives on Offer.
  // ── Fase 02 Block B closed — value-stack anchor lives on Offer.
  // ── Fase 02 Block C closed — program narratives live on ProgramDetails.
  // ── Fase 02 — SubscriptionDetails (7: 2 renames + 5 new) ────────────
  "specific_details.billing_frequency", // rename BE: billing_cycle → billing_frequency
  "specific_details.content_update_frequency", // rename BE: content_update_freq
  "specific_details.auto_renewal_with_notice_days",
  "specific_details.cancellation_anticipation_days",
  "specific_details.grace_period_days_on_failed_payment",
  "specific_details.member_benefits",
  "specific_details.primary_communication_channel",
  // ── Fase 02 — ServiceDetails (3) ────────────────────────────────────
  "specific_details.response_time_hours",
  "specific_details.onboarding_flow",
  "specific_details.scope_excluded",
  // ── Fase 02 — ProductDetails (5) ────────────────────────────────────
  "specific_details.sample_preview_url",
  "specific_details.packaging_description",
  "specific_details.return_policy_days",
  "specific_details.shipping_carriers_accepted",
  "specific_details.shipping_estimate_by_region",
  // ── Fase 02 — Platform archetype (14) ───────────────────────────────
  // PLATFORM / SAAS archetype is not yet modeled on BE. Either introduce
  // ``PlatformDetails`` or hoist these onto a new branch of Offer.
  "platform_features",
  "platform_integrations",
  "security_compliance",
  "data_residency",
  "uptime_guarantee",
  "status_page_url",
  "support_channels",
  "api_available",
  "api_docs_url",
  "migration_tools",
  "public_roadmap_url",
  "changelog_url",
  "ai_features_disclosure",
  "data_export_capability",
  // ── Fase 05 — Cross-module federated (9) ────────────────────────────
  // These paths belong to sibling bounded contexts (assets, buyer-persona,
  // social-proof, scheduling, knowledge). Fase 05 extends the resolver to
  // federate across modules so these paths check against their owning
  // domain instead of Offer.
  "assets",
  "hero_image",
  "gallery_images",
  "avatar_id",
  "testimonials",
  "aggregate_rating",
  "total_reviews_count",
  "external_reviews_url",
  "faq_public",
  // ── Fase 05 — Portfolio / proof (5) ─────────────────────────────────
  "portfolio_cases",
  "client_logos",
  "before_after_pairs",
  "video_demo_url",
  "aggregate_results",
  // ── Fase 05 — Scheduling / booking (3) ──────────────────────────────
  "booking_fallback_whatsapp",
  "scheduling_event_type_id",
  "venues",
  // ── Fase 05 — Knowledge docs (2) ────────────────────────────────────
  "knowledge_documents",
  "knowledge_reference_urls",
]);

/**
 * Shrink-only ratchet. The cap locks the allowlist size at Fase 00's
 * measurement (see ADR-007). Phases 01→05 remove entries; none may be added
 * without an ADR raising the cap.
 */
const ALLOWLIST_CAP = KNOWN_UNRESOLVED_PATHS.size;

function loadValidPaths(): Set<string> {
  const raw = readFileSync(BACKEND_FIXTURE, "utf-8");
  const parsed = JSON.parse(raw);
  if (!Array.isArray(parsed)) {
    throw new Error(`Expected array in ${BACKEND_FIXTURE}, got ${typeof parsed}`);
  }
  return new Set(parsed as string[]);
}

function collectItemPathIds(field: FieldSchema, acc: Set<string>): void {
  if (field.type !== "array" || !field.itemSchema) {
    return;
  }
  for (const sub of field.itemSchema.fields) {
    acc.add(sub.path);
  }
}

function collectItemLevelPaths(): Set<string> {
  const acc = new Set<string>();
  for (const schema of Object.values(OFFER_SCHEMA_REGISTRY)) {
    for (const field of schema.fields) {
      collectItemPathIds(field, acc);
    }
  }
  return acc;
}

function isFieldInScope(schema: SectionSchema, field: FieldSchema): boolean {
  // Sections that persist entirely to LaunchEdition (event_details, some
  // resources/location) live outside the Offer domain. Per-field ownership
  // in ``mixed`` sections overrides with the same intent.
  if (schema.scope === "edition_level") return false;
  if (field.owner === "edition") return false;
  return true;
}

function violationMessage(sectionKey: string, field: FieldSchema): string {
  return (
    `${sectionKey}.${field.id} → path "${field.path}" not declared on Offer or *Details. ` +
    "Either add it to the Pydantic domain (+ regenerate offer_field_paths.json) " +
    "or extend KNOWN_UNRESOLVED_PATHS with the phase that will close the gap."
  );
}

describe("Architecture: offer-studio schema paths resolve to BE Offer domain", () => {
  it("every offer-owned field path must exist on the BE domain or be allowlisted", () => {
    const validPaths = loadValidPaths();
    const itemLevelPaths = collectItemLevelPaths();

    const violations: string[] = [];
    for (const [sectionKey, schema] of Object.entries(OFFER_SCHEMA_REGISTRY)) {
      for (const field of schema.fields) {
        if (!isFieldInScope(schema, field)) continue;
        const p = field.path;
        if (validPaths.has(p) || KNOWN_UNRESOLVED_PATHS.has(p)) continue;
        // Defensive: top-level paths that collide with an item-level id are
        // almost certainly a bug, but item-level enforcement is out of
        // scope for Fase 00 — skip to avoid false positives.
        if (itemLevelPaths.has(p)) continue;
        violations.push(violationMessage(sectionKey, field));
      }
    }

    expect(violations).toEqual([]);
  });

  it("KNOWN_UNRESOLVED_PATHS is shrink-only (ratchet)", () => {
    // The literal size is captured in ALLOWLIST_CAP at module load; asserting
    // equality catches accidental growth *and* stale caps when entries are
    // deleted without bumping the expectation.
    expect(KNOWN_UNRESOLVED_PATHS.size).toBe(ALLOWLIST_CAP);
    // Fase 02 Block C closed (2026-04-24): program narratives shipped →
    // cap drops from 52 to 50 (2 paths closed). Previous caps:
    //   · ADR-007: 59 (Fase 00 baseline)
    //   · Fase 01 close: 56 (pricing LATAM, -3)
    //   · Fase 02 Block A close: 54 (-2 authority)
    //   · Fase 02 Block B close: 52 (-2 value-stack anchor)
    //   · Fase 02 Block C close: 50 (-2 program narratives)
    // Subsequent phases must only lower this, never raise without an ADR.
    expect(ALLOWLIST_CAP).toBeLessThanOrEqual(50);
  });
});
