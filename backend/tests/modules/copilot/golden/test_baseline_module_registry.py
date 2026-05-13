"""Golden snapshot: copilot module registry shape.

[COPILOT-REDESIGN-2026-04 F0.5]

The module registry is the SSoT consumed by ``build_system_prompt`` and the
copilot tools that introspect available modules. F1 (provider pattern) will
move every module's entry into a per-module provider; the *shape* of what
each entry exposes (label / route_prefix / description) must remain stable
unless explicitly evolved.
"""

from __future__ import annotations

from luana_core_copilot.domain.module_registry import get_module_registry
from tests.modules.copilot.golden.conftest import assert_matches_golden


def test_module_registry_shape_matches_baseline() -> None:
    registry = get_module_registry()
    snapshot = {
        module_id: {
            "label": descriptor.label,
            "route_prefix": descriptor.route_prefix,
            "description": descriptor.description,
        }
        for module_id, descriptor in registry.items()
    }
    assert_matches_golden("module_registry_shape", snapshot)
