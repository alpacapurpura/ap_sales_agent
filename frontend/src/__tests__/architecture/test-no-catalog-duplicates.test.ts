/**
 * ARCH TEST: Catalog SSoT — frontend must not re-declare catalog data.
 *
 * Rule: The offer-studio catalogs (archetype, value level, format) and the
 * expert business types live in the backend (see
 * ``backend/src/modules/offer/domain/*_catalog.py`` and
 * ``backend/src/shared/domain/expert_business_type.py``). The frontend
 * consumes them via typed hooks — see
 * ``docs/domains/offer/catalogs-consolidation.md``.
 *
 * Adding a new hardcoded map that shadows one of the catalogs re-opens
 * the drift that the consolidation closed (the lead-magnet mis-classification
 * bug documented in commit 4083a60f). This test fails CI the moment such a
 * map appears.
 *
 * Allowlist: the only permitted occurrences are (a) the catalog APIs /
 * hooks / icon resolver themselves and (b) the archetype-catalog test
 * fixtures. Both listed below.
 */
import * as path from "path";

import { describe, it, expect } from "vitest";

import { FEATURES_DIR, walkFiles, relPath, readFile } from "./helpers";

const ALLOWED_CATALOG_FILES: readonly string[] = [
  // Backend catalog consumers — these are THE legitimate references.
  "features/offer-studio/api/archetype-catalog-api.ts",
  "features/offer-studio/api/format-catalog-api.ts",
  "features/offer-studio/api/value-level-catalog-api.ts",
  "features/offer-studio/hooks/use-archetype-catalog.ts",
  "features/offer-studio/hooks/use-archetype-display.ts",
  "features/offer-studio/hooks/use-format-catalog.ts",
  "features/offer-studio/hooks/use-section-catalog.ts",
  "features/offer-studio/hooks/use-sections-for-archetype.ts",
  "features/offer-studio/hooks/use-value-level-catalog.ts",
  "features/offer-studio/hooks/use-visible-sections.ts",
  "features/offer-studio/lib/icon-name-resolver.ts",
  "features/offer-studio/lib/__tests__/icon-name-resolver.test.ts",
  "features/brand-studio/api/expert-business-types-api.ts",
  "features/brand-studio/hooks/use-expert-business-types-catalog.ts",
  // Test fixtures: the catalog hook test wires a mocked HTTP response.
  "features/offer-studio/tests/fixtures/archetype-catalog-fixture.ts",
  "features/offer-studio/tests/use-archetype-capabilities.test.tsx",
  "features/offer-studio/tests/use-section-catalog.test.tsx",
  "features/offer-studio/tests/use-sections-for-archetype.test.tsx",
  "features/offer-studio/tests/use-visible-sections.test.tsx",
  // Legacy live-preview carries an inline ``SECTION_METADATA`` map of
  // motivational copy. It retires in Sprint 6 Phase E alongside the
  // SectionFormWrapper editor. Until then, allowlist the file and keep
  // the forbidden-token gate honest for every future additon.
  "features/offer-studio/components/editor/OfferLivePreview.tsx",
];

// Forbidden tokens — the hardcoded maps that the consolidation removed.
// If any of these reappear it means a developer introduced a new shadow
// copy instead of consuming the catalog.
const FORBIDDEN_TOKENS: readonly string[] = [
  "ARCHETYPE_METADATA",
  "ARCHETYPE_BUILDER_CONFIG",
  "FORMAT_PRESETS",
  "LEVEL_RICH_INFO",
  "VALUE_LEVEL_LABELS",
  // Section-catalog duplicates (Sprint 6 guarantee): section ordering +
  // metadata live in backend/src/modules/offer/domain/section_catalog.py
  // and archetype_catalog.py. Never in the frontend.
  "getSectionsForOffer",
  "SECTION_METADATA",
];

describe("Architecture: Offer catalogs are SSoT", () => {
  it("must not re-introduce hardcoded archetype/value-level/format maps", () => {
    const violations: string[] = [];
    const allowed = new Set<string>(ALLOWED_CATALOG_FILES);

    for (const filePath of walkFiles(FEATURES_DIR)) {
      const rel = relPath(filePath).replace(/\\/g, "/");
      if (allowed.has(rel)) continue;
      // Ignore non-code files.
      const ext = path.extname(filePath);
      if (![".ts", ".tsx"].includes(ext)) continue;

      const content = readFile(filePath);
      for (const token of FORBIDDEN_TOKENS) {
        if (content.includes(token)) {
          violations.push(`${rel} references ${token}`);
        }
      }
    }

    expect(violations).toEqual([]);
  });
});
