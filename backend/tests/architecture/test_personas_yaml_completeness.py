"""Architecture fitness gate — personas YAML completeness (Story C T-2).

Story C (T-2) cement: ``docs/specs/personas/archetype-aware/`` contains EXACTLY
15 archetype-aware YAML files (5 happy x 3 persona_kind across 5 tenant archetypes)
and ``docs/specs/personas/_legacy/`` contains EXACTLY 5 preserved legacy files.

Allowlists are intentionally empty (shrink-only). Any drift from the expected
counts or schema invariants fails the gate.

Invariants enforced:

1. 15 YAML files present in ``archetype-aware/`` (5 tenants x 3 persona_kinds).
2. 5 YAML files present in ``_legacy/``.
3. Each archetype-aware YAML: ``schema_version == 2``.
4. Each archetype-aware YAML: ``persona_kind ∈ 6-value canonical set``.
5. Each archetype-aware YAML: ``dialect_code`` matches ``ARCHETYPE_DIALECT_MAP[tenant_slug]`` strict.
6. Each archetype-aware YAML: ``metadata.tenant_slug ∈ 5 valid Story A slugs``.
7. Each archetype-aware YAML: ``metadata.archetype ∈ 5 valid archetypes``.
8. Each archetype-aware YAML: ``metadata.bloom_stages`` subset of canonical 4 stages.
9. Each archetype-aware YAML: ``metadata.persona_gym_axes`` subset of canonical 5 axes.
10. es-AR YAML files (dialect_code == 'es-AR') have ``# voseo-allowed`` or
    ``<!-- voseo-allowed -->`` magic comment on línea 2.

Static approach — reads files directly from filesystem, no LLM invocation.

# voseo-allowed: arch fitness gate cita magic comment linea 2 formato para validacion
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.no_eval

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

# parents[2] = backend/
# parents[3] = repo root
_BACKEND_ROOT: Path = Path(__file__).resolve().parents[2]
_REPO_ROOT: Path = _BACKEND_ROOT.parent
_PERSONAS_ROOT: Path = _REPO_ROOT / "docs" / "specs" / "personas"
_ARCHETYPE_AWARE_DIR: Path = _PERSONAS_ROOT / "archetype-aware"
_LEGACY_DIR: Path = _PERSONAS_ROOT / "_legacy"

# ---------------------------------------------------------------------------
# SSoT constants (mirrors Story A ARCHETYPE_DIALECT_MAP)
# ---------------------------------------------------------------------------

_ARCHETYPE_DIALECT_MAP: dict[str, str] = {
    "tenant_coach_lat": "es-PE",
    "tenant_medicina_estetica": "es-MX",
    "tenant_clinica_dental": "es-CO",
    "tenant_agencia_growth_video": "es-AR",
    "tenant_agencia_automatizacion_ia": "es-419",
}

_VALID_TENANT_SLUGS: frozenset[str] = frozenset(_ARCHETYPE_DIALECT_MAP.keys())

_VALID_ARCHETYPES: frozenset[str] = frozenset(
    {
        "coach_lat",
        "medicina_estetica",
        "clinica_dental",
        "agencia_growth_video",
        "agencia_automatizacion_ia",
    },
)

_VALID_PERSONA_KINDS: frozenset[str] = frozenset(
    {"happy", "nurture", "unqualified", "adversarial", "edge", "negative"},
)

_CANONICAL_BLOOM_STAGES: frozenset[str] = frozenset(
    {"understanding", "ideation", "rollout", "judgment"},
)

_CANONICAL_PERSONA_GYM_AXES: frozenset[str] = frozenset(
    {
        "action_justification",
        "expected_action",
        "linguistic_habits",
        "persona_consistency",
        "toxicity_control",
    },
)

# Pre-compiled magic comment pattern (mirrors pre-commit hook regex).
_VOSEO_ALLOWED_PATTERN: re.Pattern[str] = re.compile(
    r"(#\s*voseo-allowed([: \t]|$)|<!--\s*voseo-allowed[^>]*-->)",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_yaml_files(directory: Path) -> list[tuple[Path, dict[str, object]]]:
    """Return list of (path, parsed_dict) for all *.yaml files in directory.

    Raises AssertionError if any file fails yaml.safe_load (gate should catch
    malformed files explicitly, not silently skip them).
    """
    results: list[tuple[Path, dict[str, object]]] = []
    for path in sorted(directory.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(raw, dict), (
            f"{path.name}: yaml.safe_load returned {type(raw).__name__}, expected dict. Malformed YAML — fix the file."
        )
        results.append((path, raw))
    return results


def _get_archetype_aware_files() -> list[tuple[Path, dict[str, object]]]:
    return _load_yaml_files(_ARCHETYPE_AWARE_DIR)


def _get_legacy_files() -> list[tuple[Path, dict[str, object]]]:
    return _load_yaml_files(_LEGACY_DIR)


def _parse_comma_set(value: object) -> frozenset[str]:
    """Parse a comma-separated string into a frozenset of stripped values."""
    if not isinstance(value, str):
        return frozenset()
    return frozenset(s.strip() for s in value.split(",") if s.strip())


def _get_line_2(path: Path) -> str:
    """Return the raw text of line 2 (index 1) of the file, or '' if fewer lines."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 2:
        return ""
    return lines[1]


