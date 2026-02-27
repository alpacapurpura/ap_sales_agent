import os
import argparse
import sys

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def create_file(path, content):
    if not os.path.exists(path):
        with open(path, 'w') as f:
            f.write(content)
        print(f"Created file: {path}")
    else:
        print(f"File already exists: {path}")

def scaffold_feature(feature_name, base_path="src/features"):
    feature_path = os.path.join(base_path, feature_name)
    
    # Create main directories
    create_directory(feature_path)
    create_directory(os.path.join(feature_path, "components"))
    create_directory(os.path.join(feature_path, "hooks"))
    create_directory(os.path.join(feature_path, "types"))
    create_directory(os.path.join(feature_path, "utils"))

    # Create index.ts (Barrel file)
    index_content = f"""// Public API for feature: {feature_name}
// Export only what should be accessible from outside this feature

export * from './components';
export * from './hooks';
export * from './types';
"""
    create_file(os.path.join(feature_path, "index.ts"), index_content)
    
    # Create placeholder index files for subdirectories
    create_file(os.path.join(feature_path, "components", "index.ts"), "// Export components here\n")
    create_file(os.path.join(feature_path, "hooks", "index.ts"), "// Export hooks here\n")
    create_file(os.path.join(feature_path, "types", "index.ts"), "// Export types here\n")

    print(f"\nSuccessfully scaffolded feature '{feature_name}' at {feature_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scaffold a new feature following FSD structure")
    parser.add_argument("name", help="Name of the feature (kebab-case)")
    parser.add_argument("--path", default="src/features", help="Base path for features (default: src/features)")
    
    args = parser.parse_args()
    
    scaffold_feature(args.name, args.path)
