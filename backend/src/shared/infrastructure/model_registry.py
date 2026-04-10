"""Centralized model registry — ensures all SQLAlchemy models are imported.

SQLAlchemy resolves string-based relationship() targets by looking up class
names in its mapper registry.  A class only enters the registry when its
module is imported.  Because modules in this project are loosely coupled
(CRM ↔ Scheduling ↔ SalesAgent ↔ Offer ↔ IAM), not every model is
transitively imported by every entry-point.

Importing this single module guarantees every model is registered before
the first DB session triggers ``configure_mappers()``.

**Every entry-point that opens a DB session must import this module:**
  - ``main.py``        (FastAPI app)
  - ``admin/app.py``   (Streamlit admin)
  - Worker ``on_startup`` callbacks (ARQ workers / schedulers)
"""

# --- Advertising ---
from src.modules.advertising.infrastructure.models.ad_campaign_template_model import (
    AdCampaignTemplateModel,  # noqa: F401
)
from src.modules.advertising.infrastructure.models.ad_offer_association_model import (
    AdOfferAssociationModel,  # noqa: F401
)

# --- IAM ---
# --- Brand ---
from src.modules.brand.infrastructure.models.extraction_trace_model import (
    BrandExtractionTrace,  # noqa: F401
)

# --- Commercial Calendar ---
from src.modules.commercial_calendar.infrastructure.models.calendar_event_model import (
    CalendarEventModel,  # noqa: F401
)

# --- Copilot ---
from src.modules.copilot.infrastructure.models.conversation_model import (
    CopilotConversationModel,  # noqa: F401
)
from src.modules.copilot.infrastructure.models.event_model import (
    CopilotEventModel,  # noqa: F401
)
from src.modules.crm.infrastructure.models.customer_model import (  # noqa: F401
    CustomerIdentityModel,
    CustomerProfileModel,
    JourneyEventModel,
)

# --- CRM ---
from src.modules.crm.infrastructure.models.lead_model import LeadModel  # noqa: F401
from src.modules.crm.infrastructure.models.sale_model import SaleModel  # noqa: F401
from src.modules.iam.infrastructure.models.tenant_model import TenantModel  # noqa: F401
from src.modules.iam.infrastructure.models.user_model import UserModel  # noqa: F401
from src.modules.iam.infrastructure.models.user_tenant_model import (
    UserTenantModel,  # noqa: F401
)
from src.modules.offer.infrastructure.models.external_product_mapping_model import (
    ExternalProductMappingModel,  # noqa: F401
)

# --- Offer ---
from src.modules.offer.infrastructure.models.launch_edition_model import (
    LaunchEditionModel,  # noqa: F401
)
from src.modules.offer.infrastructure.models.product_model import (
    ProductModel,  # noqa: F401
)
from src.modules.sales_agent.infrastructure.models.agent_trace_model import (
    AgentTrace,  # noqa: F401
)
from src.modules.sales_agent.infrastructure.models.llm_log_model import (
    LLMLog,  # noqa: F401
)

# --- Sales Agent ---
from src.modules.sales_agent.infrastructure.models.message_model import (
    MessageModel,  # noqa: F401
)

# --- Scheduling ---
from src.modules.scheduling.infrastructure.models.appointment_model import (
    AppointmentModel,  # noqa: F401
)
from src.modules.scheduling.infrastructure.models.booking_link import (
    BookingLink,  # noqa: F401
)

# --- Domains ---
from src.modules.tenant_domains.infrastructure.models.tenant_domain_model import (
    TenantDomainModel,  # noqa: F401
)
