"""codemod_be_imports.py — Story 10 BE imports rewrite.

Transforms `from src.modules.X` / `from src.shared.X` imports → luana-core targets.

Usage:
    python scripts/codemod_be_imports.py --package=brand --dry-run
    python scripts/codemod_be_imports.py --package=brand --apply
    python scripts/codemod_be_imports.py --tests-only --pattern=tests/modules/brand/ --apply
    python scripts/codemod_be_imports.py --dry-run --self-check

Idempotent: running twice on already-rewritten files produces no changes.

Decisions:
    D5 — fix-on-discovery cap delta=0 (new failures vs baseline = 0)
    D1 — full big-bang scope (all 18 modules + 11 shared subsystems)
    D10 — Session 5 pre-auth (T-1 is baseline/tooling only, no auth changes)
"""

import argparse
import sys
import textwrap
from pathlib import Path

import libcst as cst

# MAPPING — source module prefix → target module prefix
# Sorted longest-first during matching to avoid prefix shadowing (e.g., src.shared.domain_events
# must match before src.shared.domain).
# Full table per 03-arch-be.md §2.1
MAPPING: dict[str, str] = {
    # ===== BE modules (18 total) =====
    "src.modules.brand": "luana_core_brand_studio",
    "src.modules.offer": "luana_core_offer_studio",
    "src.modules.landing": "luana_core_landing",
    "src.modules.assets": "luana_core_assets",
    "src.modules.connections": "luana_core_connections",
    "src.modules.iam": "luana_core_iam",
    "src.modules.crm": "luana_core_crm",
    "src.modules.commercial_calendar": "luana_core_commercial_calendar",
    "src.modules.analytics": "luana_core_analytics_engine",
    "src.modules.campaigns": "luana_core_campaigns",
    "src.modules.social_proof": "luana_core_social_proof",
    "src.modules.tenant_profile": "luana_core_tenant_profile",
    "src.modules.tenant_domains": "luana_core_tenant_domains",
    "src.modules.copilot": "luana_core_copilot",
    "src.modules.sales_agent": "luana_core_sales_agent",
    # Nicolify-local modules (scheduling/advertising/social_media) — NOT rewritten.
    # Per architect Phase 0 resolution #7: these stay Nicolify-vertical-specific.
    # No MAPPING entry = codemod leaves `src.modules.scheduling.X` etc. unchanged.
    # When Wave 5 moves files to luana-platform/nicolify/backend/, namespace handled there.
    # ===== Shared subsystems (11 subsystems) =====
    # Order matters: more specific prefixes must precede less specific ones.
    "src.shared.agent_observability": "luana_core_observability",
    # domain_events.outbox must precede domain_events (specificity)
    "src.shared.domain_events.outbox": "luana_core_events.outbox",
    "src.shared.domain_events": "luana_core_events",
    "src.shared.events": "luana_core_events",
    "src.shared.billing": "luana_core_billing",
    "src.shared.compliance": "luana_core_compliance",
    "src.shared.idempotency": "luana_core_idempotency",
    "src.shared.infrastructure.llm": "luana_core_llm",
    # application.extraction must precede application (specificity)
    "src.shared.application.extraction": "luana_core_extraction",
    "src.shared.application": "luana_core_platform.application",
    # domain.locale must precede domain (specificity)
    "src.shared.domain.locale": "luana_core_platform.domain.locale",
    "src.shared.domain": "luana_core_platform.domain",
    "src.shared.api": "luana_core_platform.api",
    # ===== Cross-module ports (links/ports/) =====
    # AUDIT FIX 2026-05-12 (T-1.6 by /pm Opus orchestrator): All cross-module ports
    # physically live in luana_core_platform/links/ports/ — verified by `ls` of
    # /home/chris/luana-platform/core/luana-core-platform/src/luana_core_platform/links/ports/.
    # Original per-consumer MAPPING (architect 03-arch-be.md §1.2) was WRONG — distributed
    # ports across 10+ packages that don't have links/ports/ subdirs (e.g., luana_core_landing
    # has no links/, luana_core_brand_studio has no links/). T-2 builder spawn hit Trigger #11
    # on first invocation. Fix: delete per-consumer entries, rely on catch-all (next line) which
    # is sorted-by-length-asc but still wins because per-consumer entries removed.
    "src.shared.links": "luana_core_platform.links",
    # ===== DEFERRED — Workers (Story 10b) =====
    # "src.shared.workers": DEFERRED Story 10b — halt if encountered during T-7
    # "src.workers": DEFERRED Story 10b
    # Do NOT add here — encountering these triggers Halt Trigger #1
}

# Sorted by key length descending to ensure longest prefix wins
_SORTED_MAPPING = sorted(MAPPING.items(), key=lambda kv: -len(kv[0]))


