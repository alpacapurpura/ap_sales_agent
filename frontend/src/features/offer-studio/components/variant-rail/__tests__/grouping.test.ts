import { describe, expect, it } from "vitest";

import { EditionStatus, EditionVisibility } from "../../../types";
import { groupVariantsByStructure } from "../grouping";

import type { VariantStructure } from "../../../api/archetype-catalog-api";
import type { LaunchEdition } from "../../../types";

// ── Fixture factory ──────────────────────────────────────────────────────────

function makeVariant(overrides: Partial<LaunchEdition> & { id: string }): LaunchEdition {
  const base: LaunchEdition = {
    id: overrides.id,
    offer_id: "offer-1",
    edition_name: "Variante",
    edition_number: 1,
    variant_structure: "temporal_cohort",
    structure_data: {},
    sort_rank: null,
    start_date: null,
    end_date: null,
    registration_start: null,
    registration_end: null,
    timezone: "UTC",
    pricing_override: null,
    pricing_tiers: [],
    active_tier: null,
    effective_pricing: [],
    currency: "USD",
    capacity: null,
    enrollment_count: 0,
    status: EditionStatus.ACTIVE,
    visibility: EditionVisibility.PUBLIC,
    is_placeholder: false,
    location_override: null,
    notes: null,
    cloned_from_edition_id: null,
    created_at: null,
    updated_at: null,
  };
  return { ...base, ...overrides };
}

// ── Helper to find group by key ───────────────────────────────────────────────

function findGroup(groups: ReturnType<typeof groupVariantsByStructure>, key: string) {
  return groups.find((g) => g.key === key);
}

// ── 1. TEMPORAL_COHORT ───────────────────────────────────────────────────────

describe("groupVariantsByStructure — temporal_cohort", () => {
  const structure: VariantStructure = "temporal_cohort";

  it("distributes into active / upcoming / drafts / past groups", () => {
    const variants = [
      makeVariant({
        id: "a",
        status: EditionStatus.ACTIVE,
        variant_structure: structure,
        start_date: "2026-06-01",
      }),
      makeVariant({
        id: "b",
        status: EditionStatus.UPCOMING,
        variant_structure: structure,
        start_date: "2026-09-01",
      }),
      makeVariant({ id: "c", status: EditionStatus.DRAFT, variant_structure: structure }),
      makeVariant({
        id: "d",
        status: EditionStatus.COMPLETED,
        variant_structure: structure,
        start_date: "2025-01-01",
      }),
      makeVariant({
        id: "e",
        status: EditionStatus.CANCELLED,
        variant_structure: structure,
        start_date: "2025-03-01",
      }),
    ];
    const groups = groupVariantsByStructure(variants, structure);
    expect(findGroup(groups, "active")?.items).toHaveLength(1);
    expect(findGroup(groups, "upcoming")?.items).toHaveLength(1);
    expect(findGroup(groups, "drafts")?.items).toHaveLength(1);
    expect(findGroup(groups, "past")?.items).toHaveLength(2);
  });

  it("filters out empty groups", () => {
    const variants = [
      makeVariant({ id: "a", status: EditionStatus.ACTIVE, variant_structure: structure }),
    ];
    const groups = groupVariantsByStructure(variants, structure);
    expect(groups).toHaveLength(1);
    expect(groups[0].key).toBe("active");
  });

  it("past entries are sorted most-recent first", () => {
    const variants = [
      makeVariant({
        id: "old",
        status: EditionStatus.COMPLETED,
        variant_structure: structure,
        start_date: "2024-01-01",
      }),
      makeVariant({
        id: "recent",
        status: EditionStatus.COMPLETED,
        variant_structure: structure,
        start_date: "2025-06-01",
      }),
    ];
    const groups = groupVariantsByStructure(variants, structure);
    const pastGroup = findGroup(groups, "past");
    expect(pastGroup?.items[0].id).toBe("recent");
    expect(pastGroup?.items[1].id).toBe("old");
  });

  it("group labels use emoji LatAm text", () => {
    const variants = [
      makeVariant({ id: "a", status: EditionStatus.ACTIVE, variant_structure: structure }),
      makeVariant({ id: "b", status: EditionStatus.DRAFT, variant_structure: structure }),
    ];
    const groups = groupVariantsByStructure(variants, structure);
    const activeGroup = findGroup(groups, "active");
    const draftGroup = findGroup(groups, "drafts");
    expect(activeGroup?.label).toContain("En curso");
    expect(draftGroup?.label).toContain("Borradores");
  });
});

