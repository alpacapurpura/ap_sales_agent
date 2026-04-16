/**
 * ARCH TEST: fetchClient calls must be inside api/ directories.
 *
 * Rule: any file using `fetchClient` must reside inside an `api/` folder.
 * This enforces the pattern: components and hooks import from api/, they do
 * not call fetchClient directly.
 *
 * Why: centralising API calls in api/ makes mocking, type safety, and
 * refactoring predictable. Hooks that call fetchClient directly bypass
 * the API layer and create hidden data-fetching logic.
 *
 * Ratchet pattern: KNOWN_FETCHCLIENT_OUTSIDE_API is frozen at 2026-04-15.
 * This set MUST only shrink — never add new entries.
 * To fix: extract the fetch call to api/<name>.ts and import from there.
 */
import { describe, it, expect } from "vitest";
import * as path from "path";
import { FEATURES_DIR, walkFiles, relPath, isTestFile, readFile } from "./helpers";

// ── Ratchet allowlist ─────────────────────────────────────────────────────────
const KNOWN_FETCHCLIENT_OUTSIDE_API = new Set([
  "features/audit/hooks/use-audit.ts",
  "features/brand/sections/voice/voice-manager.tsx",
  "features/connections/components/meta-view.tsx",
  "features/growth-studio/hooks/use-connection-health.ts",
  "features/growth-studio/hooks/use-mail-dashboard.ts",
  "features/growth-studio/hooks/use-sync-channel.ts",
  "features/offer-studio/hooks/use-offer-metadata.ts",
  // sales/services/dashboardService.ts → moved to api/dashboard-service.ts (fixed)
  // sales/services/leadService.ts → moved to api/lead-service.ts (fixed)
]);

// ─────────────────────────────────────────────────────────────────────────────

const FETCHCLIENT_RE = /\bfetchClient\b/;

describe("Architecture: API call location", () => {
  it("fetchClient must only be used inside api/ directories", () => {
    const violations: string[] = [];

    for (const file of walkFiles(FEATURES_DIR)) {
      if (isTestFile(file)) continue;
      if (!file.endsWith(".ts") && !file.endsWith(".tsx")) continue;

      // Files already in api/ are compliant
      const segments = file.split(path.sep);
      if (segments.includes("api")) continue;

      const content = readFile(file);
      if (FETCHCLIENT_RE.test(content)) {
        violations.push(relPath(file));
      }
    }

    const newViolations = violations.filter((v) => !KNOWN_FETCHCLIENT_OUTSIDE_API.has(v));
    const alreadyFixed = [...KNOWN_FETCHCLIENT_OUTSIDE_API].filter((v) => !violations.includes(v));

    if (alreadyFixed.length > 0) {
      console.info(
        `[arch] Allowlist can shrink: ${alreadyFixed.length} entries already fixed:\n  ${alreadyFixed.join("\n  ")}`,
      );
    }

    expect(
      newViolations,
      `NEW fetchClient-outside-api/ violations (move fetch call to api/ and import from there):\n${newViolations.join("\n")}`,
    ).toEqual([]);
  });
});
