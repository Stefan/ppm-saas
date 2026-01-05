from fastapi import FastAPI, HTTPException, status, Query, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv
from pydantic import BaseModel
from uuid import UUID
import os
import jwt
from typing import List, Dict, Any, Optional
import json
from datetime import date, datetime, timedelta
from enum import Enum

# Import AI agents
from ai_agents import create_ai_agents, RAGReporterAgent, ResourceOptimizerAgent, RiskForecasterAgent

# Load environment variables
load_dotenv()

# Environment variables with fallbacks and validation
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print(f"🔍 Backend Environment Check:")
print(f"- SUPABASE_URL set: {bool(SUPABASE_URL)}")
print(f"- SUPABASE_ANON_KEY set: {bool(SUPABASE_ANON_KEY)}")
print(f"- OPENAI_API_KEY set: {bool(OPENAI_API_KEY)}")
print(f"- SUPABASE_URL: {SUPABASE_URL}")
print(f"- SUPABASE_ANON_KEY length: {len(SUPABASE_ANON_KEY) if SUPABASE_ANON_KEY else 0}")
print(f"- OPENAI_API_KEY length: {len(OPENAI_API_KEY) if OPENAI_API_KEY else 0}")

# Create Supabase client with enhanced error handling
supabase: Client = None
try:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print(f"⚠️ WARNING: Missing environment variables - URL: {bool(SUPABASE_URL)}, KEY: {bool(SUPABASE_ANON_KEY)}")
        # Use fallback values from vercel.json
        SUPABASE_URL = SUPABASE_URL or "https://xceyrfvxooiplbmwavlb.supabase.co"
        SUPABASE_ANON_KEY = SUPABASE_ANON_KEY or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhjZXlyZnZ4b29pcGxibXdhdmxiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY4Mjg3ODEsImV4cCI6MjA4MjQwNDc4MX0.jIyJlwx2g9xn8OTSaLum6H8BKqknyxB8gYxgEKdfgqo"
        print(f"🔄 Using fallback values from configuration")
    
    # Validate JWT token format with tolerance for timestamp issues
    if SUPABASE_ANON_KEY:
        parts = SUPABASE_ANON_KEY.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid JWT format: expected 3 parts, got {len(parts)}")
        if not SUPABASE_ANON_KEY.startswith('eyJ'):
            raise ValueError("Invalid JWT format: must start with 'eyJ'")
        
        # Check JWT payload but be tolerant of timestamp issues
        try:
            payload = jwt.decode(SUPABASE_ANON_KEY, options={"verify_signature": False})
            print(f"✅ JWT payload decoded: iss={payload.get('iss')}, role={payload.get('role')}")
            
            # Check expiration but be tolerant
            now = int(datetime.now().timestamp())
            if payload.get('exp') and payload.get('exp') < now:
                print(f"⚠️ JWT token expired but continuing (exp: {payload.get('exp')}, now: {now})")
            
            if payload.get('iat') and payload.get('iat') > now:
                print(f"⚠️ JWT token issued in future but continuing (iat: {payload.get('iat')}, now: {now})")
                
        except Exception as jwt_error:
            print(f"⚠️ JWT validation warning: {jwt_error}")
        
        print(f"✅ JWT token format validated")
    
    # Create Supabase client with error handling
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print(f"✅ Supabase client created successfully")
    
    # Initialize AI agents
    ai_agents = None
    if OPENAI_API_KEY:
        try:
            ai_agents = create_ai_agents(supabase, OPENAI_API_KEY)
            print(f"✅ AI agents initialized successfully")
        except Exception as ai_error:
            print(f"⚠️ AI agents initialization failed: {ai_error}")
            print(f"⚠️ Continuing without AI functionality")
    else:
        print(f"⚠️ OPENAI_API_KEY not set - AI features disabled")
    
    # Test connection with graceful failure
    try:
        # Simple test query with timeout
        test_response = supabase.table("portfolios").select("count", count="exact").limit(1).execute()
        print(f"✅ Supabase connection test successful")
    except Exception as test_error:
        print(f"⚠️ Supabase connection test failed: {test_error}")
        print(f"⚠️ Continuing with degraded functionality")
        
except Exception as e:
    print(f"❌ Error creating Supabase client: {e}")
    print(f"❌ Error type: {type(e).__name__}")
    print(f"⚠️ Continuing without database functionality")
    # Set supabase to None for graceful degradation
    supabase = None

