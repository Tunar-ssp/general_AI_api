import os
import time
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader, APIKeyQuery
from pydantic import BaseModel
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Define API key security schemes
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)

# Load API keys from environment
API_KEYS = {}

# Add admin API key from environment
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")
if ADMIN_API_KEY:
    API_KEYS[ADMIN_API_KEY] = {"role": "admin", "name": "admin"}

# Function to add a new API key
def add_api_key(key: str, user_data: Dict[str, Any]) -> None:
    """Add a new API key to the system"""
    API_KEYS[key] = user_data

# Function to get API key from header or query parameter
async def get_api_key(
    api_key_header: str = Security(api_key_header),
    api_key_query: str = Security(api_key_query),
) -> str:
    """Get API key from header or query parameter"""
    if api_key_header:
        return api_key_header
    if api_key_query:
        return api_key_query
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="API key is missing",
        headers={"WWW-Authenticate": "ApiKey"},
    )

# Function to validate API key
async def validate_api_key(api_key: str = Depends(get_api_key)) -> Dict[str, Any]:
    """Validate API key and return user data"""
    if api_key in API_KEYS:
        # Log API key usage
        logger.info(f"API key used: {api_key[:5]}...")
        return API_KEYS[api_key]
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "ApiKey"},
    )

# Function to check if user has admin role
async def validate_admin(user_data: Dict[str, Any] = Depends(validate_api_key)) -> Dict[str, Any]:
    """Validate if the user has admin role"""
    if user_data.get("role") == "admin":
        return user_data
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions",
    )

# API key management models
class APIKeyCreate(BaseModel):
    """Model for creating a new API key"""
    name: str
    role: str = "user"

class APIKeyResponse(BaseModel):
    """Model for API key response"""
    key: str
    name: str
    role: str
    created_at: float

# Function to generate a new API key
def generate_api_key(name: str, role: str = "user") -> APIKeyResponse:
    """Generate a new API key"""
    import uuid
    key = f"ak-{uuid.uuid4().hex}"
    created_at = time.time()
    user_data = {"name": name, "role": role, "created_at": created_at}
    API_KEYS[key] = user_data
    return APIKeyResponse(key=key, name=name, role=role, created_at=created_at)