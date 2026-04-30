"""Architectural fitness — tenant isolation en queries SQLA del módulo campaigns.

AST scan: toda ``select(CampaignModel | CampaignTaskModel | SegmentModel ...)``
en ``infrastructure/repositories/`` DEBE filtrar por ``Model.tenant_id == ...``
en la misma statement.

Excepciones documentadas (frozenset shrink-only):
- ``claim_pending_for_worker`` — worker cross-tenant scope (FOR UPDATE SKIP LOCKED,
  mismo patrón outbox). Documentado en docstring del repo impl.
- ``list_globals`` — campaign_template.tenant_id NULL semantics (global templates).
  Documentado en docstring del CampaignTemplateRepository.

Ratchet pattern: nuevas queries cross-tenant requieren entry en
``CROSS_TENANT_ALLOWED_METHODS`` + razón documentada en docstring del método.

# [CAMPAIGNS-TENANT-ISOLATION-PR3-S1]
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CAMPAIGNS_REPOS_DIR = REPO / "src" / "modules" / "campaigns" / "infrastructure" / "repositories"

# Modelos que deben tener tenant_id filtrado en toda query directa.
TENANT_SCOPED_MODELS: frozenset[str] = frozenset(
    {
        "CampaignModel",
        "CampaignStepModel",
        "CampaignTaskModel",
        "SegmentModel",
        "SegmentSnapshotModel",
        # CampaignTemplateModel: tenant_id es nullable (global=NULL).
        # Las queries sobre este modelo PUEDEN ser cross-tenant legítimamente.
        # No incluido aquí — su aislamiento se valida en lógica de negocio PR-4.
    }
)

# Métodos permitidos de hacer queries cross-tenant.
# Ratchet shrink-only: jamás agregar sin razón documentada.
CROSS_TENANT_ALLOWED_METHODS: frozenset[str] = frozenset(
    {
        # Worker scope cross-tenant: polls tasks FOR UPDATE SKIP LOCKED sin tenant filter.
        # Razón: worker único procesa tareas de múltiples tenants. Mismo patrón que
        # domain_event_outbox.claim_pending. Documentado en CampaignTaskRepositoryImpl.
        "claim_pending_for_worker",
        # Global templates: campaign_template.tenant_id NULL = Nicolify-provided.
        # list_globals hace SELECT WHERE tenant_id IS NULL — no aplica tenant filter.
        # Documentado en CampaignTemplateRepository.
        "list_globals",
    }
)


def _enclosing_function_name(tree: ast.Module, lineno: int) -> str | None:
    """Retorna el nombre de la función que contiene ``lineno``, o None."""
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        end = getattr(node, "end_lineno", None)
        if end is None:
            continue
        if node.lineno <= lineno <= end:
            return node.name
    return None


def _is_select_of_tenant_scoped_model(call: ast.Call) -> str | None:
    """Si ``call`` es ``select(TenantScopedModel, ...)``, retorna el model name."""
    func = call.func
    if isinstance(func, ast.Name) and func.id == "select":
        for arg in call.args:
            target = arg if isinstance(arg, ast.Name) else getattr(arg, "value", None)
            if isinstance(target, ast.Name) and target.id in TENANT_SCOPED_MODELS:
                return target.id
    return None


def _statement_contains_tenant_id_filter(stmt: ast.AST, model_name: str) -> bool:
    """¿``stmt`` tiene ``Compare`` con ``Model.tenant_id == ...``?"""
    for node in ast.walk(stmt):
        if not isinstance(node, ast.Compare):
            continue
        sides = [node.left, *node.comparators]
        for side in sides:
            if (
                isinstance(side, ast.Attribute)
                and side.attr == "tenant_id"
                and isinstance(side.value, ast.Name)
                and side.value.id == model_name
            ):
                return True
    return False


def _enclosing_statement(tree: ast.Module, lineno: int) -> ast.AST | None:
    """Encuentra la statement más anidada que contiene ``lineno``."""
    candidate: ast.AST | None = None
    for node in ast.walk(tree):
        if not isinstance(node, ast.stmt):
            continue
        end = getattr(node, "end_lineno", None)
        if end is None or not node.lineno <= lineno <= end:
            continue
        if candidate is None or end - node.lineno < getattr(candidate, "end_lineno", 0) - candidate.lineno:
            candidate = node
    return candidate


def _violations_in_file(path: Path) -> list[tuple[int, str, str | None]]:
    """Returns list of (lineno, model_name, func_name) for violations."""
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    offenders: list[tuple[int, str, str | None]] = []

    for call in ast.walk(tree):
        if not isinstance(call, ast.Call):
            continue
        model = _is_select_of_tenant_scoped_model(call)
        if model is None:
            continue

        # Skip si el método está allowlisteado.
        fn_name = _enclosing_function_name(tree, call.lineno)
        if fn_name in CROSS_TENANT_ALLOWED_METHODS:
            continue

        stmt = _enclosing_statement(tree, call.lineno)
        if stmt is None or not _statement_contains_tenant_id_filter(stmt, model):
            offenders.append((call.lineno, model, fn_name))

    return offenders


class TestCampaignsTenantIsolation:
    """Tenant isolation fitness tests for campaigns repositories."""

    def test_every_query_filters_tenant_id(self) -> None:
        """Toda query sobre modelos tenant-scoped debe filtrar por tenant_id."""
        assert CAMPAIGNS_REPOS_DIR.exists(), (
            f"Campaigns repositories dir not found: {CAMPAIGNS_REPOS_DIR}. Verificar que Sub-C está commited."
        )
        all_offenders: list[str] = []
        for py in CAMPAIGNS_REPOS_DIR.rglob("*.py"):
            for lineno, model, fn_name in _violations_in_file(py):
                rel = py.relative_to(REPO).as_posix()
                all_offenders.append(f"{rel}:{lineno}  select({model}, ...) en fn={fn_name!r} sin filtro tenant_id")
        assert not all_offenders, (
            "Cada query sobre modelos campaigns debe filtrar por tenant_id. "
            "Para métodos cross-tenant intencionales (worker, globals), agregar a "
            "CROSS_TENANT_ALLOWED_METHODS con razón documentada.\n"
            "Violations:\n  - " + "\n  - ".join(all_offenders)
        )

    def test_cross_tenant_allowlist_methods_exist_in_codebase(self) -> None:
        """Ratchet: allowlist entries deben corresponder a métodos reales."""
        all_method_names: set[str] = set()
        for py in CAMPAIGNS_REPOS_DIR.rglob("*.py"):
            src = py.read_text(encoding="utf-8")
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    all_method_names.add(node.name)

        stale: list[str] = []
        for method in CROSS_TENANT_ALLOWED_METHODS:
            if method not in all_method_names:
                stale.append(method)

        assert not stale, (
            "CROSS_TENANT_ALLOWED_METHODS contiene métodos que ya no existen. Shrink the allowlist: " + str(stale)
        )
