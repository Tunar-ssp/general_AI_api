from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import time
from app.services.api_client import GeminiClient, DeepseekClient, OlamaClient
from app.cache.redis import cache
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize API clients
gemini_client = GeminiClient()
deepseek_client = DeepseekClient()
olama_client = OlamaClient()

# Define request models
class GenerateRequest(BaseModel):
    prompt: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1024
    top_p: Optional[float] = 0.95
    top_k: Optional[int] = 40
    force_provider: Optional[str] = None  # Optional: force a specific provider

# Define response models
class GenerateResponse(BaseModel):
    content: str
    provider: str
    cached: bool = False
    latency_ms: float

@router.post("/generate", response_model=GenerateResponse)
async def generate_content(request: GenerateRequest):
    """Generate content using the best available AI API"""
    start_time = time.time()
    
    # Check if we have a cached response
    cached_response = cache.get_cached_response(request.prompt)
    if cached_response and not request.force_provider:
        logger.info(f"Using cached response from {cached_response['api_name']}")
        return GenerateResponse(
            content=cached_response["response"].get("content", ""),
            provider=cached_response["api_name"],
            cached=True,
            latency_ms=(time.time() - start_time) * 1000
        )
    
    # If force_provider is specified, try to use that provider
    if request.force_provider:
        response = await _try_specific_provider(request)
        if response:
            return response
        else:
            raise HTTPException(status_code=503, detail=f"Forced provider {request.force_provider} is not available")
    
    # Try each provider in order of preference
    response = await _try_all_providers(request)
    if response:
        return response
    
    # If we get here, all providers failed
    raise HTTPException(status_code=503, detail="All AI providers are currently unavailable")

async def _try_specific_provider(request: GenerateRequest):
    """Try to use a specific provider"""
    if request.force_provider == "gemini" and gemini_client.check_availability():
        return await _generate_with_gemini(request)
    elif request.force_provider == "deepseek" and deepseek_client.check_availability():
        return await _generate_with_deepseek(request)
    elif request.force_provider == "olama" and olama_client.check_availability():
        return await _generate_with_olama(request)
    return None

async def _try_all_providers(request: GenerateRequest):
    """Try all providers in order of preference"""
    # Try Gemini first
    if gemini_client.check_availability():
        return await _generate_with_gemini(request)
    
    # Try Deepseek second
    if deepseek_client.check_availability():
        return await _generate_with_deepseek(request)
    
    # Try Olama last
    if olama_client.check_availability():
        return await _generate_with_olama(request)
    
    return None

async def _generate_with_gemini(request: GenerateRequest):
    """Generate content using Gemini API"""
    start_time = time.time()
    try:
        response = gemini_client.generate_content(
            prompt=request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            top_k=request.top_k
        )
        
        # Extract content from Gemini response format
        content = ""
        if "candidates" in response and len(response["candidates"]) > 0:
            if "content" in response["candidates"][0]:
                if "parts" in response["candidates"][0]["content"]:
                    for part in response["candidates"][0]["content"]["parts"]:
                        if "text" in part:
                            content += part["text"]
        
        # Cache the response
        cache.cache_response(request.prompt, "gemini", {"content": content})
        
        return GenerateResponse(
            content=content,
            provider="gemini",
            cached=False,
            latency_ms=(time.time() - start_time) * 1000
        )
    except Exception as e:
        logger.error(f"Error generating content with Gemini: {str(e)}")
        return None

async def _generate_with_deepseek(request: GenerateRequest):
    """Generate content using Deepseek API"""
    start_time = time.time()
    try:
        response = deepseek_client.generate_content(
            prompt=request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p
        )
        
        # Extract content from Deepseek response format
        content = ""
        if "choices" in response and len(response["choices"]) > 0:
            if "message" in response["choices"][0]:
                content = response["choices"][0]["message"].get("content", "")
        
        # Cache the response
        cache.cache_response(request.prompt, "deepseek", {"content": content})
        
        return GenerateResponse(
            content=content,
            provider="deepseek",
            cached=False,
            latency_ms=(time.time() - start_time) * 1000
        )
    except Exception as e:
        logger.error(f"Error generating content with Deepseek: {str(e)}")
        return None

async def _generate_with_olama(request: GenerateRequest):
    """Generate content using Olama API"""
    start_time = time.time()
    try:
        response = olama_client.generate_content(
            prompt=request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p
        )
        
        # Extract content from Olama response format
        content = ""
        if "choices" in response and len(response["choices"]) > 0:
            if "message" in response["choices"][0]:
                content = response["choices"][0]["message"].get("content", "")
        
        # Cache the response
        cache.cache_response(request.prompt, "olama", {"content": content})
        
        return GenerateResponse(
            content=content,
            provider="olama",
            cached=False,
            latency_ms=(time.time() - start_time) * 1000
        )
    except Exception as e:
        logger.error(f"Error generating content with Olama: {str(e)}")
        return None

# Add a stats endpoint to monitor API usage
@router.get("/stats")
async def get_api_stats():
    """Get API usage statistics"""
    return {
        "gemini": {
            "minute": cache.get_api_counter("gemini", "minute"),
            "hour": cache.get_api_counter("gemini", "hour"),
            "day": cache.get_api_counter("gemini", "day"),
            "limit_per_minute": settings.GEMINI_RATE_LIMIT
        },
        "deepseek": {
            "minute": cache.get_api_counter("deepseek", "minute"),
            "hour": cache.get_api_counter("deepseek", "hour"),
            "day": cache.get_api_counter("deepseek", "day"),
            "limit_per_minute": settings.DEEPSEEK_RATE_LIMIT
        },
        "olama": {
            "minute": cache.get_api_counter("olama", "minute"),
            "hour": cache.get_api_counter("olama", "hour"),
            "day": cache.get_api_counter("olama", "day"),
            "limit_per_minute": settings.OLAMA_RATE_LIMIT
        }
    }