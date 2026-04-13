from enum import StrEnum


class MessageSender(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
