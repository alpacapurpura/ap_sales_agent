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
import { describe, it, expect } from "vitest";
import * as path from "path";
import { FEATURES_DIR, walkDirs, relPath, isKebabCase } from "./helpers";

// ── Ratchet allowlist ─────────────────────────────────────────────────────────
// These 1 entry existed on 2026-04-15. Fix and remove.
const KNOWN_BAD_FOLDERS = new Set([
  "features/tenant_domains", // snake_case — rename to tenant-domains
]);

// ─────────────────────────────────────────────────────────────────────────────

const EXEMPT_PREFIXES = new Set(["__tests__", "__mocks__"]);

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
