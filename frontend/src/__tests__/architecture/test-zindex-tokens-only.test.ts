/**
 * ARCH FITNESS: Shell + copilot scope components MUST use Z_INDEX_CLASSES tokens
 * (imported from `@/lib/tokens/z-index`) for all z-index styling. Hardcoded
 * Tailwind z-NN utility classes (e.g., `z-50`, `z-40`) are forbidden.
 *
 * Origin: T-7 (app-shell-sidebar-copilot-decoupling). AD5 mandates a fluid
 * z-index scale via Z_INDEX_CLASSES tokens to prevent undocumented z-stacking.
 *
 * Detection:
 *  - Hardcoded Tailwind z-integer classes: `z-0`, `z-10`, `z-20`, `z-30`,
 *    `z-40`, `z-50`, `z-[50]`, `z-[40]`, etc. in JSX className strings.
 *  - Excludes: `z-auto`, `z-inherit`, `z-initial`, `z-unset` (valid utilities).
 *  - Pattern: `z-\d+` and `z-[\d+]` literals inside className values.
 *
 * Scope: `components/shared/layout/` + `features/copilot/components/`
 * (T-9 Phase 10 covers `components/ui/` Shadcn primitives — separate ticket).
 *
 * Ratchet: KNOWN_VIOLATIONS_UI is empty — new violations are build breaks.
 *
 * Skip set: __tests__, __mocks__, .test|.spec files.
 */
import { readFileSync, statSync, readdirSync } from "fs";
import * as path from "path";

import { describe, it, expect } from "vitest";

const SRC_ROOT = path.resolve(__dirname, "../../");
const SHELL_LAYOUT_DIR = path.join(SRC_ROOT, "components", "shared", "layout");
const COPILOT_COMPONENTS_DIR = path.join(SRC_ROOT, "features", "copilot", "components");

/**
 * Matches hardcoded z-index Tailwind utility classes in className strings.
 *
 * Matches:
 *   - `z-0`, `z-10`, `z-20`, `z-30`, `z-40`, `z-50` (standard scale)
 *   - `z-[40]`, `z-[50]`, `z-[60]` (arbitrary value brackets)
 *   - Any `z-<digits>` pattern (catches non-standard values)
 *
 * Does NOT match:
 *   - `z-auto` (valid utility)
 *   - `z-index` (CSS property name — not a utility class)
 *   - Z_INDEX (constant name — not a class string)
 *   - Comments (test skips comment-only lines)
 */
const HARDCODED_Z_REGEX = /\bz-(?:\d+|\[\d+\])\b/;

/**
 * Only flag occurrences inside className/class attribute values.
 * We look for the pattern in lines that contain className/class context,
 * or as standalone string literals (template literals, cn() args).
 *
 * Strategy: scan full file text for hardcoded z patterns. Then verify
 * the file imports Z_INDEX_CLASSES. If hardcoded patterns exist AND
 * the file does NOT import Z_INDEX_CLASSES, it's a violation.
 * If the file imports Z_INDEX_CLASSES AND has hardcoded z patterns,
 * the hardcoded patterns are likely from comments or stale code — flag it.
 */
const Z_INDEX_CLASSES_IMPORT_REGEX = /from\s+["']@\/lib\/tokens\/z-index["']/;

const SKIP_DIRS = new Set(["node_modules", ".next", "dist", "__mocks__", "__tests__"]);

/**
 * Allowlist: empty post T-6. Shell + copilot components fully migrated
 * to Z_INDEX_CLASSES tokens. Shrink-only — new entries = build break.
 *
 * Phase 10 (T-9) handles `components/ui/` Shadcn primitives separately.
 */
const KNOWN_VIOLATIONS_UI: ReadonlySet<string> = new Set([]);

/** Walk source .ts/.tsx files, skipping test/spec/mock dirs. */
function* walkSourceFiles(dir: string): Generator<string> {
  const entries = readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    if (SKIP_DIRS.has(entry.name)) continue;
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      yield* walkSourceFiles(fullPath);
      continue;
    }
    if (!entry.isFile()) continue;
    if (
      entry.name.endsWith(".test.ts") ||
      entry.name.endsWith(".test.tsx") ||
      entry.name.endsWith(".spec.ts") ||
      entry.name.endsWith(".spec.tsx")
    ) {
      continue;
    }
    if (entry.name.endsWith(".ts") || entry.name.endsWith(".tsx")) {
      yield fullPath;
    }
  }
}

