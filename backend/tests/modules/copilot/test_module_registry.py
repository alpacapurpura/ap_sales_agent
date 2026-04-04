"""
Tests for copilot MODULE_REGISTRY.

Validates that:
- Every registered module_id maps to a real directory in backend/src/modules/
- All required descriptor fields are populated (module_id, label, description, route_prefix)
- The registry is a singleton (same object on repeated calls)
- Known modules are present
"""

from pathlib import Path


def _modules_root() -> Path:
    """Return the path to backend/src/modules/."""
    # __file__ is tests/modules/copilot/test_module_registry.py
    return Path(__file__).parents[3] / "src" / "modules"


class TestModuleRegistryStructure:
    def test_all_registered_modules_have_real_directories(self):
        """Each module_id in the registry corresponds to an existing directory."""
        from src.modules.copilot.domain.module_registry import get_module_registry

        registry = get_module_registry()
        modules_root = _modules_root()

        for module_id, descriptor in registry.items():
            module_dir = modules_root / module_id
            assert module_dir.is_dir(), (
                f"Module '{module_id}' is registered in MODULE_REGISTRY but "
                f"no directory found at {module_dir}"
            )

    def test_all_descriptors_have_required_fields(self):
        """Each descriptor has non-empty module_id, label, description, route_prefix."""
        from src.modules.copilot.domain.module_registry import get_module_registry

        registry = get_module_registry()
        for module_id, descriptor in registry.items():
            assert descriptor.module_id, f"module_id is empty for key '{module_id}'"
            assert descriptor.label, f"label is empty for '{module_id}'"
            assert descriptor.description, f"description is empty for '{module_id}'"
            assert descriptor.route_prefix, f"route_prefix is empty for '{module_id}'"

    def test_known_core_modules_are_present(self):
        """brand, offer, crm, analytics, commercial_calendar and landing are registered."""
        from src.modules.copilot.domain.module_registry import get_module_registry

        registry = get_module_registry()
        expected = {"brand", "offer", "crm", "analytics", "commercial_calendar", "landing"}
        missing = expected - set(registry.keys())
        assert not missing, f"Expected modules not in registry: {missing}"

    def test_registry_is_singleton(self):
        """Repeated calls return the same object (no rebuild)."""
        from src.modules.copilot.domain.module_registry import get_module_registry

        first = get_module_registry()
        second = get_module_registry()
        assert first is second
