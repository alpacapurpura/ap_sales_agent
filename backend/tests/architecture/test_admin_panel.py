"""Architecture gate: the admin panel navigation must stay consistent.

Complements `backend/tests/admin/` by running in the architecture suite, which
catches drift before dev even gets to the smoke tests. Kept minimal on purpose
so this file does not duplicate the richer contract tests — only enforces the
"no orphaned pages / no orphaned modules" invariant.
"""

from __future__ import annotations

from pathlib import Path

from src.admin.app import PAGE_SPECS

ADMIN_ROOT = Path(__file__).resolve().parents[2] / "src" / "admin"
PAGES_DIR = ADMIN_ROOT / "pages"
MODULES_DIR = ADMIN_ROOT / "modules"


def test_admin_pages_match_registry() -> None:
    page_files = {p.stem for p in PAGES_DIR.glob("*.py") if p.name != "__init__.py"}
    registered = {s.slug for s in PAGE_SPECS}
    assert page_files == registered, (
        "src/admin/pages/ drifted from PAGE_SPECS. "
        f"Only in pages/: {sorted(page_files - registered)}. "
        f"Only in registry: {sorted(registered - page_files)}."
    )


def test_admin_modules_have_render_function() -> None:
    """Every module intended as a page exposes at least one `render_*`."""
    offenders: list[str] = []
    for path in MODULES_DIR.glob("*.py"):
        if path.name in {"__init__.py", "_shared.py"}:
            continue
        source = path.read_text(encoding="utf-8")
        if "def render_" not in source:
            offenders.append(path.name)
    assert not offenders, (
        f"Admin modules without a render_* function: {offenders}. "
        "Move helpers to _shared.py or add a render_* entry point."
    )
