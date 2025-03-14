from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv
import sys

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.agents.multi_agent import BlogRequest, generate_blog_post

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="Technical Blog Generator API",
    description="API for generating technical blog posts using AI agents",
    version="1.0.0"
)

class BlogResponse(BaseModel):
    title: str
    content: str
    keywords: List[str]
    depth: str

@app.get("/health")
async def health_check():
    """Check if the API is running and properly configured"""
    return {
        "status": "healthy",
        "environment": "development",
        "api_key_configured": bool(os.getenv("OPENAI_API_KEY"))
    }

@app.post("/generate", response_model=BlogResponse)
async def generate_blog(request: BlogRequest):
    """Generate a technical blog post based on the provided topic"""
    try:
        # Validate API keys
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        if not (os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_CSE_ID")):
            raise HTTPException(status_code=500, detail="Google Search API credentials not configured")
        
        # Generate the blog post
        result = generate_blog_post(request)
        
        # Check for errors
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Return the result
        return {
            "title": result["title"],
            "content": result["content"],
            "keywords": result["keywords"],
            "depth": result["depth"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 