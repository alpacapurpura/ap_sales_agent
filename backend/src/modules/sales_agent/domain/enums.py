"""Enums domain module."""

from enum import StrEnum


class MessageSender(StrEnum):
    """Message Sender enumeration."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
