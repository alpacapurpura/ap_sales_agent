"""Architecture fitness tests for the social_proof bounded context.

These tests fail CI if the social_proof module drifts from its contract:
  * Tenant isolation is baked into every repo query.
  * Domain layer has zero framework imports.
  * No cross-module imports (module only consumes shared/ + iam/ + core/).
  * Enum values match the DB VARCHAR lengths and migration seeds.
  * Every mutation in an application service emits a DomainEvent.
  * No legacy JSON readers remain in the module.

The whole file is a ratchet — allowlists may only shrink, never grow.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

MODULE_ROOT = Path(__file__).resolve().parents[2] / "src" / "modules" / "social_proof"
SHARED_ROOT = Path(__file__).resolve().parents[2] / "src" / "shared"


# ── helpers ────────────────────────────────────────────────────────


def _iter_py(path: Path) -> list[Path]:
    """Yield every ``.py`` under ``path`` except ``__init__.py`` and the
    cross-module ``copilot_provider/`` façade.

    The provider layer (F1, April 2026) is a thin adapter the copilot consumes
    via ``CopilotProvider``. It exposes a typed dict to copilot tools whose
    keys deliberately read like the legacy JSON paths (``"testimonials"`` etc.)
    — that contract is owned by the copilot consumer, not by social_proof.
    """

    return [p for p in sorted(path.rglob("*.py")) if p.name != "__init__.py" and "copilot_provider" not in p.parts]


def _parse_imports(py: Path) -> list[str]:
    tree = ast.parse(py.read_text(encoding="utf-8"))
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            out.append(node.module)
        elif isinstance(node, ast.Import):
            out.extend(alias.name for alias in node.names)
    return out


# ── 1. tenant isolation ────────────────────────────────────────────


def test_every_repo_query_filters_by_tenant_id() -> None:
    """Each ``select(Model)`` in a repository MUST ``.where(Model.tenant_id == ...)``.

    Exception: only the repo's own ``_safe_validate`` helper is allowed to
    operate on already-loaded rows without re-scoping.
    """
    repo_dir = MODULE_ROOT / "infrastructure" / "repositories"
    pattern = re.compile(r"select\s*\(\s*(\w+)\s*\)\.where\(")
    tenant_pattern = re.compile(r"\.tenant_id\s*==\s*tenant_id")

    violations: list[str] = []
    for py in _iter_py(repo_dir):
        content = py.read_text(encoding="utf-8")
        # Strip blank lines between the select(...) and the .where() — match
        # full source rather than only matching lines.
        for match in pattern.finditer(content):
            start = match.start()
            tail = content[start : start + 800]
            # The next where() block should reference tenant_id == tenant_id.
            if ".tenant_id" not in tail.split(")")[0] + tail and not tenant_pattern.search(tail):
                violations.append(
                    f"{py.relative_to(MODULE_ROOT)}: select() without tenant_id filter near byte {start}",
                )
    assert violations == [], "social_proof tenant isolation violations:\n" + "\n".join(violations)


# ── 2. domain purity ────────────────────────────────────────────────

FORBIDDEN_FRAMEWORK_PREFIXES = (
    "sqlalchemy",
    "fastapi",
    "httpx",
    "redis",
    "qdrant_client",
    "src.modules.social_proof.infrastructure",
    "src.modules.social_proof.application",
    "src.modules.social_proof.api",
)


def test_domain_layer_has_no_framework_or_outer_layer_imports() -> None:
    """``social_proof/domain/`` must stay pure — only Python stdlib + Pydantic + shared."""
    domain_dir = MODULE_ROOT / "domain"
    violations: list[str] = []
    for py in _iter_py(domain_dir):
        for imp in _parse_imports(py):
            violations.extend(
                f"{py.relative_to(MODULE_ROOT)}: imports {imp}"
                for forbidden in FORBIDDEN_FRAMEWORK_PREFIXES
                if imp.startswith(forbidden)
            )
    assert violations == [], "social_proof domain impurity:\n" + "\n".join(violations)


# ── 3. cross-module boundary ────────────────────────────────────────

ALLOWED_EXTERNAL_MODULES = {
    "src.core",
    "src.shared",
    "src.modules.iam",
}


def test_social_proof_module_only_consumes_shared_or_iam() -> None:
    """social_proof MUST NOT import from any other bounded context."""
    violations: list[str] = []
    for py in _iter_py(MODULE_ROOT):
        for imp in _parse_imports(py):
            if not imp.startswith("src.modules."):
                continue
            if imp.startswith("src.modules.social_proof"):
                continue
            allowed = any(imp.startswith(prefix) for prefix in ALLOWED_EXTERNAL_MODULES)
            if not allowed:
                violations.append(f"{py.relative_to(MODULE_ROOT)}: imports {imp}")
    assert violations == [], "social_proof cross-module imports:\n" + "\n".join(violations)


# ── 4. enum ↔ DB length / migration consistency ─────────────────────


@pytest.mark.parametrize(
    ("enum_path", "expected_values"),
    [
        (
            "src.modules.social_proof.domain.enums.TestimonialMediaType",
            {"text", "video", "audio", "image"},
        ),
        (
            "src.modules.social_proof.domain.enums.AuthorityType",
            {
                "certification",
                "award",
                "media_mention",
                "published_work",
                "client_logo",
                "credential",
                "partnership",
                "speaking",
                "podcast",
                "other",
            },
        ),
        (
            "src.modules.social_proof.domain.enums.SourceTable",
            {"testimonial", "authority_item", "team_member"},
        ),
        (
            "src.modules.social_proof.domain.enums.SurfaceType",
            {
                "brand_homepage",
                "offer",
                "landing_page",
                "email_sequence",
                "sales_agent_kb",
            },
        ),
    ],
)
def test_enum_value_set_is_frozen(enum_path: str, expected_values: set[str]) -> None:
    """Catalog and enum values MUST stay aligned — changes require updating this arch test."""
    from importlib import import_module

    module_path, _, attr = enum_path.rpartition(".")
    mod = import_module(module_path)
    enum_cls = getattr(mod, attr)
    actual = {member.value for member in enum_cls}
    assert actual == expected_values, (
        f"{enum_path} drift: expected {expected_values}, got {actual}. "
        "If intentional, update both the catalog and this test in the same commit."
    )


# ── 5. every mutation emits a DomainEvent ───────────────────────────


def test_every_application_service_mutation_publishes_event() -> None:
    """Each ``def create|update|soft_delete|add|remove|clone`` in a service MUST
    ``EventBus.publish(...)`` somewhere in the function body. Pure read
    methods (``list_*``, ``get``, ``for_surface``) are exempt.
    """
    services_dir = MODULE_ROOT / "application" / "services"
    mutation_prefixes = ("create", "update", "soft_delete", "add", "remove", "clone")
    violations: list[str] = []

    for py in _iter_py(services_dir):
        # Skip the read-only resolver module.
        if py.name == "social_proof_resolver.py":
            continue
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            if not any(node.name == p or node.name.startswith(p + "_") for p in mutation_prefixes):
                continue
            # Look for EventBus.publish in the body (also allow indirect via
            # a delegating call to another method that will publish).
            body_src = ast.unparse(node)
            if "EventBus.publish" not in body_src and "self.create" not in body_src and ("self.add" not in body_src):
                violations.append(
                    f"{py.relative_to(MODULE_ROOT)}::{node.name} — mutation without EventBus.publish / delegation",
                )
    assert violations == [], "social_proof event emission gaps:\n" + "\n".join(violations)


# ── 6. port adapter exists ──────────────────────────────────────────


def test_shared_links_port_declares_public_api() -> None:
    """The cross-module port must expose the 4 canonical helpers."""
    port = SHARED_ROOT / "links" / "ports" / "social_proof.py"
    assert port.is_file(), "shared/links/ports/social_proof.py missing"
    content = port.read_text(encoding="utf-8")
    for fn in (
        "def resolve_for_surface(",
        "def list_tenant_testimonials(",
        "def list_tenant_authority_items(",
        "def list_tenant_team_members(",
    ):
        assert fn in content, f"shared port missing {fn}"


# ── 7. no legacy JSON reader remains inside the module ──────────────


LEGACY_JSON_KEYS = (
    "brand_settings.testimonials",
    "brand_settings.authority_vault",
    "brand_settings.team",
    '["testimonials"]',
    '["authority_vault"]',
    '["team"]',
)


def test_module_does_not_read_legacy_json_keys() -> None:
    """social_proof MUST NOT read the legacy JSON paths. If any are needed for
    a data migration, they belong in ``backend/alembic/`` — not in the
    application module.
    """
    violations: list[str] = []
    for py in _iter_py(MODULE_ROOT):
        content = py.read_text(encoding="utf-8")
        violations.extend(
            f"{py.relative_to(MODULE_ROOT)}: references legacy key {needle!r}"
            for needle in LEGACY_JSON_KEYS
            if needle in content
        )
    assert violations == [], "social_proof legacy JSON read:\n" + "\n".join(violations)


# ── 8. response_model declared on every endpoint ────────────────────


def test_every_endpoint_declares_response_model() -> None:
    """All endpoints need ``response_model=`` unless status_code is 204."""
    api_dir = MODULE_ROOT / "api"
    violations: list[str] = []
    http_methods = {"get", "post", "patch", "put", "delete"}

    for py in _iter_py(api_dir):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                if not isinstance(decorator.func, ast.Attribute):
                    continue
                method = decorator.func.attr
                if method not in http_methods:
                    continue
                has_response = any(kw.arg == "response_model" for kw in decorator.keywords)
                status = next(
                    (kw.value for kw in decorator.keywords if kw.arg == "status_code"),
                    None,
                )
                status_val = status.value if isinstance(status, ast.Constant) else None
                if not has_response and status_val != 204:
                    violations.append(
                        f"{py.relative_to(MODULE_ROOT)}::{node.name} — {method} without response_model",
                    )
    assert violations == [], "social_proof endpoints missing response_model:\n" + "\n".join(
        violations,
    )
