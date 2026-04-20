/**
 * Architecture fitness test — social_proof SSoT cleanup.
 *
 * After Phase 4 cleanup the legacy frontend symbols must stay dead. Any
 * future regression that re-imports them fails the build.
 *
 * If you genuinely need the legacy VO (e.g. to migrate the extraction
 * pipeline to the new API), add the file to ``ALLOWED_LEGACY_REFS``
 * explicitly with a justification in the commit message. The allowlist
 * is a ratchet — entries can only be removed.
 */

import { readFileSync } from "node:fs";

import { describe, expect, test } from "vitest";

import { SRC_DIR, relPath, walkFiles } from "./helpers";

// Symbols that were legal in the old array-wrapper world (brand-studio) and
// MUST stay absent from any new frontend code.
const BANNED_SYMBOLS = [
  "testimonialsSchema",
  "authoritySchema",
  "teamSchema",
  "TestimonialItem",
  // KeyFigure is OK for now — the legacy-team InstructorsManager still
  // consumes it through useBrandSettings until its migration sprint.
];

// Files that still legitimately reference the banned symbols. This set
// must only SHRINK over time.
const ALLOWED_LEGACY_REFS: ReadonlySet<string> = new Set<string>([]);

describe("no legacy social_proof references", () => {
  test("no new frontend code imports the legacy array-wrapper schemas", () => {
    const violations: string[] = [];
    const files = walkFiles(SRC_DIR).filter((f) => /\.(ts|tsx)$/.test(f));

    for (const file of files) {
      const rel = relPath(file);
      // Self-exempt: this test references the banned names in its list.
      if (rel.endsWith("test-no-legacy-social-proof.test.ts")) continue;
      if (ALLOWED_LEGACY_REFS.has(rel)) continue;

      const content = readFileSync(file, "utf8");
      for (const symbol of BANNED_SYMBOLS) {
        const pattern = new RegExp(`\\b${symbol}\\b`);
        if (pattern.test(content)) {
          violations.push(`${rel}: references legacy symbol \`${symbol}\``);
        }
      }
    }

    expect(violations).toEqual([]);
  });
});
