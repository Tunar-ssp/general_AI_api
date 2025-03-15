from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from app.core.auth import (
    validate_admin,
    generate_api_key,
    APIKeyCreate,
    APIKeyResponse,
    API_KEYS
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Create a new API key (admin only)
@router.post("/keys", response_model=APIKeyResponse, dependencies=[Depends(validate_admin)])
async def create_api_key(request: APIKeyCreate):
    """Create a new API key (admin only)"""
    try:
        api_key = generate_api_key(name=request.name, role=request.role)
        logger.info(f"New API key created for {request.name} with role {request.role}")
        return api_key
    except Exception as e:
        logger.error(f"Error creating API key: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# List all API keys (admin only)
@router.get("/keys", dependencies=[Depends(validate_admin)])
async def list_api_keys():
    """List all API keys (admin only)"""
    try:
        keys = []
        for key, data in API_KEYS.items():
            keys.append({
                "key": key[:8] + "...",  # Only show first 8 chars for security
                "name": data.get("name", ""),
                "role": data.get("role", "user"),
                "created_at": data.get("created_at", 0)
            })
        return {"keys": keys}
    except Exception as e:
        logger.error(f"Error listing API keys: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Revoke an API key (admin only)
@router.delete("/keys/{key_prefix}", dependencies=[Depends(validate_admin)])
async def revoke_api_key(key_prefix: str):
    """Revoke an API key by its prefix (admin only)"""
    try:
        # Find the key that starts with the given prefix
        key_to_revoke = None
        for key in API_KEYS.keys():
            if key.startswith(key_prefix):
                key_to_revoke = key
                break
        
        if not key_to_revoke:
            raise HTTPException(status_code=404, detail=f"API key with prefix {key_prefix} not found")
        
        # Remove the key
        user_data = API_KEYS.pop(key_to_revoke)
        logger.info(f"API key for {user_data.get('name', 'unknown')} has been revoked")
        
        return {"message": f"API key for {user_data.get('name', 'unknown')} has been revoked"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking API key: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))