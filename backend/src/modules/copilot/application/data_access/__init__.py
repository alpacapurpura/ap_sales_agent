"""Internal copilot data accessors used by ``ask_tenant_data``.

Modules that own data outside ``copilot/`` (offer, crm, …) expose their
``DataAccessProvider`` via the discovery pattern. The copilot's own data
(conversations, inspirations, mutation journal) lives here and is registered
directly by the dispatcher because there is no cross-module surface to expose.
"""

from src.modules.copilot.application.data_access.conversation import (
    ConversationDataAccessProvider,
)

__all__ = ("ConversationDataAccessProvider",)
