
import sys
import os
from unittest.mock import MagicMock

# Add project root to path (backend directory)
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

print(f"Added to sys.path: {backend_dir}")
print("Verifying IAM module imports...")

try:
    print("Importing domain models...")
    from src.modules.iam.domain.user import User
    from src.modules.iam.domain.tenant import Tenant
    print("Domain models imported successfully.")

    print("Importing infrastructure models...")
    from src.modules.iam.infrastructure.models.user_model import UserModel
    from src.modules.iam.infrastructure.models.tenant_model import TenantModel
    from src.modules.iam.infrastructure.models.user_tenant_model import UserTenantModel
    print("Infrastructure models imported successfully.")

    print("Importing repositories...")
    from src.modules.iam.infrastructure.repositories.tenant_repository import TenantRepository
    from src.modules.iam.infrastructure.repositories.user_repository import UserRepository
    from src.modules.iam.infrastructure.repositories.user_tenant_repository import UserTenantRepository
    print("Repositories imported successfully.")

    print("Importing services...")
    from src.modules.iam.application.services.tenant_service import TenantService
    from src.modules.iam.application.services.user_service import UserService
    print("Services imported successfully.")

    print("Importing API routers...")
    from src.modules.iam.api.routers import auth_router, tenant_router
    from src.modules.iam.api import settings, webhooks
    print("API routers imported successfully.")

    print("Importing dependencies...")
    from src.modules.iam.api.dependencies import get_current_user, get_tenant_context
    print("Dependencies imported successfully.")

    print("Testing Service Instantiation...")
    mock_db = MagicMock()
    tenant_service = TenantService(mock_db)
    user_service = UserService(mock_db)
    print("Services instantiated successfully.")

    print("ALL CHECKS PASSED.")

except ImportError as e:
    print(f"IMPORT ERROR: {e}")
    sys.exit(1)
except Exception as e:
    print(f"RUNTIME ERROR: {e}")
    sys.exit(1)
