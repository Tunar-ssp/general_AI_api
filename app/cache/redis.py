import redis
import time
import json
import logging
from typing import Dict, Any, Optional, List, Union
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis cache for storing API responses and tracking API usage"""
    def __init__(self):
        self.redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        self.cache_expiration = settings.CACHE_EXPIRATION
        logger.info(f"Redis cache initialized with expiration: {self.cache_expiration}s")
        
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a value from the cache"""
        try:
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting key {key} from Redis: {str(e)}")
            return None
    
    def set(self, key: str, value: Dict[str, Any], expiration: Optional[int] = None) -> bool:
        """Set a value in the cache"""
        try:
            exp = expiration if expiration is not None else self.cache_expiration
            return self.redis_client.setex(
                key,
                exp,
                json.dumps(value)
            )
        except Exception as e:
            logger.error(f"Error setting key {key} in Redis: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a value from the cache"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Error deleting key {key} from Redis: {str(e)}")
            return False
    
    def get_api_counter(self, api_name: str, time_window: str) -> int:
        """Get the current API usage count for a specific time window"""
        try:
            # Key format: api:{api_name}:count:{time_window}:{timestamp}
            timestamp = self._get_timestamp_for_window(time_window)
            key = f"api:{api_name}:count:{time_window}:{timestamp}"
            count = self.redis_client.get(key)
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Error getting API counter for {api_name}: {str(e)}")
            return 0
    
    def increment_api_counter(self, api_name: str, time_window: str) -> int:
        """Increment the API usage count for a specific time window"""
        try:
            timestamp = self._get_timestamp_for_window(time_window)
            key = f"api:{api_name}:count:{time_window}:{timestamp}"
            
            # Set expiration based on time window
            if time_window == "minute":
                expiration = 60
            elif time_window == "hour":
                expiration = 3600
            elif time_window == "day":
                expiration = 86400
            else:
                expiration = 60  # Default to minute
            
            # Increment counter and set expiration if it's a new key
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, expiration)
            result = pipe.execute()
            return result[0]  # Return the incremented value
        except Exception as e:
            logger.error(f"Error incrementing API counter for {api_name}: {str(e)}")
            return 0
    
    def _get_timestamp_for_window(self, time_window: str) -> int:
        """Get the timestamp for the current time window"""
        current_time = int(time.time())
        if time_window == "minute":
            return current_time // 60
        elif time_window == "hour":
            return current_time // 3600
        elif time_window == "day":
            return current_time // 86400
        else:
            return current_time // 60  # Default to minute
    
    def cache_response(self, prompt: str, api_name: str, response: Dict[str, Any]) -> bool:
        """Cache an API response"""
        try:
            # Create a hash of the prompt to use as the key
            key = f"response:{self._hash_prompt(prompt)}"
            value = {
                "api_name": api_name,
                "response": response,
                "timestamp": int(time.time())
            }
            return self.set(key, value)
        except Exception as e:
            logger.error(f"Error caching response: {str(e)}")
            return False
    
    def get_cached_response(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Get a cached API response"""
        try:
            key = f"response:{self._hash_prompt(prompt)}"
            return self.get(key)
        except Exception as e:
            logger.error(f"Error getting cached response: {str(e)}")
            return None
    
    def _hash_prompt(self, prompt: str) -> str:
        """Create a simple hash of the prompt"""
        import hashlib
        return hashlib.md5(prompt.encode()).hexdigest()

# Create a singleton instance
cache = RedisCache()