// ── 2. TEMPORAL_SINGLE_DATE ───────────────────────────────────────────────────

describe("groupVariantsByStructure — temporal_single_date", () => {
  const structure: VariantStructure = "temporal_single_date";

  it("groups identically to temporal_cohort", () => {
    const variants = [
      makeVariant({ id: "a", status: EditionStatus.UPCOMING, variant_structure: structure }),
      makeVariant({ id: "b", status: EditionStatus.COMPLETED, variant_structure: structure }),
    ];
    const groups = groupVariantsByStructure(variants, structure);
    expect(findGroup(groups, "upcoming")?.items).toHaveLength(1);
    expect(findGroup(groups, "past")?.items).toHaveLength(1);
  });
});

// ── 3. RECURRING_INTAKE ───────────────────────────────────────────────────────

describe("groupVariantsByStructure — recurring_intake", () => {
  const structure: VariantStructure = "recurring_intake";

  it("groups identically to temporal_cohort", () => {
    const variants = [
      makeVariant({ id: "a", status: EditionStatus.ACTIVE, variant_structure: structure }),
      makeVariant({ id: "b", status: EditionStatus.DRAFT, variant_structure: structure }),
    ];
    const groups = groupVariantsByStructure(variants, structure);
    expect(groups).toHaveLength(2);
  });
});

// ── 4. TIER ──────────────────────────────────────────────────────────────────

describe("groupVariantsByStructure — tier", () => {
  const structure: VariantStructure = "tier";

  it("uses published / drafts / archived groups (not temporal labels)", () => {
    const variants = [
      makeVariant({ id: "a", status: EditionStatus.ACTIVE, variant_structure: structure }),
      makeVariant({ id: "b", status: EditionStatus.UPCOMING, variant_structure: structure }),
      makeVariant({ id: "c", status: EditionStatus.DRAFT, variant_structure: structure }),
      makeVariant({ id: "d", status: EditionStatus.COMPLETED, variant_structure: structure }),
    ];
    const groups = groupVariantsByStructure(variants, structure);
    const published = findGroup(groups, "published");
    const drafts = findGroup(groups, "drafts");
    const archived = findGroup(groups, "archived");
    // ACTIVE + UPCOMING → published
    expect(published?.items).toHaveLength(2);
    // DRAFT → drafts
    expect(drafts?.items).toHaveLength(1);
    // COMPLETED → archived
    expect(archived?.items).toHaveLength(1);
  });

  it("published group label contains '🟢 Publicados'", () => {
    const variants = [
      makeVariant({ id: "a", status: EditionStatus.ACTIVE, variant_structure: structure }),
    ];
    const groups = groupVariantsByStructure(variants, structure);
    expect(findGroup(groups, "published")?.label).toContain("Publicados");
  });

  it("filters empty groups", () => {
    const variants = [
      makeVariant({ id: "a", status: EditionStatus.ACTIVE, variant_structure: structure }),
    ];
    const groups = groupVariantsByStructure(variants, structure);
    expect(groups).toHaveLength(1);
  });
});

// ── 5. SKU_VARIANT ────────────────────────────────────────────────────────────

