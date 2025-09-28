"""
Redis service following Single Responsibility Principle
"""
from typing import Optional, Any
import redis
from loguru import logger

from config import Config


class RedisService:
    """Service responsible for Redis operations"""
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
    
    def initialize(self) -> None:
        """Initialize Redis connection"""
        try:
            self._client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                decode_responses=True
            )
            # Test connection
            self._client.ping()
            logger.info("Redis connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            raise
    
    def get(self, key: str) -> Optional[str]:
        """
        Get value from Redis
        
        Args:
            key: Redis key
            
        Returns:
            Value or None if not found
        """
        try:
            return self._client.get(key)
        except Exception as e:
            logger.error(f"Failed to get key {key}: {e}")
            return None
    
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """
        Set value in Redis
        
        Args:
            key: Redis key
            value: Value to store
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if ttl:
                self._client.setex(key, ttl, value)
            else:
                self._client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Failed to set key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from Redis
        
        Args:
            key: Redis key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self._client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis
        
        Args:
            key: Redis key to check
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            return bool(self._client.exists(key))
        except Exception as e:
            logger.error(f"Failed to check existence of key {key}: {e}")
            return False
    
    def get_robots_txt(self, domain: str) -> Optional[str]:
        """
        Get robots.txt content for domain
        
        Args:
            domain: Domain to get robots.txt for
            
        Returns:
            Robots.txt content or None if not found
        """
        key = f"robots_txt:{domain}"
        return self.get(key)
    
    def set_robots_txt(self, domain: str, content: str, ttl: int = 86400) -> bool:
        """
        Set robots.txt content for domain
        
        Args:
            domain: Domain to set robots.txt for
            content: Robots.txt content
            ttl: Time to live in seconds (default: 24 hours)
            
        Returns:
            True if successful, False otherwise
        """
        key = f"robots_txt:{domain}"
        return self.set(key, content, ttl)
    
    def get_crawl_delay(self, domain: str) -> Optional[int]:
        """
        Get crawl delay for domain
        
        Args:
            domain: Domain to get crawl delay for
            
        Returns:
            Crawl delay in milliseconds or None if not found
        """
        key = f"crawl_delay:{domain}"
        value = self.get(key)
        return int(value) if value else None
    
    def set_crawl_delay(self, domain: str, delay: int, ttl: int = 86400) -> bool:
        """
        Set crawl delay for domain
        
        Args:
            domain: Domain to set crawl delay for
            delay: Crawl delay in milliseconds
            ttl: Time to live in seconds (default: 24 hours)
            
        Returns:
            True if successful, False otherwise
        """
        key = f"crawl_delay:{domain}"
        return self.set(key, str(delay), ttl)
    
    def close(self) -> None:
        """Close Redis connection"""
        try:
            if self._client:
                self._client.close()
                logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