# ════════════════════════════════════════════════════════════════════════
# Directory existence sanity
# ════════════════════════════════════════════════════════════════════════


def test_archetype_aware_directory_exists() -> None:
    """``docs/specs/personas/archetype-aware/`` MUST exist."""
    assert _ARCHETYPE_AWARE_DIR.is_dir(), (
        f"archetype-aware/ directory not found at {_ARCHETYPE_AWARE_DIR}. T-2 deliverable absent."
    )


def test_legacy_directory_exists() -> None:
    """``docs/specs/personas/_legacy/`` MUST exist."""
    assert _LEGACY_DIR.is_dir(), (
        f"_legacy/ directory not found at {_LEGACY_DIR}. T-2 deliverable absent — legacy YAML files not moved."
    )


# ════════════════════════════════════════════════════════════════════════
# Count invariants (D14 — 3 kinds x 5 tenants = 15)
# ════════════════════════════════════════════════════════════════════════


def test_archetype_aware_count_is_15() -> None:
    """EXACTLY 15 YAML files MUST exist in ``archetype-aware/``.

    3 persona_kinds (happy, nurture, unqualified) x 5 tenant archetypes = 15.
    Adding or removing files without updating this gate fails the ratchet.
    """
    files = list(_ARCHETYPE_AWARE_DIR.glob("*.yaml"))
    assert len(files) == 15, (
        f"archetype-aware/ MUST contain exactly 15 YAML files; found {len(files)}. "
        f"Files present: {sorted(f.name for f in files)}."
    )


def test_legacy_count_is_5() -> None:
    """EXACTLY 5 YAML files MUST be preserved in ``_legacy/``.

    Story C moved 5 original personas to _legacy/ (git mv preserving history).
    These must not be deleted or added to (Story I may optionally reactivate).
    """
    files = list(_LEGACY_DIR.glob("*.yaml"))
    assert len(files) == 5, (
        f"_legacy/ MUST contain exactly 5 YAML files; found {len(files)}. "
        f"Files present: {sorted(f.name for f in files)}."
    )


# ════════════════════════════════════════════════════════════════════════
# Schema version invariant
# ════════════════════════════════════════════════════════════════════════


