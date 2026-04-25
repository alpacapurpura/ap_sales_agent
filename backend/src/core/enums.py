"""Core enumerations for AI provider, model role, and prompt source."""

from enum import StrEnum


class PromptSource(StrEnum):
    """Prompt resolution strategy."""

    HYBRID = "hybrid"  # DB > File (Default)
    FILE = "file"  # Local File System only (Dev)
    DB = "db"  # DB Only (Strict Prod)


class AIProvider(StrEnum):
    """Supported AI provider backends."""

    OPENAI = "openai"
    GEMINI = "gemini"


class ModelRole(StrEnum):
    """Semantic roles for AI model selection.

    Each role maps to a specific model via env vars (AI_MODEL_<ROLE>).
    Consumers declare WHAT they need, not WHICH model.
    """

    NANO = "nano"  # Ultra-low-latency classification, intent routing — F8
    REASONING = "reasoning"  # Complex analysis, structured JSON extraction
    FAST = "fast"  # Simple/cheap tasks, low latency
    VISION = "vision"  # Multimodal (image analysis)
    AGENT = "agent"  # Tool-calling, long context
    EMBEDDING = "embedding"  # Dense vector embeddings