def _dotted_name_to_str(node: cst.Attribute | cst.Name) -> str:
    """Convert a libcst dotted name node to a Python string like 'a.b.c'."""
    if isinstance(node, cst.Name):
        return node.value
    elif isinstance(node, cst.Attribute):
        return _dotted_name_to_str(node.value) + "." + node.attr.value
    return ""


def _str_to_dotted_name(s: str) -> cst.Attribute | cst.Name:
    """Convert a Python string like 'a.b.c' to a libcst dotted name node."""
    parts = s.split(".")
    node: cst.Attribute | cst.Name = cst.Name(parts[0])
    for part in parts[1:]:
        node = cst.Attribute(value=node, attr=cst.Name(part))
    return node


class ImportRewriter(cst.CSTTransformer):
    """Rewrite `from src.X import Y` → `from luana_core_X import Y`.

    Handles:
    - Simple imports: `from src.modules.brand import BrandService`
    - Aliased imports: `from src.modules.brand import BrandService as BS`
    - Multi-line imports: `from src.modules.brand import (\n    A,\n    B,\n)`
    - Nested dotted paths: `from src.modules.brand.domain.models import X`
    - Test mock paths: `mocker.patch("src.modules.brand.X.BrandService.method")` [TODO T-2+]
    """

    def __init__(self) -> None:
        super().__init__()
        self.changes: list[str] = []

    def leave_ImportFrom(
        self,
        original_node: cst.ImportFrom,
        updated_node: cst.ImportFrom,
    ) -> cst.ImportFrom:
        if updated_node.module is None:
            return updated_node

        module_str = _dotted_name_to_str(updated_node.module)

        for src_prefix, target_prefix in _SORTED_MAPPING:
            if module_str == src_prefix or module_str.startswith(src_prefix + "."):
                suffix = module_str[len(src_prefix):]
                new_module_str = target_prefix + suffix
                self.changes.append(f"  {module_str!r} → {new_module_str!r}")
                return updated_node.with_changes(
                    module=_str_to_dotted_name(new_module_str)
                )

        return updated_node


def rewrite_file(path: Path, dry_run: bool = True) -> tuple[bool, list[str]]:
    """Rewrite imports in a single .py file. Returns (changed, changes_list)."""
    original_text = path.read_text(encoding="utf-8")
    try:
        tree = cst.parse_module(original_text)
    except cst.ParserSyntaxError as exc:
        print(f"  PARSE ERROR {path}: {exc}", file=sys.stderr)
        return False, []

    rewriter = ImportRewriter()
    new_tree = tree.visit(rewriter)
    new_text = new_tree.code

    if new_text == original_text:
        return False, []

    if not dry_run:
        path.write_text(new_text, encoding="utf-8")

    return True, rewriter.changes


def walk_py_files(root: Path) -> list[Path]:
    """Walk directory tree and yield .py files."""
    return sorted(root.rglob("*.py"))