app = FastAPI(
    title="PPM SaaS MVP API",
    description="AI-powered Project Portfolio Management Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enhanced CORS configuration for Vercel deployment (maximum flexibility)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://orka-ppm.vercel.app",           # Current URL
        "https://ppm-saas.vercel.app",           # Likely new URL
        "https://ppm-saas-git-main.vercel.app",  # Git branch deployments
        "https://ppm-saas-*.vercel.app",         # Preview deployments
        "https://*.vercel.app",                  # All Vercel deployments
        "https://ppm-pearl.vercel.app",          # Legacy URL
        "http://localhost:3000",                 # Local development
        "http://127.0.0.1:3000",
        "https://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-Client-Info",
        "Cache-Control"
    ],
)

# ---------- Pydantic Models ----------
class HealthIndicator(str, Enum):
    green = "green"
    yellow = "yellow"
    red = "red"

class ProjectStatus(str, Enum):
    planning = "planning"
    active = "active"
    on_hold = "on-hold"
    completed = "completed"
    cancelled = "cancelled"

class ProjectCreate(BaseModel):
    portfolio_id: UUID
    name: str
    description: str | None = None
    status: ProjectStatus = ProjectStatus.planning
    priority: str | None = None
    budget: float | None = None
    start_date: date | None = None
    end_date: date | None = None
    manager_id: UUID | None = None
    team_members: List[UUID] = []

class ProjectResponse(BaseModel):
    id: str
    portfolio_id: str
    name: str
    description: str | None
    status: str
    priority: str | None
    budget: float | None
    actual_cost: float | None
    start_date: date | None
    end_date: date | None
    manager_id: str | None
    team_members: List[str]
    health: str
    created_at: datetime
    updated_at: datetime

class PortfolioCreate(BaseModel):
    name: str
    description: str | None = None
    owner_id: UUID

class PortfolioResponse(BaseModel):
    id: str
    name: str
    description: str | None
    owner_id: str
    created_at: datetime
    updated_at: datetime

