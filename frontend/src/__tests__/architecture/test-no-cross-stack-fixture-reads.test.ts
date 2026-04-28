/**
 * ARCH TEST: tests that read files outside the FE stack (e.g. fixtures
 * under ``backend/tests/...``) MUST be guarded by ``describe.skipIf``
 * with an ``existsSync`` check on the fixture path.
 *
 * Why
 * ===
 * The FE Dockerfile (target=test) only ships ``frontend/`` as build
 * context. ``backend/`` is absent, so any test that resolves a path
 * crossing into ``../*backend`` fails with ENOENT inside CI quality-
 * gates and inside the ``ci-parity.sh`` Docker gate.
 *
 * Run 25027765663 (2026-04-28) hit this exact failure on
 * ``test-fe-schema-paths-resolve.test.ts`` while every native
 * ``/test-all`` reported PASS. This guard makes the failure mode
 * impossible to ship: every cross-stack file read must declare a
 * ``describe.skipIf(!existsSync(...))`` so Docker silently skips the
 * test instead of crashing the suite.
 *
 * Detection
 * =========
 * Regex-scan every ``*.test.ts(x)`` file in ``src/`` for path literals
 * that traverse out of the FE root (``../*backend``, ``../*../backend``,
 * etc.). For every match, the same file MUST also contain a
 * ``describe.skipIf(`` and an ``existsSync(`` call. AST parsing is
 * overkill for this guard — strings are local to a single file and
 * the false-positive rate of regex is essentially zero.
 *
 * Failure mode
 * ============
 * If a new test reads ``backend/...`` without the skip guard, this
 * test prints the offending file + the suggested code shape and the
 * push is blocked.
 */
import { readdirSync, readFileSync, statSync } from "fs";
import * as path from "path";

import { describe, expect, it } from "vitest";

const FRONTEND_SRC = path.resolve(__dirname, "../..");

const CROSS_STACK_PATTERNS = [
  /["'`][^"'`]*\.\.\/[^"'`]*backend\/[^"'`]+["'`]/g,
  /path\.resolve\([^)]*backend\/[^)]+\)/g,
];

function walk(dir: string, acc: string[]): void {
  for (const entry of readdirSync(dir)) {
    const full = path.join(dir, entry);
    const stats = statSync(full);
    if (stats.isDirectory()) {
      if (entry === "node_modules" || entry === ".next") continue;
      walk(full, acc);
    } else if (/\.test\.tsx?$/.test(entry)) {
      acc.push(full);
    }
  }
}

function findCrossStackReads(): { file: string; matches: string[] }[] {
  const testFiles: string[] = [];
  walk(FRONTEND_SRC, testFiles);
  const violations: { file: string; matches: string[] }[] = [];
  for (const file of testFiles) {
    const source = readFileSync(file, "utf-8");
    const matches: string[] = [];
    for (const pattern of CROSS_STACK_PATTERNS) {
      const found = source.match(pattern);
      if (found) matches.push(...found);
    }
    if (matches.length === 0) continue;
    if (!source.includes("describe.skipIf(") || !source.includes("existsSync(")) {
      violations.push({ file, matches });
    }
  }
  return violations;
}

describe("Architecture: cross-stack fixture reads must be skipIf-guarded", () => {
  it("every test that reads ../*backend/* declares describe.skipIf + existsSync", () => {
    const violations = findCrossStackReads();
    if (violations.length > 0) {
      const report = violations
        .map((v) => {
          const rel = path.relative(FRONTEND_SRC, v.file);
          return `  ${rel}\n    paths: ${v.matches.join(", ")}`;
        })
        .join("\n");
      throw new Error(
        `\nThe following tests read paths outside the FE Docker build context\n` +
          `but are NOT guarded by describe.skipIf(!existsSync(...)). They will\n` +
          `crash quality-gates with ENOENT.\n\n${report}\n\n` +
          `Fix shape:\n\n` +
          `  import { existsSync, readFileSync } from "fs";\n` +
          `  const FIXTURE = path.resolve(__dirname, "../../../../backend/...");\n` +
          `  const FIXTURE_AVAILABLE = existsSync(FIXTURE);\n` +
          `  describe.skipIf(!FIXTURE_AVAILABLE)("...", () => { ... });\n`,
      );
    }
    expect(violations).toEqual([]);
  });
});
