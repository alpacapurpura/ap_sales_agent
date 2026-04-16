/**
 * ARCH TEST: Non-component .ts files must be kebab-case.
 *
 * Rule: .ts(x) files inside hooks/, api/, types/, utils/, config/, lib/,
 * context/, store/, services/ directories must have a kebab-case stem.
 * Uses ignoreMiddleExtensions: true logic (checks only first segment).
 *
 * Ratchet pattern: KNOWN_CAMELCASE_FILES is frozen at 2026-04-15 violations.
 * This set MUST only shrink — never add new entries.
 */
import { describe, it, expect } from "vitest";
import * as path from "path";
import { FEATURES_DIR, walkFiles, relPath, isKebabCase, stemName, isTestFile } from "./helpers";

// ── Ratchet allowlist ─────────────────────────────────────────────────────────
// All hooks renamed to kebab-case on 2026-04-15.
// Context PascalCase files are exempt by the test logic (parent dir = context + "context" in filename,
// or filename matches *Context.tsx). GrowthStudioContext and LandingThemeContext pass the exemption.
const KNOWN_CAMELCASE_FILES = new Set<string>([]);

// ─────────────────────────────────────────────────────────────────────────────

const SCANNED_DIRS = new Set(["hooks", "api", "types", "utils", "config", "lib", "context", "store", "services"]);

// PascalCase context files (e.g. GrowthStudioContext.tsx) are exempt:
// they export a React Context object (PascalCase is the React convention for context exports).
const CONTEXT_FILE_RE = /Context\.(ts|tsx)$/;

describe("Architecture: File naming (non-components)", () => {
  it("every .ts(x) file in hooks/api/types/utils/config/lib/context/store/services/ must be kebab-case", () => {
    const violations: string[] = [];

    for (const file of walkFiles(FEATURES_DIR)) {
      if (isTestFile(file)) continue;
      if (!file.endsWith(".ts") && !file.endsWith(".tsx")) continue;

      const basename = path.basename(file);
      if (basename === "index.ts" || basename === "index.tsx") continue;

      const parentDir = path.basename(path.dirname(file));
      if (!SCANNED_DIRS.has(parentDir)) continue;

      // Exempt: *Context.(ts|tsx) files — PascalCase is React Context convention
      if (CONTEXT_FILE_RE.test(basename)) continue;

      const stem = stemName(basename);
      if (!isKebabCase(stem)) {
        violations.push(relPath(file));
      }
    }

    const newViolations = violations.filter((v) => !KNOWN_CAMELCASE_FILES.has(v));
    const alreadyFixed = [...KNOWN_CAMELCASE_FILES].filter((v) => !violations.includes(v));

    if (alreadyFixed.length > 0) {
      console.info(
        `[arch] Allowlist can shrink: ${alreadyFixed.length} entries already fixed:\n  ${alreadyFixed.join("\n  ")}`,
      );
    }

    expect(
      newViolations,
      `NEW file naming violations (rename to kebab-case, update imports):\n${newViolations.join("\n")}`,
    ).toEqual([]);
  });
});