def test_all_archetype_aware_yaml_schema_version_2() -> None:
    """Every archetype-aware YAML MUST declare ``schema_version: 2``.

    Story C bumped schema from 1 (Story B) to 2 (v2 sub-slots + nurture/unqualified
    persona_kind extension). Files at v1 are backward-compat via identity migrator
    but MUST be re-authored to v2 in archetype-aware/.
    """
    errors: list[str] = []
    for path, data in _get_archetype_aware_files():
        actual = data.get("schema_version")
        if actual != 2:
            errors.append(f"{path.name}: schema_version={actual!r} (expected 2)")
    assert not errors, f"schema_version != 2 in {len(errors)} file(s):\n" + "\n".join(f"  {e}" for e in errors)


# ════════════════════════════════════════════════════════════════════════
# persona_kind invariant (D13 — 6-value canonical set v2)
# ════════════════════════════════════════════════════════════════════════


def test_all_archetype_aware_yaml_persona_kind_in_canonical_set() -> None:
    """Every archetype-aware YAML ``persona_kind`` MUST be in the 6-value v2 set.

    v2 adds ``nurture`` + ``unqualified`` to the v1 set
    (happy, edge, negative, adversarial).
    """
    errors: list[str] = []
    for path, data in _get_archetype_aware_files():
        kind = data.get("persona_kind")
        if kind not in _VALID_PERSONA_KINDS:
            errors.append(f"{path.name}: persona_kind={kind!r} not in {sorted(_VALID_PERSONA_KINDS)}")
    assert not errors, f"Invalid persona_kind in {len(errors)} file(s):\n" + "\n".join(f"  {e}" for e in errors)


# ════════════════════════════════════════════════════════════════════════
# metadata.tenant_slug invariant (D5 — 5 valid Story A slugs)
# ════════════════════════════════════════════════════════════════════════


def test_all_archetype_aware_yaml_tenant_slug_valid() -> None:
    """Every archetype-aware YAML ``metadata.tenant_slug`` MUST be one of the 5 valid slugs.

    The 5 slugs mirror Story A eval seed tenants (ARCHETYPE_SLUGS).
    """
    errors: list[str] = []
    for path, data in _get_archetype_aware_files():
        meta = data.get("metadata", {})
        if not isinstance(meta, dict):
            errors.append(f"{path.name}: metadata is not a dict")
            continue
        slug = meta.get("tenant_slug")
        if slug not in _VALID_TENANT_SLUGS:
            errors.append(f"{path.name}: tenant_slug={slug!r} not in {sorted(_VALID_TENANT_SLUGS)}")
    assert not errors, f"Invalid tenant_slug in {len(errors)} file(s):\n" + "\n".join(f"  {e}" for e in errors)


# ════════════════════════════════════════════════════════════════════════
# metadata.archetype invariant (5 valid archetypes)
# ════════════════════════════════════════════════════════════════════════


def test_all_archetype_aware_yaml_archetype_valid() -> None:
    """Every archetype-aware YAML ``metadata.archetype`` MUST be one of the 5 valid archetypes."""
    errors: list[str] = []
    for path, data in _get_archetype_aware_files():
        meta = data.get("metadata", {})
        if not isinstance(meta, dict):
            continue
        arch = meta.get("archetype")
        if arch not in _VALID_ARCHETYPES:
            errors.append(f"{path.name}: archetype={arch!r} not in {sorted(_VALID_ARCHETYPES)}")
    assert not errors, f"Invalid archetype in {len(errors)} file(s):\n" + "\n".join(f"  {e}" for e in errors)


# ════════════════════════════════════════════════════════════════════════
# dialect_code cross-check (D-AG-1 — strict match vs ARCHETYPE_DIALECT_MAP)
# ════════════════════════════════════════════════════════════════════════


