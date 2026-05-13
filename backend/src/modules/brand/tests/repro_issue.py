"""Brand issue reproduction test."""

import sys
from pathlib import Path

# Ajustar PYTHONPATH para que encuentre 'src'
# Asumiendo que el script está en backend/src/modules/brand/tests/repro_issue.py
# Necesitamos agregar 'backend/' al path para importar 'src.modules...'
current_dir = Path(__file__).resolve().parent
backend_dir = (current_dir / "../../../../").resolve()
sys.path.append(str(backend_dir))

try:
    from luana_core_brand_studio.domain.models import BrandSettings
except ImportError as e:
    print(f"ImportError: {e}")
    # Try alternate import if running from root
    try:
        from backend.src.modules.brand.domain.models import BrandSettings
    except ImportError as e2:
        print(f"Second ImportError: {e2}")
        print("Could not import BrandSettings")
        sys.exit(1)


def run_tests() -> None:
    """Run tests."""
    print("Running reproduction script...")

    # 1. Test BrandSettings(**None)
    print("\n--- Test 1: BrandSettings(**None) ---")
    try:
        # This is expected to crash because **None is invalid syntax/runtime behavior
        BrandSettings(**None)
        print("PASSED")
    except Exception as e:  # noqa: BLE001 — test infrastructure resilience
        print(f"CRASHED: {type(e).__name__}: {e}")

    # 2. Test Logic Simulation (WITH FIX)
    print("\n--- Test 2: Logic Simulation (FIXED) ---")
    config = {"brand_settings": None}

    # NEW LOGIC: Use 'or {}' to handle None
    brand_data = config.get("brand_settings") or {}

    print(f"config: {config}")
    print(f"brand_data result: {brand_data}")

    if brand_data == {}:
        print("VERIFIED: brand_data is {} (Empty Dict)")
        try:
            BrandSettings(**brand_data)
            print("PASSED: BrandSettings(**{}) works!")
        except Exception as e:  # noqa: BLE001 — test infrastructure resilience
            print(f"FAILED: BrandSettings(**{{}}) raised {e}")
    else:
        print(f"FAILED: brand_data is {brand_data}")


if __name__ == "__main__":
    run_tests()
