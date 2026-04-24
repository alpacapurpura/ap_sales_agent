/**
 * ARCH TEST: Feature folders must be kebab-case.
 *
 * Rule: every directory under src/features/ must be named in kebab-case.
 * Exceptions: __tests__, __mocks__ (double-underscore convention).
 *
 * Ratchet pattern: KNOWN_BAD_FOLDERS is frozen at 2026-04-15 violations.
 * This set MUST only shrink — never add new entries.
 * To fix: git mv old-dir new-dir, update all imports, run tsc --noEmit.
 */
import * as path from "path";

import { describe, it, expect } from "vitest";

import { FEATURES_DIR, walkDirs, relPath, isKebabCase } from "./helpers";

// ── Ratchet allowlist ─────────────────────────────────────────────────────────
// Empty — tenant_domains was renamed to tenant-domains (2026-04-15).
const KNOWN_BAD_FOLDERS = new Set<string>([]);

// ─────────────────────────────────────────────────────────────────────────────

const EXEMPT_PREFIXES = new Set(["__tests__", "__mocks__", "__generated__"]);

describe("Architecture: Folder naming", () => {
  it("every directory under features/ must be kebab-case", () => {
    const violations: string[] = [];

    for (const dir of walkDirs(FEATURES_DIR)) {
      const name = path.basename(dir);
      if (EXEMPT_PREFIXES.has(name)) continue;
      if (!isKebabCase(name)) {
        violations.push(relPath(dir));
      }
    }

    const newViolations = violations.filter((v) => !KNOWN_BAD_FOLDERS.has(v));
    const alreadyFixed = [...KNOWN_BAD_FOLDERS].filter((v) => !violations.includes(v));

    if (alreadyFixed.length > 0) {
      console.info(
        `[arch] Allowlist can shrink: ${alreadyFixed.length} entries already fixed:\n  ${alreadyFixed.join("\n  ")}`,
      );
    }

    expect(
      newViolations,
      `NEW folder naming violations (rename to kebab-case, update imports):\n${newViolations.join("\n")}`,
    ).toEqual([]);
  });
});
