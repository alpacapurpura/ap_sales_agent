/**
 * ARCH FITNESS: `useCopilotOffset` MUST be imported from a single canonical
 * source. Forbids shadowing via re-export from non-canonical paths.
 *
 * Origin: T-7 (app-shell-sidebar-copilot-decoupling). AD6 — drift between
 * `useCopilotOffset` consumers historically caused 80-220px misalignment of
 * dialogs vs copilot rail. Single SSoT prevents the regression.
 *
 * Allowed import paths:
 *   - "@/hooks/use-copilot-offset" (canonical declaration)
 *   - "@/features/copilot/lib/copilot-shell-widths" (re-exports COPILOT_WIDTHS
 *     consumed by the hook — allowed re-export site)
 *
 * Detection:
 *   - Pattern matches `import { ..., useCopilotOffset, ... } from "<source>"`
 *     in any frontend/src file (.ts/.tsx).
 *   - Captures the source string and rejects any path not in the allowlist.
 *
 * Skip set: __tests__, __mocks__, .test|.spec, node_modules, .next.
 */
import { readFileSync, readdirSync } from "fs";
import * as path from "path";

import { describe, it, expect } from "vitest";

const SRC_ROOT = path.resolve(__dirname, "../../");

const ALLOWED_SOURCES = new Set([
  "@/hooks/use-copilot-offset",
  "@/features/copilot/lib/copilot-shell-widths",
]);

const SKIP_DIRS = new Set([
  "node_modules",
  ".next",
  "dist",
  "__mocks__",
  "__tests__",
  "storybook-static",
]);

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
    const name = entry.name;
    if (
      name.endsWith(".test.ts") ||
      name.endsWith(".test.tsx") ||
      name.endsWith(".spec.ts") ||
      name.endsWith(".spec.tsx")
    ) {
      continue;
    }
    if (name.endsWith(".ts") || name.endsWith(".tsx")) {
      yield fullPath;
    }
  }
}

function relPath(absPath: string): string {
  return path.relative(SRC_ROOT, absPath).replace(/\\/g, "/");
}

/**
 * Match `import {...useCopilotOffset...} from "..."` capturing source.
 *
 * Tolerant to multi-line imports + named/default mix.
 */
const IMPORT_REGEX =
  /import\s*(?:type\s+)?\{[^}]*\buseCopilotOffset\b[^}]*\}\s*from\s*["']([^"']+)["']/g;

describe("Architecture: useCopilotOffset has single canonical import source", () => {
  it("rejects shadowing — useCopilotOffset only from @/hooks or @/features/copilot/lib", () => {
    const violations: { file: string; source: string }[] = [];

    for (const file of walkSourceFiles(SRC_ROOT)) {
      const text = readFileSync(file, "utf-8");
      if (!text.includes("useCopilotOffset")) continue;

      IMPORT_REGEX.lastIndex = 0;
      let match: RegExpExecArray | null;
      while ((match = IMPORT_REGEX.exec(text)) !== null) {
        const source = match[1];
        if (ALLOWED_SOURCES.has(source)) continue;
        violations.push({ file: relPath(file), source });
      }
    }

    if (violations.length > 0) {
      const msg = [
        "useCopilotOffset imports detected from non-canonical sources.",
        "",
        "Allowed sources:",
        ...[...ALLOWED_SOURCES].map((s) => `  - ${s}`),
        "",
        "Violations:",
        ...violations.map((v) => `  - ${v.file} imports from "${v.source}"`),
        "",
        "Fix: change import to '@/hooks/use-copilot-offset'.",
        "See AD6 in 03-arch-fe.md.",
      ].join("\n");
      expect.fail(msg);
    }

    expect(violations).toEqual([]);
  });
});
