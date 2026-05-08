/**
 * ARCH FITNESS: Raw width literal values specific to copilot sidebar dimensions
 * MUST only appear in the SSoT module, not scattered across the codebase.
 *
 * Origin: T-7 (app-shell-sidebar-copilot-decoupling). AD6 mandates that all
 * copilot width constants live exclusively in:
 *   `frontend/src/features/copilot/lib/copilot-shell-widths.ts`
 *
 * Problem: Prior to T-2, `useCopilotOffset` returned 380/60/0 while
 * `CopilotSidebar` grid rendered 460/680/60 — an 80-220px drift causing
 * mis-centered dialogs. SSoT consolidation eliminates drift.
 *
 * Detection scope:
 *   Values checked: {380, 460, 680} — the UNIQUE copilot composite widths.
 *   (60, 280, 400 are excluded: too common in Tailwind utility classes for
 *   unrelated components — checked only in copilot-specific contexts below.)
 *
 *   Patterns matched inside NON-comment lines:
 *   - Inline style px: `style={{ width: 380 }}`, `paddingRight: 460`
 *   - Template literal: `${380}px`, `${460}px`
 *   - Tailwind arbitrary px: `w-[380px]`, `w-[460px]`, `w-[680px]`
 *   - minWidth/maxWidth: `minWidth: 460`, `maxWidth: 680`
 *   - paddingRight: `paddingRight: 380`
 *
 * SSoT allowlist: ONLY `features/copilot/lib/copilot-shell-widths.ts`
 * is permitted to declare these constants. All other files must import.
 *
 * Skip: __tests__, __mocks__, .test|.spec, node_modules, .next.
 */
import { readFileSync, readdirSync } from "fs";
import * as path from "path";

import { describe, it, expect } from "vitest";

const SRC_ROOT = path.resolve(__dirname, "../../");

/**
 * The canonical SSoT file for copilot width constants.
 * This is the ONLY file permitted to declare these literals.
 */
const SSOT_REL_PATH = "features/copilot/lib/copilot-shell-widths.ts";

/**
 * Unique copilot composite widths that MUST NOT appear as raw literals
 * outside the SSoT. Values 60/280/400 excluded — too common in Tailwind.
 *
 * - 380: deprecated "open" width (was the hook return before T-2)
 * - 460: expanded = chat(400) + rail(60) — the composite open width
 * - 680: max = chat(400) + history(280) — the full history width
 */
const UNIQUE_COPILOT_WIDTHS = [380, 460, 680] as const;

const SKIP_DIRS = new Set([
  "node_modules",
  ".next",
  "dist",
  "__mocks__",
  "__tests__",
  "storybook-static",
]);

/**
 * For each unique width value, build a regex that matches it only in
 * contexts that suggest it's being used as a pixel dimension.
 * Excludes color codes (e.g., text-slate-380 doesn't exist, but similar).
 */
function buildWidthRegex(value: number): RegExp {
  return new RegExp(
    `(?:` +
      // style={{ width: VALUE }} or width: VALUE,
      `(?:(?:min|max)?[Ww]idth|paddingRight|marginRight)\\s*[=:]\\s*${value}\\b` +
      `|` +
      // template literal: ${VALUE}px
      `\\$\\{${value}\\}px` +
      `|` +
      // Tailwind arbitrary value: w-[VALUEpx] min-w-[VALUEpx] max-w-[VALUEpx]
      `(?:min-|max-)?w-\\[${value}px\\]` +
      `)`,
    "g",
  );
}

const WIDTH_REGEXES = UNIQUE_COPILOT_WIDTHS.map(buildWidthRegex);

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

/** Check if file contains width literal in non-comment lines. */
function fileContainsWidthLiteral(text: string): boolean {
  const lines = text.split("\n");
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("//") || trimmed.startsWith("*")) continue;
    for (const regex of WIDTH_REGEXES) {
      regex.lastIndex = 0;
      if (regex.test(line)) return true;
    }
  }
  return false;
}

/**
 * Files explicitly allowlisted to use these literal values.
 * Entries require justification. Shrink-only ratchet.
 *
 * app/playground/** — manual test/dev pages, not production code.
 */
const KNOWN_VIOLATIONS: ReadonlyMap<string, string> = new Map([
  [
    "app/playground/detail-panel-test/page.tsx",
    "Playground page for manual testing — not production. Uses old 380 literal. TODO: update to COPILOT_WIDTHS.",
  ],
  [
    "features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/PendientesView.tsx",
    "Coincidental 380px sidebar panel width unrelated to copilot drawer (PendientesView master-list left panel). NOT a copilot composite — pre-existing layout. Shrink when refactored to standard Tailwind preset (w-96=384px) in future Story.",
  ],
]);

describe("Architecture: unique copilot width literals (380/460/680) only in SSoT module", () => {
  it("raw composite copilot width literals only appear in copilot-shell-widths.ts", () => {
    const newViolations: string[] = [];
    const seenAllowlistEntries = new Set<string>();

    for (const file of walkSourceFiles(SRC_ROOT)) {
      const rel = relPath(file);

      // SSoT itself is the only allowed declaration site
      if (rel === SSOT_REL_PATH) continue;

      const text = readFileSync(file, "utf-8");
      if (!fileContainsWidthLiteral(text)) continue;

      if (KNOWN_VIOLATIONS.has(rel)) {
        seenAllowlistEntries.add(rel);
        continue;
      }
      newViolations.push(rel);
    }

    if (newViolations.length > 0) {
      const msg = [
        "Unique copilot width literals (380px / 460px / 680px) detected outside SSoT.",
        "These composite values MUST only appear in:",
        `  ${SSOT_REL_PATH}`,
        "",
        "Violations detected:",
        ...newViolations.map((v) => `  - ${v}`),
        "",
        "Fix: import { COPILOT_WIDTHS } from '@/features/copilot/lib/copilot-shell-widths'",
        "and use COPILOT_WIDTHS.expanded (460), COPILOT_WIDTHS.max (680), etc.",
        "See AD6 in 03-arch-fe.md for background.",
      ].join("\n");
      throw new Error(msg);
    }

    // Ratchet: stale allowlist entries = build break (remove when fixed).
    const staleAllowlist = [...KNOWN_VIOLATIONS.keys()].filter(
      (entry) => !seenAllowlistEntries.has(entry),
    );
    expect(staleAllowlist).toEqual([]);
  });
});
