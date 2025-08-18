import redis
from typing import Optional
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    _instance: Optional[redis.Redis] = None
    _pool: Optional[redis.ConnectionPool] = None

    @classmethod
    def get_instance(cls) -> redis.Redis:
        if cls._instance is None:
            cls._pool = redis.ConnectionPool(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=settings.redis_decode_responses,
                max_connections=20,
            )
            cls._instance = redis.Redis(connection_pool=cls._pool)

            try:
                cls._instance.ping()
                logger.info("Redis connection established successfully")
            except redis.ConnectionError as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise  # Re-raise the exception so it doesn't fail silently

        return cls._instance

    @classmethod
    def close_connection(cls):
        if cls._instance:
            cls._instance.close()
            cls._instance = None
        if cls._pool:
            cls._pool.disconnect()
            cls._pool = None

    @property
    def connection(self) -> redis.Redis:
        """Property to access the Redis connection - for compatibility with session_manager"""
        return self.get_instance()


# Create a RedisClient instance (not just the Redis connection)
redis_client = RedisClient()
