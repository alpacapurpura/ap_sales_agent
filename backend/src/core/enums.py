from enum import Enum

class PromptSource(str, Enum):
    HYBRID = "hybrid"   # DB > File (Default)
    FILE = "file"       # Local File System only (Dev)
    DB = "db"           # DB Only (Strict Prod)

class AIProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"


class ModelRole(str, Enum):
    """Semantic roles for AI model selection.

    Each role maps to a specific model via env vars (AI_MODEL_<ROLE>).
    Consumers declare WHAT they need, not WHICH model.
    """
    REASONING = "reasoning"  # Complex analysis, structured JSON extraction
    FAST = "fast"            # Simple/cheap tasks, low latency
    VISION = "vision"        # Multimodal (image analysis)
    AGENT = "agent"          # Tool-calling, long context
    EMBEDDING = "embedding"  # Dense vector embeddings
