import pytest
from unittest.mock import patch, MagicMock


def test_graceful_degradation_no_redis():
    """When Redis is unavailable, RedisClient should degrade gracefully."""
    with patch("app.utils.redis_client.settings") as mock_settings:
        mock_settings.REDIS_URL = "redis://nonexistent:9999/0"

        # Force re-creation of the client
        from app.utils.redis_client import RedisClient
        client = RedisClient()

        assert client.connected is False
        assert client.get("anything") is None
        assert client.set("key", "value") is False
        assert client.exists("key") is False


def test_cache_operations_when_connected():
    """When Redis is mocked as connected, operations should work."""
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True
    mock_redis.get.return_value = '{"test": true}'
    mock_redis.exists.return_value = True

    with patch("redis.from_url", return_value=mock_redis):
        from app.utils.redis_client import RedisClient
        client = RedisClient()

        assert client.connected is True
        assert client.get("key") == '{"test": true}'

        client.set("key", "value", ttl=60)
        mock_redis.set.assert_called_with("key", "value", ex=60)

        assert client.exists("key") is True

        result = client.get_json("key")
        assert result == {"test": True}


def test_set_json_and_get_json():
    """JSON serialization/deserialization should round-trip."""
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True
    stored = {}

    def mock_set(key, value, ex=None):
        stored[key] = value

    def mock_get(key):
        return stored.get(key)

    mock_redis.set.side_effect = mock_set
    mock_redis.get.side_effect = mock_get

    with patch("redis.from_url", return_value=mock_redis):
        from app.utils.redis_client import RedisClient
        client = RedisClient()

        data = {"keyword": "CRISPR", "count": 3}
        client.set_json("test:key", data)
        result = client.get_json("test:key")
        assert result == data
