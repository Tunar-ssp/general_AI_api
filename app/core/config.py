import os
from pydantic_settings import BaseSettings
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "AI API Management System"
    APP_VERSION: str = "0.1.0"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    OLAMA_API_KEY: str = os.getenv("OLAMA_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    
    # API Endpoints
    GEMINI_ENDPOINT: str = os.getenv("GEMINI_ENDPOINT", "")
    DEEPSEEK_ENDPOINT: str = os.getenv("DEEPSEEK_ENDPOINT", "")
    OLAMA_ENDPOINT: str = os.getenv("OLAMA_ENDPOINT", "")
    OPENROUTER_ENDPOINT: str = os.getenv("OPENROUTER_ENDPOINT", "https://openrouter.ai/api/v1/chat/completions")
    
    # API Rate Limits
    GEMINI_RATE_LIMIT: int = int(os.getenv("GEMINI_RATE_LIMIT", 60))
    DEEPSEEK_RATE_LIMIT: int = int(os.getenv("DEEPSEEK_RATE_LIMIT", 20))
    OLAMA_RATE_LIMIT: int = int(os.getenv("OLAMA_RATE_LIMIT", 30))
    OPENROUTER_RATE_LIMIT: int = int(os.getenv("OPENROUTER_RATE_LIMIT", 50))
    
    # Database Configuration
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "ai_api_manager")
    DATABASE_URL: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_URL: str = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}" if REDIS_PASSWORD else f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    
    # Cache settings
    CACHE_EXPIRATION: int = int(os.getenv("CACHE_EXPIRATION", 3600))  # in seconds
    
    # Retry settings
    RETRY_ATTEMPTS: int = int(os.getenv("RETRY_ATTEMPTS", 3))
    RETRY_BACKOFF: int = int(os.getenv("RETRY_BACKOFF", 2))
    
    # Application URL for OpenRouter
    APP_URL: str = os.getenv("APP_URL", "http://localhost:8000")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()