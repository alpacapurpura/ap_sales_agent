/**
 * codemod_fe_imports.ts — Story 10 FE imports rewrite.
 *
 * Transforms internal Nicolify @/ imports → @luana/* workspace-member imports.
 * Used via jscodeshift:
 *   npx jscodeshift -t scripts/codemod_fe_imports.ts frontend/src/ --extensions=ts,tsx --dry
 *   npx jscodeshift -t scripts/codemod_fe_imports.ts frontend/src/ --extensions=ts,tsx
 *
 * Mapping per 03-arch.md §2 Feature 2 table.
 * Idempotent: running twice produces same output.
 *
 * Decisions honored:
 *   D5 — fix-on-discovery cap delta=0
 *   D1 — full big-bang scope
 *   D10 — T-1 is tooling only (this script not executed until T-8)
 *
 * NOTE: This script is authored in T-1 as tooling. Execution happens in T-8.
 * The exact mapping will be verified during T-8 Phase 0 spike (pnpm workspace
 * symlink resolution + @luana/* package exports). If a mapping is incomplete
 * → Halt Trigger #1 per 05-guidelines.md.
 */

import type { Transform, FileInfo, API, Options } from "jscodeshift";

// MAPPING — source @/ path prefix → target @luana/* package
// Format: [source_prefix, target_replacement]
// Order matters: longer/more specific matches first.
const MAPPING: Array<[string, string]> = [
  // ===== Shared @luana/* packages (from 03-arch.md §2 Feature 2) =====
  ["@/components/ui", "@luana/ui-kit"],
  ["@/lib/api/fetchClient", "@luana/api-client"],
  ["@/lib/format", "@luana/format"],
  ["@/lib/tokens", "@luana/design-tokens"],
  ["@/lib/zod-schemas", "@luana/schemas"],

  // @/lib/utils/* — GUARD: Nicolify-local subpaths must appear BEFORE @/lib/utils
  // so they match exact-first and short-circuit before the prefix rule below.
  // These paths are Nicolify-local (no @luana/* equivalent) — guard returns self,
  // caller sees rewritten === source.value and skips rewrite.
  ["@/lib/utils/colors", "@/lib/utils/colors"], // Nicolify-local getContrastColor — guard
  ["@/lib/utils/assets", "@/lib/utils/assets"], // Nicolify-local — guard

  // @/lib/utils (exact only — cn() → @luana/format). After guards above.
  // T-8.bis D1: cn() is re-exported from @luana/format main barrel (src/index.ts line 3).
  ["@/lib/utils", "@luana/format"],

  // Format helpers lifted to @luana/format (T-8.bis D1: same exports verified)
  ["@/lib/format-money", "@luana/format"],
  ["@/lib/format-date", "@luana/format"],
  ["@/lib/case-conversion", "@luana/format"],
  ["@/lib/constants/currencies", "@luana/format"],
  ["@/lib/constants/channel-colors", "@luana/format"],

  // Hooks: leaf hooks lifted to @luana/hooks (T-8 T-8.bis)
  ["@/hooks/useTenantLocale", "@luana/hooks"],
  ["@/hooks/useTenantConfig", "@luana/hooks"],
  ["@/hooks/use-copilot-offset", "@luana/hooks"], // T-8.bis D1: subpath export added
  ["@/hooks/use-is-mounted", "@luana/hooks"],     // already in @luana/hooks barrel
  ["@/hooks/use-viewport", "@luana/hooks"],       // already in @luana/hooks barrel

  // Extension SDK (TypeScript side of extension points)
  ["@/lib/extension-sdk", "@luana/extension-sdk"],

  // ===== STAY LOCAL — Nicolify-specific (NO rewrite) =====
  // The following prefixes must NOT be rewritten — they are Nicolify-vertical-specific:
  //   @/app/...                    — Next.js route segments (Nicolify routes are brand-specific)
  //   @/features/...               — Nicolify business feature modules
  //   @/stores/...                 — Nicolify-local Zustand stores
  //   @/components/shared/...      — Nicolify layouts and shared UI (NOT lifted to @luana/ui-kit)
  //   @/lib/form-runtime/*         — Nicolify form-runtime engine (NOT in @luana/*)
  //   @/lib/http-client            — Nicolify fetchClient wrapper
  //   @/lib/config                 — Nicolify app config
  //   @/lib/edge                   — Nicolify edge runtime utils
  //   @/lib/api/*                  — Nicolify-local API helpers (connections/settings/buyer-persona/etc)
  //   @/lib/studio-section-page    — Nicolify lazy-loading factory (NOT in @luana/*)
  //   @/lib/mock-config            — Nicolify dev mock config (NOT in @luana/*)
  //   @/lib/utils/colors           — Nicolify getContrastColor (guarded above)
  //   @/lib/utils/assets           — Nicolify asset helpers (guarded above)
  //   @/components/form-runtime/*  — Nicolify form-runtime components (NOT in @luana/ui-kit)
  //   @/hooks/use-shell-mutex      — deferred T-12 (requires @/components/shared + @/stores)
  //   @/hooks/use-currency-catalog — deferred T-12 (requires @/lib/api)
  // These are excluded from MAPPING intentionally.
];

