from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from core.config import get_settings, Settings
import os
import sys
import pathlib

# Add the parent directory to sys.path to enable imports
parent_dir = pathlib.Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Load environment variables
load_dotenv()

app = FastAPI(title="Technical Blog Generator API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Technical Blog Generator API is running"}

@app.get("/health")
async def health_check(settings: Settings = Depends(get_settings)):
    return {
        "status": "healthy",
        "environment": settings.environment,
        "api_key_configured": bool(settings.openai_api_key)
    } 