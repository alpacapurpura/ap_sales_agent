"""Generate the canonical list of ``Offer`` field paths.

Produces ``backend/tests/architecture/fixtures/offer_field_paths.json``, a
sorted JSON array of every ``path`` string a frontend offer-studio schema is
allowed to target.

The list is the union of:

- Every top-level ``Offer.model_fields`` key (flat, e.g. ``headline_promise``).
- Every field of every polymorphic ``*Details`` model, prefixed with
  ``specific_details.`` (e.g. ``specific_details.duration_weeks``). The union
  is computed across all archetypes deliberately — the frontend schema does
  not know which archetype is loaded at arch-test time.

The arch test at
``frontend/src/__tests__/architecture/test-fe-schema-paths-resolve.test.ts``
consumes this JSON (plus a shrinking allowlist) so a schema introducing a
path that is not declared on the Pydantic domain fails CI.

Run native (no DB required — pure Pydantic introspection):

    cd backend && .venv/bin/python scripts/generate_offer_field_paths.py

Commit the generated JSON. Regenerate whenever ``Offer`` or any
``*Details`` model adds/removes/renames a field (Fase 01+).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.modules.offer.domain.offer import ARCHETYPE_TO_DETAILS_MAPPING, Offer

OUTPUT_PATH = BACKEND_ROOT / "tests" / "architecture" / "fixtures" / "offer_field_paths.json"


def _collect_paths() -> list[str]:
    paths: set[str] = set(Offer.model_fields.keys())
    for details_cls in ARCHETYPE_TO_DETAILS_MAPPING.values():
        for field_name in details_cls.model_fields:
            paths.add(f"specific_details.{field_name}")
    return sorted(paths)


def main() -> None:
    paths = _collect_paths()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(paths, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(paths)} paths to {OUTPUT_PATH.relative_to(BACKEND_ROOT.parent)}")


if __name__ == "__main__":
    main()
