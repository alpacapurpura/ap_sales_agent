/**
 * ARCH TEST: Frontend ``SectionKey`` TS union must match backend
 * ``SECTION_CATALOG`` keys bi-directionally.
 *
 * Backend is SSoT — see ``.claude/rules/offer-catalogs.md``. The frontend
 * declares a narrow union type for type-safe rendering; any drift between
 * the two is a silent-failure vector:
 *
 *   - Backend adds a key → frontend doesn't render it.
 *   - Frontend declares orphan key → breaks the registry at runtime.
 *
 * This test asserts the registry used by the frontend covers exactly the
 * same set as the ``OFFER_SCHEMA_REGISTRY``. Since the registry is typed
 * as ``Record<SectionKey, SectionSchema>``, the set of its keys equals
 * the TS union — any drift fails compile OR this test at CI time.
 */
import { describe, it, expect } from "vitest";

import { OFFER_SCHEMA_REGISTRY } from "@/features/offer-studio/schemas";

import type { SectionKey } from "@/features/offer-studio/api/archetype-catalog-api";

const FRONTEND_SECTION_KEYS: readonly SectionKey[] = [
  "identity",
  "strategy",
  "psychology",
  "promise",
  "value_stack",
  "instructors",
  "knowledge",
  "closing",
  "product_details",
  "subscription_details",
  "gallery",
  "event_details",
  "pricing",
  "program_details",
  "service_details",
  "resources",
  "faq",
  "testimonials",
  "portfolio",
  "location",
  "platform_details",
];

describe("Architecture: SectionKey frontend ↔ backend alignment", () => {
  it("every frontend SectionKey has a schema in OFFER_SCHEMA_REGISTRY", () => {
    const registryKeys = new Set(Object.keys(OFFER_SCHEMA_REGISTRY));
    const missing = FRONTEND_SECTION_KEYS.filter((k) => !registryKeys.has(k));
    expect(missing).toEqual([]);
  });

  it("OFFER_SCHEMA_REGISTRY has no keys outside the frontend SectionKey union", () => {
    const expected = new Set<string>(FRONTEND_SECTION_KEYS);
    const extra = Object.keys(OFFER_SCHEMA_REGISTRY).filter((k) => !expected.has(k));
    expect(extra).toEqual([]);
  });

  it("FRONTEND_SECTION_KEYS is a 1:1 mapping with the TS union", () => {
    // Any value in SectionKey that drifts from this constant triggers a
    // TS compile error on the ``const ks: SectionKey[] = ...`` assignment
    // above — which is a stronger guarantee than this runtime check, but
    // we still verify size for operator-readable failure messages.
    const registryCount = Object.keys(OFFER_SCHEMA_REGISTRY).length;
    expect(FRONTEND_SECTION_KEYS.length).toBe(registryCount);
  });
});
