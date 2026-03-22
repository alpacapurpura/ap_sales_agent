from enum import Enum

class PromptSource(str, Enum):
    HYBRID = "hybrid"   # DB > File (Default)
    FILE = "file"       # Local File System only (Dev)
    DB = "db"           # DB Only (Strict Prod)

class AIProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
