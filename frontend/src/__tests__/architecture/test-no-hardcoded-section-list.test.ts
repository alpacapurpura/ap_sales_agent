/**
 * ARCH TEST: no hardcoded section list in offer-studio or brand-studio.
 *
 * After Fase 03 (see ``docs/refactors/field-contract-ssot/phases/03-section-catalog-dedup/``),
 * both studios consume the section list from the backend catalog via
 * React Query hooks:
 *
 *  - offer-studio → ``/api/v1/offer/archetypes/catalog`` (section_catalog field)
 *  - brand-studio → ``/api/v1/brand/sections/catalog``
 *
 * This test prevents regression — if any FE file reintroduces the
 * hardcoded ``OFFER_SECTIONS`` or ``BRAND_SECTIONS`` array constant,
 * the build fails. Mocks in test files are allowed (different prefix
 * like ``MOCK_BRAND_SECTIONS``).
 */

import { readdirSync, readFileSync, statSync } from "fs";
import * as path from "path";

import { describe, it, expect } from "vitest";

const SRC_ROOT = path.resolve(__dirname, "../../");

// Match an exported top-level ``OFFER_SECTIONS`` or ``BRAND_SECTIONS``
// constant array. The leading word boundary + `export const` gate
// ensures unrelated identifiers (``MOCK_BRAND_SECTIONS``, docstrings,
// comments) don't trigger.
const OFFENDING_PATTERN = /export\s+const\s+(OFFER_SECTIONS|BRAND_SECTIONS)\b/;

const SKIP_DIRS = new Set(["node_modules", ".next", "dist", "__mocks__"]);

function* walkSourceFiles(dir: string): Generator<string> {
  for (const entry of readdirSync(dir)) {
    if (SKIP_DIRS.has(entry)) continue;
    const fullPath = path.join(dir, entry);
    const stats = statSync(fullPath);
    if (stats.isDirectory()) {
      yield* walkSourceFiles(fullPath);
      continue;
    }
    if (entry.endsWith(".ts") || entry.endsWith(".tsx")) {
      yield fullPath;
    }
  }
}

describe("Architecture: section list comes from the BE catalog", () => {
  it("no FE file exports hardcoded OFFER_SECTIONS or BRAND_SECTIONS array", () => {
    const violations: string[] = [];
    for (const file of walkSourceFiles(SRC_ROOT)) {
      const text = readFileSync(file, "utf-8");
      if (OFFENDING_PATTERN.test(text)) {
        violations.push(path.relative(SRC_ROOT, file));
      }
    }
    expect(violations).toEqual([]);
  });
});
