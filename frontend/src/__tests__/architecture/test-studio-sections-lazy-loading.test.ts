/**
 * ARCH TEST: brand/offer-studio section pages must be lazy-loaded via next/dynamic.
 *
 * Reglas enforced (para cada studio en STUDIOS):
 *
 *   1. `features/{studio}/pages/section-slugs.ts` existe y exporta
 *      `is{Studio}StudioSection` + `{STUDIO}_STUDIO_SECTION_SLUGS`.
 *
 *   2. `features/{studio}/pages/SectionDispatcher.tsx` existe con
 *      directiva `"use client"` y usa `dynamic(() => import(...))` —
 *      al menos una instancia por archivo.
 *
 *   3. `features/{studio}/pages/sections/` existe y contiene archivos
 *      `*-page.tsx` con **named exports** (no `export default`), por la
 *      política `test-no-default-exports`.
 *
 *   4. Los `sections/*-page.tsx` NO se importan entre sí (isolation per
 *      chunk) — cada uno debe ser un entry independiente para que
 *      Turbopack/webpack code-splitée correctamente.
 *
 *   5. Los Server Components de App Router que sirven el catch-all
 *      (`brand-studio/[section]/page.tsx`,
 *      `offer-studio/offer/[id]/editor/[section]/page.tsx`) importan
 *      **solo** de `section-slugs.ts` y `SectionDispatcher.tsx` del
 *      feature — nunca schemas, ni componentes client, ni el barrel
 *      del studio.
 *
 *   6. NO deben existir `section-page-map.ts` ni `section-pages.tsx`
 *      en ninguno de los features (bloqueo contra resurrección del
 *      patrón monolítico anterior).
 *
 * Contexto: el patrón monolítico causaba OOM loop en `visionarias_client_dev`
 * al compilar el catch-all — ver `docs/mejoras-proceso/plan-refactor-studio-sections-lazy-loading.md`.
 */
import * as path from "path";

import { describe, it, expect } from "vitest";

import { SRC_DIR, walkFiles, readFile } from "./helpers";

interface StudioConfig {
  name: string;
  featureDir: string;
  serverRoute: string;
}

const STUDIOS: readonly StudioConfig[] = [
  {
    name: "brand",
    featureDir: path.join(SRC_DIR, "features", "brand-studio", "pages"),
    serverRoute: path.join(
      SRC_DIR,
      "app",
      "(main)",
      "[tenantId]",
      "(dashboard)",
      "brand-studio",
      "[section]",
      "page.tsx",
    ),
  },
  {
    name: "offer",
    featureDir: path.join(SRC_DIR, "features", "offer-studio", "pages"),
    serverRoute: path.join(
      SRC_DIR,
      "app",
      "(main)",
      "[tenantId]",
      "(dashboard)",
      "offer-studio",
      "offer",
      "[id]",
      "editor",
      "[section]",
      "page.tsx",
    ),
  },
];

const DYNAMIC_IMPORT_RE = /\bdynamic\s*\(\s*\(\s*\)\s*=>\s*import\s*\(/;
const USE_CLIENT_RE = /^\s*["']use client["']\s*;?/m;
const DEFAULT_EXPORT_RE = /^export\s+default\b/m;

describe("Architecture: studio sections lazy-loading", () => {
  for (const studio of STUDIOS) {
    describe(`${studio.name}-studio`, () => {
      it("pages/section-slugs.ts exists with isSection + SLUGS exports", () => {
        const slugsFile = path.join(studio.featureDir, "section-slugs.ts");
        const content = readFile(slugsFile);
        expect(content, `missing ${slugsFile}`).not.toBe("");
        expect(content).not.toMatch(USE_CLIENT_RE);
        expect(content).toMatch(/export\s+function\s+is\w+StudioSection\b/);
        expect(content).toMatch(/export\s+const\s+\w+_STUDIO_SECTION_SLUGS\b/);
      });

      it("pages/SectionDispatcher.tsx exists with 'use client' + dynamic imports", () => {
        const file = path.join(studio.featureDir, "SectionDispatcher.tsx");
        const content = readFile(file);
        expect(content, `missing ${file}`).not.toBe("");
        expect(content).toMatch(USE_CLIENT_RE);
        expect(content).toMatch(DYNAMIC_IMPORT_RE);
      });

      it("pages/sections/*-page.tsx files use named exports (no default)", () => {
        const sectionsDir = path.join(studio.featureDir, "sections");
        const files = walkFiles(sectionsDir).filter((f) => f.endsWith("-page.tsx"));
        expect(files.length, `sections/ must contain per-section files`).toBeGreaterThan(0);

        for (const file of files) {
          const content = readFile(file);
          expect(
            content,
            `${path.basename(file)} must NOT use 'export default' (policy: test-no-default-exports)`,
          ).not.toMatch(DEFAULT_EXPORT_RE);
        }
      });

      it("pages/sections/*-page.tsx do not import each other (chunk isolation)", () => {
        const sectionsDir = path.join(studio.featureDir, "sections");
        const files = walkFiles(sectionsDir).filter((f) => f.endsWith("-page.tsx"));

        for (const file of files) {
          const content = readFile(file);
          // Un import a otra página del mismo sections/ viola isolation.
          const crossImport = /from\s+["'](?:\.\/)?[a-z0-9-]+-page["']/i;
          expect(
            content,
            `${path.basename(file)} imports another section page — breaks chunk isolation`,
          ).not.toMatch(crossImport);
        }
      });

      it("Server route imports only section-slugs + SectionDispatcher from feature", () => {
        const content = readFile(studio.serverRoute);
        expect(content, `missing Server Component ${studio.serverRoute}`).not.toBe("");

        // Server Components NO pueden tener "use client".
        expect(content).not.toMatch(USE_CLIENT_RE);

        // Imports permitidos del feature: section-slugs + SectionDispatcher.
        const featureImports =
          content.match(/from\s+["']@\/features\/\w+-studio\/[^"']+["']/g) ?? [];
        for (const imp of featureImports) {
          const ok =
            imp.includes("/pages/section-slugs") || imp.includes("/pages/SectionDispatcher");
          expect(
            ok,
            `Server route imports ${imp} — solo section-slugs + SectionDispatcher permitido`,
          ).toBe(true);
        }
      });

      it("section-page-map.ts and section-pages.tsx must NOT exist (resurrection guard)", () => {
        const forbidden = [
          path.join(studio.featureDir, "section-page-map.ts"),
          path.join(studio.featureDir, "section-pages.tsx"),
        ];
        for (const f of forbidden) {
          expect(readFile(f), `${f} resurrecta del patrón monolítico pre-refactor`).toBe("");
        }
      });
    });
  }
});
