"""Architectural fitness: coding convention enforcement.

Validates project-wide conventions that Ruff cannot catch:
- No hard deletes (session.delete)
- SA 2.0 syntax only (no session.query)
"""
import re
from pathlib import Path

from tests.architecture.conftest import MODULES_DIR

# ──────────────────────────────────────────────────────────────
# KNOWN VIOLATIONS — ratchet: only remove lines, never add.
# ──────────────────────────────────────────────────────────────
KNOWN_HARD_DELETE_FILES: set[str] = {
    "assets/infrastructure/repositories/asset_repository.py",
    "assets/infrastructure/repositories/gallery_repository.py",
    "brand/infrastructure/repositories/avatar_repository.py",
    "connections/infrastructure/repositories/channel_connection_repository.py",
}

KNOWN_SA1X_VIOLATIONS: set[str] = {
    "assets/application/assets_service.py",
    "assets/infrastructure/repositories/asset_repository.py",
    "assets/infrastructure/repositories/gallery_repository.py",
    "brand/api/style.py",
    "connections/api/calendar.py",
    "connections/api/webhook.py",
    "crm/api/pipeline.py",
    "crm/api/sales.py",
    "crm/application/services/ig_profile_enricher.py",
    "crm/infrastructure/repositories/lead_metrics_repository.py",
    "crm/infrastructure/repositories/lead_repository.py",
    "crm/infrastructure/repositories/sale_repository.py",
    "iam/api/dependencies.py",
    "iam/api/settings.py",
    "iam/infrastructure/repositories/tenant_repository.py",
    "iam/infrastructure/repositories/user_repository.py",
    "iam/infrastructure/repositories/user_tenant_repository.py",
    "iam/infrastructure/user.py",
    "sales_agent/api/audit.py",
    "sales_agent/api/closer_studio.py",
    "sales_agent/application/orchestrator/chat.py",
    "sales_agent/application/services/channel_resolver.py",
    "sales_agent/infrastructure/db/repositories/business_repository.py",
    "sales_agent/infrastructure/memory/audit_repository.py",
    "sales_agent/infrastructure/prompts/base.py",
    "sales_agent/infrastructure/repositories/message_repository.py",
    "scheduling/api/agenda.py",
    "scheduling/api/public_links.py",
    "scheduling/application/services/availability_service.py",
    "scheduling/application/services/event_type_service.py",
    "scheduling/infrastructure/repositories/appointment_repository.py",
}


def test_no_hard_deletes():
    """No repository uses session.delete() — only soft delete via deleted_at.

    Hard deletes violate data retention policy and break audit trails.
    Use: obj.deleted_at = datetime.utcnow() instead.
    """
    delete_pattern = re.compile(r"(?:session|db|self\.db|self\.session)\.delete\s*\(")
    violations: list[str] = []

    for py_file in sorted(MODULES_DIR.rglob("*.py")):
        if "migrations" in py_file.parts or "alembic" in py_file.parts:
            continue
        rel = py_file.relative_to(MODULES_DIR)
        if str(rel) in KNOWN_HARD_DELETE_FILES:
            continue
        content = py_file.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if delete_pattern.search(line):
                violations.append(f"{rel}:{i}: {stripped.strip()}")

    assert violations == [], (
        "Hard deletes detected. Use soft delete (deleted_at) instead.\n\n"
        "Violations:\n" + "\n".join(f"  - {v}" for v in violations)
    )


def test_no_sqlalchemy_1x_query_syntax():
    """No new code uses session.query() — must use select(Model).where(...).

    SA 2.0 select() is required for async compatibility and type safety.
    """
    query_pattern = re.compile(
        r"(?:session|db|self\.db|self\.session)\.query\s*\("
    )
    violations: list[str] = []

    for py_file in sorted(MODULES_DIR.rglob("*.py")):
        if "migrations" in py_file.parts:
            continue
        content = py_file.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if query_pattern.search(line):
                rel = py_file.relative_to(MODULES_DIR)
                violation_key = str(rel)
                if violation_key in KNOWN_SA1X_VIOLATIONS:
                    continue
                violations.append(f"{rel}:{i}: {stripped.strip()}")

    assert violations == [], (
        "SA 1.x session.query() detected. Use SA 2.0 select(Model).where(...).\n\n"
        "Options:\n"
        "  1. Refactor to: result = await session.execute(select(Model).where(...))\n"
        "  2. If legacy code you can't touch now, add file to KNOWN_SA1X_VIOLATIONS\n\n"
        "Violations:\n" + "\n".join(f"  - {v}" for v in violations)
    )
