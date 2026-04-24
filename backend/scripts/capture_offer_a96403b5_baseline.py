"""Capture golden baseline snapshot of reference offer a96403b5.

Regenerates ``backend/tests/modules/offer/fixtures/offer_a96403b5_baseline.json``
with three payloads:

1. ``offer_db_state``: full ``Offer.model_dump(mode="json", exclude_none=True)``
   of the real offer (loaded via ``OfferRepository.get_by_id``).
2. ``rendered_identity_prompt``: string output of
   ``TenantKnowledgeBuilder.build_identity``.
3. ``landing_config``: dry-run ``LandingPageConfig.model_dump(mode="json")``
   computed via the same resolver that ``landing_service.generate_landing_for_offer``
   uses, **without** persisting to ``landing_pages``.

Run NATIVE WSL (not Docker):

    docker exec -w /app visionarias_brain_dev python scripts/capture_offer_a96403b5_baseline.py

The script runs inside the brain container because only that network can
reach ``visionarias_postgres``. Pass ``--output /tmp/<file>`` and ``docker cp``
out when the fixtures directory is owned by the host user (default behaviour).

Requires the dev stack up (``docker compose up -d``) and the offer row
present. When the offer is absent the script exits 1 — do not stub the
fixture manually, regenerate from a real snapshot.

Safe to re-run. Output file is committed and acts as the golden baseline for
``tests/modules/offer/test_offer_a96403b5_baseline.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from uuid import UUID

from sqlalchemy import text as sa_text

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.core.database import SessionLocal
from src.modules.landing.application.landing_content_builders import _resolve_content
from src.modules.landing.application.landing_service import LandingService
from src.modules.landing.domain.content import LandingPageConfig
from src.modules.offer.infrastructure.repositories.offer_repository import OfferRepository
from src.modules.sales_agent.application.services.knowledge_builder import TenantKnowledgeBuilder
from src.shared.infrastructure import model_registry  # noqa: F401 — registers all SQLA models

TENANT_ID = UUID("1fd1562b-2101-410a-870c-dc2f7e27b355")
OFFER_ID = UUID("a96403b5-c1db-4b31-97aa-cb18d08ad9f9")
FIXTURE_PATH = BACKEND_ROOT / "tests" / "modules" / "offer" / "fixtures" / "offer_a96403b5_baseline.json"

# Keys excluded from the offer dump because they are wall-clock timestamps
# that mutate on every autosave / lifecycle change. The fixture would flake
# without this guard. Add new ephemeral keys here (never to _resolve_content).
EPHEMERAL_OFFER_KEYS = {"archived_at", "deleted_at"}


def _landing_config_dry_run(db, tenant_id: UUID, offer_id: UUID) -> dict:
    row = (
        db.execute(
            sa_text(
                "SELECT name, headline_promise, primary_outcome, marketing_pain_points,"
                " preset_id,"
                " before_state, after_state, why_now, measurable_outcomes,"
                " objections, marketing_desires, cultural_trust_barriers,"
                " emotional_triggers, status_drivers, regret_scenarios,"
                " refund_process_description, urgency_drivers, scarcity_reason_honest,"
                " bonus_if_act_now, final_push_copy,"
                " guarantee_terms, guarantee_type, support_duration_days,"
                " deliverables, pricing"
                " FROM products WHERE id = :oid AND tenant_id = :tid",
            ),
            {"oid": str(offer_id), "tid": str(tenant_id)},
        )
        .mappings()
        .first()
    )
    if not row:
        msg = f"Offer {offer_id} not found in local DB."
        raise SystemExit(msg)

    public_name: str = row["name"] or "Mi oferta"
    preset_id = row["preset_id"]
    slug = f"{public_name.lower().replace(' ', '-')}-{str(offer_id)[:8]}"

    landing_archetype = LandingService._select_landing_archetype_from_preset(preset_id)
    actual_archetype, content = _resolve_content(landing_archetype, row)

    config = LandingPageConfig(
        archetype=actual_archetype,
        slug=slug,
        content=content,
        seo_title=public_name,
        seo_description=row.get("headline_promise") or public_name,
    )
    return config.model_dump(mode="json")


def _dump_offer_state(db) -> dict:
    repo = OfferRepository(db)
    offer = repo.get_by_id(OFFER_ID, TENANT_ID)
    if offer is None:
        msg = f"Offer {OFFER_ID} not found for tenant {TENANT_ID}."
        raise SystemExit(msg)

    payload = offer.model_dump(mode="json", exclude_none=True)
    for key in EPHEMERAL_OFFER_KEYS:
        payload.pop(key, None)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=FIXTURE_PATH,
        help="Destination JSON path. Use /tmp/... when running inside Docker.",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        offer_state = _dump_offer_state(db)
        identity_prompt = TenantKnowledgeBuilder(db).build_identity(TENANT_ID)
        landing_config = _landing_config_dry_run(db, TENANT_ID, OFFER_ID)
    finally:
        db.close()

    payload = {
        "_meta": {
            "tenant_id": str(TENANT_ID),
            "offer_id": str(OFFER_ID),
            "captured_by": "backend/scripts/capture_offer_a96403b5_baseline.py",
            "excludes": sorted(EPHEMERAL_OFFER_KEYS),
        },
        "offer_db_state": offer_state,
        "rendered_identity_prompt": identity_prompt,
        "landing_config": landing_config,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Baseline written: {args.output}")


if __name__ == "__main__":
    main()
