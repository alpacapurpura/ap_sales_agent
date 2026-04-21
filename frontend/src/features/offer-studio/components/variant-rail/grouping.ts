/**
 * grouping.ts — Pure grouping logic for the polymorphic VariantRail.
 *
 * Architectural decision: this module is intentionally free of React and UI
 * imports so it can be unit-tested without a DOM environment.
 *
 * Groups are dispatched by variant_structure:
 *   - Temporal structures (temporal_cohort, temporal_single_date,
 *     recurring_intake): active → upcoming → drafts → past (mirrors the
 *     legacy groupEditions() in EditionsRail.tsx so both rails share the
 *     same mental model until F4 removes the legacy rail).
 *   - TIER / REGIONAL / MODALITY / LANGUAGE: published → drafts → archived.
 *   - SKU_VARIANT: in_stock → low_stock → pre_venta → discontinued.
 */

import { EditionStatus } from "../../types";

import type { VariantStructure } from "../../api/archetype-catalog-api";
import type { LaunchEdition } from "../../types";

export type GroupTone = "active" | "next" | "draft" | "past";

export interface Group {
  key: string;
  label: string;
  tone: GroupTone;
  items: LaunchEdition[];
}

// ─── Temporal grouping ────────────────────────────────────────────────────────

function groupTemporal(variants: LaunchEdition[]): Group[] {
  const active = variants.filter((e) => e.status === EditionStatus.ACTIVE);
  const upcoming = variants.filter((e) => e.status === EditionStatus.UPCOMING);
  const drafts = variants.filter((e) => e.status === EditionStatus.DRAFT);
  const past = variants
    .filter((e) => e.status === EditionStatus.COMPLETED || e.status === EditionStatus.CANCELLED)
    .sort((a, b) => ((a.start_date ?? "") > (b.start_date ?? "") ? -1 : 1));

  const groups: Group[] = [
    { key: "active", label: "🔴 En curso", tone: "active", items: active },
    { key: "upcoming", label: "⭐ Próxima", tone: "next", items: upcoming },
    { key: "drafts", label: "✏ Borradores", tone: "draft", items: drafts },
    { key: "past", label: "✓ Pasadas", tone: "past", items: past },
  ];
  return groups.filter((g) => g.items.length > 0);
}

// ─── Tier / Regional / Modality / Language grouping ──────────────────────────

function groupPublishedDraftsArchived(variants: LaunchEdition[]): Group[] {
  const published = variants.filter(
    (e) => e.status === EditionStatus.ACTIVE || e.status === EditionStatus.UPCOMING,
  );
  const drafts = variants.filter((e) => e.status === EditionStatus.DRAFT);
  const archived = variants.filter(
    (e) => e.status === EditionStatus.COMPLETED || e.status === EditionStatus.CANCELLED,
  );

  const groups: Group[] = [
    { key: "published", label: "🟢 Publicados", tone: "active", items: published },
    { key: "drafts", label: "✏ Borradores", tone: "draft", items: drafts },
    { key: "archived", label: "✓ Archivados", tone: "past", items: archived },
  ];
  return groups.filter((g) => g.items.length > 0);
}

// ─── SKU grouping ─────────────────────────────────────────────────────────────

function getLowStockThreshold(variant: LaunchEdition): number {
  const threshold = variant.structure_data?.low_stock_threshold;
  return typeof threshold === "number" ? threshold : 10;
}

function groupSku(variants: LaunchEdition[]): Group[] {
  const inStock: LaunchEdition[] = [];
  const lowStock: LaunchEdition[] = [];
  const preVenta: LaunchEdition[] = [];
  const discontinued: LaunchEdition[] = [];

  for (const v of variants) {
    if (v.status === EditionStatus.COMPLETED || v.status === EditionStatus.CANCELLED) {
      discontinued.push(v);
      continue;
    }
    if (v.status === EditionStatus.DRAFT) {
      preVenta.push(v);
      continue;
    }
    // ACTIVE or UPCOMING — check capacity
    const threshold = getLowStockThreshold(v);
    if (v.capacity === null || v.capacity === undefined) {
      // No capacity tracking → treat as in_stock
      inStock.push(v);
    } else if (v.capacity <= 0) {
      preVenta.push(v);
    } else if (v.capacity <= threshold) {
      lowStock.push(v);
    } else {
      inStock.push(v);
    }
  }

  const groups: Group[] = [
    { key: "in_stock", label: "🟢 En stock", tone: "active", items: inStock },
    { key: "low_stock", label: "⚠ Low stock", tone: "next", items: lowStock },
    { key: "pre_venta", label: "✏ Pre-venta", tone: "draft", items: preVenta },
    { key: "discontinued", label: "✓ Descontinuadas", tone: "past", items: discontinued },
  ];
  return groups.filter((g) => g.items.length > 0);
}

// ─── Main dispatcher ──────────────────────────────────────────────────────────

/**
 * Group a list of variants by their structure type.
 * Empty groups are always filtered out to keep the rail compact.
 */
export function groupVariantsByStructure(
  variants: LaunchEdition[],
  structure: VariantStructure,
): Group[] {
  switch (structure) {
    case "temporal_cohort":
    case "temporal_single_date":
    case "recurring_intake":
      return groupTemporal(variants);

    case "tier":
    case "regional":
    case "modality":
    case "language":
      return groupPublishedDraftsArchived(variants);

    case "sku_variant":
      return groupSku(variants);

    default:
      // Defensive: unknown structure falls back to published/drafts/archived
      return groupPublishedDraftsArchived(variants);
  }
}
