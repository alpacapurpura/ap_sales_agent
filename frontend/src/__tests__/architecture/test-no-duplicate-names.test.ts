/**
 * ARCH TEST: No duplicate component names across different features.
 *
 * Rule: two different features must not have a component with the same
 * basename. Same-feature duplicates (e.g. different sub-dirs) are OK.
 *
 * Why: cross-feature duplicates cause import confusion and suggest missing
 * shared component extraction.
 *
 * Note: ChartInfoTooltip.tsx appears twice but both are inside growth-studio
 * (intra-feature duplicate) — that is OK and excluded from cross-feature check.
 *
 * This test currently passes with an empty allowlist. The allowlist is here
 * as a ratchet gate to catch future regressions.
 */
import { describe, it, expect } from "vitest";
import * as path from "path";
import { FEATURES_DIR, getFeatureNames, walkFiles, isTestFile } from "./helpers";

// ── Ratchet allowlist ─────────────────────────────────────────────────────────
// Pre-existing cross-feature duplicates (existed before PascalCase rename on 2026-04-15).
// These must shrink over time: extract to components/shared/ or rename.
const KNOWN_CROSS_FEATURE_DUPLICATES = new Set<string>([
  // closer-studio and sales both have a PipelineBoard component
  "PipelineBoard.tsx",
  // growth-studio and offer-studio both have an OfferCard component
  "OfferCard.tsx",
]);

// ─────────────────────────────────────────────────────────────────────────────

describe("Architecture: No duplicate component names", () => {
  it("no two different features may share a component filename", () => {
    const featureNames = getFeatureNames();

    // Map basename → Set of feature names that contain it
    const basenameToFeatures = new Map<string, Set<string>>();

    for (const feature of featureNames) {
      const featureDir = path.join(FEATURES_DIR, feature);
      const files = walkFiles(featureDir).filter(
        (f) => f.endsWith(".tsx") && f.includes(path.sep + "components" + path.sep) && !isTestFile(f),
      );

      for (const file of files) {
        const basename = path.basename(file);
        if (!basenameToFeatures.has(basename)) {
          basenameToFeatures.set(basename, new Set());
        }
        basenameToFeatures.get(basename)!.add(feature);
      }
    }

    const violations: string[] = [];
    for (const [basename, features] of basenameToFeatures) {
      if (features.size > 1) {
        violations.push(`${basename} → [${[...features].sort().join(", ")}]`);
      }
    }

    const newViolations = violations.filter((v) => {
      const name = v.split(" → ")[0];
      return !KNOWN_CROSS_FEATURE_DUPLICATES.has(name);
    });

    const alreadyFixed = [...KNOWN_CROSS_FEATURE_DUPLICATES].filter((name) => {
      const entry = violations.find((v) => v.startsWith(name));
      return !entry;
    });

    if (alreadyFixed.length > 0) {
      console.info(
        `[arch] Allowlist can shrink: ${alreadyFixed.length} entries already fixed:\n  ${alreadyFixed.join("\n  ")}`,
      );
    }

    expect(
      newViolations,
      `NEW cross-feature duplicate component names (extract to components/shared/ or rename):\n${newViolations.join("\n")}`,
    ).toEqual([]);
  });
});
