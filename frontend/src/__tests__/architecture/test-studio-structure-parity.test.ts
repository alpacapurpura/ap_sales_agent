/**
 * ARCH TEST: brand + offer-studio mantienen paridad estructural en pages/.
 *
 * La idea: el patrón de lazy-loading homologado vive bajo
 * `features/{studio}/pages/` con la misma forma. Cualquier evolución
 * del patrón debe aplicarse a ambos studios — si alguien agrega un
 * archivo de infraestructura (`create-*`, dispatcher helper, etc.) a
 * uno pero no al otro, este test falla para forzar alineación
 * deliberada.
 *
 * Archivos canónicos (MUST existir en ambos):
 *   - pages/section-slugs.ts
 *   - pages/SectionDispatcher.tsx
 *   - pages/sections/ (directorio con N archivos *-page.tsx)
 *
 * Este test NO enforza que N sea igual (brand=10, offer=21) ni los
 * mismos slugs — eso lo valida `test-section-key-backend-alignment`.
 * Solo valida que la *forma* del módulo sea la misma.
 */
import * as fs from "fs";
import * as path from "path";

import { describe, it, expect } from "vitest";

import { SRC_DIR } from "./helpers";

const CANONICAL_FILES = ["section-slugs.ts", "SectionDispatcher.tsx"] as const;

const STUDIO_PAGE_DIRS: Record<string, string> = {
  brand: path.join(SRC_DIR, "features", "brand-studio", "pages"),
  offer: path.join(SRC_DIR, "features", "offer-studio", "pages"),
};

describe("Architecture: studio structure parity", () => {
  for (const filename of CANONICAL_FILES) {
    it(`both studios define ${filename}`, () => {
      for (const [studio, dir] of Object.entries(STUDIO_PAGE_DIRS)) {
        const full = path.join(dir, filename);
        expect(
          fs.existsSync(full),
          `${studio}-studio falta ${filename} — patrón homologado requiere ambos.`,
        ).toBe(true);
      }
    });
  }

  it("both studios have a sections/ directory with at least one *-page.tsx", () => {
    for (const [studio, dir] of Object.entries(STUDIO_PAGE_DIRS)) {
      const sectionsDir = path.join(dir, "sections");
      expect(fs.existsSync(sectionsDir), `${studio}-studio falta pages/sections/`).toBe(true);

      const files = fs.readdirSync(sectionsDir).filter((f) => f.endsWith("-page.tsx"));
      expect(
        files.length,
        `${studio}-studio/pages/sections/ sin *-page.tsx files`,
      ).toBeGreaterThan(0);
    }
  });
});
