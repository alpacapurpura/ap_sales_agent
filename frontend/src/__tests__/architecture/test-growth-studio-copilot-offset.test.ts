/**
 * ARCH FITNESS: Growth Studio fixed/portal elements MUST consume `useCopilotOffset`
 * (directly OR via `DetailPanel` wrapper which already uses the hook).
 *
 * Origin: PI-8 PR-1 drawer-bowtie hotfix. Multiple full-screen overlays in
 * `features/growth-studio/**` extend behind the copilot drawer on tablet+desktop
 * viewports, distorting the dashboard layout.
 *
 * Ratchet pattern: ALLOWLIST below shrinks only. Adding a new fixed/portal
 * element in growth-studio that does NOT consume `useCopilotOffset` (or
 * `DetailPanel`) is a build break. PI-9/PI-10 will reduce the allowlist.
 *
 * Detection regex:
 *  - `createPortal(` from react-dom
 *  - `className="<...> fixed <...>"` Tailwind class
 *
 * Skip set: __tests__, __mocks__, .test|.spec files.
 */
import { readFileSync, statSync, readdirSync } from "fs";
import * as path from "path";

import { describe, it, expect } from "vitest";

const SRC_ROOT = path.resolve(__dirname, "../../");
const GROWTH_STUDIO_DIR = path.join(SRC_ROOT, "features", "growth-studio");

const PORTAL_REGEX = /\bcreatePortal\s*\(/;
const FIXED_CLASS_REGEX = /className\s*=\s*["`'][^"`']*\bfixed\b[^"`']*["`']/;
const USE_COPILOT_OFFSET_REGEX = /\buseCopilotOffset\b/;
const DETAIL_PANEL_IMPORT_REGEX = /from\s+["']@\/components\/ui\/detail-panel["']/;

const SKIP_DIRS = new Set(["node_modules", ".next", "dist", "__mocks__", "__tests__"]);

/**
 * Allowlist — files KNOWN to violate the rule but explicitly deferred to
 * PI-9 / PI-10 territory. SHRINK ONLY: removing entries is a green ratchet,
 * adding entries requires explicit Chris approval (the new violation should
 * be FIXED, not allowlisted).
 *
 * Paths relative to SRC_ROOT, forward slashes.
 */
const KNOWN_VIOLATIONS: ReadonlySet<string> = new Set([
  "features/growth-studio/components/metrics-dashboard/sidebar/youtube-organic/YouTubeDashboard.tsx",
  "features/growth-studio/components/metrics-dashboard/sidebar/mail/MailDashboard.tsx",
  "features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/MetaAdsDashboard.tsx",
  "features/growth-studio/components/metrics-dashboard/sidebar/ig-organic/IgOrganicDashboard.tsx",
  "features/growth-studio/components/metrics-dashboard/sidebar/website/WebsiteDashboard.tsx",
  "features/growth-studio/components/metrics-dashboard/channel-widgets/ChannelConnectionModal.tsx",
]);

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

function relPath(absPath: string): string {
  return path.relative(SRC_ROOT, absPath).replace(/\\/g, "/");
}

describe("Architecture: growth-studio fixed/portal elements consume useCopilotOffset", () => {
  it("every fixed/portal element imports useCopilotOffset OR uses DetailPanel", () => {
    statSync(GROWTH_STUDIO_DIR);

    const newViolations: string[] = [];
    const seenAllowlistEntries = new Set<string>();

    for (const file of walkSourceFiles(GROWTH_STUDIO_DIR)) {
      const text = readFileSync(file, "utf-8");
      const hasPortal = PORTAL_REGEX.test(text);
      const hasFixedClass = FIXED_CLASS_REGEX.test(text);
      if (!hasPortal && !hasFixedClass) continue;

      const consumesOffset = USE_COPILOT_OFFSET_REGEX.test(text);
      const usesDetailPanel = DETAIL_PANEL_IMPORT_REGEX.test(text);
      if (consumesOffset || usesDetailPanel) continue;

      const rel = relPath(file);
      if (KNOWN_VIOLATIONS.has(rel)) {
        seenAllowlistEntries.add(rel);
        continue;
      }
      newViolations.push(rel);
    }

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

    // Ratchet: shrink-only — fail if allowlist contains stale entries.
    const staleAllowlist = [...KNOWN_VIOLATIONS].filter(
      (entry) => !seenAllowlistEntries.has(entry),
    );
    expect(staleAllowlist).toEqual([]);
  });
});
