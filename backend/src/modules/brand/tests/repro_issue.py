import sys
import os

# Ajustar PYTHONPATH para que encuentre 'src'
# Asumiendo que el script está en backend/src/modules/brand/tests/repro_issue.py
# Necesitamos agregar 'backend/' al path para importar 'src.modules...'
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, '../../../../'))
sys.path.append(backend_dir)

try:
    from src.modules.brand.domain.models import BrandSettings
except ImportError as e:
    print(f"ImportError: {e}")
    # Try alternate import if running from root
    try:
        from backend.src.modules.brand.domain.models import BrandSettings
    except ImportError as e2:
        print(f"Second ImportError: {e2}")
        print("Could not import BrandSettings")
        sys.exit(1)

def run_tests():
    print("Running reproduction script...")
    
    # 1. Test BrandSettings(**None)
    print("\n--- Test 1: BrandSettings(**None) ---")
    try:
        # This is expected to crash because **None is invalid syntax/runtime behavior
        BrandSettings(**None)
        print("PASSED")
    except Exception as e:
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
        except Exception as e:
            print(f"FAILED: BrandSettings(**{{}}) raised {e}")
    else:
        print(f"FAILED: brand_data is {brand_data}")

if __name__ == "__main__":
    run_tests()