describe("groupVariantsByStructure — sku_variant", () => {
  const structure: VariantStructure = "sku_variant";

  it("puts high-stock into in_stock, low-stock into low_stock (capacity ≤ threshold)", () => {
    const variants = [
      makeVariant({
        id: "a",
        status: EditionStatus.ACTIVE,
        variant_structure: structure,
        capacity: 100,
        structure_data: {},
      }),
      makeVariant({
        id: "b",
        status: EditionStatus.ACTIVE,
        variant_structure: structure,
        capacity: 5,
        structure_data: {},
      }),
      makeVariant({
        id: "c",
        status: EditionStatus.DRAFT,
        variant_structure: structure,
        capacity: 0,
        structure_data: {},
      }),
      makeVariant({
        id: "d",
        status: EditionStatus.COMPLETED,
        variant_structure: structure,
        capacity: null,
        structure_data: {},
      }),
    ];
    const groups = groupVariantsByStructure(variants, structure);
    expect(findGroup(groups, "in_stock")?.items.map((i) => i.id)).toContain("a");
    expect(findGroup(groups, "low_stock")?.items.map((i) => i.id)).toContain("b");
    expect(findGroup(groups, "pre_venta")?.items.map((i) => i.id)).toContain("c");
    expect(findGroup(groups, "discontinued")?.items.map((i) => i.id)).toContain("d");
  });

  it("uses custom low_stock_threshold from structure_data", () => {
    const variants = [
      makeVariant({
        id: "borderline",
        status: EditionStatus.ACTIVE,
        variant_structure: structure,
        capacity: 15,
        structure_data: { low_stock_threshold: 20 },
      }),
    ];
    const groups = groupVariantsByStructure(variants, structure);
    // capacity 15 ≤ threshold 20 → low_stock
    expect(findGroup(groups, "low_stock")?.items.map((i) => i.id)).toContain("borderline");
  });

  it("labels in_stock group correctly", () => {
    const variants = [
      makeVariant({
        id: "a",
        status: EditionStatus.ACTIVE,
        variant_structure: structure,
        capacity: 100,
      }),
    ];
    const groups = groupVariantsByStructure(variants, structure);
    expect(findGroup(groups, "in_stock")?.label).toContain("En stock");
  });
});

// ── 6. REGIONAL ──────────────────────────────────────────────────────────────

describe("groupVariantsByStructure — regional", () => {
  const structure: VariantStructure = "regional";

  it("groups into published / drafts / archived", () => {
    const variants = [
      makeVariant({ id: "a", status: EditionStatus.ACTIVE, variant_structure: structure }),
      makeVariant({ id: "b", status: EditionStatus.DRAFT, variant_structure: structure }),
      makeVariant({ id: "c", status: EditionStatus.CANCELLED, variant_structure: structure }),
    ];
    const groups = groupVariantsByStructure(variants, structure);
    expect(findGroup(groups, "published")?.items).toHaveLength(1);
    expect(findGroup(groups, "drafts")?.items).toHaveLength(1);
    expect(findGroup(groups, "archived")?.items).toHaveLength(1);
  });
});

// ── 7. LANGUAGE ───────────────────────────────────────────────────────────────

describe("groupVariantsByStructure — language", () => {
  const structure: VariantStructure = "language";

  it("groups into published / drafts / archived", () => {
    const variants = [
      makeVariant({ id: "a", status: EditionStatus.UPCOMING, variant_structure: structure }),
      makeVariant({ id: "b", status: EditionStatus.DRAFT, variant_structure: structure }),
    ];
    const groups = groupVariantsByStructure(variants, structure);
    expect(findGroup(groups, "published")?.items).toHaveLength(1);
    expect(findGroup(groups, "drafts")?.items).toHaveLength(1);
  });

  it("archived group label contains 'Archivados'", () => {
    const variants = [
      makeVariant({ id: "a", status: EditionStatus.COMPLETED, variant_structure: structure }),
    ];
    const groups = groupVariantsByStructure(variants, structure);
    expect(findGroup(groups, "archived")?.label).toContain("Archivados");
  });
});
