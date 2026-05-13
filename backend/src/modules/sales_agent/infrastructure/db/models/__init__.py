"""Models package."""
# Bootstrap Module: Import all models here to ensure SQLAlchemy Registry is fully populated.
# This prevents "Lazy Loading" errors and "Mapper failed to initialize" issues in modular architectures.
# NOTE: Cross-module models are registered via shared/infrastructure/model_registry.py.

from luana_core_iam.infrastructure.models import (
    TenantModel,
    UserModel,
    UserTenantModel,
)
from luana_core_platform.infrastructure.models.agent_trace_model import AgentTrace
from luana_core_platform.infrastructure.models.llm_log_model import LLMLog
from luana_core_platform.infrastructure.models.prompt_version_model import PromptVersion
from luana_core_sales_agent.infrastructure.models.message_model import (
    MessageModel as Message,
)

__all__ = [
    "AgentTrace",
    "LLMLog",
    "Message",
    "PromptVersion",
    "TenantModel",
    "UserModel",
    "UserTenantModel",
]
