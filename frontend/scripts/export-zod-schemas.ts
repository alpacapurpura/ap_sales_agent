/**
 * Export growth-studio zod schemas as JSON Schema format.
 *
 * Used by backend/tests/architecture/test_be_fe_schema_alignment_growth_studio.py
 * to verify BE Pydantic ↔ FE zod schema alignment (T-5 Story 2B).
 *
 * Imports schema files directly (not via barrel index) to avoid
 * loading React components or @/ path aliases — this script runs
 * in Node.js via tsx, not in a browser.
 *
 * Output: frontend/dist/growth-studio-zod-schemas.json
 *
 * Usage:
 *   npm run schema:export
 *   # or:
 *   npx tsx scripts/export-zod-schemas.ts
 */

import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { z } from "zod";

// ─── Import schemas directly (bypass barrel index to avoid React imports) ────

// Registry-derived slugs must be inlined here since we can't import from
// src/ paths that transitively pull in React components.
// These values MUST stay in sync with the SSoT registries in:
//   src/features/growth-studio/lib/registries/stage-registry.ts
//   src/features/growth-studio/lib/registries/channel-registry.ts
const STAGE_SLUGS = [
  "atraccion-captura",
  "nutricion-oportunidad",
  "ventas",
  "adopcion",
  "expansion-evangelizacion",
] as const;

const CHANNEL_SLUGS = [
  "meta-ads",
  "yt-organic",
  "email-nurture",
  "ig-organic",
  "website-total",
] as const;

// ─── Re-declare schemas inline (mirrors src/features/growth-studio/schemas/*.ts)
// Inlined because tsx cannot resolve transitive @/ or React imports.
// If a schema changes, this file MUST be updated in lock-step — the
// backend arch test will catch any drift immediately.

const stageFilterParamsSchema = z
  .object({
    stage: z.enum(STAGE_SLUGS),
    channel: z.enum(CHANNEL_SLUGS).optional(),
    period: z.enum(["7d", "30d", "90d"]).default("30d"),
  })
  .strict();

const channelOverviewParamsSchema = z
  .object({
    channel: z.enum(CHANNEL_SLUGS),
  })
  .strict();

const triggerEtlRefreshParamsSchema = z
  .object({
    channel: z.enum(CHANNEL_SLUGS),
    confirmed: z.boolean().default(false),
  })
  .strict();

// ─── Export ───────────────────────────────────────────────────────────────────

const schemas = {
  StageFilterParams: z.toJSONSchema(stageFilterParamsSchema),
  ChannelOverviewParams: z.toJSONSchema(channelOverviewParamsSchema),
  TriggerEtlRefreshParams: z.toJSONSchema(triggerEtlRefreshParamsSchema),
};

// Write to frontend/dist/ (gitignored; regenerated on demand)
// Use __dirname-relative path: scripts/ is one level below frontend/
const OUTPUT_DIR = join(__dirname, "..", "dist");
const OUTPUT_FILE = join(OUTPUT_DIR, "growth-studio-zod-schemas.json");

async function main(): Promise<void> {
  await mkdir(OUTPUT_DIR, { recursive: true });
  await writeFile(OUTPUT_FILE, JSON.stringify(schemas, null, 2), "utf-8");
  console.log(`Exported growth-studio zod schemas → ${OUTPUT_FILE}`);
}

main().catch((err: unknown) => {
  console.error("export-zod-schemas failed:", err);
  process.exit(1);
});