def test_all_archetype_aware_yaml_dialect_code_matches_dialect_map() -> None:
    """Every archetype-aware YAML ``dialect_code`` MUST match ``ARCHETYPE_DIALECT_MAP[tenant_slug]``.

    D-AG-1 cross-check: personas are pre-validated so loader cross-check
    (D-AG-1) finds zero mismatches at runtime. Static enforcement here
    catches drift before runtime.
    """
    errors: list[str] = []
    for path, data in _get_archetype_aware_files():
        meta = data.get("metadata", {})
        if not isinstance(meta, dict):
            continue
        slug = meta.get("tenant_slug")
        if slug not in _ARCHETYPE_DIALECT_MAP:
            continue  # already caught by tenant_slug test
        expected = _ARCHETYPE_DIALECT_MAP[slug]
        actual = data.get("dialect_code")
        if actual != expected:
            errors.append(
                f"{path.name}: dialect_code={actual!r} but tenant_slug={slug!r} requires {expected!r}",
            )
    assert not errors, f"Dialect code mismatch (D-AG-1) in {len(errors)} file(s):\n" + "\n".join(
        f"  {e}" for e in errors
    )


# ════════════════════════════════════════════════════════════════════════
# metadata.bloom_stages invariant (D8 — subset of canonical 4)
# ════════════════════════════════════════════════════════════════════════


def test_all_archetype_aware_yaml_bloom_stages_valid_subset() -> None:
    """Every archetype-aware YAML ``metadata.bloom_stages`` MUST be a non-empty subset of the 4 canonical stages.

    Canonical: ``understanding, ideation, rollout, judgment`` (Anthropic Bloom framework).
    """
    errors: list[str] = []
    for path, data in _get_archetype_aware_files():
        meta = data.get("metadata", {})
        if not isinstance(meta, dict):
            continue
        bloom_str = meta.get("bloom_stages", "")
        bloom_set = _parse_comma_set(bloom_str)
        if not bloom_set:
            errors.append(f"{path.name}: bloom_stages is empty — must declare at least one canonical stage")
        elif not bloom_set.issubset(_CANONICAL_BLOOM_STAGES):
            invalid = bloom_set - _CANONICAL_BLOOM_STAGES
            errors.append(
                f"{path.name}: bloom_stages contains invalid stages {sorted(invalid)}. "
                f"Canonical: {sorted(_CANONICAL_BLOOM_STAGES)}."
            )
    assert not errors, f"Invalid bloom_stages in {len(errors)} file(s):\n" + "\n".join(f"  {e}" for e in errors)


# ════════════════════════════════════════════════════════════════════════
# metadata.persona_gym_axes invariant (D9 — subset of canonical 5)
# ════════════════════════════════════════════════════════════════════════


def test_all_archetype_aware_yaml_persona_gym_axes_valid_subset() -> None:
    """Every archetype-aware YAML ``metadata.persona_gym_axes`` MUST be a non-empty subset of the 5 canonical axes.

    Canonical axes (PersonaGym 2024 paper):
    action_justification, expected_action, linguistic_habits, persona_consistency, toxicity_control.
    """
    errors: list[str] = []
    for path, data in _get_archetype_aware_files():
        meta = data.get("metadata", {})
        if not isinstance(meta, dict):
            continue
        axes_str = meta.get("persona_gym_axes", "")
        axes_set = _parse_comma_set(axes_str)
        if not axes_set:
            errors.append(f"{path.name}: persona_gym_axes is empty — must declare at least one canonical axis")
        elif not axes_set.issubset(_CANONICAL_PERSONA_GYM_AXES):
            invalid = axes_set - _CANONICAL_PERSONA_GYM_AXES
            errors.append(
                f"{path.name}: persona_gym_axes contains invalid axes {sorted(invalid)}. "
                f"Canonical: {sorted(_CANONICAL_PERSONA_GYM_AXES)}."
            )
    assert not errors, f"Invalid persona_gym_axes in {len(errors)} file(s):\n" + "\n".join(f"  {e}" for e in errors)


# ════════════════════════════════════════════════════════════════════════
# es-AR voseo magic comment (D12 — línea 2 enforcement)
# ════════════════════════════════════════════════════════════════════════


