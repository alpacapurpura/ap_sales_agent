/**
 * ARCH FITNESS: Fixed/portal elements in shell + copilot scopes MUST consume
 * `useCopilotOffset` (directly OR via `DetailPanel` wrapper which already uses
 * the hook), OR be an explicit chrome-component that IS part of the shell itself.
 *
 * Origin: PI-8 PR-1 drawer-bowtie hotfix (growth-studio scope). Extended in
 * T-7 (app-shell-sidebar-copilot-decoupling) to cover 3 directories:
 *   1. features/growth-studio  — original scope
 *   2. components/shared/layout — shell chrome scope (NEW T-7)
 *   3. features/copilot/components — copilot chrome scope (NEW T-7)
 *
 * Ratchet pattern: allowlists are per-scope and shrink only. Adding a new
 * fixed/portal element that does NOT consume `useCopilotOffset` (and is not
 * an explicit chrome component) is a build break.
 *
 * Shell/copilot chrome components (AppSidebar, CopilotSidebar, CopilotFAB)
 * ARE the chrome itself — they are in KNOWN_VIOLATIONS_SHELL /
 * KNOWN_VIOLATIONS_COPILOT with explicit justification.
 *
 * Detection regex:
 *  - `createPortal(` from react-dom
 *  - `className="<...> fixed <...>"` Tailwind class (template literal / backtick / quote)
 *
 * Skip set: __tests__, __mocks__, .test|.spec files.
 */
import { readFileSync, statSync, readdirSync } from "fs";
import * as path from "path";

import { describe, it, expect } from "vitest";

const SRC_ROOT = path.resolve(__dirname, "../../");
const GROWTH_STUDIO_DIR = path.join(SRC_ROOT, "features", "growth-studio");
const SHELL_LAYOUT_DIR = path.join(SRC_ROOT, "components", "shared", "layout");
const COPILOT_COMPONENTS_DIR = path.join(SRC_ROOT, "features", "copilot", "components");

