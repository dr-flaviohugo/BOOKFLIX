from redis import Redis
from redis.exceptions import RedisError


class CacheService:
    def __init__(self, redis_url: str, ttl_seconds: int):
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.ttl_seconds = ttl_seconds

    def get_audio_path(self, key: str) -> str | None:
        try:
            return self.redis.get(key)
        except RedisError:
            return None

    def set_audio_path(self, key: str, path: str) -> None:
        try:
            self.redis.setex(key, self.ttl_seconds, path)
        except RedisError:
            return