def test_es_ar_yaml_files_have_voseo_magic_comment_line_2() -> None:
    """Every es-AR archetype-aware YAML MUST have the voseo magic comment on línea 2.

    Enforcement mirrors the pre-commit hook regex:
    ``(#\\s*voseo-allowed([: \\t]|$)|<!--\\s*voseo-allowed[^>]*-->)``

    Lines are 1-indexed in user-facing messages; the check is line index 1
    (second line in 0-indexed access). This prevents accidental voseo-text
    in es-AR personas from triggering the pre-commit hook block.

    D12 ratificado: 3 es-AR files must have the magic comment.
    """
    errors: list[str] = []
    for path, data in _get_archetype_aware_files():
        if data.get("dialect_code") != "es-AR":
            continue
        line_2 = _get_line_2(path)
        if not _VOSEO_ALLOWED_PATTERN.search(line_2):
            errors.append(
                f"{path.name}: es-AR file missing voseo magic comment on línea 2. "
                f"Line 2 found: {line_2!r}. "
                f"Expected: '# voseo-allowed: ...' or '<!-- voseo-allowed ... -->'."
            )
    assert not errors, f"Missing voseo magic comment in {len(errors)} es-AR file(s):\n" + "\n".join(
        f"  {e}" for e in errors
    )


# ════════════════════════════════════════════════════════════════════════
# Coverage invariant — 3 kinds present per tenant
# ════════════════════════════════════════════════════════════════════════


def test_each_tenant_has_happy_nurture_unqualified_personas() -> None:
    """Each of the 5 tenant slugs MUST have exactly 3 persona_kinds: happy, nurture, unqualified.

    This enforces the 3x5 matrix (D14) at the tenant level.
    """
    from collections import defaultdict

    tenant_kinds: dict[str, set[str]] = defaultdict(set)
    for _path, data in _get_archetype_aware_files():
        meta = data.get("metadata", {})
        if not isinstance(meta, dict):
            continue
        slug = meta.get("tenant_slug")
        kind = data.get("persona_kind")
        if slug and kind:
            tenant_kinds[slug].add(str(kind))

    _EXPECTED_KINDS: frozenset[str] = frozenset({"happy", "nurture", "unqualified"})
    errors: list[str] = []
    for slug in sorted(_VALID_TENANT_SLUGS):
        actual_kinds = tenant_kinds.get(slug, set())
        missing = _EXPECTED_KINDS - actual_kinds
        extra = actual_kinds - _EXPECTED_KINDS
        if missing:
            errors.append(f"{slug}: missing persona_kinds {sorted(missing)}")
        if extra:
            errors.append(f"{slug}: unexpected extra persona_kinds {sorted(extra)}")
    assert not errors, "3-kinds x 5-tenants matrix (D14) violations:\n" + "\n".join(f"  {e}" for e in errors)


# ════════════════════════════════════════════════════════════════════════
# Required schema fields present
# ════════════════════════════════════════════════════════════════════════


_REQUIRED_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "schema_version",
        "name",
        "actor_goal",
        "dialect_code",
        "traits",
        "pain_points",
        "objections",
        "budget_hint",
        "urgency",
        "communication_style",
        "initial_message",
        "persona_kind",
        "metadata",
    },
)

_REQUIRED_METADATA_KEYS: frozenset[str] = frozenset(
    {
        "archetype",
        "tenant_slug",
        "bloom_stages",
        "persona_gym_axes",
        "story_origin",
    },
)


def test_all_archetype_aware_yaml_required_fields_present() -> None:
    """Every archetype-aware YAML MUST include all required top-level and metadata fields.

    Mirrors the Pydantic ConfigDict(extra='forbid') contract on ActorProfile
    — files missing required fields will fail ActorProfile.model_validate() at runtime.
    """
    errors: list[str] = []
    for path, data in _get_archetype_aware_files():
        missing_top = _REQUIRED_TOP_LEVEL_KEYS - set(data.keys())
        if missing_top:
            errors.append(f"{path.name}: missing top-level keys {sorted(missing_top)}")
        meta = data.get("metadata", {})
        if isinstance(meta, dict):
            missing_meta = _REQUIRED_METADATA_KEYS - set(meta.keys())
            if missing_meta:
                errors.append(f"{path.name}: missing metadata keys {sorted(missing_meta)}")
    assert not errors, f"Missing required fields in {len(errors)} file(s):\n" + "\n".join(f"  {e}" for e in errors)


