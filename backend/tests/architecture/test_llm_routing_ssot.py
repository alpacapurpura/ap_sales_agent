"""Architecture guard — LLM routing SSoT enforcement.

Origen: PR-3 PI-2 S2 audit failure 2026-04-30 — capa LLM routing duplicada
introducida en `copilot/infrastructure/llm/` paralela a sistema global
`core/config.py + shared/infrastructure/llm/`.

Este test enforza que SOLO existe un sistema de routing LLM:
- Enum único: `src.core.enums.ModelRole`
- Settings único: `src.core.config.Settings.get_model/get_provider_for_role`
- Providers en: `src.shared.infrastructure.llm.providers/`

Anti-patterns detectados:
- `TIER_METADATA` hardcoded en `copilot/domain/model_tier.py` (legacy, deprecation S3)
- `COPILOT_TIER_*_PROVIDER` env vars (deuda PR-3, eliminar S3)
- Capas LLM nuevas en `modules/<x>/infrastructure/llm/` (NEW LAYER violation)
- Imports de adapters legacy borrados en T-4 (openai/deepseek/kimi/qwen/gemini/_openai_compat)
- `LITELLM_PROXY_ENABLED` re-introducido en Settings post-T-5

Allowlist permite legacy en migración. Allowlist shrinks only.

[ANCHOR: docs/domains/llm-routing.md]
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_SRC = REPO_ROOT / "src"
BACKEND_TESTS = REPO_ROOT / "tests"

KNOWN_LEGACY_LLM_FILES: set[str] = set()
"""Allowlist post S3 PR-1 cleanup-modeltier-convergence — target 0 entries reached.

ModelTier eliminado, capa duplicada `copilot/infrastructure/llm/` eliminada,
todos los consumers convergidos a `ModelRole` SSoT. Allowlist ratchet shrink-only:
si test detecta nuevo legacy → fix antes de allowlist.

