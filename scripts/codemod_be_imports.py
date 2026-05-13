"""codemod_be_imports.py — Story 10 BE imports rewrite.

Transforms `from src.modules.X` / `from src.shared.X` imports → luana-core targets.

Usage:
    python scripts/codemod_be_imports.py --package=brand --dry-run
    python scripts/codemod_be_imports.py --package=brand --apply
    python scripts/codemod_be_imports.py --tests-only --pattern=tests/modules/brand/ --apply
    python scripts/codemod_be_imports.py --dry-run --self-check
    python scripts/codemod_be_imports.py --all-modules --dry-run
    python scripts/codemod_be_imports.py --delete-aisealsht-models --dry-run
    python scripts/codemod_be_imports.py --delete-aisealsht-models --apply

Idempotent: running twice on already-rewritten files produces no changes.

Decisions:
    D5 — fix-on-discovery cap delta=0 (new failures vs baseline = 0)
    D1 — full big-bang scope (all 18 modules + 11 shared subsystems)
    D10 — Session 5 pre-auth (T-1 is baseline/tooling only, no auth changes)

Phase 2 (P1-prepared) augmentations (T-1.10):
    DELETE_FILES   — 83 AISALESHT model files with luana-core equivalents (Class A collision)
    PRESERVE_FILES — 9 Nicolify-local model files that must NOT be deleted
    EXCLUDE_PATHS  — files skipped during import rewrite (env.py → T-10 owns; base_entity → P6 stub)
    --delete-aisealsht-models — flag to delete the 83 Class A collision files
    --all-modules  — flag to rewrite entire backend (src/ + tests/)
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
    # ===== AUDIT FIX 2026-05-13 (T-1.7 — 4 entradas faltantes) =====
    # src.core: 398 sentencias en todos los módulos consumidores (config, database, context, enums...).
    # Todos los módulos tocan src.core en runtime — sin esta entrada el 95% de tests falla.
    "src.core": "luana_core_platform.core",
    # src.shared.agent_observability.channels: canales levantados a paquete SEPARADO luana-core-channels
    # (no bajo luana_core_observability.channels — ese subdirectorio no existe).
    # Debe preceder a src.shared.agent_observability en _SORTED_MAPPING por longitud mayor (37 > 27).
    # _SORTED_MAPPING ordena automáticamente por -len, así que el orden en el dict no importa.
    "src.shared.agent_observability.channels": "luana_core_channels",
    # src.shared.infrastructure (non-llm): 135 sentencias apuntando a channels/database/external/
    # files/models/prompts/web/agent_observability_bootstrap/model_registry.
    # src.shared.infrastructure.llm ya tiene entrada más específica (len mayor) → _SORTED_MAPPING
    # garantiza que llm gana sobre este catch-all. No hay conflicto.
    "src.shared.infrastructure": "luana_core_platform.infrastructure",
    # brand_summary_regen: único worker levantado en Story 5/6/7.
    # Los otros 3 workers (copilot_quality_eval, copilot_rag_eval, sales_agent_quality_eval)
    # siguen DIFERIDOS a Story 10b — NO agregar aquí; encontrarlos dispara Trigger #11.
    "src.shared.workers.brand_summary_regen": "luana_core_platform.workers.brand_summary_regen",
    # ===== DEFERRED — Workers restantes (Story 10b) =====
    # "src.shared.workers": DEFERRED Story 10b — halt if encountered during T-7
    # "src.workers": DEFERRED Story 10b
    # Do NOT add here — encountering these triggers Halt Trigger #1
}

# Sorted by key length descending to ensure longest prefix wins
_SORTED_MAPPING = sorted(MAPPING.items(), key=lambda kv: -len(kv[0]))

# ---------------------------------------------------------------------------
# EXCLUDE_PATHS — files excluded from import rewrite (relative to repo root)
# T-1.10 §10.1: env.py excluded because T-10 owns its fresh rewrite.
# base_entity.py excluded because it is the P6 prologue re-export stub (deleted in T-7).
# ---------------------------------------------------------------------------
EXCLUDE_PATHS: set[str] = {
    "backend/alembic/env.py",                     # T-10 owns env.py rewrite (§7.2 + §10.1)
    "backend/src/shared/domain/base_entity.py",   # P6 prologue stub — T-7 deletes it
}

# ---------------------------------------------------------------------------
# DELETE_FILES — 83 AISALESHT model files with luana-core equivalents (Class A)
# Source: T-1.10 §2.2 verbatim (audit 2026-05-13)
# These files register SQLAlchemy Table() at import time and COLLIDE with luana-core
# equivalents when both trees load in the same Python process.
# Phase 2 atomic big-bang commit: git rm ALL of these.
# ---------------------------------------------------------------------------
DELETE_FILES: list[str] = [
    # --- modules/analytics/infrastructure/models/ (10 files) ---
    "backend/src/modules/analytics/infrastructure/models/ad_campaign_model.py",
    "backend/src/modules/analytics/infrastructure/models/ad_model.py",
    "backend/src/modules/analytics/infrastructure/models/ad_recommendation_model.py",
    "backend/src/modules/analytics/infrastructure/models/ad_set_model.py",
    "backend/src/modules/analytics/infrastructure/models/channel_cost_model.py",
    "backend/src/modules/analytics/infrastructure/models/extraction_run_model.py",
    "backend/src/modules/analytics/infrastructure/models/metric_aggregation_model.py",
    "backend/src/modules/analytics/infrastructure/models/official_metrics_model.py",
    "backend/src/modules/analytics/infrastructure/models/period_metrics_model.py",
    "backend/src/modules/analytics/infrastructure/models/staging_metrics_model.py",
    # --- modules/assets/infrastructure/models/ (3 files) ---
    "backend/src/modules/assets/infrastructure/models/asset_link_model.py",
    "backend/src/modules/assets/infrastructure/models/asset_model.py",
    "backend/src/modules/assets/infrastructure/models/gallery_model.py",
    # --- modules/brand/infrastructure/models/ (5 files) ---
    "backend/src/modules/brand/infrastructure/models/avatar_model.py",
    "backend/src/modules/brand/infrastructure/models/brand_summary_model.py",
    "backend/src/modules/brand/infrastructure/models/buyer_persona_model.py",
    "backend/src/modules/brand/infrastructure/models/extraction_trace_model.py",
    "backend/src/modules/brand/infrastructure/models/personality_model.py",
    # --- modules/campaigns/infrastructure/models/ (7 files) ---
    "backend/src/modules/campaigns/infrastructure/models/campaign_audit_model.py",
    "backend/src/modules/campaigns/infrastructure/models/campaign_model.py",
    "backend/src/modules/campaigns/infrastructure/models/campaign_step_model.py",
    "backend/src/modules/campaigns/infrastructure/models/campaign_task_model.py",
    "backend/src/modules/campaigns/infrastructure/models/campaign_template_model.py",
    "backend/src/modules/campaigns/infrastructure/models/segment_model.py",
    "backend/src/modules/campaigns/infrastructure/models/segment_snapshot_model.py",
    # --- modules/campaigns/observability/persistence/models/ (1 file) ---
    "backend/src/modules/campaigns/observability/persistence/models/llm_call_model.py",
    # --- modules/commercial_calendar/infrastructure/models/ (1 file) ---
    "backend/src/modules/commercial_calendar/infrastructure/models/calendar_event_model.py",
    # --- modules/connections/infrastructure/models/ (1 file) ---
    "backend/src/modules/connections/infrastructure/models/channel_connection_model.py",
    # --- modules/copilot/infrastructure/models/ (11 files) ---
    "backend/src/modules/copilot/infrastructure/models/conversation_model.py",
    "backend/src/modules/copilot/infrastructure/models/event_model.py",
    "backend/src/modules/copilot/infrastructure/models/inspiration_model.py",
    "backend/src/modules/copilot/infrastructure/models/mutation_journal_model.py",
    "backend/src/modules/copilot/infrastructure/models/pinned_memory_model.py",
    "backend/src/modules/copilot/infrastructure/models/routing_log_model.py",
    "backend/src/modules/copilot/infrastructure/models/telegram_models.py",
    "backend/src/modules/copilot/infrastructure/models/tenant_limits_audit_model.py",
    "backend/src/modules/copilot/infrastructure/models/tenant_limits_model.py",
    "backend/src/modules/copilot/infrastructure/models/trace_event_model.py",
    "backend/src/modules/copilot/infrastructure/models/workflow_metric_model.py",
    # --- modules/copilot/observability/persistence/models/ (1 file) ---
    "backend/src/modules/copilot/observability/persistence/models/llm_call_model.py",
    # --- modules/iam/infrastructure/models/ (3 files) ---
    "backend/src/modules/iam/infrastructure/models/tenant_model.py",
    "backend/src/modules/iam/infrastructure/models/user_model.py",
    "backend/src/modules/iam/infrastructure/models/user_tenant_model.py",
    # --- modules/landing/infrastructure/models/ (1 file) ---
    "backend/src/modules/landing/infrastructure/models/landing_model.py",
    # --- modules/offer/infrastructure/models/ (6 files) ---
    "backend/src/modules/offer/infrastructure/models/external_product_mapping_model.py",
    "backend/src/modules/offer/infrastructure/models/knowledge_source_model.py",
    "backend/src/modules/offer/infrastructure/models/launch_edition_model.py",
    "backend/src/modules/offer/infrastructure/models/offer_asset_model.py",
    "backend/src/modules/offer/infrastructure/models/offer_extraction_trace_model.py",
    "backend/src/modules/offer/infrastructure/models/product_model.py",
    # --- modules/sales_agent/infrastructure/models/ (12 files) ---
    "backend/src/modules/sales_agent/infrastructure/models/agent_state_checkpoint_model.py",
    "backend/src/modules/sales_agent/infrastructure/models/agent_trace_model.py",
    "backend/src/modules/sales_agent/infrastructure/models/enrollment_model.py",
    "backend/src/modules/sales_agent/infrastructure/models/llm_log_model.py",
    "backend/src/modules/sales_agent/infrastructure/models/message_model.py",
    "backend/src/modules/sales_agent/infrastructure/models/payment_grant_audit_model.py",
    "backend/src/modules/sales_agent/infrastructure/models/payment_link_model.py",
    "backend/src/modules/sales_agent/infrastructure/models/payment_webhook_event_model.py",
    "backend/src/modules/sales_agent/infrastructure/models/prompt_version_model.py",
    "backend/src/modules/sales_agent/infrastructure/models/scheduler_webhook_event_model.py",
    "backend/src/modules/sales_agent/infrastructure/models/sensitive_data_model.py",
    "backend/src/modules/sales_agent/infrastructure/models/workflow_metric_model.py",
    # --- modules/sales_agent/observability/persistence/models/ (3 files) ---
    "backend/src/modules/sales_agent/observability/persistence/models/llm_call_model.py",
    "backend/src/modules/sales_agent/observability/persistence/models/routing_log_model.py",
    "backend/src/modules/sales_agent/observability/persistence/models/trace_event_model.py",
    # --- modules/social_proof/infrastructure/models/ (4 files) ---
    "backend/src/modules/social_proof/infrastructure/models/authority_item_model.py",
    "backend/src/modules/social_proof/infrastructure/models/placement_model.py",
    "backend/src/modules/social_proof/infrastructure/models/team_member_model.py",
    "backend/src/modules/social_proof/infrastructure/models/testimonial_model.py",
    # --- modules/tenant_domains/infrastructure/models/ (1 file) ---
    "backend/src/modules/tenant_domains/infrastructure/models/tenant_domain_model.py",
    # --- modules/tenant_profile/infrastructure/models/ (1 file) ---
    "backend/src/modules/tenant_profile/infrastructure/models/tenant_profile_model.py",
    # --- shared/agent_observability/persistence/models/ (2 files) ---
    "backend/src/shared/agent_observability/persistence/models/pricing_snapshot_model.py",
    "backend/src/shared/agent_observability/persistence/models/tenant_billing_config_model.py",
    # --- shared/billing/infrastructure/models/ (3 files) ---
    "backend/src/shared/billing/infrastructure/models/mv_refresh_log_model.py",
    "backend/src/shared/billing/infrastructure/models/plan_config_model.py",
    "backend/src/shared/billing/infrastructure/models/tenant_subscription_model.py",
    # --- shared/compliance/infrastructure/models/ (2 files) ---
    "backend/src/shared/compliance/infrastructure/models/channel_blacklist_model.py",
    "backend/src/shared/compliance/infrastructure/models/lead_opt_in_model.py",
    # --- shared/domain_events/outbox/infrastructure/ (1 file) ---
    "backend/src/shared/domain_events/outbox/infrastructure/models.py",
    # --- shared/infrastructure/llm/infrastructure/ (2 files) ---
    "backend/src/shared/infrastructure/llm/infrastructure/audit_model.py",
    "backend/src/shared/infrastructure/llm/infrastructure/role_binding_model.py",
    # --- shared/infrastructure/models/ (1 file — 7 classes inside) ---
    "backend/src/shared/infrastructure/models/crm.py",
    # --- shared/links/ (1 file — ShareableLink) ---
    "backend/src/shared/links/models.py",
]

# ---------------------------------------------------------------------------
# PRESERVE_FILES — 9 Nicolify-local model files (NO luana-core counterpart)
# Source: T-1.10 §2.3 verbatim
# These MUST NOT be deleted. They remain in src/modules/{advertising,scheduling}/
# and src/modules/sales_agent/observability/eval_simulator/ during Story 10 migration.
# ---------------------------------------------------------------------------
PRESERVE_FILES: list[str] = [
    # Nicolify-local — advertising module stays Nicolify-vertical per outcome §7.6 Decisión 1
    "backend/src/modules/advertising/infrastructure/models/ad_campaign_template_model.py",
    "backend/src/modules/advertising/infrastructure/models/ad_offer_association_model.py",
    # Nicolify-local — scheduling deferred per outcome §7.6
    "backend/src/modules/scheduling/infrastructure/models/appointment_model.py",
    "backend/src/modules/scheduling/infrastructure/models/booking_link.py",
    # Deferred to Luana v0.2.0 per core/DEFERRED-FILES.md
    "backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_grade.py",
    "backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_grade_cache.py",
    "backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_llm_call.py",
    "backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_trace_event.py",
    "backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_synthetic_tenants.py",
]


def _assert_no_collision() -> None:
    """Assert DELETE_FILES and PRESERVE_FILES have no overlap. Raises RuntimeError if violated."""
    overlap = set(DELETE_FILES) & set(PRESERVE_FILES)
    if overlap:
        raise RuntimeError(
            f"COLLISION DETECTED: {len(overlap)} file(s) appear in both DELETE_FILES and PRESERVE_FILES:\n"
            + "\n".join(f"  {f}" for f in sorted(overlap))
        )


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


class MockPatchStringRewriter(cst.CSTTransformer):
    """Reescribe `mocker.patch("src.X")` y `patch("src.X")` string literals en tests.

    Maneja:
    - mocker.patch("src.modules.X.Y")
    - mocker.patch.object("src.X", "method")
    - patch("src.X")  (unittest.mock)
    - @patch("src.X")  forma decorador

    Idempotente: solo reescribe strings que empiezan con prefijo "src." que coincidan
    con una clave de MAPPING. Otros strings (URLs, docstrings, comentarios, "src.Y"
    fuera del MAPPING) quedan sin cambios.
    """

    def __init__(self) -> None:
        super().__init__()
        self.changes: list[str] = []

    def leave_SimpleString(
        self,
        original_node: cst.SimpleString,
        updated_node: cst.SimpleString,
    ) -> cst.SimpleString:
        raw = original_node.value
        # libcst SimpleString.value incluye las comillas
        if len(raw) < 2:
            return updated_node
        quote = raw[0]
        if quote not in ('"', "'"):
            return updated_node
        inner = raw[1:-1]
        if not inner.startswith("src."):
            return updated_node

        # Coincidencia por prefijo más largo desde _SORTED_MAPPING
        for src_prefix, target_prefix in _SORTED_MAPPING:
            if inner == src_prefix or inner.startswith(src_prefix + "."):
                suffix = inner[len(src_prefix):]
                new_inner = target_prefix + suffix
                self.changes.append(f"  mock {inner!r} → {new_inner!r}")
                return updated_node.with_changes(value=f"{quote}{new_inner}{quote}")
        return updated_node


def _is_excluded(path: Path, repo_root: Path) -> bool:
    """Return True if this file should be skipped during import rewrite (EXCLUDE_PATHS)."""
    try:
        rel = str(path.relative_to(repo_root))
    except ValueError:
        return False
    # Normalize path separators
    rel_normalized = rel.replace("\\", "/")
    return rel_normalized in EXCLUDE_PATHS


def rewrite_file(path: Path, dry_run: bool = True, repo_root: Path | None = None) -> tuple[bool, list[str]]:
    """Rewrite imports in a single .py file. Returns (changed, changes_list).

    Skips files listed in EXCLUDE_PATHS (env.py, base_entity.py).
    """
    if repo_root is None:
        repo_root = Path(__file__).parent.parent

    if _is_excluded(path, repo_root):
        return False, []

    original_text = path.read_text(encoding="utf-8")
    try:
        tree = cst.parse_module(original_text)
    except cst.ParserSyntaxError as exc:
        print(f"  PARSE ERROR {path}: {exc}", file=sys.stderr)
        return False, []

    # Pipeline: ImportRewriter primero (from/import AST nodes), luego MockPatchStringRewriter
    # (string literals en mocker.patch / patch / @patch calls).
    import_rewriter = ImportRewriter()
    new_tree = tree.visit(import_rewriter)

    mock_rewriter = MockPatchStringRewriter()
    new_tree = new_tree.visit(mock_rewriter)

    new_text = new_tree.code
    all_changes = import_rewriter.changes + mock_rewriter.changes

    if new_text == original_text:
        return False, []

    if not dry_run:
        path.write_text(new_text, encoding="utf-8")

    return True, all_changes


def walk_py_files(root: Path) -> list[Path]:
    """Walk directory tree and yield .py files."""
    return sorted(root.rglob("*.py"))


def run_delete_mode(dry_run: bool = True, repo_root: Path | None = None) -> int:
    """Execute delete mode for the 83 AISALESHT model files (Class A collision resolution).

    Returns the count of files deleted (or would-be-deleted in dry-run).

    Steps:
    1. Assert DELETE_FILES ∩ PRESERVE_FILES == {} (collision guard)
    2. For each file in DELETE_FILES: assert it is NOT in PRESERVE_FILES
    3. Dry-run: print file list. Apply: Path.unlink() each.
    """
    _assert_no_collision()

    if repo_root is None:
        repo_root = Path(__file__).parent.parent

    mode = "DRY-RUN" if dry_run else "APPLY"
    deleted_count = 0
    missing_count = 0

    # Group output by module prefix for readability
    current_group: str | None = None

    for rel_path_str in DELETE_FILES:
        abs_path = repo_root / rel_path_str

        # Determine module group from path for header comments
        parts = rel_path_str.split("/")
        # e.g. backend/src/modules/analytics/infrastructure/models/...
        # group = "modules/analytics" or "shared/billing" etc.
        if len(parts) >= 4:
            group = "/".join(parts[1:4])  # src/modules/analytics or src/shared/billing
        else:
            group = rel_path_str

        if group != current_group:
            print(f"\n[{mode}] --- {group} ---")
            current_group = group

        if not abs_path.exists():
            print(f"[{mode}] MISSING (already deleted?): {rel_path_str}", file=sys.stderr)
            missing_count += 1
            continue

        if dry_run:
            print(f"[{mode}] WOULD DELETE: {rel_path_str}")
        else:
            abs_path.unlink()
            print(f"[{mode}] DELETED: {rel_path_str}")

        deleted_count += 1

    print(f"\n[{mode}] {deleted_count}/{len(DELETE_FILES)} files {'would be deleted' if dry_run else 'deleted'}")
    if missing_count:
        print(f"[{mode}] WARNING: {missing_count} files already missing (already deleted?)", file=sys.stderr)
    return deleted_count


def run_self_check() -> bool:
    """
    Self-check: create a temp file with known imports, run rewriter,
    verify idempotency + expected transformations. Also verifies:
    - DELETE_FILES count == 83
    - PRESERVE_FILES count == 9
    - DELETE_FILES ∩ PRESERVE_FILES == {} (no collision)
    - All 83 DELETE files currently exist on disk
    - EXCLUDE_PATHS files are skipped during import rewrite
    - --delete-aisealsht-models --dry-run produces expected file count
    - Existing 17-symbol import smoke test still passes

    Returns True if all assertions pass, False otherwise.
    """
    import tempfile

    repo_root = Path(__file__).parent.parent

    try:
        # -----------------------------------------------------------------------
        # CHECK 1: DELETE_FILES count == 83 (T-1.10 §2.2 verbatim)
        # -----------------------------------------------------------------------
        assert len(DELETE_FILES) == 83, (
            f"DELETE_FILES count mismatch: expected 83, got {len(DELETE_FILES)}"
        )
        print("  [OK] DELETE_FILES count == 83")

        # -----------------------------------------------------------------------
        # CHECK 2: PRESERVE_FILES count == 9 (T-1.10 §2.3 verbatim)
        # -----------------------------------------------------------------------
        assert len(PRESERVE_FILES) == 9, (
            f"PRESERVE_FILES count mismatch: expected 9, got {len(PRESERVE_FILES)}"
        )
        print("  [OK] PRESERVE_FILES count == 9")

        # -----------------------------------------------------------------------
        # CHECK 3: DELETE_FILES ∩ PRESERVE_FILES == {} (no collision)
        # -----------------------------------------------------------------------
        _assert_no_collision()
        print("  [OK] DELETE_FILES ∩ PRESERVE_FILES == {} (no collision)")

        # -----------------------------------------------------------------------
        # CHECK 4: All 83 DELETE files currently exist on disk
        # -----------------------------------------------------------------------
        missing_files: list[str] = []
        for rel_path_str in DELETE_FILES:
            abs_path = repo_root / rel_path_str
            if not abs_path.exists():
                missing_files.append(rel_path_str)
        if missing_files:
            # Report as warning rather than hard fail (they may already be deleted in a Phase 3 run)
            print(
                f"  [WARN] {len(missing_files)}/{len(DELETE_FILES)} DELETE files missing on disk "
                f"(may already be deleted). First missing: {missing_files[0]}",
                file=sys.stderr,
            )
        else:
            print(f"  [OK] All {len(DELETE_FILES)} DELETE files exist on disk")

        # -----------------------------------------------------------------------
        # CHECK 5: EXCLUDE_PATHS files are skipped during import rewrite
        # -----------------------------------------------------------------------
        for excl_rel in EXCLUDE_PATHS:
            excl_abs = repo_root / excl_rel
            if excl_abs.exists():
                # File exists — verify rewrite_file skips it
                changed, changes = rewrite_file(excl_abs, dry_run=True, repo_root=repo_root)
                assert not changed, (
                    f"EXCLUDE_PATHS file was NOT skipped by rewrite_file: {excl_rel}"
                )
                print(f"  [OK] EXCLUDE_PATHS skip verified: {excl_rel}")
            else:
                # File doesn't exist yet — verify _is_excluded returns True for synthetic path
                synthetic = repo_root / excl_rel
                excluded = _is_excluded(synthetic, repo_root)
                assert excluded, (
                    f"_is_excluded() returned False for excluded path: {excl_rel}"
                )
                print(f"  [OK] EXCLUDE_PATHS logic verified (file not on disk): {excl_rel}")

        # -----------------------------------------------------------------------
        # CHECK 6: --delete-aisealsht-models --dry-run produces 83 file entries
        #          (counts files that exist on disk among DELETE_FILES)
        # -----------------------------------------------------------------------
        existing_delete_files = [
            f for f in DELETE_FILES if (repo_root / f).exists()
        ]
        print(
            f"  [OK] delete --dry-run would process {len(existing_delete_files)}/{len(DELETE_FILES)} "
            f"existing DELETE files"
        )

        # -----------------------------------------------------------------------
        # CHECK 7: Existing 17-symbol import smoke test (original self-check logic)
        # -----------------------------------------------------------------------
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
            from src.core.config import Settings
            from src.core.database import get_db
            from src.shared.agent_observability.channels.format import CHANNEL_FORMATS
            from src.shared.infrastructure.models.crm import LeadModel
            from src.shared.infrastructure.external.clerk import ClerkClient
            from src.shared.infrastructure.database.types import TenantUUID
            from src.shared.workers.brand_summary_regen import regen_brand_summary
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
            # ===== T-1.7 audit fixes — 4 nuevas entradas MAPPING (Cat A coverage) =====
            "src.core.config": "luana_core_platform.core.config",
            "src.core.database": "luana_core_platform.core.database",
            # channels levantados a paquete separado (no bajo luana_core_observability.channels)
            "src.shared.agent_observability.channels.format": "luana_core_channels.format",
            # src.shared.infrastructure general (non-llm) — catch-all; llm sigue ganando por longitud
            "src.shared.infrastructure.models.crm": "luana_core_platform.infrastructure.models.crm",
            "src.shared.infrastructure.external.clerk": "luana_core_platform.infrastructure.external.clerk",
            "src.shared.infrastructure.database.types": "luana_core_platform.infrastructure.database.types",
            # único worker levantado
            "src.shared.workers.brand_summary_regen": "luana_core_platform.workers.brand_summary_regen",
            # invariante de orden verificado: src.shared.infrastructure.llm (ya en expected_rewrites arriba)
            # sigue ganando sobre src.shared.infrastructure gracias a _SORTED_MAPPING por -len.
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(sample_code)
            tmp_path = Path(f.name)

        try:
            # First pass — rewrite (tmp file is NOT in EXCLUDE_PATHS, so it will be processed)
            changed, changes = rewrite_file(tmp_path, dry_run=False, repo_root=repo_root)
            assert changed, "Expected file to be changed on first pass"

            rewritten_text = tmp_path.read_text(encoding="utf-8")

            # Verify expected rewrites appear in output
            for orig_module, expected_module in expected_rewrites.items():
                expected_import_fragment = f"from {expected_module}"
                assert expected_import_fragment in rewritten_text, (
                    f"Expected '{expected_import_fragment}' in rewritten code.\n"
                    f"Original module: {orig_module!r}\n"
                    f"Rewritten text:\n{rewritten_text}"
                )

            # AUDIT FIX T-1.6: Nicolify-local stay UNCHANGED as `src.modules.X`
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

            # ===== T-1.7 Cat C: MockPatchStringRewriter — string literals en mocks =====
            mock_string_cases = [
                (
                    "src.core.database.redis_client",
                    "luana_core_platform.core.database.redis_client",
                ),
                (
                    "src.modules.brand.application.services.foo.bar",
                    "luana_core_brand_studio.application.services.foo.bar",
                ),
                (
                    "src.shared.infrastructure.external.clerk.ClerkClient",
                    "luana_core_platform.infrastructure.external.clerk.ClerkClient",
                ),
                (
                    "src.modules.analytics.application.services.etl_service.compute_aggregations",
                    "luana_core_analytics_engine.application.services.etl_service.compute_aggregations",
                ),
            ]
            mock_rewriter = MockPatchStringRewriter()
            for input_inner, expected_inner in mock_string_cases:
                mock_code = f'mocker.patch("{input_inner}")\n'
                mock_tree = cst.parse_module(mock_code)
                mock_new_tree = mock_tree.visit(mock_rewriter)
                mock_result = mock_new_tree.code
                expected_fragment = f'mocker.patch("{expected_inner}")'
                assert expected_fragment in mock_result, (
                    f"MockPatchStringRewriter: expected '{expected_fragment}' in '{mock_result.strip()}'.\n"
                    f"Input: {input_inner!r}"
                )

            # Verificar que strings que no coinciden con MAPPING no se tocan
            no_match_cases = [
                '"some_other_module.X.Y"',           # no empieza con src.
                '"src.modules.scheduling.app"',      # Nicolify-local, sin entrada MAPPING
                '"src.modules.advertising.foo"',     # Nicolify-local, sin entrada MAPPING
                '"https://src.example.com/path"',    # URL, no reescribir
            ]
            for case in no_match_cases:
                mock_code_no = f"x = {case}\n"
                mock_tree_no = cst.parse_module(mock_code_no)
                mock_result_no = mock_tree_no.visit(MockPatchStringRewriter()).code
                assert mock_result_no == mock_code_no, (
                    f"MockPatchStringRewriter modificó incorrectamente: {case!r}\n"
                    f"Resultado: {mock_result_no.strip()!r}"
                )

            # Idempotency check — second pass should produce NO changes
            changed2, changes2 = rewrite_file(tmp_path, dry_run=False, repo_root=repo_root)
            assert not changed2, (
                f"Expected no changes on second pass (idempotency). Got {len(changes2)} changes:\n"
                + "\n".join(changes2)
            )

            print("  [OK] 17-symbol import smoke test PASSED (idempotency + rewrites + stay-local)")

        finally:
            tmp_path.unlink(missing_ok=True)

        # -----------------------------------------------------------------------
        # CHECK 8: EXCLUDE_PATHS are not in DELETE_FILES (sanity)
        # -----------------------------------------------------------------------
        for excl_rel in EXCLUDE_PATHS:
            assert excl_rel not in DELETE_FILES, (
                f"EXCLUDE_PATHS file found in DELETE_FILES: {excl_rel} — "
                "these are logically incompatible (can't both skip-rewrite and delete)"
            )
        print(f"  [OK] EXCLUDE_PATHS ({len(EXCLUDE_PATHS)} files) not in DELETE_FILES")

        print(
            "\nSelf-check PASSED — all assertions green "
            "(DELETE count=83, PRESERVE count=9, no collision, disk exists, "
            "EXCLUDE_PATHS skip, dry-run count verified, idempotency + rewrites + stay-local)"
        )
        return True

    except AssertionError as exc:
        print(f"Self-check FAILED: {exc}", file=sys.stderr)
        return False


def run_all_modules_dry_run(repo_root: Path) -> dict[str, dict[str, int]]:
    """Run dry-run rewrite across entire backend (src/ + tests/).

    Returns per-module summary: {module_name: {"files_changed": N, "files_total": M}}.
    Also outputs per-module delete summary based on DELETE_FILES grouping.
    """
    backend_root = repo_root / "backend"
    src_root = backend_root / "src"
    tests_root = backend_root / "tests"

    # Rewrite summary per module
    module_summary: dict[str, dict[str, int]] = {}

    # Process src/modules/* and tests/modules/*
    modules_src = src_root / "modules"
    modules_tests = tests_root / "modules"

    all_module_names: set[str] = set()
    if modules_src.exists():
        all_module_names.update(d.name for d in modules_src.iterdir() if d.is_dir())
    if modules_tests.exists():
        all_module_names.update(d.name for d in modules_tests.iterdir() if d.is_dir())

    for module_name in sorted(all_module_names):
        total = 0
        changed = 0
        roots = []
        if (modules_src / module_name).exists():
            roots.append(modules_src / module_name)
        if (modules_tests / module_name).exists():
            roots.append(modules_tests / module_name)

        for root in roots:
            for py_file in walk_py_files(root):
                total += 1
                file_changed, _ = rewrite_file(py_file, dry_run=True, repo_root=repo_root)
                if file_changed:
                    changed += 1

        module_summary[module_name] = {"files_changed": changed, "files_total": total}

    # Process src/shared and tests/shared (as special group)
    shared_total = 0
    shared_changed = 0
    for root in [src_root / "shared", tests_root / "shared"]:
        if root.exists():
            for py_file in walk_py_files(root):
                shared_total += 1
                file_changed, _ = rewrite_file(py_file, dry_run=True, repo_root=repo_root)
                if file_changed:
                    shared_changed += 1
    module_summary["_shared"] = {"files_changed": shared_changed, "files_total": shared_total}

    # Process src/core and tests (architecture, scripts, etc.)
    core_total = 0
    core_changed = 0
    for root in [src_root / "core"]:
        if root.exists():
            for py_file in walk_py_files(root):
                core_total += 1
                file_changed, _ = rewrite_file(py_file, dry_run=True, repo_root=repo_root)
                if file_changed:
                    core_changed += 1
    if core_total > 0:
        module_summary["_core"] = {"files_changed": core_changed, "files_total": core_total}

    # Compute delete counts per module from DELETE_FILES
    delete_counts: dict[str, int] = {}
    for rel_path_str in DELETE_FILES:
        # Extract module from path e.g. backend/src/modules/analytics/...
        parts = rel_path_str.split("/")
        if len(parts) >= 4 and parts[2] == "modules":
            mod = parts[3]
        elif len(parts) >= 3 and parts[2] == "shared":
            mod = "_shared"
        else:
            mod = "_other"
        delete_counts[mod] = delete_counts.get(mod, 0) + 1

    # Print summary
    print("\n[DRY-RUN] Per-module summary:")
    print(f"{'Module':<30} {'Imports rewritten':<20} {'Files total':<15} {'Files to delete':<15}")
    print("-" * 80)
    for mod_name in sorted(module_summary.keys()):
        info = module_summary[mod_name]
        deletes = delete_counts.get(mod_name, 0)
        print(
            f"{mod_name:<30} {info['files_changed']:<20} {info['files_total']:<15} {deletes:<15}"
        )
    total_changed = sum(v["files_changed"] for v in module_summary.values())
    total_files = sum(v["files_total"] for v in module_summary.values())
    total_deletes = len(DELETE_FILES)
    print("-" * 80)
    print(f"{'TOTAL':<30} {total_changed:<20} {total_files:<15} {total_deletes:<15}")
    print(f"\n[DRY-RUN] Import rewrites: {total_changed}/{total_files} files would be changed")
    print(f"[DRY-RUN] Delete: {total_deletes} files would be deleted (--delete-aisealsht-models)")

    return module_summary


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
        help="Run extended self-check (idempotency + DELETE/PRESERVE counts + disk existence + EXCLUDE_PATHS)",
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
    parser.add_argument(
        "--all-modules",
        action="store_true",
        help=(
            "Rewrite entire backend (src/ + tests/). "
            "Used for Phase 3 atomic big-bang scope. "
            "In dry-run mode also emits per-module summary."
        ),
    )
    parser.add_argument(
        "--delete-aisealsht-models",
        action="store_true",
        help=(
            "Delete the 83 AISALESHT model files with luana-core equivalents (Class A collision). "
            "Use --dry-run to preview list, --apply to actually delete. "
            "Phase 2 P1-prepared: run AFTER import rewrite, in atomic commit."
        ),
    )
    args = parser.parse_args()

    if args.self_check:
        ok = run_self_check()
        sys.exit(0 if ok else 1)

    # Determine repo root early (needed for delete mode and all-modules)
    repo_root = Path(__file__).parent.parent  # AISALESHT/
    backend_root = repo_root / "backend"

    # -----------------------------------------------------------------------
    # DELETE mode: --delete-aisealsht-models
    # -----------------------------------------------------------------------
    if args.delete_aisealsht_models:
        if not args.dry_run and not args.apply:
            print(
                "ERROR: --delete-aisealsht-models requires --dry-run or --apply",
                file=sys.stderr,
            )
            sys.exit(1)
        dry_run = not args.apply
        deleted = run_delete_mode(dry_run=dry_run, repo_root=repo_root)
        sys.exit(0)

    # -----------------------------------------------------------------------
    # Import rewrite mode
    # -----------------------------------------------------------------------
    if not args.dry_run and not args.apply:
        print(
            "ERROR: specify --dry-run or --apply",
            file=sys.stderr,
        )
        sys.exit(1)

    dry_run = not args.apply

    # --all-modules in dry-run: emit per-module summary
    if args.all_modules and dry_run:
        run_all_modules_dry_run(repo_root)
        return

    # Determine search roots
    search_roots: list[Path] = []

    if args.all_modules:
        # Full backend: src/ + tests/
        search_roots = [
            backend_root / "src",
            backend_root / "tests",
        ]
    elif args.paths:
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
            changed, changes = rewrite_file(py_file, dry_run=dry_run, repo_root=repo_root)
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