# ---------- Utility Functions ----------
def convert_uuids(data):
    """Convert UUID objects to strings for JSON serialization"""
    if isinstance(data, list):
        return [convert_uuids(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_uuids(value) for key, value in data.items()}
    elif hasattr(data, '__dict__'):
        return convert_uuids(data.__dict__)
    else:
        return str(data) if isinstance(data, UUID) else data

# ---------- Authentication ----------
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract user from JWT token"""
    try:
        token = credentials.credentials
        # For now, just decode without verification for development
        payload = jwt.decode(token, options={"verify_signature": False})
        return {"user_id": payload.get("sub"), "email": payload.get("email")}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

# ---------- Endpoints ----------
@app.get("/")
async def root():
    try:
        return {
            "message": "Willkommen zur PPM SaaS API – Deine Cora-Alternative mit agentic AI 🚀",
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "database_status": "connected" if supabase else "degraded"
        }
    except Exception as e:
        print(f"Root endpoint error: {e}")
        return {
            "message": "PPM SaaS API",
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/debug")
async def debug_info():
    """Debug endpoint to check environment variables and system status"""
    try:
        env_vars = {
            "supabase_url_set": bool(os.getenv("SUPABASE_URL")),
            "supabase_key_set": bool(os.getenv("SUPABASE_ANON_KEY")),
            "supabase_url_length": len(os.getenv("SUPABASE_URL", "")),
            "supabase_key_length": len(os.getenv("SUPABASE_ANON_KEY", "")),
            "environment": "production" if os.getenv("VERCEL") else "development",
            "vercel_env": os.getenv("VERCEL_ENV", "unknown"),
            "timestamp": datetime.now().isoformat()
        }
        
        # Add actual values for debugging (be careful in production)
        if not os.getenv("VERCEL"):  # Only in development
            env_vars.update({
                "supabase_url": os.getenv("SUPABASE_URL", "not_set"),
                "supabase_key_preview": (os.getenv("SUPABASE_ANON_KEY", "")[:50] + "...") if os.getenv("SUPABASE_ANON_KEY") else "not_set"
            })
        
        # Test Supabase client status
        supabase_status = {
            "client_initialized": supabase is not None,
            "client_type": str(type(supabase)) if supabase else "None"
        }
        
        # Test database connection
        db_status = {"connected": False, "error": None}
        if supabase:
            try:
                response = supabase.table("portfolios").select("count", count="exact").limit(1).execute()
                db_status["connected"] = True
                db_status["table_accessible"] = True
            except Exception as db_error:
                db_status["error"] = str(db_error)
                db_status["error_type"] = type(db_error).__name__
        
        return {
            "status": "debug_info",
            "environment": env_vars,
            "supabase": supabase_status,
            "database": db_status,
            "message": "Backend debug information"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        if supabase is None:
            return {
                "status": "degraded",
                "database": "not_configured",
                "message": "Supabase client not initialized",
                "timestamp": datetime.now().isoformat()
            }
        
        # Test Supabase connection with timeout
        try:
            response = supabase.table("portfolios").select("count", count="exact").execute()
            return {
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as db_error:
            return {
                "status": "degraded",
                "database": "connection_failed",
                "error": str(db_error),
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "database": "unknown",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Portfolio Endpoints
@app.post("/portfolios/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(portfolio: PortfolioCreate, current_user = Depends(get_current_user)):
    try:
        response = supabase.table("portfolios").insert(portfolio.dict()).execute()
        if not response.data:
            raise HTTPException(status_code=400, detail="Fehler beim Erstellen des Portfolios")
        
        return convert_uuids(response.data[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/portfolios/")
async def list_portfolios(current_user = Depends(get_current_user)):
    response = supabase.table("portfolios").select("*").execute()
    return convert_uuids(response.data)

@app.get("/portfolios/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(portfolio_id: UUID, current_user = Depends(get_current_user)):
    response = supabase.table("portfolios").select("*").eq("id", str(portfolio_id)).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return convert_uuids(response.data[0])

# Project Endpoints
@app.post("/projects/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate, current_user = Depends(get_current_user)):
    try:
        project_data = project.dict()
        project_data['health'] = HealthIndicator.green.value
        
        response = supabase.table("projects").insert(project_data).execute()
        if not response.data:
            raise HTTPException(status_code=400, detail="Fehler beim Erstellen des Projekts")
        
        return convert_uuids(response.data[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/projects/")
async def list_projects(
    portfolio_id: UUID | None = Query(None),
    status: ProjectStatus | None = Query(None),
    current_user = Depends(get_current_user)
):
    query = supabase.table("projects").select("*")
    
    if portfolio_id:
        query = query.eq("portfolio_id", str(portfolio_id))
    if status:
        query = query.eq("status", status.value)
    
    response = query.execute()
    return convert_uuids(response.data)

@app.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID, current_user = Depends(get_current_user)):
    response = supabase.table("projects").select("*").eq("id", str(project_id)).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Project not found")
    return convert_uuids(response.data[0])

# Dashboard endpoint
@app.get("/dashboard")
async def get_dashboard_data(current_user = Depends(get_current_user)):
    """Get dashboard data for the authenticated user"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Get portfolios
        portfolios_response = supabase.table("portfolios").select("*").execute()
        portfolios = convert_uuids(portfolios_response.data)
        
        # Get projects
        projects_response = supabase.table("projects").select("*").execute()
        projects = convert_uuids(projects_response.data)
        
        # Calculate basic metrics
        total_projects = len(projects)
        active_projects = len([p for p in projects if p.get('status') == 'active'])
        completed_projects = len([p for p in projects if p.get('status') == 'completed'])
        
        # Health distribution
        health_distribution = {
            'green': len([p for p in projects if p.get('health') == 'green']),
            'yellow': len([p for p in projects if p.get('health') == 'yellow']),
            'red': len([p for p in projects if p.get('health') == 'red'])
        }
        
        # Budget summary
        total_budget = sum(float(p.get('budget', 0)) for p in projects if p.get('budget'))
        total_actual = sum(float(p.get('actual_cost', 0)) for p in projects if p.get('actual_cost'))
        
        return {
            "portfolios": portfolios,
            "projects": projects,
            "metrics": {
                "total_projects": total_projects,
                "active_projects": active_projects,
                "completed_projects": completed_projects,
                "health_distribution": health_distribution,
                "budget_summary": {
                    "total_budget": total_budget,
                    "total_actual": total_actual,
                    "variance": total_actual - total_budget
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Dashboard error: {e}")  # Server-side logging
        raise HTTPException(status_code=500, detail=f"Dashboard data retrieval failed: {str(e)}")

# Portfolio-specific endpoints that frontend expects
@app.get("/portfolio/kpis")
async def get_portfolio_kpis(current_user = Depends(get_current_user)):
    """Get portfolio KPIs - redirects to dashboard data"""
    try:
        dashboard_data = await get_dashboard_data(current_user)
        return {
            "kpis": dashboard_data["metrics"],
            "timestamp": dashboard_data["timestamp"]
        }
    except Exception as e:
        print(f"Portfolio KPIs error: {e}")
        raise HTTPException(status_code=500, detail=f"KPI data retrieval failed: {str(e)}")

@app.get("/portfolio/trends")
async def get_portfolio_trends(current_user = Depends(get_current_user)):
    """Get portfolio trends data"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Get projects for trend analysis
        projects_response = supabase.table("projects").select("*").execute()
        projects = convert_uuids(projects_response.data)
        
        # Calculate simple trends (this would be more sophisticated in production)
        trends = {
            "project_completion_rate": {
                "current": len([p for p in projects if p.get('status') == 'completed']) / max(len(projects), 1) * 100,
                "trend": "up",  # This would be calculated from historical data
                "change": 5.2
            },
            "budget_utilization": {
                "current": 75.5,  # This would be calculated from actual data
                "trend": "stable",
                "change": 0.8
            },
            "health_score": {
                "current": len([p for p in projects if p.get('health') == 'green']) / max(len(projects), 1) * 100,
                "trend": "up",
                "change": 3.1
            }
        }
        
        return {
            "trends": trends,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Portfolio trends error: {e}")
        raise HTTPException(status_code=500, detail=f"Trends data retrieval failed: {str(e)}")

@app.get("/portfolio/metrics")
async def get_portfolio_metrics(current_user = Depends(get_current_user)):
    """Get detailed portfolio metrics"""
    try:
        dashboard_data = await get_dashboard_data(current_user)
        
        # Enhanced metrics
        enhanced_metrics = {
            **dashboard_data["metrics"],
            "resource_utilization": 82.3,  # This would be calculated from resource data
            "risk_score": 2.1,  # This would be calculated from risk register
            "on_time_delivery": 87.5,  # This would be calculated from project timelines
            "cost_performance_index": 0.95  # This would be calculated from budget vs actual
        }
        
        return {
            "metrics": enhanced_metrics,
            "portfolios": dashboard_data["portfolios"],
            "timestamp": dashboard_data["timestamp"]
        }
    except Exception as e:
        print(f"Portfolio metrics error: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics data retrieval failed: {str(e)}")

# Resources Endpoints
@app.get("/resources/")
async def list_resources(current_user = Depends(get_current_user)):
    """Get all resources with utilization data"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Get resources from database
        resources_response = supabase.table("resources").select("*").execute()
        resources = convert_uuids(resources_response.data)
        
        # If no resources exist, return mock data for development
        if not resources:
            mock_resources = [
                {
                    "id": "1",
                    "name": "Alice Johnson",
                    "email": "alice.johnson@company.com",
                    "role": "Senior Developer",
                    "capacity": 40,
                    "availability": 32,
                    "hourly_rate": 85,
                    "skills": ["React", "TypeScript", "Node.js", "Python"],
                    "location": "New York",
                    "current_projects": ["proj-1", "proj-2"],
                    "utilization_percentage": 80.0,
                    "available_hours": 8.0,
                    "allocated_hours": 32.0,
                    "capacity_hours": 40.0,
                    "availability_status": "partially_allocated",
                    "can_take_more_work": True,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                },
                {
                    "id": "2",
                    "name": "Bob Smith",
                    "email": "bob.smith@company.com",
                    "role": "Project Manager",
                    "capacity": 40,
                    "availability": 40,
                    "hourly_rate": 95,
                    "skills": ["Project Management", "Agile", "Scrum", "Leadership"],
                    "location": "San Francisco",
                    "current_projects": ["proj-1"],
                    "utilization_percentage": 100.0,
                    "available_hours": 0.0,
                    "allocated_hours": 40.0,
                    "capacity_hours": 40.0,
                    "availability_status": "fully_allocated",
                    "can_take_more_work": False,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                },
                {
                    "id": "3",
                    "name": "Carol Davis",
                    "email": "carol.davis@company.com",
                    "role": "UX Designer",
                    "capacity": 40,
                    "availability": 20,
                    "hourly_rate": 75,
                    "skills": ["UI/UX Design", "Figma", "Adobe Creative Suite", "User Research"],
                    "location": "Remote",
                    "current_projects": ["proj-2", "proj-3"],
                    "utilization_percentage": 50.0,
                    "available_hours": 20.0,
                    "allocated_hours": 20.0,
                    "capacity_hours": 40.0,
                    "availability_status": "available",
                    "can_take_more_work": True,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                },
                {
                    "id": "4",
                    "name": "David Wilson",
                    "email": "david.wilson@company.com",
                    "role": "DevOps Engineer",
                    "capacity": 40,
                    "availability": 45,
                    "hourly_rate": 90,
                    "skills": ["AWS", "Docker", "Kubernetes", "CI/CD", "Terraform"],
                    "location": "Austin",
                    "current_projects": ["proj-1", "proj-2", "proj-3"],
                    "utilization_percentage": 112.5,
                    "available_hours": -5.0,
                    "allocated_hours": 45.0,
                    "capacity_hours": 40.0,
                    "availability_status": "fully_allocated",
                    "can_take_more_work": False,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            ]
            return mock_resources
        
        return resources
    except Exception as e:
        print(f"Resources error: {e}")
        raise HTTPException(status_code=500, detail=f"Resources data retrieval failed: {str(e)}")

# AI Endpoints - Real Implementation

# Pydantic models for AI requests
class RAGQueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

class ResourceOptimizationRequest(BaseModel):
    project_id: Optional[str] = None

class RiskForecastRequest(BaseModel):
    project_id: Optional[str] = None

@app.post("/ai/rag-query")
async def process_rag_query(request: RAGQueryRequest, current_user = Depends(get_current_user)):
    """Process natural language queries using RAG (Retrieval-Augmented Generation)"""
    try:
        if not ai_agents or not ai_agents.get("rag_reporter"):
            # Fallback to mock response if AI agents not available
            return {
                "response": f"I understand you're asking: '{request.query}'. However, AI features are currently unavailable. Please check that OPENAI_API_KEY is configured.",
                "sources": [],
                "confidence_score": 0.0,
                "conversation_id": request.conversation_id or f"mock_{int(datetime.now().timestamp())}",
                "response_time_ms": 100,
                "status": "ai_unavailable"
            }
        
        rag_agent = ai_agents["rag_reporter"]
        result = await rag_agent.process_rag_query(
            request.query, 
            current_user["user_id"], 
            request.conversation_id
        )
        
        return result
        
    except Exception as e:
        print(f"RAG query error: {e}")
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")

@app.post("/ai/resource-optimizer")
async def optimize_resources(request: ResourceOptimizationRequest = None, current_user = Depends(get_current_user)):
    """AI-powered resource optimization suggestions"""
    try:
        if not ai_agents or not ai_agents.get("resource_optimizer"):
            # Enhanced mock response for development
            suggestions = [
                {
                    "type": "skill_match",
                    "resource_id": "11111111-1111-1111-1111-111111111111",
                    "resource_name": "Alice Johnson",
                    "match_score": 0.95,
                    "matching_skills": ["React", "TypeScript"],
                    "current_utilization": 65.0,
                    "available_hours": 12.0,
                    "recommendation": "High skill match for frontend development tasks with available capacity",
                    "priority": "high"
                },
                {
                    "type": "underutilized",
                    "resource_id": "33333333-3333-3333-3333-333333333333",
                    "resource_name": "Carol Davis",
                    "current_utilization": 45.0,
                    "available_hours": 20.0,
                    "recommendation": "Consider allocating more work to Carol Davis who has 20.0 available hours",
                    "priority": "medium"
                }
            ]
            
            return {
                "suggestions": suggestions,
                "utilization_analysis": {
                    "11111111-1111-1111-1111-111111111111": {
                        "resource_name": "Alice Johnson",
                        "utilization_percent": 65.0,
                        "available_hours": 12.0,
                        "skills": ["React", "TypeScript", "Node.js"]
                    }
                },
                "summary": {
                    "total_suggestions": len(suggestions),
                    "high_priority": 1,
                    "avg_utilization": 55.0
                },
                "status": "ai_unavailable"
            }
        
        optimizer_agent = ai_agents["resource_optimizer"]
        project_id = request.project_id if request else None
        result = await optimizer_agent.analyze_resource_allocation(
            current_user["user_id"], 
            project_id
        )
        
        return result
        
    except Exception as e:
        print(f"Resource optimization error: {e}")
        raise HTTPException(status_code=500, detail=f"Resource optimization failed: {str(e)}")

@app.post("/ai/risk-forecast")
async def forecast_risks(request: RiskForecastRequest = None, current_user = Depends(get_current_user)):
    """AI-powered risk forecasting for projects"""
    try:
        if not ai_agents or not ai_agents.get("risk_forecaster"):
            # Mock risk predictions for development
            predictions = [
                {
                    "project_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                    "risk_type": "budget_overrun",
                    "description": "Project is at 85.0% of budget with 60% completion",
                    "probability": 0.75,
                    "impact_score": 4,
                    "confidence_score": 0.8,
                    "predicted_date": (datetime.now() + timedelta(days=14)).date().isoformat(),
                    "mitigation_suggestions": [
                        "Review remaining tasks and budget allocation",
                        "Consider scope reduction or additional funding"
                    ]
                },
                {
                    "project_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                    "risk_type": "schedule_delay",
                    "description": "Project appears behind schedule (70% time elapsed, ~50% complete)",
                    "probability": 0.6,
                    "impact_score": 3,
                    "confidence_score": 0.6,
                    "predicted_date": (datetime.now() + timedelta(days=21)).date().isoformat(),
                    "mitigation_suggestions": [
                        "Reassess project timeline and milestones",
                        "Consider additional resources"
                    ]
                }
            ]
            
            return {
                "predictions": predictions,
                "summary": {
                    "total_risks": len(predictions),
                    "high_probability": 1,
                    "critical_impact": 1
                },
                "status": "ai_unavailable"
            }
        
        forecaster_agent = ai_agents["risk_forecaster"]
        project_id = request.project_id if request else None
        result = await forecaster_agent.forecast_project_risks(
            current_user["user_id"], 
            project_id
        )
        
        return result
        
    except Exception as e:
        print(f"Risk forecasting error: {e}")
        raise HTTPException(status_code=500, detail=f"Risk forecasting failed: {str(e)}")

@app.get("/ai/conversation-history/{conversation_id}")
async def get_conversation_history(conversation_id: str, current_user = Depends(get_current_user)):
    """Get RAG conversation history"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        response = supabase.table("rag_contexts").select("*").eq(
            "conversation_id", conversation_id
        ).eq("user_id", current_user["user_id"]).order("created_at").execute()
        
        return {"conversation_history": response.data or []}
        
    except Exception as e:
        print(f"Conversation history error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation history: {str(e)}")

@app.get("/ai/metrics")
async def get_ai_metrics(current_user = Depends(get_current_user)):
    """Get AI agent performance metrics"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Get recent metrics (last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        
        response = supabase.table("ai_agent_metrics").select("*").gte(
            "created_at", thirty_days_ago
        ).execute()
        
        metrics_data = response.data or []
        
        # Aggregate metrics by agent type
        agent_stats = {}
        for metric in metrics_data:
            agent_type = metric["agent_type"]
            if agent_type not in agent_stats:
                agent_stats[agent_type] = {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "avg_response_time": 0,
                    "avg_confidence": 0,
                    "total_tokens": 0
                }
            
            stats = agent_stats[agent_type]
            stats["total_requests"] += 1
            if metric["success"]:
                stats["successful_requests"] += 1
            stats["avg_response_time"] += metric.get("response_time_ms", 0)
            if metric.get("confidence_score"):
                stats["avg_confidence"] += metric["confidence_score"]
            stats["total_tokens"] += metric.get("input_tokens", 0) + metric.get("output_tokens", 0)
        
        # Calculate averages
        for agent_type, stats in agent_stats.items():
            if stats["total_requests"] > 0:
                stats["avg_response_time"] = stats["avg_response_time"] / stats["total_requests"]
                stats["avg_confidence"] = stats["avg_confidence"] / stats["total_requests"]
                stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
        
        return {
            "agent_statistics": agent_stats,
            "total_requests": len(metrics_data),
            "ai_status": "available" if ai_agents else "unavailable"
        }
        
    except Exception as e:
        print(f"AI metrics error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get AI metrics: {str(e)}")

# For deployment - Vercel serverless function handler
handler = app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)