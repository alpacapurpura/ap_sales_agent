
import sys
import os

# Add backend to python path
sys.path.append(os.path.join(os.getcwd(), "backend"))

try:
    print("Attempting to import src.main...")
    from src.main import app
    print("Successfully imported src.main.app!")
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)
