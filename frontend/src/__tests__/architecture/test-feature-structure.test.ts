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
  "sections", // brand-style section grouping
  "services", // legacy — prefer api/ for new features
  "mocks", // manual mock data
  "tests", // alternative to __tests__
  "__tests__",
  "__mocks__",
]);

// ── Ratchet allowlist ─────────────────────────────────────────────────────────
// brand-studio introduces schemas/, actions/, pages/ during the form-runtime
// migration (Sprint 1, see docs/ux-sessions/2026-04-17-universal-editable-form-component/
// DECISIONS.md D17). The entry shrinks as Sprint 5 deletes old brand/.
// offer-studio mirrors the same form-runtime structure (Sprint 6+, Phase 12
// pre-sale consolidation): schemas/ hosts field-by-field validators,
// actions/ hosts copilot-aware custom actions, pages/ hosts Next.js-level
// route shells that compose feature slices.
// settings adopts the same pages/ pattern on 2026-04-20 to homologate with
// brand-studio + offer-studio Finder-style navigation (see
// docs/ux-sessions/2026-04-20-settings-finder-nav/UI-SPEC.md). pages/ hosts
// the SETTINGS_SECTION_MAP + factory wrappers indexed by the server dispatcher.
// growth-studio joins on 2026-05-08 (Story 2A folder-parity, ratificado Chris
// 2026-05-07): factory propia adapter mode (5 stages × N channels). pages/
// hosts StageDispatcher + ChannelDispatcher + sections/. actions/ + schemas/
// land in T-7 placeholders for Story 2B (real actions/schemas).
const KNOWN_NONSTANDARD: Record<string, string[]> = {
  "brand-studio": ["schemas", "actions", "pages"],
  "offer-studio": ["schemas", "actions", "pages"],
  "growth-studio": ["schemas", "actions", "pages"],
  settings: ["pages"],
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