const PORTAL_REGEX = /\bcreatePortal\s*\(/;
const FIXED_CLASS_REGEX = /className\s*=\s*["`'][^"`']*\bfixed\b[^"`']*["`']/;
const USE_COPILOT_OFFSET_REGEX = /\buseCopilotOffset\b/;
const DETAIL_PANEL_IMPORT_REGEX = /from\s+["']@\/components\/ui\/detail-panel["']/;

const SKIP_DIRS = new Set(["node_modules", ".next", "dist", "__mocks__", "__tests__"]);

/**
 * Growth Studio allowlist — was drained to empty in T-5 (growth-studio-folder-parity).
 * All 6 dashboards adopted useCopilotOffset. Shrink-only.
 */
const KNOWN_VIOLATIONS_GROWTH: ReadonlySet<string> = new Set([]);

/**
 * Shell layout allowlist — drained empty post T-7 closure (orchestrator).
 * AppSidebar.tsx pre-cataloged but stale: post-T-6 z-index migration, the
 * scan no longer flags it (likely consumes shell-mutex flow that bypasses
 * the fixed/portal trigger criteria). Shrink-only.
 */
const KNOWN_VIOLATIONS_SHELL: ReadonlySet<string> = new Set([]);

/**
 * Copilot components allowlist — drained empty post T-7 closure (orchestrator).
 * CopilotSidebar + CopilotFAB pre-cataloged but stale: both consume mutex
 * dispatch (T-4/T-5) which the scan does not flag as offset-violation.
 * Shrink-only.
 */
const KNOWN_VIOLATIONS_COPILOT: ReadonlySet<string> = new Set([]);

/** Walk source .ts/.tsx files, skipping test/spec/mock/generated dirs. */
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
 * Shared violation checker — runs for a given dir + allowlist pair.
 * Returns { newViolations, seenAllowlistEntries }.
 */
function checkDir(
  dir: string,
  allowlist: ReadonlySet<string>,
): { newViolations: string[]; seenAllowlistEntries: Set<string> } {
  const newViolations: string[] = [];
  const seenAllowlistEntries = new Set<string>();

  for (const file of walkSourceFiles(dir)) {
    const text = readFileSync(file, "utf-8");
    const hasPortal = PORTAL_REGEX.test(text);
    const hasFixedClass = FIXED_CLASS_REGEX.test(text);
    if (!hasPortal && !hasFixedClass) continue;

    const consumesOffset = USE_COPILOT_OFFSET_REGEX.test(text);
    const usesDetailPanel = DETAIL_PANEL_IMPORT_REGEX.test(text);
    if (consumesOffset || usesDetailPanel) continue;

    const rel = relPath(file);
    if (allowlist.has(rel)) {
      seenAllowlistEntries.add(rel);
      continue;
    }
    newViolations.push(rel);
  }

  return { newViolations, seenAllowlistEntries };
}

describe("Architecture: fixed/portal elements consume useCopilotOffset (shell + copilot scope)", () => {
  it("growth-studio: every fixed/portal element imports useCopilotOffset OR uses DetailPanel", () => {
    statSync(GROWTH_STUDIO_DIR);

    const { newViolations, seenAllowlistEntries } = checkDir(
      GROWTH_STUDIO_DIR,
      KNOWN_VIOLATIONS_GROWTH,
    );

    if (newViolations.length > 0) {
      const msg = [
        "Growth Studio fixed/portal elements MUST consume useCopilotOffset",
        "(or use DetailPanel which wraps the hook). New offenders detected:",
        ...newViolations.map((v) => `  - ${v}`),
        "",
        "Fix: import { useCopilotOffset } from '@/hooks/use-copilot-offset' and",
        "apply { right: copilotWidth } / { paddingRight: copilotWidth } to the",
        "fixed/portal element. OR wrap the content with <DetailPanel>.",
      ].join("\n");
      throw new Error(msg);
    }

    const staleAllowlist = [...KNOWN_VIOLATIONS_GROWTH].filter(
      (entry) => !seenAllowlistEntries.has(entry),
    );
    expect(staleAllowlist).toEqual([]);
  });

  it("shell layout: fixed/portal elements are chrome components (allowlisted) or consume useCopilotOffset", () => {
    statSync(SHELL_LAYOUT_DIR);

    const { newViolations, seenAllowlistEntries } = checkDir(
      SHELL_LAYOUT_DIR,
      KNOWN_VIOLATIONS_SHELL,
    );

    if (newViolations.length > 0) {
      const msg = [
        "Shell layout fixed/portal elements must either:",
        "  (a) be in KNOWN_VIOLATIONS_SHELL (chrome components that ARE the shell), OR",
        "  (b) consume useCopilotOffset / use DetailPanel.",
        "",
        "New offenders detected (add to KNOWN_VIOLATIONS_SHELL with justification OR fix):",
        ...newViolations.map((v) => `  - ${v}`),
      ].join("\n");
      throw new Error(msg);
    }

    const staleAllowlist = [...KNOWN_VIOLATIONS_SHELL].filter(
      (entry) => !seenAllowlistEntries.has(entry),
    );
    expect(staleAllowlist).toEqual([]);
  });

  it("copilot components: fixed/portal elements are chrome components (allowlisted) or consume useCopilotOffset", () => {
    statSync(COPILOT_COMPONENTS_DIR);

    const { newViolations, seenAllowlistEntries } = checkDir(
      COPILOT_COMPONENTS_DIR,
      KNOWN_VIOLATIONS_COPILOT,
    );

    if (newViolations.length > 0) {
      const msg = [
        "Copilot component fixed/portal elements must either:",
        "  (a) be in KNOWN_VIOLATIONS_COPILOT (chrome components that ARE the copilot drawer), OR",
        "  (b) consume useCopilotOffset / use DetailPanel.",
        "",
        "New offenders detected (add to KNOWN_VIOLATIONS_COPILOT with justification OR fix):",
        ...newViolations.map((v) => `  - ${v}`),
      ].join("\n");
      throw new Error(msg);
    }

    const staleAllowlist = [...KNOWN_VIOLATIONS_COPILOT].filter(
      (entry) => !seenAllowlistEntries.has(entry),
    );
    expect(staleAllowlist).toEqual([]);
  });
});
