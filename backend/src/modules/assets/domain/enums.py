from enum import Enum

class AssetType(str, Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"

class StorageProvider(str, Enum):
    LOCAL = "LOCAL"
    S3 = "S3"
    R2 = "R2"

class AssetStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
