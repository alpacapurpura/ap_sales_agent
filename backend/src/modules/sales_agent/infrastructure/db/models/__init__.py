# Bootstrap Module: Import all models here to ensure SQLAlchemy Registry is fully populated.
# This prevents "Lazy Loading" errors and "Mapper failed to initialize" issues in modular architectures.

from src.shared.infrastructure.models.agent_trace_model import AgentTrace
from src.shared.infrastructure.models.llm_log_model import LLMLog
from src.shared.infrastructure.models.prompt_version_model import PromptVersion

from src.modules.crm.infrastructure.models.lead_model import LeadModel
from src.modules.iam.infrastructure.models import (
    TenantModel,
    UserModel,
    UserTenantModel,
)
from src.modules.offer.infrastructure.models.product_model import (
    ProductModel as Product,
)
from src.modules.sales_agent.infrastructure.models.channel_model import (
    ChannelConnectionModel as ChannelConnection,
)
from src.modules.sales_agent.infrastructure.models.message_model import (
    MessageModel as Message,
)
from src.modules.scheduling.infrastructure.models.appointment_model import (
    AppointmentModel as Appointment,
)

__all__ = [
    "AgentTrace",
    "Appointment",
    "ChannelConnection",
    "LLMLog",
    "LeadModel",
    "Message",
    "Product",
    "PromptVersion",
    "TenantModel",
    "UserModel",
    "UserTenantModel",
]