/** Return path relative to SRC_ROOT with forward slashes. */
function relPath(absPath: string): string {
  return path.relative(SRC_ROOT, absPath).replace(/\\/g, "/");
}

/**
 * Extracts lines from file text that contain hardcoded z-index classes,
 * excluding pure comment lines (// ... and * ... block comment lines).
 */
function findHardcodedZLines(text: string): string[] {
  return text.split("\n").filter((line) => {
    const trimmed = line.trim();
    if (trimmed.startsWith("//") || trimmed.startsWith("*")) return false;
    return HARDCODED_Z_REGEX.test(line);
  });
}

/** Check a directory for hardcoded z-index violations. */
function checkDir(
  dir: string,
  allowlist: ReadonlySet<string>,
): { newViolations: string[]; seenAllowlistEntries: Set<string> } {
  const newViolations: string[] = [];
  const seenAllowlistEntries = new Set<string>();

  for (const file of walkSourceFiles(dir)) {
    const text = readFileSync(file, "utf-8");
    const hardcodedLines = findHardcodedZLines(text);
    if (hardcodedLines.length === 0) continue;

    const rel = relPath(file);
    if (allowlist.has(rel)) {
      seenAllowlistEntries.add(rel);
      continue;
    }
    newViolations.push(rel);
  }

  return { newViolations, seenAllowlistEntries };
}

describe("Architecture: z-index classes use Z_INDEX_CLASSES tokens (shell + copilot scope)", () => {
  it("shell layout components have no hardcoded z-NN Tailwind classes outside comments", () => {
    statSync(SHELL_LAYOUT_DIR);

    const { newViolations, seenAllowlistEntries } = checkDir(SHELL_LAYOUT_DIR, KNOWN_VIOLATIONS_UI);

    if (newViolations.length > 0) {
      const msg = [
        "Shell layout components MUST use Z_INDEX_CLASSES tokens from '@/lib/tokens/z-index'.",
        "Hardcoded z-NN Tailwind classes detected (e.g., z-50, z-[60]):",
        ...newViolations.map((v) => `  - ${v}`),
        "",
        "Fix: import { Z_INDEX_CLASSES } from '@/lib/tokens/z-index' and replace",
        "hardcoded z-50 → Z_INDEX_CLASSES.TOPBAR, z-40 → Z_INDEX_CLASSES.APP_SIDEBAR, etc.",
        "See AD5 in 03-arch-fe.md for the full z-index scale.",
      ].join("\n");
      throw new Error(msg);
    }

    const staleAllowlist = [...KNOWN_VIOLATIONS_UI].filter(
      (entry) => !seenAllowlistEntries.has(entry),
    );
    expect(staleAllowlist).toEqual([]);
  });

  it("copilot components have no hardcoded z-NN Tailwind classes outside comments", () => {
    statSync(COPILOT_COMPONENTS_DIR);

    const { newViolations, seenAllowlistEntries } = checkDir(
      COPILOT_COMPONENTS_DIR,
      KNOWN_VIOLATIONS_UI,
    );

    if (newViolations.length > 0) {
      const msg = [
        "Copilot components MUST use Z_INDEX_CLASSES tokens from '@/lib/tokens/z-index'.",
        "Hardcoded z-NN Tailwind classes detected (e.g., z-50, z-[60]):",
        ...newViolations.map((v) => `  - ${v}`),
        "",
        "Fix: import { Z_INDEX_CLASSES } from '@/lib/tokens/z-index' and replace",
        "hardcoded z-50 → Z_INDEX_CLASSES.COPILOT_BACKDROP, z-60 → Z_INDEX_CLASSES.COPILOT_DRAWER, etc.",
        "See AD5 in 03-arch-fe.md for the full z-index scale.",
      ].join("\n");
      throw new Error(msg);
    }

    const staleAllowlist = [...KNOWN_VIOLATIONS_UI].filter(
      (entry) => !seenAllowlistEntries.has(entry),
    );
    expect(staleAllowlist).toEqual([]);
  });
});
