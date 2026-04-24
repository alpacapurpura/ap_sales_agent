"""Generate the canonical list of ``Offer`` field paths.

Produces **two** artefacts:

1. ``backend/tests/architecture/fixtures/offer_field_paths.json`` — sorted
   JSON array consumed by the backend arch tests and by
   ``frontend/src/__tests__/architecture/test-fe-schema-paths-resolve.test.ts``.
2. ``frontend/src/features/offer-studio/api/__generated__/offer-field-paths.ts``
   — codegen TS module exporting the same list plus a ``OfferFieldPath``
   string literal union. FE schemas import the union to typecheck their
   ``path`` literals (Fase 01 pilot). TSC fails if a schema invents a
   path that is not declared on the BE domain.

The list is the union of:

- Every top-level ``Offer.model_fields`` key (flat, e.g. ``headline_promise``).
- Every field of every polymorphic ``*Details`` model, prefixed with
  ``specific_details.`` (e.g. ``specific_details.duration_weeks``). The union
  is computed across all archetypes deliberately — the frontend schema does
  not know which archetype is loaded at arch-test time.

Run native (no DB required — pure Pydantic introspection):

    cd backend && .venv/bin/python scripts/generate_offer_field_paths.py

Commit both generated files. Regenerate whenever ``Offer`` or any
``*Details`` model adds/removes/renames a field (Fase 01+).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.modules.offer.domain.details import PlatformDetails
from src.modules.offer.domain.offer import ARCHETYPE_TO_DETAILS_MAPPING, Offer

REPO_ROOT = BACKEND_ROOT.parent

OUTPUT_JSON_PATH = BACKEND_ROOT / "tests" / "architecture" / "fixtures" / "offer_field_paths.json"
OUTPUT_TS_PATH = (
    REPO_ROOT / "frontend" / "src" / "features" / "offer-studio" / "api" / "__generated__" / "offer-field-paths.ts"
)

TS_HEADER = """/**
 * AUTO-GENERATED from Offer Pydantic model. DO NOT EDIT BY HAND.
 *
 * Regenerate via:
 *   cd backend && .venv/bin/python scripts/generate_offer_field_paths.py
 *
 * Source of truth:
 *   backend/src/modules/offer/domain/offer.py
 *   backend/src/modules/offer/domain/details.py
 *
 * Consumed by offer-studio schemas (pricing.schema.ts, etc.) to typecheck
 * field ``path`` literals against the backend domain (Fase 01 pilot —
 * see docs/refactors/field-contract-ssot/).
 */
"""


def _collect_paths() -> list[str]:
    paths: set[str] = set(Offer.model_fields.keys())
    for details_cls in ARCHETYPE_TO_DETAILS_MAPPING.values():
        for field_name in details_cls.model_fields:
            paths.add(f"specific_details.{field_name}")
    # Composable top-level details (ADR-010, Fase 02 · Block G).
    # Orthogonal to archetype — the walker hard-codes the prefix list
    # of composable nested models so FE schemas can opt-in to any offer.
    for field_name in PlatformDetails.model_fields:
        paths.add(f"platform_details.{field_name}")
    return sorted(paths)


def _write_json(paths: list[str]) -> None:
    OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON_PATH.write_text(
        json.dumps(paths, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_ts(paths: list[str]) -> None:
    OUTPUT_TS_PATH.parent.mkdir(parents=True, exist_ok=True)
    literals = "\n".join(f"  | {json.dumps(p)}" for p in paths)
    array_entries = ",\n".join(f"  {json.dumps(p)}" for p in paths)
    body = (
        f"{TS_HEADER}\n"
        "export type OfferFieldPath =\n"
        f"{literals};\n\n"
        "export const OFFER_FIELD_PATHS: readonly OfferFieldPath[] = [\n"
        f"{array_entries},\n"
        "] as const;\n"
    )
    OUTPUT_TS_PATH.write_text(body, encoding="utf-8")


def main() -> None:
    paths = _collect_paths()
    _write_json(paths)
    _write_ts(paths)
    print(f"Wrote {len(paths)} paths to {OUTPUT_JSON_PATH.relative_to(REPO_ROOT)}")
    print(f"Wrote {len(paths)} paths to {OUTPUT_TS_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
