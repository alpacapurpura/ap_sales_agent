import time
import json
from typing import List, Optional
from src.services.database import redis_client
import structlog

logger = structlog.get_logger()

class SmartBufferService:
    """
    Manages the message buffer in Redis for the Dynamic Debounce strategy.
    """
    def __init__(self):
        self.redis = redis_client
        self.buffer_ttl = 3600 # 1 hour expiration for stale buffers
    
    def _key_buffer(self, user_id: str) -> str:
        return f"chat:buffer:{user_id}"
    
    def _key_meta(self, user_id: str) -> str:
        return f"chat:meta:{user_id}"

    def _key_lock(self, user_id: str) -> str:
        return f"chat:lock:{user_id}"

    def add_message(self, user_id: str, text: str, channel_type: str, metadata: dict = None):
        """
        Appends a message to the user's buffer and updates the last timestamp.
        """
        # 1. Push text to list
        self.redis.rpush(self._key_buffer(user_id), text)
        self.redis.expire(self._key_buffer(user_id), self.buffer_ttl)
        
        # 2. Update Metadata (Timestamp + Channel + User Info)
        # We store channel_type to know where to reply later
        meta = {
            "last_ts": time.time(),
            "channel_type": channel_type,
            "metadata_json": json.dumps(metadata or {})
        }
        self.redis.hset(self._key_meta(user_id), mapping=meta)
        self.redis.expire(self._key_meta(user_id), self.buffer_ttl)

    def get_metadata(self, user_id: str) -> dict:
        """
        Retrieves stored metadata.
        """
        raw = self.redis.hget(self._key_meta(user_id), "metadata_json")
        return json.loads(raw) if raw else {}

    def get_last_timestamp(self, user_id: str) -> float:
        """
        Returns the timestamp of the last received message.
        """
        ts = self.redis.hget(self._key_meta(user_id), "last_ts")
        return float(ts) if ts else 0.0

    def get_channel_type(self, user_id: str) -> Optional[str]:
        return self.redis.hget(self._key_meta(user_id), "channel_type")

    def get_and_clear_buffer(self, user_id: str) -> List[str]:
        """
        Retrieves all messages and clears the buffer atomically-ish.
        """
        pipe = self.redis.pipeline()
        pipe.lrange(self._key_buffer(user_id), 0, -1)
        pipe.delete(self._key_buffer(user_id))
        results = pipe.execute()
        return results[0] # List of messages

    def peek_buffer(self, user_id: str) -> List[str]:
        """
        Returns current messages without clearing.
        """
        return self.redis.lrange(self._key_buffer(user_id), 0, -1)

    def acquire_lock(self, user_id: str, expire: int = 30) -> bool:
        """
        Tries to acquire a lock for processing. Returns True if acquired.
        """
        return bool(self.redis.set(self._key_lock(user_id), "locked", ex=expire, nx=True))

    def release_lock(self, user_id: str):
        self.redis.delete(self._key_lock(user_id))
