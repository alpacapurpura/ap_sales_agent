/**
 * ARCH TEST: No default exports in features/.
 *
 * Rule: `export default` is forbidden in src/features/**. Named exports only.
 * Exception: Next.js App Router pages in src/app/ (already excluded from scan).
 *
 * Why: default exports break tree-shaking, make refactoring harder (rename
 * requires finding every import), and allow inconsistent import names.
 *
 * Ratchet pattern: KNOWN_DEFAULT_EXPORTS is frozen at 2026-04-15 violations.
 * This set MUST only shrink — never add new entries.
 * To fix: change `export default function X` → `export function X`,
 * then update `import X from '...'` → `import { X } from '...'`.
 */
import { describe, it, expect } from "vitest";

import { FEATURES_DIR, walkFiles, relPath, isTestFile, readFile } from "./helpers";

// ── Ratchet allowlist ─────────────────────────────────────────────────────────
// Empty — all 10 default exports fixed on 2026-04-15.
const KNOWN_DEFAULT_EXPORTS = new Set<string>([]);

// ─────────────────────────────────────────────────────────────────────────────

const DEFAULT_EXPORT_RE = /^export\s+default\b/m;

describe("Architecture: No default exports", () => {
  it("no file in features/ may use `export default`", () => {
    const violations: string[] = [];

    for (const file of walkFiles(FEATURES_DIR)) {
      if (isTestFile(file)) continue;
      if (!file.endsWith(".ts") && !file.endsWith(".tsx")) continue;
      // Storybook stories require `export default meta` per Storybook's CSF contract.
      if (file.endsWith(".stories.ts") || file.endsWith(".stories.tsx")) continue;

      const content = readFile(file);
      if (DEFAULT_EXPORT_RE.test(content)) {
        violations.push(relPath(file));
      }
    }

    const newViolations = violations.filter((v) => !KNOWN_DEFAULT_EXPORTS.has(v));
    const alreadyFixed = [...KNOWN_DEFAULT_EXPORTS].filter((v) => !violations.includes(v));

    if (alreadyFixed.length > 0) {
      console.info(
        `[arch] Allowlist can shrink: ${alreadyFixed.length} entries already fixed:\n  ${alreadyFixed.join("\n  ")}`,
      );
    }

    expect(
      newViolations,
      `NEW default export violations (convert to named exports):\n${newViolations.join("\n")}`,
    ).toEqual([]);
  });
});
