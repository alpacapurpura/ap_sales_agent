/**
 * ARCH TEST: Global page padding (p-6|md:p-8) only in PageContainer.
 *
 * Rule: the Tailwind classes `p-6 md:p-8` that form the dashboard's
 * default content padding may only appear in `components/shared/layout/PageContainer.tsx`.
 * Every other file must either use <PageContainer> or define its own padding
 * scheme (`p-10`, `p-8`, flex paddings, etc).
 *
 * Why: a previous refactor hardcoded `p-6 md:p-8` in the dashboard layout,
 * silently adding a 24–32px margin to workspace-style apps (inbox, editors)
 * that need every pixel. The new contract is "each element decides its
 * padding" — PageContainer is the single opt-in for the legacy default.
 *
 * Ratchet pattern: KNOWN_PADDING_VIOLATIONS is frozen at 2026-04-17 and
 * MUST only shrink. To fix: replace the literal `p-6 md:p-8` classes with
 * <PageContainer> or a feature-local padding value, then remove the path
 * from the allowlist.
 */
import { describe, it, expect } from "vitest";
import * as path from "path";
import { SRC_DIR, walkFiles, relPath, isTestFile, readFile } from "./helpers";

// ── Ratchet allowlist ─────────────────────────────────────────────────────────
const KNOWN_PADDING_VIOLATIONS = new Set<string>([
  // Feature-owned roots that intentionally use the same legacy padding.
  // Migrate to <PageContainer> when touched.
  "features/offer-studio/components/dashboard/OfferStudioView.tsx",
  // Public routes (outside the dashboard shell) that define their own canvas.
  "app/(main)/book/[tenant_slug]/[event_slug]/page.tsx",
  "app/(main)/visit/[token]/page.tsx",
]);

// ─────────────────────────────────────────────────────────────────────────────

const PADDING_RE = /\bp-6\b[^"`'\n]*\bmd:p-8\b|\bmd:p-8\b[^"`'\n]*\bp-6\b/;
const ALLOWED_FILE = path.join(SRC_DIR, "components", "shared", "layout", "PageContainer.tsx");

describe("Architecture: Page padding", () => {
  it("p-6 md:p-8 only allowed in PageContainer", () => {
    const violations: string[] = [];

    for (const file of walkFiles(SRC_DIR)) {
      if (isTestFile(file)) continue;
      if (!file.endsWith(".ts") && !file.endsWith(".tsx")) continue;
      if (file === ALLOWED_FILE) continue;

      const content = readFile(file);
      if (PADDING_RE.test(content)) {
        violations.push(relPath(file));
      }
    }

    const newViolations = violations.filter((v) => !KNOWN_PADDING_VIOLATIONS.has(v));
    const alreadyFixed = [...KNOWN_PADDING_VIOLATIONS].filter((v) => !violations.includes(v));

    if (alreadyFixed.length > 0) {
      console.info(
        `[arch] Allowlist can shrink: ${alreadyFixed.length} entries already fixed:\n  ${alreadyFixed.join("\n  ")}`,
      );
    }

    expect(
      newViolations,
      `NEW global-padding violations (use <PageContainer> or define your own padding):\n${newViolations.join("\n")}`,
    ).toEqual([]);
  });
});
