from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI(
    title="PPM SaaS MVP API - Minimal",
    description="Minimal version for debugging",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {
        "message": "Minimal PPM SaaS API is working! 🚀",
        "status": "healthy",
        "version": "minimal-1.0.0",
        "timestamp": datetime.now().isoformat(),
        "environment": "production" if os.getenv("VERCEL") else "development"
    }

@app.get("/debug")
async def debug_info():
    """Minimal debug endpoint"""
    return {
        "status": "debug_minimal",
        "environment_vars": {
            "vercel": bool(os.getenv("VERCEL")),
            "vercel_env": os.getenv("VERCEL_ENV", "unknown"),
            "supabase_url_set": bool(os.getenv("SUPABASE_URL")),
            "supabase_key_set": bool(os.getenv("SUPABASE_ANON_KEY"))
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Minimal health check"""
    return {
        "status": "healthy",
        "service": "minimal_backend",
        "timestamp": datetime.now().isoformat()
    }

# For deployment - Vercel serverless function handler
handler = app