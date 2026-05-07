"""Regression tests for the sales-agent-expert skill audit (T-1).

Validates that the skill SSoT reflects live code reality post-homologization
with copilot (May 2026). Tests are pure filesystem + regex + AST — no DB,
no network, no LLM calls.

Scenarios covered:
  1 (happy)       — paths resolve or have OBSOLETO: marker
  2 (negative)    — OBSOLETO: marker always has inline reason
  3 (edge)        — shared/agent_observability consumers documented
  4 (adversarial) — no self-contradiction; contradiction detector works

AD1 — Single test file, no exotic markdown parsers.
AD5 — OBSOLETO: marker regex: ^OBSOLETO:\\s*(.+?)\\s*[—:→]\\s*(.+)$
AD6 — production_code=false (R23); zero src/ touches.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from collections.abc import Callable

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "sales-agent-expert"
SKILL_MD = SKILL_DIR / "SKILL.md"
REFERENCES_DIR = SKILL_DIR / "references"
IMPL_LOG = REPO_ROOT / "docs" / "product" / "stories" / "maintenance-skill-sales-agent-audit" / "T-1-impl-log.md"

REFERENCE_FILES = [
    REFERENCES_DIR / "conversation-stages.md",
    REFERENCES_DIR / "humanization-rules.md",
    REFERENCES_DIR / "sales-agent-brand-voice.md",
    REFERENCES_DIR / "tool-patterns.md",
]

# Regex: OBSOLETO: <symbol> [—:→] <reason>
OBSOLETO_FULL_RE = re.compile(r"^OBSOLETO:\s*(.+?)\s*[—:→]\s*(.+)$", re.MULTILINE)
OBSOLETO_PREFIX_RE = re.compile(r"^OBSOLETO:", re.MULTILINE)


# ---------------------------------------------------------------------------
# Helper check functions (module-level, avoids PLW0108 lambda warning)
# ---------------------------------------------------------------------------


def _path_in_src(relative: str) -> bool:
    """Return True if path exists under backend/src/."""
    return (REPO_ROOT / "backend" / "src" / relative).exists()


def _text_in_src_py(needle: str, subdir: str = "") -> bool:
    """Return True if needle appears in any .py file under backend/src/{subdir}."""
    base = REPO_ROOT / "backend" / "src"
    if subdir:
        base = base / subdir
    return any(needle in f.read_text(errors="ignore") for f in base.rglob("*.py"))


def _text_in_alembic(needle: str, name_filter: str = "") -> bool:
    """Return True if needle appears in any alembic version file matching name_filter."""
    versions = REPO_ROOT / "backend" / "alembic" / "versions"
    files = versions.glob("*.py")
    if name_filter:
        files = (f for f in files if name_filter in f.name.lower())  # type: ignore[assignment]
    return any(needle in f.read_text(errors="ignore") for f in files)


def _path_in_docs(relative: str) -> bool:
    """Return True if path exists under docs/."""
    return (REPO_ROOT / "docs" / relative).exists()


# ---------------------------------------------------------------------------
# Paths/symbols extracted from SKILL.md that must either resolve or have
# OBSOLETO: marker. Format: (description, Callable[[], bool])
# ---------------------------------------------------------------------------

SKILL_SYMBOLS: list[tuple[str, Callable[[], bool]]] = [
    # domain paths
    (
        "domain/model_tier.py::SPECIALIST_TO_ROLE",
        lambda: _path_in_src("modules/sales_agent/domain/model_tier.py"),
    ),
    (
        "domain/model_tier.py::LLM_ROLE_BY_SITE",
        lambda: _path_in_src("modules/sales_agent/domain/model_tier.py"),
    ),
    (
        "application/tools/registry.py",
        lambda: _path_in_src("modules/sales_agent/application/tools/registry.py"),
    ),
    (
        "shared/agent_observability/channels/format.py::CHANNEL_FORMATS",
        lambda: _path_in_src("shared/agent_observability/channels/format.py"),
    ),
    (
        "personality_profiles table",
        lambda: _text_in_alembic("personality_profiles", "personality_profile"),
    ),
    (
        "model_pricing_snapshot table",
        lambda: _text_in_alembic("model_pricing_snapshot"),
    ),
    (
        "mv_daily_llm_cost_per_tenant_v2",
        lambda: _text_in_src_py("mv_daily_llm_cost_per_tenant_v2"),
    ),
    (
        "sales_agent_routing_log table",
        lambda: _text_in_src_py("sales_agent_routing_log"),
    ),
    (
        "SalesAgentJudge",
        lambda: _text_in_src_py("SalesAgentJudge", "modules/sales_agent"),
    ),
    (
        "application/orchestrator/tool_call_dedup.py",
        lambda: _path_in_src("modules/sales_agent/application/orchestrator/tool_call_dedup.py"),
    ),
    (
        "closer_studio.py API",
        lambda: _path_in_src("modules/sales_agent/api/closer_studio.py"),
    ),
    (
        "workers/follow_up_engine.py",
        lambda: _path_in_src("modules/sales_agent/workers/follow_up_engine.py"),
    ),
    (
        "pricing/aliases.py",
        lambda: _path_in_src("shared/agent_observability/pricing/aliases.py"),
    ),
    (
        "pricing/resolver.py",
        lambda: _path_in_src("shared/agent_observability/pricing/resolver.py"),
    ),
    (
        "docs/domains/sales-agent/redesign-2026-04/README.md",
        lambda: _path_in_docs("domains/sales-agent/redesign-2026-04/README.md"),
    ),
    (
        "docs/domains/sales-agent/redesign-2026-04/00-vision-and-objectives.md",
        lambda: _path_in_docs("domains/sales-agent/redesign-2026-04/00-vision-and-objectives.md"),
    ),
    (
        "docs/domains/sales-agent/redesign-2026-04/02-architecture-target.md",
        lambda: _path_in_docs("domains/sales-agent/redesign-2026-04/02-architecture-target.md"),
    ),
    (
        "docs/domains/sales-agent/redesign-2026-04/04-principles.md",
        lambda: _path_in_docs("domains/sales-agent/redesign-2026-04/04-principles.md"),
    ),
    (
        "docs/domains/sales-agent/redesign-2026-04/05-tech-debt-log.md",
        lambda: _path_in_docs("domains/sales-agent/redesign-2026-04/05-tech-debt-log.md"),
    ),
]

# Shared observability subsystems that MUST be documented in SKILL.md
# Format: (subsystem_identifier, one or more strings that MUST appear in skill text)
SHARED_CONSUMERS_REQUIRED: list[tuple[str, list[str]]] = [
    (
        "shared.agent_observability BaseAgentCallbackHandler",
        ["BaseAgentCallbackHandler"],
    ),
    (
        "shared.agent_observability FXResolver",
        ["FXResolver", "fx_resolver"],
    ),
    (
        "shared.agent_observability PricingResolver / pricing_resolver",
        ["PricingResolver", "pricing/resolver", "pricing_resolver"],
    ),
    (
        "shared.agent_observability base_trace_event_repo",
        ["base_trace_event_repo", "BaseTraceEventRepo"],
    ),
    (
        "shared.agent_observability base_llm_call_repo",
        ["base_llm_call_repo", "BaseLlmCallRepo"],
    ),
    (
        "shared.agent_observability format_for_channel / get_channel_format",
        ["get_channel_format", "format_for_channel", "CHANNEL_FORMATS"],
    ),
    (
        "shared.agent_observability sanitize_payload",
        ["sanitize_payload"],
    ),
    (
        "shared.billing BudgetGuard + RateLimiter",
        ["BudgetGuard", "budget_guard"],
    ),
    (
        "shared.agent_observability tenant_billing_config_repository",
        [
            "tenant_billing_config_repository",
            "TenantBillingConfigRepository",
        ],
    ),
]

# Required H3 sections in impl-log
IMPL_LOG_REQUIRED_H3 = [
    "Claims removed (archived)",
    "Claims updated",
    "Claims added",
    "Utility verdicts",
]

# Required H2 sections in SKILL.md after the audit
SKILL_REQUIRED_NEW_SECTIONS = [
    "Surfaces compartidas con copilot",
    "Decisiones cardinales",
]

# All H2 sections expected in SKILL.md (used by utility-verdicts coverage test)
SKILL_H2_SECTIONS_RE = re.compile(r"^## (.+)", re.MULTILINE)

# Contradiction patterns: pairs of claims that would be contradictory
# Each entry: (label, pattern_a_re, pattern_b_re, scope_files)
# If both match in the same set of files → flag as contradiction
CONTRADICTION_CHECKS: list[tuple[str, str, str, list[Path]]] = [
    (
        "voseo-tenant respected vs hard prohibition",
        r"voseo.*(tenant|respet|output|agente)",
        r"PROHIBIDO.*voseo",
        [SKILL_MD],
    ),
    (
        "SKILL.md says format.py; references say different module",
        r"channels/format\.py",
        r"channels/format_for_channel\.py.*SSoT\|SSoT.*channels/format_for_channel",
        [SKILL_MD, *REFERENCE_FILES],
    ),
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _skill_text() -> str:
    """Read full SKILL.md text."""
    return SKILL_MD.read_text(encoding="utf-8")


def _all_skill_text() -> str:
    """Read SKILL.md + all reference files concatenated."""
    parts = [SKILL_MD.read_text(encoding="utf-8")]
    for ref in REFERENCE_FILES:
        if ref.exists():
            parts.append(ref.read_text(encoding="utf-8"))
    return "\n".join(parts)


def _symbol_appears_in_skill(patterns: list[str]) -> bool:
    """Return True if ANY of the given string patterns appears in skill text (case-insensitive)."""
    text = _all_skill_text().lower()
    return any(p.lower() in text for p in patterns)


def _get_skill_h2_sections() -> list[str]:
    """Extract all H2 section titles from SKILL.md."""
    text = _skill_text()
    return SKILL_H2_SECTIONS_RE.findall(text)


def _impl_log_text() -> str:
    """Read T-1-impl-log.md if it exists, else return empty string."""
    if not IMPL_LOG.exists():
        return ""
    return IMPL_LOG.read_text(encoding="utf-8")


def _impl_log_h3_sections() -> list[str]:
    """Extract H3 section titles from T-1-impl-log.md."""
    text = _impl_log_text()
    return re.findall(r"^### (.+)", text, re.MULTILINE)


def _obsolete_lines_in_skill() -> list[str]:
    """Return lines in any skill file that start with 'OBSOLETO:'."""
    lines = []
    for f in [SKILL_MD, *REFERENCE_FILES]:
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("OBSOLETO:"):
                lines.append(stripped)
    return lines


# ---------------------------------------------------------------------------
# Test functions
# ---------------------------------------------------------------------------


def test_skill_paths_resolve_or_have_obsolete_marker() -> None:
    """Scenario 1 (happy): every symbol cited in SKILL.md either resolves or has OBSOLETO: marker.

    Each entry in SKILL_SYMBOLS is checked:
    - If the resolution function returns True → path/symbol resolved, OK.
    - If resolution returns False → look for OBSOLETO: marker covering that symbol
      in any skill file.
    - If neither → test FAILS.
    """
    all_skill_text = _all_skill_text()
    failures: list[str] = []

    for label, check_fn in SKILL_SYMBOLS:
        try:
            resolved = bool(check_fn())
        except Exception as exc:  # noqa: BLE001
            resolved = False
            failures.append(f"[ERROR checking '{label}': {exc}]")
            continue

        if not resolved:
            # Look for OBSOLETO: marker with the symbol name or a substring
            short_label = label.split("::")[0].split("/")[-1].split(".")[0]
            marker_found = "OBSOLETO:" in all_skill_text and any(
                short_label.lower() in line.lower() for line in all_skill_text.splitlines() if "OBSOLETO:" in line
            )
            if not marker_found:
                failures.append(f"'{label}' does not resolve AND has no OBSOLETO: marker in skill files.")

    assert not failures, f"{len(failures)} symbol(s) unresolved without OBSOLETO: marker:\n" + "\n".join(
        f"  - {f}" for f in failures
    )


def test_skill_has_new_canonical_sections() -> None:
    """Scenario 1 (happy): SKILL.md contains 2 required new sections added by the audit.

    Validates AD3: both 'Surfaces compartidas con copilot' and
    'Decisiones cardinales' sections exist in SKILL.md as H2 headers.
    """
    text = _skill_text()
    missing = []
    for section in SKILL_REQUIRED_NEW_SECTIONS:
        pattern = re.compile(rf"^## .*{re.escape(section)}", re.MULTILINE | re.IGNORECASE)
        if not pattern.search(text):
            missing.append(section)

    assert not missing, (
        f"SKILL.md is missing required H2 sections: {missing}\nThese sections must be added by the audit (AD3)."
    )


def test_impl_log_has_required_sections() -> None:
    """Scenario 1 (happy): T-1-impl-log.md exists and has the 4 mandatory H3 sections."""
    assert IMPL_LOG.exists(), (
        f"T-1-impl-log.md not found at {IMPL_LOG}. Create the impl-log with all 4 mandatory H3 sections."
    )

    h3_sections = _impl_log_h3_sections()
    missing = [req for req in IMPL_LOG_REQUIRED_H3 if not any(req.lower() in s.lower() for s in h3_sections)]

    assert not missing, f"T-1-impl-log.md is missing mandatory H3 sections: {missing}\nFound H3 sections: {h3_sections}"


def test_utility_verdicts_cover_all_skill_sections() -> None:
    """Scenario 1 (happy): utility verdicts table in impl-log covers 100% SKILL.md H2 sections.

    Each H2 section in SKILL.md must have a row in the 'Utility verdicts' table
    in T-1-impl-log.md. Also checks the 4 reference files have entries.
    """
    assert IMPL_LOG.exists(), f"T-1-impl-log.md not found at {IMPL_LOG}"

    h2_sections = _get_skill_h2_sections()
    impl_log_text = _impl_log_text()

    missing_sections = []
    for section in h2_sections:
        # Check if the section name appears in the utility verdicts table
        if section.strip("# ").lower() not in impl_log_text.lower():
            missing_sections.append(f"SKILL.md '## {section}'")

    # Check each reference file has an entry
    for ref in REFERENCE_FILES:
        ref_name = ref.name
        if ref_name.lower() not in impl_log_text.lower():
            missing_sections.append(f"reference file '{ref_name}'")

    assert not missing_sections, (
        f"Utility verdicts table is missing coverage for {len(missing_sections)} item(s):\n"
        + "\n".join(f"  - {s}" for s in missing_sections)
    )


def test_obsolete_marker_has_inline_reason() -> None:
    """Scenario 2 (negative): every OBSOLETO: marker in skill files has an inline reason.

    Pattern per AD5: 'OBSOLETO: <symbol> [—:→] <reason>'
    A bare 'OBSOLETO: foo' without a separator + reason is invalid.
    """
    obsolete_lines = _obsolete_lines_in_skill()

    if not obsolete_lines:
        # If no OBSOLETO: markers exist (post-audit all paths resolved), test passes.
        return

    bad_markers = []
    for line in obsolete_lines:
        if not OBSOLETO_FULL_RE.match(line):
            bad_markers.append(line)

    assert not bad_markers, (
        f"{len(bad_markers)} OBSOLETO: marker(s) missing inline reason:\n"
        + "\n".join(f"  - {m}" for m in bad_markers)
        + "\n\nRequired format: 'OBSOLETO: <symbol> [—:→] <reason>'"
    )


def test_shared_observability_consumers_documented() -> None:
    """Scenario 3 (edge): all shared/agent_observability subsystems consumed by sales_agent
    are documented in the skill (SKILL.md or references/).

    Checks the 'Surfaces compartidas con copilot' section specifically,
    but also accepts documentation anywhere in the skill text.
    """
    all_text = _all_skill_text()
    missing = []

    for subsystem_label, patterns in SHARED_CONSUMERS_REQUIRED:
        if not any(p.lower() in all_text.lower() for p in patterns):
            missing.append(f"'{subsystem_label}' — expected one of {patterns} in skill text")

    assert not missing, f"{len(missing)} shared consumer(s) not documented in skill:\n" + "\n".join(
        f"  - {m}" for m in missing
    )


def test_skill_no_self_contradiction() -> None:
    """Scenario 4 (adversarial): no logical contradictions detected within skill files.

    Checks CONTRADICTION_CHECKS list — each entry defines two regex patterns
    that, if both match simultaneously in the same scope, indicate a contradiction.
    """
    contradictions_found = []

    for label, pattern_a, pattern_b, scope_files in CONTRADICTION_CHECKS:
        combined_text = "\n".join(f.read_text(encoding="utf-8") for f in scope_files if f.exists())
        match_a = re.search(pattern_a, combined_text, re.IGNORECASE)
        match_b = re.search(pattern_b, combined_text, re.IGNORECASE)
        if match_a and match_b:
            contradictions_found.append(
                f"Contradiction '{label}':\n"
                f"  Pattern A matched: '{match_a.group(0)[:80]}'\n"
                f"  Pattern B matched: '{match_b.group(0)[:80]}'"
            )

    assert not contradictions_found, f"{len(contradictions_found)} contradiction(s) detected:\n" + "\n".join(
        contradictions_found
    )


def test_contradiction_detector_flags_synthetic_injection() -> None:
    """Scenario 4 (adversarial): positive control — contradiction detector works.

    Injects a known contradiction into an in-memory string and asserts the
    detector logic catches it. This proves the detector is not trivially passing.
    """
    # Synthetic text with two contradictory claims
    synthetic_text = (
        "El agente respeta voseo del tenant output\n"
        "PROHIBIDO usar voseo en la interfaz del agente (output) a toda costa\n"
    )

    pattern_a = r"voseo.*(tenant|respet|output|agente)"
    pattern_b = r"PROHIBIDO.*voseo"

    match_a = re.search(pattern_a, synthetic_text, re.IGNORECASE)
    match_b = re.search(pattern_b, synthetic_text, re.IGNORECASE)

    # Both should match — contradiction detected
    assert match_a is not None, "Pattern A should match synthetic text (positive control failed)"
    assert match_b is not None, "Pattern B should match synthetic text (positive control failed)"


def test_skill_files_parseable_as_utf8() -> None:
    """Non-functional: all skill files must be valid UTF-8 (no binary corruption)."""
    failures = []
    for f in [SKILL_MD, *REFERENCE_FILES]:
        try:
            f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError) as exc:
            failures.append(f"{f.name}: {exc}")

    assert not failures, "Skill files with encoding errors:\n" + "\n".join(failures)


def test_zero_src_changes_guard() -> None:
    """Sentinel: this test file itself has zero imports from backend/src/ or frontend/src/.

    Ensures the test does not accidentally depend on production code.
    This mirrors the gate validator zero_src_changes (A7).
    """
    test_file = Path(__file__)
    tree = ast.parse(test_file.read_text(encoding="utf-8"))

    bad_imports = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = ""
            if isinstance(node, ast.Import):
                module = node.names[0].name if node.names else ""
            elif isinstance(node, ast.ImportFrom) and node.module:
                module = node.module
            if module.startswith(("src.", "modules.", "shared.")):
                bad_imports.append(module)

    assert not bad_imports, (
        f"Test file imports production src/ modules: {bad_imports}\n"
        "This test must be pure filesystem/regex/AST — no src/ imports."
    )
