/**
 * ARCH TEST: Feature top-level folders must follow canonical structure.
 *
 * Rule: every directory directly inside a feature (e.g. features/brand/XXX)
 * must be one of the canonical folder names. Unknown folders suggest
 * an ad-hoc structure that makes the codebase unpredictable.
 *
 * Canonical folders:
 *   components, hooks, api, types, utils, config, context, store, lib,
 *   sections, services, mocks, tests, __tests__, __mocks__
 *
 * This test passes with an empty allowlist as of 2026-04-15.
 * The allowlist is a ratchet gate — any new non-canonical folder added to a
 * feature will immediately fail CI unless justified and allowlisted.
 */
import { describe, it, expect } from "vitest";
import { getFeatureNames, getFeatureTopDirs } from "./helpers";

// ── Canonical folder names ────────────────────────────────────────────────────
const CANONICAL_FOLDERS = new Set([
  "components",
  "hooks",
  "api",
  "types",
  "utils",
  "config",
  "context",
  "store",
  "lib",
  "sections",  // brand-style section grouping
  "services",  // legacy — prefer api/ for new features
  "mocks",     // manual mock data
  "tests",     // alternative to __tests__
  "__tests__",
  "__mocks__",
]);

// ── Ratchet allowlist ─────────────────────────────────────────────────────────
// Empty — all existing features use canonical folders as of 2026-04-15.
const KNOWN_NONSTANDARD: Record<string, string[]> = {
  // Example: "my-feature": ["custom-dir"],
};

// ─────────────────────────────────────────────────────────────────────────────

describe("Architecture: Feature folder structure", () => {
  it("every top-level folder in a feature must be canonical", () => {
    const violations: string[] = [];

    for (const feature of getFeatureNames()) {
      const dirs = getFeatureTopDirs(feature);
      const allowedExtra = KNOWN_NONSTANDARD[feature] ?? [];

      for (const dir of dirs) {
        if (!CANONICAL_FOLDERS.has(dir) && !allowedExtra.includes(dir)) {
          violations.push(`features/${feature}/${dir}`);
        }
      }
    }

    expect(
      violations,
      `NEW non-canonical feature folder(s) — either rename to a canonical name or add to KNOWN_NONSTANDARD with justification:\n${violations.join("\n")}`,
    ).toEqual([]);
  });
});
