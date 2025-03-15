import requests
import json
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from app.core.config import settings
from app.cache.redis import cache
from app.services.api_client import APIClient

logger = logging.getLogger(__name__)

class OpenRouterClient(APIClient):
    """Client for OpenRouter API that can access various models including Gemini and Deepseek"""
    def __init__(self):
        super().__init__(
            api_name="openrouter",
            api_key=settings.OPENROUTER_API_KEY,
            endpoint=settings.OPENROUTER_ENDPOINT,
            rate_limit=settings.OPENROUTER_RATE_LIMIT
        )
        # Add OpenRouter specific headers
        self.headers.update({
            "HTTP-Referer": settings.APP_URL,  # Optional
            "X-Title": settings.APP_NAME     # Optional
        })
    
    def generate_content(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate content using OpenRouter API"""
        model = kwargs.get("model", "openai/gpt-3.5-turbo")  # Default model
        
        # Check if a specific provider model was requested
        if kwargs.get("provider") == "gemini":
            model = "google/gemini-pro"
        elif kwargs.get("provider") == "deepseek":
            model = "deepseek/deepseek-chat"
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1024),
            "top_p": kwargs.get("top_p", 0.95),
        }
        
        response, success = self.make_request(payload)
        return response