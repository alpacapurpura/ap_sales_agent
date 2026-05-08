/**
 * ARCH TEST: no hardcoded channel slug ARRAY exported from growth-studio source.
 *
 * Los slugs canónicos de canales en forma de array exportado viven ÚNICAMENTE
 * en los archivos SSoT:
 *   - features/growth-studio/lib/registries/channel-registry.ts  (runtime SSoT)
 *   - features/growth-studio/pages/channel-slugs.ts               (server-safe thin)
 *
 * Este test detecta patrones de array literal que definen la lista completa
 * de canales fuera del SSoT. Previene regresiones donde un dev agrega una
 * constante como:
 *
 *   export const MY_CHANNELS = ["meta-ads", "yt-organic", "email-nurture", ...]
 *
 * en cualquier archivo fuera de los SSoT allowlist.
 *
 * NO bloquea:
 *   - Uso de slugs individuales por canal (ej. MetaAdsDashboard.tsx usa "meta-ads")
 *   - Record/object keys con slugs individuales (ChannelDetailSidebar usa
 *     {"ig-organic": [...], "meta-ads": [...]} — son entradas independientes)
 *   - Imports del registry ("consume, no duplica")
 *
 * La regla protege la adición FUTURA de arrays que dupliquen el registro.
 * Los archivos existentes que usan slugs individualmente (por canal) están OK.
 *
 * Scan: `frontend/src/features/growth-studio/**\/*.{ts,tsx}`
 * Excluye: test files (__tests__, .test.ts, .spec.ts, __mocks__)
 */

import * as fs from "fs";
import * as path from "path";

import { describe, it, expect } from "vitest";

import { SRC_DIR, walkFiles, isTestFile } from "./helpers";

// ─── Canonical channel slugs ───────────────────────────────────────────────

/** Los 5 slugs canónicos de canales (confirmados por grep arquitecto 2026-05-07). */
const CANONICAL_CHANNEL_SLUGS = [
  "meta-ads",
  "yt-organic",
  "email-nurture",
  "ig-organic",
  "website-total",
] as const;

// ─── Allowlist (SSoT files where slug array definitions are permitted) ────

const GROWTH_STUDIO_FEATURE = path.join(SRC_DIR, "features", "growth-studio");

const ALLOWED_FILES: ReadonlySet<string> = new Set([
  path.join(GROWTH_STUDIO_FEATURE, "lib", "registries", "channel-registry.ts"),
  path.join(GROWTH_STUDIO_FEATURE, "pages", "channel-slugs.ts"),
]);

// ─── Scan scope ──────────────────────────────────────────────────────────────

const GROWTH_STUDIO_DIR = GROWTH_STUDIO_FEATURE;

// ─── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Detect if file content contains an array literal definition with 3+
 * canonical channel slugs inside a single array bracket group.
 *
 * This specifically targets array definitions like:
 *   const CHANNELS = ["meta-ads", "yt-organic", "email-nurture", ...]
 *
 * And does NOT flag:
 *   - Individual string usages (MetaAdsDashboard uses only "meta-ads")
 *   - Object property keys spread across multiple object entries
 *     (ChannelDetailSidebar has {"ig-organic": [...], "meta-ads": [...]}
 *     — each key is in its own array, not a combined array of all slugs)
 *   - Record<ChannelSlug, ...> type annotations (TypeScript types, not values)
 */
function hasHardcodedChannelArray(content: string): { detected: boolean; matchCount: number } {
  // Remove comments to avoid false positives
  const noComments = content.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*/g, "");

  // Find all array literal blocks (content between [ and ])
  // Use a non-greedy match to avoid crossing multiple arrays
  // eslint-disable-next-line no-useless-escape -- regex char class needs escaped brackets
  const arrayPattern = /\[([^\[\]]*)\]/g;
  let match;
  let maxSlugsInArray = 0;

  while ((match = arrayPattern.exec(noComments)) !== null) {
    const [, arrayContent] = match;
    const slugCount = CANONICAL_CHANNEL_SLUGS.filter((slug) => {
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

describe("Architecture: no hardcoded channel slug list outside SSoT", () => {
  it("no growth-studio source file (outside SSoT allowlist) contains a hardcoded array of 3+ channel slugs", () => {
    const violations: string[] = [];

    const files = walkFiles(GROWTH_STUDIO_DIR).filter(
      (f) => (f.endsWith(".ts") || f.endsWith(".tsx")) && !isTestFile(f),
    );

    for (const file of files) {
      if (ALLOWED_FILES.has(file)) continue;

      const content = fs.readFileSync(file, "utf-8");
      const { detected, matchCount } = hasHardcodedChannelArray(content);

      if (detected) {
        violations.push(
          `${path.relative(SRC_DIR, file)} — array literal con ${matchCount}/${CANONICAL_CHANNEL_SLUGS.length} slugs de canal`,
        );
      }
    }

    expect(
      violations,
      [
        "Los siguientes archivos definen arrays hardcodeados de slugs de canal.",
        "Si necesitas iterar sobre canales, importar CHANNEL_REGISTRY de lib/registries/channel-registry.ts.",
        "Allowlist solo permite: channel-registry.ts + pages/channel-slugs.ts (server-safe thin).",
        "",
        "Nota: Usar UN slug individual por archivo (ej. MetaAdsDashboard.tsx con 'meta-ads') está OK.",
        "Lo que se bloquea es definir un array con 3+ slugs del conjunto canónico fuera del SSoT.",
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
