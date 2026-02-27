import os
import sys
from pathlib import Path

# Configuration
# Path is adjusted to run from project root or any subdir, targeting backend/src
BASE_DIR = Path("backend/src").resolve()
if not BASE_DIR.exists():
    # Fallback if running from within backend/
    BASE_DIR = Path("src").resolve()

# Strict Modular Monolith Structure Definition
SHARED_DIRS = [
    "shared/domain",
    "shared/infrastructure",
    "shared/utils",
    "shared/application",
    "shared/core",
]

# Every module MUST have these layers
MODULE_LAYERS = [
    "domain",
    "application",
    "infrastructure",
    "api",
]

# Rules for file placement
FORBIDDEN_PATTERNS = {
    "domain": ["sqlalchemy", "fastapi", "db.", "Model", "router"],  # Pure Logic only
    "application": ["fastapi", "router", "def post(", "def get("], # Orchestration only, no HTTP details
}

def check_structure():
    print(f"🔍 Starting Modular Monolith Audit of {BASE_DIR}...\n")
    
    if not BASE_DIR.exists():
        print(f"CRITICAL: Backend directory not found at {BASE_DIR}")
        sys.exit(1)

    missing_count = 0
    
    # 1. Check Shared Kernel
    print("Checking Shared Kernel...")
    for rel_path in SHARED_DIRS:
        full_path = BASE_DIR / rel_path
        if not full_path.exists():
            print(f"❌ MISSING: {rel_path} (Required Shared Kernel)")
            missing_count += 1
        else:
            print(f"✅ FOUND: {rel_path}")

    # 2. Check Modules (Vertical Slices)
    print("\nChecking Modules (Bounded Contexts)...")
    modules_dir = BASE_DIR / "modules"
    if not modules_dir.exists():
        print(f"❌ MISSING: modules/ directory")
        missing_count += 1
    else:
        # Scan each module
        modules = [d for d in modules_dir.iterdir() if d.is_dir() and not d.name.startswith("__")]
        if not modules:
            print("⚠️  WARNING: No modules found in src/modules/")
        
        for module in modules:
            print(f"  > Auditing Module: {module.name}")
            for layer in MODULE_LAYERS:
                layer_path = module / layer
                if not layer_path.exists():
                    print(f"    ❌ MISSING LAYER: {layer} in {module.name}")
                    missing_count += 1
                else:
                    # Check for layer violations
                    check_layer_integrity(layer_path, layer)

    # 3. Check for Legacy/Misplaced Folders
    print("\nChecking for Legacy Structures...")
    legacy_dirs = ["core", "services", "api/routers"]
    for legacy in legacy_dirs:
        if (BASE_DIR / legacy).exists():
            print(f"⚠️  DEPRECATED: Found '{legacy}' folder. Move contents to 'modules/' or 'shared/'.")

def check_layer_integrity(layer_path, layer_name):
    """Checks for forbidden imports/patterns in specific layers."""
    if layer_name not in FORBIDDEN_PATTERNS:
        return

    patterns = FORBIDDEN_PATTERNS[layer_name]
    for root, _, files in os.walk(layer_path):
        for file in files:
            if not file.endswith(".py"):
                continue
            
            file_path = Path(root) / file
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    for term in patterns:
                        if term in content:
                            print(f"    ⚠️  VIOLATION: {file_path.name} contains '{term}' -> Forbidden in {layer_name}")
            except Exception:
                pass

if __name__ == "__main__":
    check_structure()
    print("\nAudit Complete.")
