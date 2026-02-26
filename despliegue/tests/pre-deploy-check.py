import os
import sys
import subprocess
import time
import requests
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load Environment
load_dotenv()

def check_env_vars():
    required = ["DATABASE_URL", "OPENAI_API_KEY", "CLERK_SECRET_KEY"]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        print(f"❌ Falta configuración crítica: {', '.join(missing)}")
        return False
    print("✅ Variables de Entorno: OK")
    return True

def check_database():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("⚠️  DATABASE_URL no definida. Saltando check de BD.")
        return True
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Conexión a Base de Datos: OK")
        return True
    except Exception as e:
        print(f"❌ Error conectando a BD: {e}")
        return False

def check_frontend_build():
    print("🏗️  Verificando Build de Frontend (Simulacro)...")
    try:
        # Dry run build or just check if package.json is valid
        if os.path.exists("frontend/package.json"):
            # Check for critical scripts
            with open("frontend/package.json") as f:
                if '"build":' not in f.read():
                    print("❌ Frontend no tiene script de build.")
                    return False
            print("✅ Configuración de Frontend: OK")
            return True
        else:
            print("⚠️  No se encontró frontend/package.json")
            return True
    except Exception as e:
        print(f"❌ Error verificando frontend: {e}")
        return False

def main():
    print("🔍 Iniciando Verificación Pre-Despliegue...")
    
    checks = [
        check_env_vars(),
        check_database(),
        check_frontend_build()
    ]
    
    if all(checks):
        print("\n✨ Todo listo para el despliegue. Sistema estable.")
        sys.exit(0)
    else:
        print("\n🚫 Se encontraron errores críticos. No desplegar.")
        sys.exit(1)

if __name__ == "__main__":
    main()
