/**
 * ARCH TEST: Hook exports must live in hooks/ directories.
 *
 * Rule: any file exporting `function use[A-Z]...` or `const use[A-Z]...`
 * must reside in a directory named `hooks/`.
 *
 * Exemptions (not violations):
 * - Files in `api/` dirs (React Query hooks co-located with API calls).
 * - Files matching *Context.(ts|tsx) (context files that export useXxxContext).
 *
 * Ratchet pattern: KNOWN_HOOKS_OUTSIDE_HOOKS is frozen at 2026-04-15 violations.
 * This set MUST only shrink — never add new entries.
 */
import { describe, it, expect } from "vitest";
import * as path from "path";
import { FEATURES_DIR, walkFiles, relPath, isTestFile, readFile } from "./helpers";

// ── Ratchet allowlist ─────────────────────────────────────────────────────────
const KNOWN_HOOKS_OUTSIDE_HOOKS = new Set([
  // Component that also exports a hook — hooks should be extracted to hooks/ dir
  "features/offer-studio/components/container/offer-shell.tsx",
]);

// ─────────────────────────────────────────────────────────────────────────────

const HOOK_EXPORT_RE = /export\s+(?:function|const)\s+use[A-Z]/;
const CONTEXT_FILE_RE = /Context\.(ts|tsx)$/;

describe("Architecture: Hook location", () => {
  it("files exporting use[A-Z] hooks must be in hooks/ or api/ dirs, or be Context files", () => {
    const violations: string[] = [];

    for (const file of walkFiles(FEATURES_DIR)) {
      if (isTestFile(file)) continue;
      if (!file.endsWith(".ts") && !file.endsWith(".tsx")) continue;

      const content = readFile(file);
      if (!HOOK_EXPORT_RE.test(content)) continue;

      const parentDir = path.basename(path.dirname(file));
      const filename = path.basename(file);

      // Exempt: already in hooks/
      if (parentDir === "hooks") continue;
      // Exempt: in api/ (React Query hooks pattern)
      if (parentDir === "api") continue;
      // Exempt: in store/ (Zustand stores follow use* naming convention)
      if (parentDir === "store") continue;
      // Exempt: context files (*Context.ts or *Context.tsx)
      if (CONTEXT_FILE_RE.test(filename)) continue;
      // Exempt: context provider files in context/ dir with "context" in filename
      if (parentDir === "context" && filename.toLowerCase().includes("context")) continue;

      violations.push(relPath(file));
    }

    // Deduplicate (a file can match multiple times if it has multiple hook exports)
    const unique = [...new Set(violations)];
    const newViolations = unique.filter((v) => !KNOWN_HOOKS_OUTSIDE_HOOKS.has(v));
    const alreadyFixed = [...KNOWN_HOOKS_OUTSIDE_HOOKS].filter((v) => !unique.includes(v));

    if (alreadyFixed.length > 0) {
      console.info(
        `[arch] Allowlist can shrink: ${alreadyFixed.length} entries already fixed:\n  ${alreadyFixed.join("\n  ")}`,
      );
    }

    expect(
      newViolations,
      `NEW hook location violations (move to hooks/ or extract hook):\n${newViolations.join("\n")}`,
    ).toEqual([]);
  });
});
