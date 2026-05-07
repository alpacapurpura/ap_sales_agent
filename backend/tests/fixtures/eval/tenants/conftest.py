"""Shared pytest fixtures for eval tenant seed tests.

Provides shared fixtures for realism-smoke test parametrization.
The pytest_generate_tests hook handles the 5 x 6 = 30 combination
for test_realism_smoke.py (both archetype_slug + yaml_filename in args).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.fixtures.eval.tenants.loader import ARCHETYPE_SLUGS, YAML_FILENAMES

# ---------------------------------------------------------------------------
# Parametrize helpers
# ---------------------------------------------------------------------------


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Auto-parametrize archetype_slug x yaml_filename combos for smoke tests.

    Only activates when BOTH archetype_slug AND yaml_filename are declared
    in the test function signature (i.e., test_realism_smoke.py).
    Tests using only archetype_slug should use @pytest.mark.parametrize directly.
    """
    if "archetype_slug" in metafunc.fixturenames and "yaml_filename" in metafunc.fixturenames:
        combos = [(slug, fname) for slug in ARCHETYPE_SLUGS for fname in YAML_FILENAMES]
        metafunc.parametrize("archetype_slug,yaml_filename", combos)


# ---------------------------------------------------------------------------
# Path fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def tenants_dir() -> Path:
    """Absolute path to backend/tests/fixtures/eval/tenants/."""
    return Path(__file__).resolve().parent


@pytest.fixture(scope="session")
def dialect_catalog_path(tenants_dir: Path) -> Path:
    """Absolute path to dialect_catalog.yaml."""
    return tenants_dir / "dialect_catalog.yaml"


# ---------------------------------------------------------------------------
# Archetype slug list fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def all_archetype_slugs() -> tuple[str, ...]:
    """Return the 5 ratified archetype slugs."""
    return ARCHETYPE_SLUGS


@pytest.fixture(scope="session")
def all_yaml_filenames() -> tuple[str, ...]:
    """Return the 6 YAML filenames per archetype folder."""
    return YAML_FILENAMES
