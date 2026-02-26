# Bootstrap Module: Import all models here to ensure SQLAlchemy Registry is fully populated.
# This prevents "Lazy Loading" errors and "Mapper failed to initialize" issues in modular architectures.

from src.modules.iam.infrastructure.models.user import UserModel
from src.modules.iam.infrastructure.models.tenant import TenantModel
from src.modules.iam.infrastructure.models.user_tenant import UserTenantModel

from src.modules.sales.infrastructure.models.lead_model import LeadModel

from src.modules.communication.infrastructure.models.message import Message
from src.modules.communication.infrastructure.models.appointment import Appointment
from src.modules.communication.domain.channel_connection import ChannelConnection

from src.shared.infrastructure.db.models.audit import AgentTrace, LLMLog
from src.shared.infrastructure.db.models.prompt import PromptVersion

from src.modules.offer.infrastructure.models import Product

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
