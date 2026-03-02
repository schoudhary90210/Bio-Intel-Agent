import json
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis cache wrapper with graceful degradation.
    If Redis is unavailable, all operations silently no-op.
    """

    def __init__(self):
        self._client = None
        self._available = False
        self._connect()

    def _connect(self):
        try:
            import redis
            self._client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            self._client.ping()
            self._available = True
            logger.info(f"Redis connected at {settings.REDIS_URL}")
        except Exception as e:
            self._available = False
            logger.warning(f"Redis unavailable ({e}). Caching disabled — continuing without cache.")

    @property
    def connected(self) -> bool:
        return self._available

    def get(self, key: str) -> Optional[str]:
        if not self._available:
            return None
        try:
            return self._client.get(key)
        except Exception as e:
            logger.warning(f"Redis GET failed: {e}")
            return None

    def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        if not self._available:
            return False
        try:
            self._client.set(key, value, ex=ttl)
            return True
        except Exception as e:
            logger.warning(f"Redis SET failed: {e}")
            return False

    def exists(self, key: str) -> bool:
        if not self._available:
            return False
        try:
            return bool(self._client.exists(key))
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        if not self._available:
            return False
        try:
            self._client.delete(key)
            return True
        except Exception:
            return False

    def get_json(self, key: str) -> Optional[dict]:
        raw = self.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def set_json(self, key: str, data: dict, ttl: int = 3600) -> bool:
        return self.set(key, json.dumps(data), ttl=ttl)


# Singleton instance — import and use directly
cache = RedisClient()
