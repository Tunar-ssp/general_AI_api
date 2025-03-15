from fastapi import APIRouter, HTTPException, Depends, Request, Body, Query, Path
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
import logging
import time
import json
from datetime import datetime

from app.cache.redis import cache
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Define request and response models
class GenericRequest(BaseModel):
    """Generic request model that can handle any JSON payload"""
    data: Dict[str, Any] = Field(..., description="Any JSON data to be processed")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata for the request")

class GenericResponse(BaseModel):
    """Generic response model"""
    data: Dict[str, Any] = Field(..., description="Response data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")
    success: bool = Field(True, description="Whether the request was successful")
    error: Optional[str] = Field(None, description="Error message if any")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Response timestamp")

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Response timestamp")

# Generic CRUD endpoints
@router.post("/data", response_model=GenericResponse, description="Create a new data entry")
async def create_data(request: GenericRequest):
    """Create a new data entry"""
    try:
        # Generate a unique ID for the data
        import uuid
        data_id = str(uuid.uuid4())
        
        # Add timestamp
        timestamp = datetime.now().isoformat()
        
        # Prepare data to store
        data_to_store = {
            "id": data_id,
            "created_at": timestamp,
            "updated_at": timestamp,
            **request.data
        }
        
        # Store in cache (in a real app, you might want to use a database)
        cache_key = f"data:{data_id}"
        cache.set(cache_key, data_to_store)
        
        return GenericResponse(
            data={"id": data_id, **request.data},
            metadata={
                "created_at": timestamp,
                **(request.metadata or {})
            }
        )
    except Exception as e:
        logger.error(f"Error creating data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/{data_id}", response_model=GenericResponse, description="Get data by ID")
async def get_data(data_id: str = Path(..., description="The ID of the data to retrieve")):
    """Get data by ID"""
    try:
        # Retrieve from cache
        cache_key = f"data:{data_id}"
        data = cache.get(cache_key)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"Data with ID {data_id} not found")
        
        return GenericResponse(
            data=data,
            metadata={
                "retrieved_at": datetime.now().isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/data/{data_id}", response_model=GenericResponse, description="Update data by ID")
async def update_data(
    request: GenericRequest,
    data_id: str = Path(..., description="The ID of the data to update")
):
    """Update data by ID"""
    try:
        # Retrieve existing data
        cache_key = f"data:{data_id}"
        existing_data = cache.get(cache_key)
        
        if not existing_data:
            raise HTTPException(status_code=404, detail=f"Data with ID {data_id} not found")
        
        # Update data
        updated_data = {
            **existing_data,
            **request.data,
            "updated_at": datetime.now().isoformat()
        }
        
        # Store updated data
        cache.set(cache_key, updated_data)
        
        return GenericResponse(
            data=updated_data,
            metadata={
                "updated_at": updated_data["updated_at"],
                **(request.metadata or {})
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/data/{data_id}", response_model=GenericResponse, description="Delete data by ID")
async def delete_data(data_id: str = Path(..., description="The ID of the data to delete")):
    """Delete data by ID"""
    try:
        # Retrieve existing data to confirm it exists
        cache_key = f"data:{data_id}"
        existing_data = cache.get(cache_key)
        
        if not existing_data:
            raise HTTPException(status_code=404, detail=f"Data with ID {data_id} not found")
        
        # Delete data
        cache.delete(cache_key)
        
        return GenericResponse(
            data={"id": data_id, "deleted": True},
            metadata={
                "deleted_at": datetime.now().isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", description="Health check endpoint")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis connection
        redis_ok = cache.redis_client.ping()
        
        return GenericResponse(
            data={
                "status": "healthy" if redis_ok else "degraded",
                "services": {
                    "redis": "up" if redis_ok else "down"
                }
            },
            metadata={
                "checked_at": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return GenericResponse(
            data={
                "status": "unhealthy",
                "services": {
                    "redis": "down"
                }
            },
            metadata={
                "checked_at": datetime.now().isoformat()
            },
            success=False,
            error=str(e)
        )

# File upload/download endpoints (mock implementation)
class FileMetadata(BaseModel):
    """File metadata model"""
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="File content type")
    size: int = Field(..., description="File size in bytes")

@router.post("/files", response_model=GenericResponse, description="Upload a file (mock)")
async def upload_file(file_metadata: FileMetadata):
    """Mock file upload endpoint"""
    try:
        # Generate a file ID
        import uuid
        file_id = str(uuid.uuid4())
        
        # In a real implementation, you would save the file to disk or cloud storage
        # Here we just store the metadata in cache
        file_data = {
            "id": file_id,
            **file_metadata.dict(),
            "uploaded_at": datetime.now().isoformat()
        }
        
        cache_key = f"file:{file_id}"
        cache.set(cache_key, file_data)
        
        return GenericResponse(
            data={
                "file_id": file_id,
                **file_metadata.dict()
            },
            metadata={
                "uploaded_at": file_data["uploaded_at"]
            }
        )
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/{file_id}", response_model=GenericResponse, description="Get file metadata")
async def get_file_metadata(file_id: str = Path(..., description="The ID of the file")):
    """Get file metadata"""
    try:
        cache_key = f"file:{file_id}"
        file_data = cache.get(cache_key)
        
        if not file_data:
            raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
        
        return GenericResponse(
            data=file_data,
            metadata={
                "retrieved_at": datetime.now().isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving file metadata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))