def test_all_archetype_aware_yaml_traits_non_empty() -> None:
    """Every archetype-aware YAML ``traits`` field MUST be a non-empty list."""
    errors: list[str] = []
    for path, data in _get_archetype_aware_files():
        traits = data.get("traits")
        if not isinstance(traits, list) or len(traits) == 0:
            errors.append(f"{path.name}: traits must be non-empty list; got {traits!r}")
    assert not errors, f"Empty or invalid traits in {len(errors)} file(s):\n" + "\n".join(f"  {e}" for e in errors)


def test_all_archetype_aware_yaml_pain_points_non_empty() -> None:
    """Every archetype-aware YAML ``pain_points`` field MUST be a non-empty list."""
    errors: list[str] = []
    for path, data in _get_archetype_aware_files():
        pains = data.get("pain_points")
        if not isinstance(pains, list) or len(pains) == 0:
            errors.append(f"{path.name}: pain_points must be non-empty list; got {pains!r}")
    assert not errors, f"Empty or invalid pain_points in {len(errors)} file(s):\n" + "\n".join(f"  {e}" for e in errors)


def test_all_archetype_aware_yaml_objections_non_empty() -> None:
    """Every archetype-aware YAML ``objections`` field MUST be a non-empty list."""
    errors: list[str] = []
    for path, data in _get_archetype_aware_files():
        objs = data.get("objections")
        if not isinstance(objs, list) or len(objs) == 0:
            errors.append(f"{path.name}: objections must be non-empty list; got {objs!r}")
    assert not errors, f"Empty or invalid objections in {len(errors)} file(s):\n" + "\n".join(f"  {e}" for e in errors)


def test_all_archetype_aware_yaml_initial_message_non_empty() -> None:
    """Every archetype-aware YAML ``initial_message`` MUST be a non-empty string."""
    errors: list[str] = []
    for path, data in _get_archetype_aware_files():
        msg = data.get("initial_message")
        if not isinstance(msg, str) or not msg.strip():
            errors.append(f"{path.name}: initial_message must be non-empty string; got {msg!r}")
    assert not errors, f"Empty or invalid initial_message in {len(errors)} file(s):\n" + "\n".join(
        f"  {e}" for e in errors
    )


# ════════════════════════════════════════════════════════════════════════
# Legacy files integrity (D2 — 5 preserved, not modified)
# ════════════════════════════════════════════════════════════════════════

_EXPECTED_LEGACY_NAMES: frozenset[str] = frozenset(
    {
        "lead-frio-impaciente.yaml",
        "lead-tibio-dudoso.yaml",
        "lead-caliente-ready.yaml",
        "tenant-experto-saturado.yaml",
        "tenant-novato-tech.yaml",
    },
)


def test_legacy_files_names_match_expected() -> None:
    """The 5 legacy YAML files MUST have the exact expected filenames.

    ``git mv`` was used to preserve git history — names are immutable.
    Story I may optionally reactivate these files; any name change must
    update this gate.
    """
    actual_names = frozenset(f.name for f in _LEGACY_DIR.glob("*.yaml"))
    assert actual_names == _EXPECTED_LEGACY_NAMES, (
        f"_legacy/ filename drift. Expected {sorted(_EXPECTED_LEGACY_NAMES)}; "
        f"got {sorted(actual_names)}. "
        f"Missing: {sorted(_EXPECTED_LEGACY_NAMES - actual_names)}; "
        f"unexpected: {sorted(actual_names - _EXPECTED_LEGACY_NAMES)}."
    )
