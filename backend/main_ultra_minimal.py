def handler(request):
    """Ultra minimal handler for Vercel"""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": '{"message": "Ultra minimal backend is working!", "status": "healthy"}'
    }

# Also support FastAPI style for testing
try:
    from fastapi import FastAPI
    
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {"message": "Ultra minimal FastAPI backend is working!", "status": "healthy"}
    
    @app.get("/debug")
    async def debug():
        return {"status": "ultra_minimal", "message": "Debug endpoint working"}
        
except ImportError:
    # Fallback if FastAPI is not available
    pass