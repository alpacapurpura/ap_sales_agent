/**
 * ARCH TEST: Component files must be PascalCase.
 *
 * Rule: every .tsx file under any components/ directory or components/shared/ must have
 * a PascalCase basename (e.g. MyWidget.tsx, not my-widget.tsx).
 *
 * Ratchet pattern: KNOWN_KEBAB_COMPONENTS is frozen at 2026-04-15 violations.
 * This set MUST only shrink — never add new entries.
 * To fix: git mv old.tsx New.tsx, update all imports, run tsc --noEmit.
 */
import * as path from "path";

import { describe, it, expect } from "vitest";

import {
  FEATURES_DIR,
  SHARED_COMPONENTS_DIR,
  walkFiles,
  relPath,
  isPascalCase,
  isTestFile,
} from "./helpers";

// ── Ratchet allowlist ─────────────────────────────────────────────────────────
// All 187 kebab-case components fixed on 2026-04-15 (PascalCase renames).
// PERMANENT: puck.config.tsx — the ".config" suffix is part of Puck editor's
// semantic contract. Imports reference "./puck.config" by name. Do not rename.
const KNOWN_KEBAB_COMPONENTS = new Set([
  "features/offer-studio/components/landing/utils/puck.config.tsx",
]);

// ─────────────────────────────────────────────────────────────────────────────

const COMPONENTS_SEGMENT = `${path.sep}components${path.sep}`;

describe("Architecture: Component naming", () => {
  it("every .tsx file under components/ must be PascalCase", () => {
    const featureFiles = walkFiles(FEATURES_DIR)
      .filter((f) => f.includes(COMPONENTS_SEGMENT) && f.endsWith(".tsx"))
      .filter((f) => !isTestFile(f));

    const sharedFiles = walkFiles(SHARED_COMPONENTS_DIR)
      .filter((f) => f.endsWith(".tsx"))
      .filter((f) => !isTestFile(f));

    const violations: string[] = [];

    for (const file of [...featureFiles, ...sharedFiles]) {
      const basename = path.basename(file, ".tsx");
      if (!isPascalCase(basename)) {
        violations.push(relPath(file));
      }
    }

    const newViolations = violations.filter((v) => !KNOWN_KEBAB_COMPONENTS.has(v));
    const alreadyFixed = [...KNOWN_KEBAB_COMPONENTS].filter((v) => !violations.includes(v));

    if (alreadyFixed.length > 0) {
      console.info(
        `[arch] Allowlist can shrink: ${alreadyFixed.length} entries already fixed:\n  ${alreadyFixed.join("\n  ")}`,
      );
    }

    expect(
      newViolations,
      `NEW component naming violations (rename to PascalCase and update imports):\n${newViolations.join("\n")}`,
    ).toEqual([]);
  });
});
