from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime

app = FastAPI(
    title="PPM SaaS Test API",
    description="Minimal test version",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://orka-ppm.vercel.app",
        "https://ppm-pearl.vercel.app", 
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "PPM SaaS Test API is running",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": "test"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/debug")
async def debug():
    return {
        "status": "debug",
        "environment_vars": {
            "vercel": bool(os.getenv("VERCEL")),
            "vercel_env": os.getenv("VERCEL_ENV", "unknown")
        },
        "timestamp": datetime.now().isoformat()
    }

# For Vercel deployment
handler = app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)