def run_self_check() -> bool:
    """
    Self-check: create a temp file with known imports, run rewriter,
    verify idempotency + expected transformations.

    Returns True if all assertions pass, False otherwise.
    """
    import tempfile

    sample_code = textwrap.dedent("""
        from src.modules.brand.domain.models import BrandSettings
        from src.modules.offer.application.offer_service import OfferService
        from src.modules.scheduling.application.scheduler import SchedulerService
        from src.modules.advertising.domain.meta_campaign import MetaCampaign
        from src.shared.agent_observability.recording.turn_envelope import TurnEnvelope
        from src.shared.domain_events.outbox.model import DomainEventOutboxModel
        from src.shared.domain_events.bus import EventBus
        from src.shared.infrastructure.llm.router import LLMRouter
        from src.shared.application.extraction.base_orchestrator import BaseExtractionOrchestrator
        from src.shared.domain.locale import TenantLocale
        from src.shared.links.ports.brand import BrandDataPort
        from src.shared.links.ports.advertising import AdvertisingPort
        import os
        from typing import Optional
    """).strip()

    expected_rewrites = {
        "src.modules.brand.domain.models": "luana_core_brand_studio.domain.models",
        "src.modules.offer.application.offer_service": "luana_core_offer_studio.application.offer_service",
        # scheduling/advertising removed — Nicolify-local, NOT rewritten (verified separately below)
        "src.shared.agent_observability.recording.turn_envelope": "luana_core_observability.recording.turn_envelope",
        "src.shared.domain_events.outbox.model": "luana_core_events.outbox.model",
        "src.shared.domain_events.bus": "luana_core_events.bus",
        "src.shared.infrastructure.llm.router": "luana_core_llm.router",
        "src.shared.application.extraction.base_orchestrator": "luana_core_extraction.base_orchestrator",
        "src.shared.domain.locale": "luana_core_platform.domain.locale",
        # AUDIT FIX T-1.6: ports live in luana_core_platform.links.ports.X (catch-all rewrite)
        "src.shared.links.ports.brand": "luana_core_platform.links.ports.brand",
        "src.shared.links.ports.advertising": "luana_core_platform.links.ports.advertising",
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(sample_code)
        tmp_path = Path(f.name)

    try:
        # First pass — rewrite
        changed, changes = rewrite_file(tmp_path, dry_run=False)
        assert changed, "Expected file to be changed on first pass"

        rewritten_text = tmp_path.read_text(encoding="utf-8")

        # Verify expected rewrites appear in output
        for orig_module, expected_module in expected_rewrites.items():
            # The expected_module (or its final segment) should appear in rewritten
            expected_import_fragment = f"from {expected_module}"
            assert expected_import_fragment in rewritten_text, (
                f"Expected '{expected_import_fragment}' in rewritten code.\n"
                f"Original module: {orig_module!r}\n"
                f"Rewritten text:\n{rewritten_text}"
            )

        # AUDIT FIX T-1.6: Nicolify-local stay UNCHANGED as `src.modules.X`
        # (no MAPPING entries → codemod leaves them alone). Wave 5 file moves handle
        # namespace transition to luana-platform/nicolify/backend/.
        assert "src.modules.scheduling.application.scheduler" in rewritten_text, (
            "Expected scheduling to stay src.modules.scheduling (Nicolify-local, unchanged)"
        )
        assert "src.modules.advertising.domain.meta_campaign" in rewritten_text, (
            "Expected advertising to stay src.modules.advertising (Nicolify-local, unchanged)"
        )

        # Verify untouched imports stay untouched
        assert "import os" in rewritten_text, "Non-src import should be untouched"
        assert "from typing import Optional" in rewritten_text, (
            "typing import should be untouched"
        )

        # Idempotency check — second pass should produce NO changes
        changed2, changes2 = rewrite_file(tmp_path, dry_run=False)
        assert not changed2, (
            f"Expected no changes on second pass (idempotency). Got {len(changes2)} changes:\n"
            + "\n".join(changes2)
        )

        print("Self-check PASSED — all assertions green (idempotency + rewrites + stay-local)")
        return True

    except AssertionError as exc:
        print(f"Self-check FAILED: {exc}", file=sys.stderr)
        return False
    finally:
        tmp_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rewrite AISALESHT BE imports → luana-core (Story 10 T-1 tooling)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without writing files",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply rewrites (writes files in-place)",
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="Run idempotency + correctness self-check on a temp file",
    )
    parser.add_argument(
        "--package",
        type=str,
        default=None,
        help="Scope rewrite to a single module (e.g. 'brand' → only src/modules/brand/ + tests/modules/brand/)",
    )
    parser.add_argument(
        "--tests-only",
        action="store_true",
        help="Rewrite only test files (use with --pattern)",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default=None,
        help="Path pattern (relative to repo root) to scope rewrites (e.g. 'tests/modules/brand/')",
    )
    parser.add_argument(
        "--paths",
        nargs="+",
        default=None,
        help="Explicit paths to rewrite (overrides --package/--pattern)",
    )
    args = parser.parse_args()

    if args.self_check:
        ok = run_self_check()
        sys.exit(0 if ok else 1)

    if not args.dry_run and not args.apply:
        print(
            "ERROR: specify --dry-run or --apply",
            file=sys.stderr,
        )
        sys.exit(1)

    # Determine search roots
    repo_root = Path(__file__).parent.parent  # AISALESHT/
    backend_root = repo_root / "backend"

    search_roots: list[Path] = []

    if args.paths:
        search_roots = [Path(p) for p in args.paths]
    elif args.pattern:
        search_roots = [backend_root / args.pattern]
    elif args.package:
        pkg = args.package
        search_roots = [
            backend_root / "src" / "modules" / pkg,
        ]
        if not args.tests_only:
            search_roots.append(backend_root / "tests" / "modules" / pkg)
    else:
        # Default: entire backend src
        search_roots = [backend_root / "src"]

    dry_run = not args.apply
    mode = "DRY-RUN" if dry_run else "APPLY"

    total_files = 0
    changed_files = 0

    for root in search_roots:
        if not root.exists():
            print(f"WARNING: path does not exist: {root}", file=sys.stderr)
            continue

        py_files = walk_py_files(root)
        for py_file in py_files:
            total_files += 1
            changed, changes = rewrite_file(py_file, dry_run=dry_run)
            if changed:
                changed_files += 1
                rel = py_file.relative_to(repo_root)
                print(f"[{mode}] {rel}")
                for change in changes:
                    print(change)

    print(
        f"\n[{mode}] {changed_files}/{total_files} files {'would be changed' if dry_run else 'changed'}"
    )


if __name__ == "__main__":
    main()