/**
 * Apply the MAPPING to a single import specifier string.
 * Returns the rewritten specifier, or null if no mapping applies.
 */
function rewriteSpecifier(source: string): string | null {
  for (const [srcPrefix, target] of MAPPING) {
    if (source === srcPrefix) {
      return target;
    }
    if (source.startsWith(srcPrefix + "/")) {
      const suffix = source.slice(srcPrefix.length); // includes leading /
      return target + suffix;
    }
  }
  return null;
}

const transform: Transform = (file: FileInfo, api: API, _options: Options) => {
  const j = api.jscodeshift;
  const root = j(file.source);
  let changed = false;

  // Rewrite static import declarations: import X from '...', import { X } from '...'
  root.find(j.ImportDeclaration).forEach((path) => {
    const source = path.node.source;
    if (typeof source.value !== "string") return;

    const rewritten = rewriteSpecifier(source.value);
    if (rewritten !== null && rewritten !== source.value) {
      source.value = rewritten;
      changed = true;
    }
  });

  // Rewrite dynamic imports: import('...')
  root
    .find(j.CallExpression, {
      callee: { type: "Import" },
    })
    .forEach((path) => {
      const args = path.node.arguments;
      if (args.length === 0) return;
      const firstArg = args[0];
      if (firstArg.type !== "StringLiteral" && firstArg.type !== "Literal") return;
      const value = (firstArg as { value: unknown }).value;
      if (typeof value !== "string") return;
      const rewritten = rewriteSpecifier(value);
      if (rewritten !== null && rewritten !== value) {
        (firstArg as { value: string }).value = rewritten;
        changed = true;
      }
    });

  // Rewrite require() calls (legacy CJS patterns, unlikely in this codebase but safe)
  root
    .find(j.CallExpression, {
      callee: { type: "Identifier", name: "require" },
    })
    .forEach((path) => {
      const args = path.node.arguments;
      if (args.length === 0) return;
      const firstArg = args[0];
      if (firstArg.type !== "StringLiteral" && firstArg.type !== "Literal") return;
      const value = (firstArg as { value: unknown }).value;
      if (typeof value !== "string") return;
      const rewritten = rewriteSpecifier(value);
      if (rewritten !== null && rewritten !== value) {
        (firstArg as { value: string }).value = rewritten;
        changed = true;
      }
    });

  // Return null (unchanged) or rewritten source
  return changed ? root.toSource({ quote: "double" }) : null;
};

export default transform;

// Export mapping for tests and dry-run verification
export { MAPPING, rewriteSpecifier };
