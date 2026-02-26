import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.services.database import engine
from src.services.db.models import PromptVersion

def update_db():
    print("Creando tabla 'prompt_versions'...")
    try:
        PromptVersion.__table__.create(bind=engine)
        print("✅ Tabla creada exitosamente.")
    except Exception as e:
        print(f"⚠️ La tabla ya existe o hubo un error: {e}")

if __name__ == "__main__":
    update_db()
