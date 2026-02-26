from enum import Enum

class ChannelType(str, Enum):
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp" # Evolution / QR
    WHATSAPP_CLOUD = "whatsapp_cloud" # Meta Cloud API
    MANYCHAT = "manychat"

class MessageSender(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class AppointmentStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"
