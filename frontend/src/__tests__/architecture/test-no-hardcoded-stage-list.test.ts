/**
 * ARCH TEST: no hardcoded stage slug ARRAY exported from growth-studio source.
 *
 * Los slugs canónicos de etapas en forma de array exportado viven ÚNICAMENTE
 * en los archivos SSoT:
 *   - features/growth-studio/lib/registries/stage-registry.ts  (runtime SSoT)
 *   - features/growth-studio/pages/stage-slugs.ts              (server-safe thin)
 *
 * Este test detecta patrones de array literal que definen la lista completa
 * de etapas fuera del SSoT. Previene regresiones donde un dev agrega una
 * constante como:
 *
 *   export const MY_STAGES = ["atraccion-captura", "nutricion-oportunidad", ...]
 *
 * en cualquier archivo fuera de los SSoT allowlist.
 *
 * NO bloquea:
 *   - Uso de slugs individuales (ej. "atraccion-captura" en el dispatcher
 *     como key de Record<GrowthStudioStageSlug, ...>)
 *   - Mapping objects con slugs como keys (not array literals)
 *   - Imports del registry ("consume, no duplica")
 *
 * Scan: `frontend/src/features/growth-studio/**\/*.{ts,tsx}`
 * Excluye: test files (__tests__, .test.ts, .spec.ts, __mocks__)
 */

import * as fs from "fs";
import * as path from "path";

import { describe, it, expect } from "vitest";

import { SRC_DIR, walkFiles, isTestFile } from "./helpers";

// ─── Canonical stage slugs ─────────────────────────────────────────────────

/** Los 5 slugs canónicos de etapas (confirmados por grep arquitecto 2026-05-07). */
const CANONICAL_STAGE_SLUGS = [
  "atraccion-captura",
  "nutricion-oportunidad",
  "ventas",
  "adopcion",
  "expansion-evangelizacion",
] as const;

// ─── Allowlist (SSoT files where slug array definitions are permitted) ────

const GROWTH_STUDIO_FEATURE = path.join(SRC_DIR, "features", "growth-studio");

const ALLOWED_FILES: ReadonlySet<string> = new Set([
  path.join(GROWTH_STUDIO_FEATURE, "lib", "registries", "stage-registry.ts"),
  path.join(GROWTH_STUDIO_FEATURE, "pages", "stage-slugs.ts"),
]);

// ─── Scan scope ──────────────────────────────────────────────────────────────

const GROWTH_STUDIO_DIR = GROWTH_STUDIO_FEATURE;

// ─── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Detect if file content contains an array literal definition with 3+
 * canonical stage slugs on consecutive lines (indicating a hardcoded list,
 * not individual slug usage).
 *
 * Pattern: looks for [ ... "slug1" ... "slug2" ... "slug3" ... ] where
 * 3+ slugs from the canonical set appear inside an array bracket group.
 *
 * This specifically targets array definitions like:
 *   const STAGES = ["atraccion-captura", "nutricion-oportunidad", ...]
 *   const x = ["atraccion-captura", ..., "expansion-evangelizacion"]
 *
 * And does NOT flag individual string usages or Record<StageSlug, ...> keys.
 */
function hasHardcodedStageArray(content: string): { detected: boolean; matchCount: number } {
  // Remove comments to avoid false positives
  const noComments = content.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*/g, "");

  // Find all array literal blocks (content between [ and ])
  // eslint-disable-next-line no-useless-escape -- regex char class needs escaped brackets
  const arrayPattern = /\[([^\[\]]*)\]/g;
  let match;
  let maxSlugsInArray = 0;

  while ((match = arrayPattern.exec(noComments)) !== null) {
    const [, arrayContent] = match;
    const slugCount = CANONICAL_STAGE_SLUGS.filter((slug) => {
      const pattern = new RegExp(`["']${slug}["']`);
      return pattern.test(arrayContent);
    }).length;
    if (slugCount > maxSlugsInArray) {
      maxSlugsInArray = slugCount;
    }
  }

  return {
    detected: maxSlugsInArray >= 3,
    matchCount: maxSlugsInArray,
  };
}

// ─── Tests ───────────────────────────────────────────────────────────────────

describe("Architecture: no hardcoded stage slug list outside SSoT", () => {
  it("no growth-studio source file (outside SSoT allowlist) contains a hardcoded array of 3+ stage slugs", () => {
    const violations: string[] = [];

    const files = walkFiles(GROWTH_STUDIO_DIR).filter(
      (f) => (f.endsWith(".ts") || f.endsWith(".tsx")) && !isTestFile(f),
    );

    for (const file of files) {
      if (ALLOWED_FILES.has(file)) continue;

      const content = fs.readFileSync(file, "utf-8");
      const { detected, matchCount } = hasHardcodedStageArray(content);

      if (detected) {
        violations.push(
          `${path.relative(SRC_DIR, file)} — array literal con ${matchCount}/${CANONICAL_STAGE_SLUGS.length} slugs de etapa`,
        );
      }
    }

    expect(
      violations,
      [
        "Los siguientes archivos definen arrays hardcodeados de slugs de etapa.",
        "Mover la definición a lib/registries/stage-registry.ts (SSoT) y consumir el registro.",
        "Allowlist solo permite: stage-registry.ts + pages/stage-slugs.ts (server-safe thin).",
        "",
        "Si el uso es legítimo (ej. Record keys vía TypeScript union), usar la union type",
        "GrowthStudioStageSlug importada del registry en lugar de un array literal.",
      ].join("\n"),
    ).toEqual([]);
  });

  it("SSoT allowlist files actually exist (guard against allowlist drift)", () => {
    for (const allowedFile of ALLOWED_FILES) {
      expect(
        fs.existsSync(allowedFile),
        `Allowlist file no encontrado: ${path.relative(SRC_DIR, allowedFile)}. ` +
          "Actualizar ALLOWED_FILES si el archivo fue movido o renombrado.",
      ).toBe(true);
    }
  });
});
