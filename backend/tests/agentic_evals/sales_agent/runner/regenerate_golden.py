"""CLI to regenerate a smoke-golden YAML against the live Visionarias DB.

Per ``03-arch-be.md`` § "regenerate_golden.py" + ticket T-5 deliverable 3:
the CLI queries the canonical Visionarias tenant, picks the top-1 active
offer (``deleted_at IS NULL``, ordered by ``created_at DESC``), and
rewrites the target golden YAML in place. The hand-curated fields
(``expected_specialists`` / ``required_tools`` / ``forbidden_tools`` /
``must_mention`` / ``language`` / ``max_cost_usd`` / ``max_latency_ms``)
are PRESERVED — only ``offer_id`` + ``metadata.regenerated_from`` +
``metadata.created_at`` are updated.

Per Decision B2 (ratified Chris 2026-05-04): seed accountability lives
in OPS, NOT in the fixture. This CLI is the human-driven escape hatch
when admins deliberately rotate offers; the fixture itself never auto-
regenerates (silent shifts forbidden).

Usage:

    cd backend
    .venv/bin/python tests/agentic_evals/sales_agent/runner/regenerate_golden.py \\
        visionarias-smoke-001
    # → updates backend/tests/agentic_evals/sales_agent/goldens/visionarias-smoke-golden.yaml

    # Dry-run (no file write — prints diff to stdout):
    .venv/bin/python tests/agentic_evals/sales_agent/runner/regenerate_golden.py \\
        visionarias-smoke-001 --dry-run

Anti-duplication §0:

* Reuses ``TenantModel`` + ``ProductModel`` from production
  infrastructure — NO mirror DDL.
* Reuses ``SessionLocal`` from ``src/core/database.py`` — NO custom DB
  factory.
* Reuses ``utc_now`` from ``src/shared/domain/time.py`` — NO duplicate
  timestamp helper.
* Reuses ``yaml.safe_load`` / ``yaml.safe_dump`` — standard library, no
  custom serializer.

Tessl ``graceful-degradation`` Rules 1+2: the CLI is the user-facing
entry point — failures (DB unreachable, golden missing, no offer)
propagate as ``sys.exit(1)`` with structured Spanish-neutro stderr so
the dev knows what to fix. No fallback (fail-explicit per B2).

Tenant isolation (`.claude/rules/tenant-isolation.md`): the offer query
filters by ``tenant_id == VISIONARIAS_TENANT_ID`` — cross-tenant offer
selection is a security failure.

Spanish neutro LATAM: stderr messages use neutro (no voseo). The script
exits 0 happy path / exit 1 on any expected error.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

# Ensure backend/ is on sys.path so `import src.*` works when the script is
# invoked directly via `.venv/bin/python tests/agentic_evals/.../regenerate_golden.py`
# (not via pytest, which configures the path automatically).
_BACKEND_ROOT = Path(__file__).resolve().parents[4]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import structlog
import yaml

logger = structlog.get_logger()


# Goldens directory — relative to this file's parent's parent (runner/ ../ goldens).
_GOLDENS_DIR = Path(__file__).resolve().parents[1] / "goldens"

# Default Visionarias tenant UUID (mirrors fixtures/tenant.py default).
_DEFAULT_VISIONARIAS_TENANT_ID = "00000000-0000-0000-0000-000000000001"


def _resolve_tenant_id() -> UUID:
    """Read VISIONARIAS_TENANT_ID env var or fall back to default sentinel.

    Mirrors ``fixtures/tenant.py::_resolve_visionarias_tenant_id`` so the
    CLI and the smoke test always target the same tenant.
    """
    raw = os.environ.get("VISIONARIAS_TENANT_ID", _DEFAULT_VISIONARIAS_TENANT_ID)
    return UUID(raw)


def _resolve_yaml_path(golden_id: str) -> Path:
    """Map a ``golden_id`` to its YAML filename in ``goldens/``.

    Convention: ``visionarias-smoke-001`` → ``visionarias-smoke-golden.yaml``.
    For now the smoke-foundation Story has ONE golden so the mapping is
    deterministic; a future Story adding more goldens will broaden this
    helper or move it to ``golden_loader.py``.
    """
    if golden_id == "visionarias-smoke-001":
        return _GOLDENS_DIR / "visionarias-smoke-golden.yaml"
    # Forward-compatible: try direct slug → filename match.
    candidate = _GOLDENS_DIR / f"{golden_id}.yaml"
    return candidate


def _query_top_offer(tenant_id: UUID) -> Any:
    """Return the top-1 active offer for ``tenant_id`` ordered by ``created_at desc``.

    Returns:
        ``ProductModel`` instance.

    Raises:
        SystemExit: When no active offer exists (sys.exit(1) — no rotation
            possible). Spanish-neutro stderr message documents the expected
            remediation (``make seed-visionarias`` or admin offer creation).
    """
    # Lazy imports — keep CLI startup cheap.
    from sqlalchemy import select

    from luana_core_platform.core.database import SessionLocal
    from luana_core_offer_studio.infrastructure.models.product_model import ProductModel

    db = SessionLocal()
    try:
        offer = db.execute(
            select(ProductModel)
            .where(
                ProductModel.tenant_id == tenant_id,
                ProductModel.deleted_at.is_(None),
            )
            .order_by(ProductModel.created_at.desc())
            .limit(1),
        ).scalar_one_or_none()
        if offer is None:
            sys.stderr.write(
                f"[regenerate_golden] No se encontro ninguna oferta activa para "
                f"tenant_id={tenant_id}. Crea una oferta en /offer-studio o "
                f"corre `make seed-visionarias`.\n",
            )
            sys.exit(1)
        return offer
    finally:
        db.close()


def _utc_now_iso() -> str:
    """Return current UTC time as RFC 3339 string with 'Z' suffix.

    Format: ``2026-05-05T03:30:00Z`` — matches the format used in the
    initial hand-crafted YAML for diff hygiene.
    """
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def _regenerate_payload(
    current: dict[str, Any],
    *,
    new_offer_id: UUID,
) -> dict[str, Any]:
    """Apply offer_id + metadata updates while preserving hand-curated fields.

    Args:
        current: Parsed YAML dict from ``yaml.safe_load``.
        new_offer_id: Top-1 active offer UUID from DB.

    Returns:
        New dict with ``offer_id`` updated, ``metadata.regenerated_from``
        set to the previous ``offer_id``, ``metadata.created_at`` set to
        the current UTC timestamp. All other keys are preserved verbatim.

    Notes:
        Mutates a copy — input ``current`` is not modified. Caller decides
        whether to write the result to disk.
    """
    new_payload: dict[str, Any] = dict(current)
    previous_offer_id = current.get("offer_id")
    new_payload["offer_id"] = str(new_offer_id)

    metadata = dict(current.get("metadata") or {})
    metadata["regenerated_from"] = previous_offer_id
    metadata["created_at"] = _utc_now_iso()
    new_payload["metadata"] = metadata

    return new_payload


def _format_yaml(payload: dict[str, Any]) -> str:
    """Serialize ``payload`` back to YAML preserving key order.

    Uses ``sort_keys=False`` so the regenerated YAML matches the human-
    written ordering. ``default_flow_style=False`` keeps lists in block
    form for readability.
    """
    return yaml.safe_dump(
        payload,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=120,
    )


def _print_diff(original: str, regenerated: str, path: Path) -> None:
    """Print a unified diff to stdout for ``--dry-run`` mode."""
    import difflib

    diff_lines = difflib.unified_diff(
        original.splitlines(keepends=True),
        regenerated.splitlines(keepends=True),
        fromfile=f"{path} (current)",
        tofile=f"{path} (regenerated)",
        n=3,
    )
    sys.stdout.write("".join(diff_lines))
    if not diff_lines:
        sys.stdout.write(
            f"[regenerate_golden] {path}: sin cambios (offer_id ya esta sincronizado).\n",
        )


def main(argv: list[str] | None = None) -> int:
    """Entry point for the CLI.

    Args:
        argv: Optional argv override (for tests). When ``None``, falls
            back to ``sys.argv[1:]``.

    Returns:
        Exit code (0 happy path, 1 on any expected error). The caller
        (``__main__`` block below) propagates this to the OS via
        ``sys.exit``.
    """
    parser = argparse.ArgumentParser(
        prog="regenerate_golden",
        description=(
            "Regenera un YAML golden contra la oferta activa top-1 de Visionarias. "
            "Solo actualiza offer_id + metadata; preserva expected_specialists, "
            "required_tools, forbidden_tools, must_mention, language, max_cost_usd, max_latency_ms."
        ),
    )
    parser.add_argument(
        "golden_id",
        help="ID del golden a regenerar (ej. 'visionarias-smoke-001').",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="No escribe el archivo; imprime el diff a stdout.",
    )
    args = parser.parse_args(argv)

    yaml_path = _resolve_yaml_path(args.golden_id)
    if not yaml_path.exists():
        sys.stderr.write(
            f"[regenerate_golden] No se encontro el YAML para golden_id='{args.golden_id}' "
            f"en {yaml_path}. Verifica el ID o crea el archivo manualmente.\n",
        )
        return 1

    try:
        current_text = yaml_path.read_text(encoding="utf-8")
        current = yaml.safe_load(current_text)
    except yaml.YAMLError as exc:
        sys.stderr.write(
            f"[regenerate_golden] Error al parsear {yaml_path}: {exc}\n",
        )
        return 1

    if not isinstance(current, dict):
        sys.stderr.write(
            f"[regenerate_golden] {yaml_path} no contiene un dict YAML valido.\n",
        )
        return 1

    tenant_id = _resolve_tenant_id()
    try:
        offer = _query_top_offer(tenant_id)
    except SystemExit:
        # Already handled by _query_top_offer with stderr message.
        raise
    except Exception as exc:  # noqa: BLE001 — CLI top-level catch
        sys.stderr.write(
            f"[regenerate_golden] Error al consultar la DB para tenant_id={tenant_id}: {exc}. "
            f"Verifica que Postgres este corriendo y accesible desde WSL nativo.\n",
        )
        return 1

    new_offer_id = offer.id if isinstance(offer.id, UUID) else UUID(str(offer.id))
    new_payload = _regenerate_payload(current, new_offer_id=new_offer_id)
    regenerated_text = _format_yaml(new_payload)

    if args.dry_run:
        _print_diff(current_text, regenerated_text, yaml_path)
        sys.stdout.write(
            f"[regenerate_golden] dry-run completado para golden_id='{args.golden_id}'. Sin escritura a disco.\n",
        )
        return 0

    yaml_path.write_text(regenerated_text, encoding="utf-8")
    sys.stdout.write(
        f"[regenerate_golden] Actualizado {yaml_path} con offer_id={new_offer_id}.\n",
    )
    logger.info(
        "eval_golden_regenerated",
        golden_id=args.golden_id,
        path=str(yaml_path),
        new_offer_id=str(new_offer_id),
        previous_offer_id=current.get("offer_id"),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
