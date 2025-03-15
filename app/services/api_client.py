import requests
import json
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.cache.redis import cache

logger = logging.getLogger(__name__)

class APIClient:
    """Base class for API clients"""
    def __init__(self, api_name: str, api_key: str, endpoint: str, rate_limit: int):
        self.api_name = api_name
        self.api_key = api_key
        self.endpoint = endpoint
        self.rate_limit = rate_limit
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def check_availability(self) -> bool:
        """Check if the API is available and not rate limited"""
        # Check if we have API key
        if not self.api_key:
            logger.warning(f"{self.api_name} API key not configured")
            return False
        
        # Check rate limits
        current_usage = cache.get_api_counter(self.api_name, "minute")
        if current_usage >= self.rate_limit:
            logger.warning(f"{self.api_name} API rate limit reached: {current_usage}/{self.rate_limit}")
            return False
        
        return True
    
    @retry(stop=stop_after_attempt(settings.RETRY_ATTEMPTS), 
           wait=wait_exponential(multiplier=settings.RETRY_BACKOFF))
    def make_request(self, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """Make a request to the API with retry logic"""
        start_time = time.time()
        success = False
        response_data = {}
        
        try:
            # Increment API counter
            cache.increment_api_counter(self.api_name, "minute")
            
            # Make the request
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=30  # 30 second timeout
            )
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            success = True
            
            # Log success
            logger.info(f"{self.api_name} API request successful")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.api_name} API request failed: {str(e)}")
            response_data = {"error": str(e)}
            # Re-raise for retry mechanism
            raise
            
        finally:
            # Calculate latency
            latency = (time.time() - start_time) * 1000  # in milliseconds
            logger.debug(f"{self.api_name} API request latency: {latency:.2f}ms")
            
        return response_data, success


class GeminiClient(APIClient):
    """Client for Gemini API"""
    def __init__(self):
        super().__init__(
            api_name="gemini",
            api_key=settings.GEMINI_API_KEY,
            endpoint=settings.GEMINI_ENDPOINT,
            rate_limit=settings.GEMINI_RATE_LIMIT
        )
    
    def generate_content(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate content using Gemini API"""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.7),
                "maxOutputTokens": kwargs.get("max_tokens", 1024),
                "topP": kwargs.get("top_p", 0.95),
                "topK": kwargs.get("top_k", 40)
            }
        }
        
        response, success = self.make_request(payload)
        return response


class DeepseekClient(APIClient):
    """Client for Deepseek API"""
    def __init__(self):
        super().__init__(
            api_name="deepseek",
            api_key=settings.DEEPSEEK_API_KEY,
            endpoint=settings.DEEPSEEK_ENDPOINT,
            rate_limit=settings.DEEPSEEK_RATE_LIMIT
        )
    
    def generate_content(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate content using Deepseek API"""
        payload = {
            "model": kwargs.get("model", "deepseek-chat"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1024),
            "top_p": kwargs.get("top_p", 0.95),
        }
        
        response, success = self.make_request(payload)
        return response


class OlamaClient(APIClient):
    """Client for Olama API"""
    def __init__(self):
        super().__init__(
            api_name="olama",
            api_key=settings.OLAMA_API_KEY,
            endpoint=settings.OLAMA_ENDPOINT,
            rate_limit=settings.OLAMA_RATE_LIMIT
        )
    
    def generate_content(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate content using Olama API"""
        payload = {
            "model": kwargs.get("model", "olama-chat"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1024),
            "top_p": kwargs.get("top_p", 0.95),
            "stream": kwargs.get("stream", False)
        }
        
        response, success = self.make_request(payload)
        return response