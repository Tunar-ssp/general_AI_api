from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional, Any
import uvicorn
import os
import json
import time
import logging
from dotenv import load_dotenv
from pydantic import BaseModel

# Import custom modules
from app.api.router import router as ai_router
from app.api.general_router import router as general_router
from app.api.admin_router import router as admin_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.auth import validate_api_key, add_api_key, generate_api_key

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI API Management System",
    description="A system to manage multiple AI API providers",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ai_router, prefix="/api/ai", dependencies=[Depends(validate_api_key)])
app.include_router(general_router, prefix="/api/general", dependencies=[Depends(validate_api_key)])
app.include_router(admin_router, prefix="/api/admin")

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to AI API Management System"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Initialize default admin API key if not exists
@app.on_event("startup")
async def startup_event():
    admin_key = os.getenv("ADMIN_API_KEY")
    if not admin_key:
        # Generate a default admin API key if not provided
        api_key_response = generate_api_key(name="admin", role="admin")
        logger.warning(f"No ADMIN_API_KEY found in environment. Generated new admin key: {api_key_response.key}")
        logger.warning(f"Please set this key in your .env file as ADMIN_API_KEY={api_key_response.key}")
    else:
        logger.info("Admin API key loaded from environment")

if __name__ == "__main__":
    # Use 0.0.0.0 to make the server globally accessible
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)