# Bootstrap Module: Import all models here to ensure SQLAlchemy Registry is fully populated.
# This prevents "Lazy Loading" errors and "Mapper failed to initialize" issues in modular architectures.

from src.modules.iam.infrastructure.models import UserModel, TenantModel, UserTenantModel

from src.modules.sales.infrastructure.models.lead_model import LeadModel

from src.modules.communication.infrastructure.models.message_model import MessageModel as Message
from src.modules.communication.infrastructure.models.appointment_model import AppointmentModel as Appointment
from src.modules.communication.infrastructure.models.channel_model import ChannelConnectionModel as ChannelConnection

from src.shared.infrastructure.models.agent_trace_model import AgentTrace
from src.shared.infrastructure.models.llm_log_model import LLMLog
from src.shared.infrastructure.models.prompt_version_model import PromptVersion

from src.modules.offer.infrastructure.models.product_model import ProductModel as Product

__all__ = [
    "UserModel",
    "TenantModel",
    "UserTenantModel",
    "LeadModel",
    "Message",
    "Appointment",
    "ChannelConnection",
    "AgentTrace",
    "LLMLog",
    "PromptVersion",
    "Product"
]