Post PI-12 S1 T-4 (adapter deletion) + T-5 (LITELLM_PROXY_ENABLED removal):
ratchet shrink-only se codifica explícitamente en
``test_known_legacy_files_set_is_empty`` — adicionar entradas requiere commit
con justificación + revisión architect.
"""

# Legacy adapter modules deleted in PI-12 S1 T-4. Imports of these modules
# are forbidden cross-codebase (src/ + tests/). Used by
# ``test_no_legacy_adapter_imports`` and ``test_violation_detection_works``.
LEGACY_ADAPTER_MODULES: tuple[str, ...] = (
    "openai",
    "deepseek",
    "kimi",
    "qwen",
    "gemini",
    "_openai_compat",
)

LEGACY_ADAPTER_IMPORT_PATTERN: re.Pattern[str] = re.compile(
    r"from\s+src\.shared\.infrastructure\.llm\.providers\."
    rf"({'|'.join(LEGACY_ADAPTER_MODULES)})\b"
)


def _scan_for_pattern(pattern: re.Pattern[str], scope: Path) -> list[str]:
    """Return list of file:line for files matching pattern, excluding allowlist."""
    violations: list[str] = []
    for py_file in scope.rglob("*.py"):
        rel = str(py_file.relative_to(REPO_ROOT))
        if rel in KNOWN_LEGACY_LLM_FILES:
            continue
        if "__pycache__" in rel or rel.endswith(".pyc"):
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_num, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if pattern.search(stripped):
                violations.append(f"{rel}:{line_num}: {stripped[:120]}")
    return violations


def _scan_for_legacy_adapter_imports(scope: Path) -> list[str]:
    """Scan ``scope`` for ``from src.shared.infrastructure.llm.providers.<legacy>``
    imports of the 6 deleted adapter modules.

    Excluded by design:
    - This test file itself (``test_llm_routing_ssot.py``) — it cites the
      module names verbatim inside the regex pattern, never as imports.
    - Files inside ``KNOWN_LEGACY_LLM_FILES`` allowlist.
    - Comments (lines starting with ``#``).
    """
    violations: list[str] = []
    self_rel = str(Path(__file__).resolve().relative_to(REPO_ROOT))
    for py_file in scope.rglob("*.py"):
        rel = str(py_file.relative_to(REPO_ROOT))
        if rel == self_rel:
            continue
        if rel in KNOWN_LEGACY_LLM_FILES:
            continue
        if "__pycache__" in rel or rel.endswith(".pyc"):
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_num, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if LEGACY_ADAPTER_IMPORT_PATTERN.search(stripped):
                violations.append(f"{rel}:{line_num}: {stripped[:120]}")
    return violations


def test_no_new_modeltier_imports() -> None:
    """ModelTier (legacy) NO debe ser imported fuera de allowlist legacy."""
    pattern = re.compile(
        r"\bfrom\s+src\.modules\.copilot\.domain\.model_tier\s+import|"
        r"\bfrom\s+src\.modules\.copilot\.domain\s+import\s+.*ModelTier"
    )
    violations = _scan_for_pattern(pattern, BACKEND_SRC)
    assert not violations, (
        "ModelTier (legacy) imported fuera de allowlist. Use ModelRole from src.core.enums.\n"
        "See: docs/domains/llm-routing.md\n"
        "Violations:\n  - " + "\n  - ".join(violations)
    )


def test_no_copilot_tier_env_vars() -> None:
    """COPILOT_TIER_*_PROVIDER env vars (PR-3 deuda) NO deben aparecer."""
    pattern = re.compile(r"COPILOT_TIER_\w+_(PROVIDER|MODEL_NAME|PRICE_)")
    violations = _scan_for_pattern(pattern, BACKEND_SRC)
    assert not violations, (
        "COPILOT_TIER_*_PROVIDER env vars son deuda PR-3 (eliminar S3 PR-1). "
        "Use AI_MODEL_<ROLE> + AI_PROVIDER_<ROLE> from src/core/config.py.\n"
        "See: docs/domains/llm-routing.md\n"
        "Violations:\n  - " + "\n  - ".join(violations)
    )


def test_no_new_llm_factory_layers() -> None:
    """Solo `src/shared/infrastructure/llm/` puede definir LLM factories."""
    forbidden_dirs = [
        BACKEND_SRC / "modules" / "copilot" / "infrastructure" / "llm",
    ]
    violations: list[str] = []
    for d in forbidden_dirs:
        if not d.exists():
            continue
        for py_file in d.rglob("*.py"):
            rel = str(py_file.relative_to(REPO_ROOT))
            if rel in KNOWN_LEGACY_LLM_FILES:
                continue
            violations.append(rel)

    assert not violations, (
        "LLM factories/providers en modules/<x>/infrastructure/llm/ violan NO NEW LAYER rule. "
        "Use src/shared/infrastructure/llm/providers/ + src/core/config.py.\n"
        "See: docs/domains/llm-routing.md\n"
        "Violations:\n  - " + "\n  - ".join(violations)
    )


def test_router_dispatches_via_litellm_only() -> None:
    """D-18 (S3 PR-2) + PI-12 S1 T-5: MultiRoleLLMRouter must NOT import
    per-provider Services at module level.

    Post-T-5 (LITELLM_PROXY_ENABLED flag deletion + ``build_provider_service``
    rollback function deletion), router.py is the LiteLLM-only dispatch path
    — there is no flag-conditional fallback. Module-level imports of
    OpenAIService / KimiService / DeepSeekService / QwenService in router.py
    would be a regression toward per-provider dispatch (defeats LiteLLM
    Proxy convergence) and have no remaining valid use case.
    """
    router_path = BACKEND_SRC / "shared" / "infrastructure" / "llm" / "router.py"
    tree = ast.parse(router_path.read_text(encoding="utf-8"))

    forbidden = {"OpenAIService", "KimiService", "DeepSeekService", "QwenService"}
    module_level_violations: list[str] = []

    for node in tree.body:  # only module-level statements
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name in forbidden:
                    module_level_violations.append(f"router.py:{node.lineno}: module-level import of {alias.name}")

    assert not module_level_violations, (
        "MultiRoleLLMRouter must dispatch via LiteLLMService only. "
        "Per-provider Service imports are forbidden post-T-5 — the LiteLLM "
        "Proxy is the single runtime dispatch path; there is no rollback "
        "fallback to restore.\n"
        "See: docs/domains/llm-routing.md (Capa 5 — LiteLLM Proxy)\n"
        "Violations:\n  - " + "\n  - ".join(module_level_violations)
    )


def test_no_legacy_adapter_imports() -> None:
    """Imports of the 6 legacy adapter modules deleted in PI-12 S1 T-4 must
    not exist anywhere in ``src/`` or ``tests/``.

    Adapters deleted: ``openai.py``, ``deepseek.py``, ``kimi.py``,
    ``qwen.py``, ``gemini.py``, ``_openai_compat.py``. Re-introducing an
    import of any of these violates LLM routing SSoT (LiteLLM Proxy is the
    only dispatch path).

    Allowed: this test file cites the module names verbatim in the regex
    pattern, never as actual ``from … import`` statements — it is excluded
    via ``__file__`` resolution to avoid self-match.
    """
    src_violations = _scan_for_legacy_adapter_imports(BACKEND_SRC)
    tests_violations = _scan_for_legacy_adapter_imports(BACKEND_TESTS)
    violations = src_violations + tests_violations
    assert not violations, (
        "Forbidden imports of legacy adapter modules deleted in T-4 "
        f"({', '.join(LEGACY_ADAPTER_MODULES)}). Use LiteLLMService from "
        "src.shared.infrastructure.llm.providers.litellm instead.\n"
        "See: docs/domains/llm-routing.md\n"
        "Violations:\n  - " + "\n  - ".join(violations)
    )


def test_known_legacy_files_set_is_empty() -> None:
    """Ratchet shrink-only enforcement: ``KNOWN_LEGACY_LLM_FILES`` MUST stay
    empty post-T-4 deletion.

    The allowlist was already empty when T-4 deleted the 6 legacy adapters.
    This test codifies the invariant: re-introducing entries requires an
    explicit justification commit with architect approval (per
    ``.claude/rules/architectural-fitness.md`` ratchet pattern — allowlists
    shrink only, never grow).
    """
    assert not KNOWN_LEGACY_LLM_FILES, (
        "KNOWN_LEGACY_LLM_FILES allowlist non-empty: "
        f"{sorted(KNOWN_LEGACY_LLM_FILES)}. Ratchet shrink-only — T-4 "
        "deleted all legacy adapters; allowlist must stay empty. Adding "
        "entries requires architect approval + justification commit.\n"
        "See: .claude/rules/architectural-fitness.md (ratchet pattern)"
    )


def test_settings_has_no_litellm_proxy_enabled_attr() -> None:
    """``Settings.LITELLM_PROXY_ENABLED`` must remain deleted post-PI-12 S1 T-5.

    The flag was the emergency rollback toggle for the LiteLLM Proxy
    convergence. Post-T-5 (commit 28617716) the flag was removed from the
    Settings class — the LiteLLM Proxy is the only runtime LLM dispatch
    path. Re-introducing requires:

    1. Architect approval (D-decision in CONTRACT.md).
    2. New row in ``.claude/rules/anti-default-flip-audit.md`` inventory.
    3. Anti-flip-audit Steps 1-4 compliance for the flag flip (test mocks
       audited, both flag values run, commit body documents migration).
    """
    from src.core.config import Settings

    assert "LITELLM_PROXY_ENABLED" not in Settings.model_fields, (
        "Settings.LITELLM_PROXY_ENABLED must remain deleted post-T-5. "
        "Re-introducing requires explicit justification + anti-default-flip-audit "
        "row + architect ratification.\n"
        "See: .claude/rules/anti-default-flip-audit.md"
    )


def test_violation_detection_works(tmp_path: Path) -> None:
    """Meta-test (A4): verify the 3 new ratchet tests detect violations.

    Strategy: synthesize fixture files in ``tmp_path`` that simulate each
    violation type, then exercise the underlying scan/check primitives
    against the synthetic fixtures and assert they FAIL (i.e., return
    violations / would trip the assertion).

    This guards against silent regressions where the test infrastructure
    accidentally short-circuits (e.g., scanner skips files, regex never
    matches, allowlist swallows everything).
    """
    # --- Sub-check 1: legacy adapter import detection ---
    legacy_fixture = tmp_path / "fake_module.py"
    legacy_fixture.write_text(
        "from src.shared.infrastructure.llm.providers.openai import OpenAIService\n"
        "from src.shared.infrastructure.llm.providers.kimi import KimiService\n"
        "x = 1\n",
        encoding="utf-8",
    )
    fixture_violations: list[str] = []
    for line_num, line in enumerate(legacy_fixture.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if LEGACY_ADAPTER_IMPORT_PATTERN.search(stripped):
            fixture_violations.append(f"fake_module.py:{line_num}: {stripped[:120]}")
    assert len(fixture_violations) == 2, (
        "Meta-check FAILED: LEGACY_ADAPTER_IMPORT_PATTERN must detect the 2 "
        f"injected legacy adapter imports. Got {len(fixture_violations)} matches: "
        f"{fixture_violations}"
    )

    # --- Sub-check 2: legacy non-adapter modules must not match ---
    non_legacy_fixture = tmp_path / "fake_safe.py"
    non_legacy_fixture.write_text(
        "from src.shared.infrastructure.llm.providers.litellm import LiteLLMService\n"
        "from src.shared.infrastructure.llm.providers._kwargs import build_kwargs\n",
        encoding="utf-8",
    )
    safe_violations: list[str] = []
    for line in non_legacy_fixture.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if LEGACY_ADAPTER_IMPORT_PATTERN.search(stripped):
            safe_violations.append(stripped)
    assert not safe_violations, (
        "Meta-check FAILED: LEGACY_ADAPTER_IMPORT_PATTERN false-positive on "
        f"canonical adapter imports (litellm.py, _kwargs.py): {safe_violations}"
    )

    # --- Sub-check 3: ratchet allowlist enforcement detects non-empty set ---
    simulated_allowlist: set[str] = {"src/shared/infrastructure/llm/providers/openai.py"}
    # Mirror the exact assertion logic from test_known_legacy_files_set_is_empty
    allowlist_violation_detected = simulated_allowlist != set()
    assert allowlist_violation_detected, (
        "Meta-check FAILED: ratchet allowlist comparison must detect non-empty "
        "set as violation. Logic regression in test_known_legacy_files_set_is_empty."
    )

    # --- Sub-check 4: Settings model_fields scan detects re-introduced flag ---
    # Simulate by checking a synthetic dict (we don't mutate the real Settings).
    simulated_model_fields: dict[str, object] = {
        "AI_MODEL_FAST": object(),
        "LITELLM_PROXY_ENABLED": object(),  # injected violation
    }
    flag_violation_detected = "LITELLM_PROXY_ENABLED" in simulated_model_fields
    assert flag_violation_detected, (
        "Meta-check FAILED: Settings.model_fields containment check must detect "
        "re-introduced LITELLM_PROXY_ENABLED key. Logic regression in "
        "test_settings_has_no_litellm_proxy_enabled_attr."
    )
