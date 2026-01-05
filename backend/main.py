from fastapi import FastAPI, HTTPException, status, Query, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv
from pydantic import BaseModel
from uuid import UUID
import os
import jwt
from typing import List, Dict, Any, Optional, Union
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
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.planning
    priority: Optional[str] = None
    budget: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    manager_id: Optional[UUID] = None
    team_members: List[UUID] = []

class ProjectResponse(BaseModel):
    id: str
    portfolio_id: str
    name: str
    description: Optional[str]
    status: str
    priority: Optional[str]
    budget: Optional[float]
    actual_cost: Optional[float]
    start_date: Optional[date]
    end_date: Optional[date]
    manager_id: Optional[str]
    team_members: List[str]
    health: str
    created_at: datetime
    updated_at: datetime

class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None
    owner_id: UUID

class PortfolioResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    owner_id: str
    created_at: datetime
    updated_at: datetime

# Resource Models
class ResourceCreate(BaseModel):
    name: str
    email: str
    role: Optional[str] = None
    capacity: int = 40  # hours per week
    availability: int = 100  # percentage
    hourly_rate: Optional[float] = None
    skills: List[str] = []
    location: Optional[str] = None

class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    capacity: Optional[int] = None
    availability: Optional[int] = None
    hourly_rate: Optional[float] = None
    skills: Optional[List[str]] = None
    location: Optional[str] = None

class ResourceResponse(BaseModel):
    id: str
    name: str
    email: str
    role: Optional[str]
    capacity: int
    availability: int
    hourly_rate: Optional[float]
    skills: List[str]
    location: Optional[str]
    current_projects: List[str] = []
    utilization_percentage: float = 0.0
    available_hours: float = 0.0
    allocated_hours: float = 0.0
    capacity_hours: int = 40
    availability_status: str = "available"
    can_take_more_work: bool = True
    created_at: datetime
    updated_at: datetime

class ResourceSearchRequest(BaseModel):
    skills: Optional[List[str]] = None
    min_capacity: Optional[int] = None
    max_capacity: Optional[int] = None
    min_availability: Optional[int] = None
    role: Optional[str] = None
    location: Optional[str] = None

class ResourceAllocationSuggestion(BaseModel):
    resource_id: str
    resource_name: str
    match_score: float
    matching_skills: List[str]
    availability: int
    reasoning: str

# Financial Tracking Models
class BudgetAlertRuleCreate(BaseModel):
    project_id: Optional[UUID] = None
    threshold_percentage: float
    alert_type: str
    recipients: List[str]
    is_active: bool = True

class BudgetAlertRuleResponse(BaseModel):
    id: str
    project_id: Optional[str]
    threshold_percentage: float
    alert_type: str
    recipients: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class BudgetAlert(BaseModel):
    project_id: UUID
    alert_type: str
    threshold_percentage: float
    current_percentage: float
    budget_amount: float
    actual_cost: float
    variance: float
    message: str
    recipients: List[str]

class BudgetAlertResponse(BaseModel):
    id: str
    project_id: str
    alert_type: str
    threshold_percentage: float
    current_percentage: float
    budget_amount: float
    actual_cost: float
    variance: float
    message: str
    recipients: List[str]
    is_resolved: bool
    created_at: datetime
    resolved_at: Optional[datetime]

class FinancialTrackingCreate(BaseModel):
    project_id: UUID
    category: str
    description: Optional[str] = None
    planned_amount: float
    actual_amount: float = 0.0
    currency: str = "USD"
    exchange_rate: float = 1.0
    date_incurred: date

class FinancialTrackingResponse(BaseModel):
    id: str
    project_id: str
    category: str
    description: Optional[str]
    planned_amount: float
    actual_amount: float
    currency: str
    exchange_rate: float
    date_incurred: date
    recorded_by: Optional[str]
    created_at: datetime
    updated_at: datetime

# Risk and Issue Management Models
class RiskCategory(str, Enum):
    technical = "technical"
    financial = "financial"
    resource = "resource"
    schedule = "schedule"
    external = "external"

class RiskStatus(str, Enum):
    identified = "identified"
    analyzing = "analyzing"
    mitigating = "mitigating"
    closed = "closed"

class IssueSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class IssueStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"

class RiskCreate(BaseModel):
    project_id: UUID
    title: str
    description: Optional[str] = None
    category: RiskCategory
    probability: float  # 0.0 to 1.0
    impact: float  # 0.0 to 1.0
    mitigation: Optional[str] = None
    owner_id: Optional[UUID] = None
    due_date: Optional[date] = None

class RiskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[RiskCategory] = None
    probability: Optional[float] = None
    impact: Optional[float] = None
    status: Optional[RiskStatus] = None
    mitigation: Optional[str] = None
    owner_id: Optional[UUID] = None
    due_date: Optional[date] = None

class RiskResponse(BaseModel):
    id: str
    project_id: str
    title: str
    description: Optional[str]
    category: str
    probability: float
    impact: float
    risk_score: float
    status: str
    mitigation: Optional[str]
    owner_id: Optional[str]
    due_date: Optional[date]
    created_at: datetime
    updated_at: datetime

class IssueCreate(BaseModel):
    project_id: UUID
    risk_id: Optional[UUID] = None  # Link to risk if issue comes from risk materialization
    title: str
    description: Optional[str] = None
    severity: IssueSeverity = IssueSeverity.medium
    assigned_to: Optional[UUID] = None
    reporter_id: Optional[UUID] = None
    due_date: Optional[date] = None

class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[IssueSeverity] = None
    status: Optional[IssueStatus] = None
    assigned_to: Optional[UUID] = None
    resolution: Optional[str] = None
    due_date: Optional[date] = None

class IssueResponse(BaseModel):
    id: str
    project_id: str
    risk_id: Optional[str]
    title: str
    description: Optional[str]
    severity: str
    status: str
    assigned_to: Optional[str]
    reporter_id: Optional[str]
    resolution: Optional[str]
    resolution_date: Optional[datetime]
    due_date: Optional[date]
    created_at: datetime
    updated_at: datetime

# Role and Permission Models
class UserRole(str, Enum):
    admin = "admin"
    portfolio_manager = "portfolio_manager"
    project_manager = "project_manager"
    resource_manager = "resource_manager"
    team_member = "team_member"
    viewer = "viewer"

class Permission(str, Enum):
    # Portfolio permissions
    portfolio_create = "portfolio_create"
    portfolio_read = "portfolio_read"
    portfolio_update = "portfolio_update"
    portfolio_delete = "portfolio_delete"
    
    # Project permissions
    project_create = "project_create"
    project_read = "project_read"
    project_update = "project_update"
    project_delete = "project_delete"
    
    # Resource permissions
    resource_create = "resource_create"
    resource_read = "resource_read"
    resource_update = "resource_update"
    resource_delete = "resource_delete"
    resource_allocate = "resource_allocate"
    
    # Financial permissions
    financial_read = "financial_read"
    financial_create = "financial_create"
    financial_update = "financial_update"
    financial_delete = "financial_delete"
    budget_alert_manage = "budget_alert_manage"
    
    # Risk and Issue permissions
    risk_create = "risk_create"
    risk_read = "risk_read"
    risk_update = "risk_update"
    risk_delete = "risk_delete"
    issue_create = "issue_create"
    issue_read = "issue_read"
    issue_update = "issue_update"
    issue_delete = "issue_delete"
    
    # AI permissions
    ai_rag_query = "ai_rag_query"
    ai_resource_optimize = "ai_resource_optimize"
    ai_risk_forecast = "ai_risk_forecast"
    ai_metrics_read = "ai_metrics_read"
    
    # Admin permissions
    user_manage = "user_manage"
    role_manage = "role_manage"
    system_admin = "system_admin"

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[Permission]
    is_active: bool = True

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[Permission]] = None
    is_active: Optional[bool] = None

class RoleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    permissions: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class UserRoleAssignment(BaseModel):
    user_id: UUID
    role_id: UUID

class UserRoleResponse(BaseModel):
    id: str
    user_id: str
    role_id: str
    role_name: str
    permissions: List[str]
    assigned_at: datetime

# AI Request Models
class RAGQueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

class ResourceOptimizationRequest(BaseModel):
    project_id: Optional[str] = None

class RiskForecastRequest(BaseModel):
    project_id: Optional[str] = None

# ---------- Financial Calculation Functions ----------
# Base exchange rates from USD (in a real system, these would be fetched from an external API)
# Using USD as base currency ensures reciprocal consistency
BASE_EXCHANGE_RATES = {
    'USD': 1.0,
    'EUR': 0.85,
    'GBP': 0.73,
    'JPY': 110.0,
    'CAD': 1.25,
    'AUD': 1.35
}

def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """Get exchange rate from one currency to another using USD as base"""
    if from_currency == to_currency:
        return 1.0
    
    # Convert via USD to ensure reciprocal consistency
    # Rate = (to_currency_per_usd) / (from_currency_per_usd)
    from_rate = BASE_EXCHANGE_RATES.get(from_currency, 1.0)
    to_rate = BASE_EXCHANGE_RATES.get(to_currency, 1.0)
    
    return to_rate / from_rate

def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    """Convert amount from one currency to another with improved precision"""
    if from_currency == to_currency:
        return amount
    
    exchange_rate = get_exchange_rate(from_currency, to_currency)
    # Round to 6 decimal places to handle floating point precision issues
    return round(amount * exchange_rate, 6)

def calculate_project_budget_variance(project: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate detailed budget variance for a project"""
    try:
        budget = float(project.get('budget', 0))
        actual_cost = float(project.get('actual_cost', 0))
        
        if budget <= 0:
            return {
                'budget_amount': budget,
                'actual_cost': actual_cost,
                'variance_amount': actual_cost,
                'variance_percentage': 0.0,
                'utilization_percentage': 0.0,
                'status': 'no_budget'
            }
        
        variance_amount = actual_cost - budget
        variance_percentage = (variance_amount / budget) * 100
        utilization_percentage = (actual_cost / budget) * 100
        
        # Determine status based on variance
        if variance_percentage > 10:
            status = 'over_budget'
        elif variance_percentage < -10:
            status = 'under_budget'
        else:
            status = 'on_budget'
        
        return {
            'budget_amount': budget,
            'actual_cost': actual_cost,
            'variance_amount': variance_amount,
            'variance_percentage': round(variance_percentage, 2),
            'utilization_percentage': round(utilization_percentage, 2),
            'status': status
        }
        
    except Exception as e:
        print(f"Error calculating project budget variance: {e}")
        return {
            'budget_amount': 0.0,
            'actual_cost': 0.0,
            'variance_amount': 0.0,
            'variance_percentage': 0.0,
            'utilization_percentage': 0.0,
            'status': 'error'
        }

# ---------- Role-Based Access Control System ----------

# Default role permissions configuration
DEFAULT_ROLE_PERMISSIONS = {
    UserRole.admin: [
        # Full access to everything
        Permission.portfolio_create, Permission.portfolio_read, Permission.portfolio_update, Permission.portfolio_delete,
        Permission.project_create, Permission.project_read, Permission.project_update, Permission.project_delete,
        Permission.resource_create, Permission.resource_read, Permission.resource_update, Permission.resource_delete, Permission.resource_allocate,
        Permission.financial_read, Permission.financial_create, Permission.financial_update, Permission.financial_delete, Permission.budget_alert_manage,
        Permission.risk_create, Permission.risk_read, Permission.risk_update, Permission.risk_delete,
        Permission.issue_create, Permission.issue_read, Permission.issue_update, Permission.issue_delete,
        Permission.ai_rag_query, Permission.ai_resource_optimize, Permission.ai_risk_forecast, Permission.ai_metrics_read,
        Permission.user_manage, Permission.role_manage, Permission.system_admin
    ],
    UserRole.portfolio_manager: [
        # Portfolio and project management
        Permission.portfolio_create, Permission.portfolio_read, Permission.portfolio_update,
        Permission.project_create, Permission.project_read, Permission.project_update,
        Permission.resource_read, Permission.resource_allocate,
        Permission.financial_read, Permission.financial_create, Permission.financial_update, Permission.budget_alert_manage,
        Permission.risk_read, Permission.risk_update,
        Permission.issue_read, Permission.issue_update,
        Permission.ai_rag_query, Permission.ai_resource_optimize, Permission.ai_risk_forecast, Permission.ai_metrics_read
    ],
    UserRole.project_manager: [
        # Project-specific management
        Permission.project_read, Permission.project_update,
        Permission.resource_read, Permission.resource_allocate,
        Permission.financial_read, Permission.financial_create, Permission.financial_update,
        Permission.risk_create, Permission.risk_read, Permission.risk_update,
        Permission.issue_create, Permission.issue_read, Permission.issue_update,
        Permission.ai_rag_query, Permission.ai_resource_optimize, Permission.ai_risk_forecast
    ],
    UserRole.resource_manager: [
        # Resource management focus
        Permission.project_read,
        Permission.resource_create, Permission.resource_read, Permission.resource_update, Permission.resource_allocate,
        Permission.financial_read,
        Permission.risk_read,
        Permission.issue_read,
        Permission.ai_rag_query, Permission.ai_resource_optimize
    ],
    UserRole.team_member: [
        # Basic project participation
        Permission.project_read,
        Permission.resource_read,
        Permission.financial_read,
        Permission.risk_read, Permission.risk_create,
        Permission.issue_read, Permission.issue_create, Permission.issue_update,
        Permission.ai_rag_query
    ],
    UserRole.viewer: [
        # Read-only access
        Permission.portfolio_read,
        Permission.project_read,
        Permission.resource_read,
        Permission.financial_read,
        Permission.risk_read,
        Permission.issue_read,
        Permission.ai_rag_query
    ]
}

class RoleBasedAccessControl:
    """Role-Based Access Control system for managing user permissions"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self._permission_cache = {}
        self._cache_ttl = 300  # 5 minutes cache TTL
        self._cache_timestamps = {}
    
    async def get_user_permissions(self, user_id: str) -> List[Permission]:
        """Get all permissions for a user based on their roles"""
        try:
            # Check cache first
            cache_key = f"user_permissions_{user_id}"
            if self._is_cache_valid(cache_key):
                return self._permission_cache[cache_key]
            
            if not self.supabase:
                # Fallback: return admin permissions for development
                permissions = DEFAULT_ROLE_PERMISSIONS[UserRole.admin]
                self._update_cache(cache_key, permissions)
                return permissions
            
            # Get user's role assignments
            response = self.supabase.table("user_roles").select(
                "role_id, roles(name, permissions)"
            ).eq("user_id", user_id).execute()
            
            if not response.data:
                # No roles assigned, return viewer permissions as default
                permissions = DEFAULT_ROLE_PERMISSIONS[UserRole.viewer]
                self._update_cache(cache_key, permissions)
                return permissions
            
            # Collect all permissions from all roles
            all_permissions = set()
            for assignment in response.data:
                role_data = assignment.get("roles", {})
                role_permissions = role_data.get("permissions", [])
                
                # Convert string permissions to Permission enum
                for perm_str in role_permissions:
                    try:
                        permission = Permission(perm_str)
                        all_permissions.add(permission)
                    except ValueError:
                        print(f"Warning: Invalid permission '{perm_str}' found in role")
                        continue
            
            permissions = list(all_permissions)
            self._update_cache(cache_key, permissions)
            return permissions
            
        except Exception as e:
            print(f"Error getting user permissions: {e}")
            # Fallback to viewer permissions on error
            return DEFAULT_ROLE_PERMISSIONS[UserRole.viewer]
    
    async def has_permission(self, user_id: str, required_permission: Permission) -> bool:
        """Check if user has a specific permission"""
        try:
            user_permissions = await self.get_user_permissions(user_id)
            return required_permission in user_permissions
        except Exception as e:
            print(f"Error checking permission: {e}")
            return False
    
    async def has_any_permission(self, user_id: str, required_permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions"""
        try:
            user_permissions = await self.get_user_permissions(user_id)
            return any(perm in user_permissions for perm in required_permissions)
        except Exception as e:
            print(f"Error checking permissions: {e}")
            return False
    
    async def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """Assign a role to a user"""
        try:
            if not self.supabase:
                return False
            
            # Check if role exists
            role_response = self.supabase.table("roles").select("id").eq("id", role_id).execute()
            if not role_response.data:
                return False
            
            # Create or update role assignment
            assignment_data = {
                "user_id": user_id,
                "role_id": role_id
            }
            
            response = self.supabase.table("user_roles").upsert(assignment_data).execute()
            
            if response.data:
                # Clear user's permission cache
                self._clear_user_cache(user_id)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error assigning role to user: {e}")
            return False
    
    async def remove_role_from_user(self, user_id: str, role_id: str) -> bool:
        """Remove a role from a user"""
        try:
            if not self.supabase:
                return False
            
            response = self.supabase.table("user_roles").delete().eq(
                "user_id", user_id
            ).eq("role_id", role_id).execute()
            
            if response.data:
                # Clear user's permission cache
                self._clear_user_cache(user_id)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error removing role from user: {e}")
            return False
    
    async def create_default_roles(self) -> bool:
        """Create default roles in the database if they don't exist"""
        try:
            if not self.supabase:
                return False
            
            for role_enum, permissions in DEFAULT_ROLE_PERMISSIONS.items():
                # Check if role already exists
                existing_role = self.supabase.table("roles").select("id").eq("name", role_enum.value).execute()
                
                if not existing_role.data:
                    # Create the role
                    role_data = {
                        "name": role_enum.value,
                        "description": f"Default {role_enum.value.replace('_', ' ').title()} role",
                        "permissions": [perm.value for perm in permissions],
                        "is_active": True
                    }
                    
                    self.supabase.table("roles").insert(role_data).execute()
                    print(f"Created default role: {role_enum.value}")
            
            return True
            
        except Exception as e:
            print(f"Error creating default roles: {e}")
            return False
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self._permission_cache:
            return False
        
        timestamp = self._cache_timestamps.get(cache_key, 0)
        return (datetime.now().timestamp() - timestamp) < self._cache_ttl
    
    def _update_cache(self, cache_key: str, permissions: List[Permission]):
        """Update permission cache"""
        self._permission_cache[cache_key] = permissions
        self._cache_timestamps[cache_key] = datetime.now().timestamp()
    
    def _clear_user_cache(self, user_id: str):
        """Clear cached permissions for a user"""
        cache_key = f"user_permissions_{user_id}"
        if cache_key in self._permission_cache:
            del self._permission_cache[cache_key]
        if cache_key in self._cache_timestamps:
            del self._cache_timestamps[cache_key]
    
    def clear_all_cache(self):
        """Clear all cached permissions"""
        self._permission_cache.clear()
        self._cache_timestamps.clear()

# Initialize RBAC system
rbac = RoleBasedAccessControl(supabase)

# Permission dependency functions
def require_permission(required_permission: Permission):
    """Dependency to require a specific permission"""
    async def permission_checker(current_user = Depends(get_current_user)):
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        has_perm = await rbac.has_permission(user_id, required_permission)
        if not has_perm:
            raise HTTPException(
                status_code=403, 
                detail=f"Insufficient permissions. Required: {required_permission.value}"
            )
        
        return current_user
    
    return permission_checker

def require_any_permission(required_permissions: List[Permission]):
    """Dependency to require any of the specified permissions"""
    async def permission_checker(current_user = Depends(get_current_user)):
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        has_any_perm = await rbac.has_any_permission(user_id, required_permissions)
        if not has_any_perm:
            perm_names = [perm.value for perm in required_permissions]
            raise HTTPException(
                status_code=403, 
                detail=f"Insufficient permissions. Required one of: {', '.join(perm_names)}"
            )
        
        return current_user
    
    return permission_checker

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

def calculate_advanced_skill_match_score(required_skills: List[str], resource_skills: List[str]) -> Dict[str, Any]:
    """Calculate advanced skill matching score with detailed breakdown"""
    if not required_skills:
        return {
            'match_score': 1.0,
            'matching_skills': resource_skills,
            'missing_skills': [],
            'extra_skills': resource_skills
        }
    
    # Normalize skills to lowercase for case-insensitive matching
    required_normalized = [skill.lower() for skill in required_skills]
    resource_normalized = [skill.lower() for skill in resource_skills]
    
    # Find matches
    matching_normalized = set(required_normalized) & set(resource_normalized)
    matching_skills = []
    
    # Get original case skills for matching ones
    for skill in required_skills:
        if skill.lower() in matching_normalized:
            matching_skills.append(skill)
    
    # Calculate missing and extra skills
    missing_skills = [skill for skill in required_skills if skill.lower() not in matching_normalized]
    extra_skills = [skill for skill in resource_skills if skill.lower() not in required_normalized]
    
    # Calculate match score
    match_score = len(matching_skills) / len(required_skills) if required_skills else 1.0
    
    return {
        'match_score': match_score,
        'matching_skills': matching_skills,
        'missing_skills': missing_skills,
        'extra_skills': extra_skills
    }

def calculate_enhanced_resource_availability(resource: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate enhanced resource availability with utilization tracking"""
    try:
        capacity_hours = resource.get('capacity', 40)
        availability_percentage = resource.get('availability', 100) / 100.0
        effective_capacity = capacity_hours * availability_percentage
        
        # Calculate current allocations from project_resources table
        total_allocated_hours = 0.0
        current_projects = resource.get('current_projects', [])
        
        if supabase and current_projects:
            for project_id in current_projects:
                try:
                    allocation_response = supabase.table("project_resources").select("allocation_percentage").eq(
                        "resource_id", resource['id']
                    ).eq("project_id", project_id).execute()
                    
                    if allocation_response.data:
                        allocation_percentage = allocation_response.data[0].get('allocation_percentage', 0) / 100.0
                        total_allocated_hours += effective_capacity * allocation_percentage
                except Exception as e:
                    print(f"Error calculating allocation for project {project_id}: {e}")
                    continue
        
        # Calculate metrics
        utilization_percentage = (total_allocated_hours / effective_capacity * 100) if effective_capacity > 0 else 0
        available_hours = max(0, effective_capacity - total_allocated_hours)
        
        # Determine availability status
        if utilization_percentage >= 100:
            availability_status = "fully_allocated"
            can_take_more_work = False
        elif utilization_percentage >= 80:
            availability_status = "mostly_allocated"
            can_take_more_work = True
        elif utilization_percentage >= 50:
            availability_status = "partially_allocated"
            can_take_more_work = True
        else:
            availability_status = "available"
            can_take_more_work = True
        
        return {
            'utilization_percentage': round(utilization_percentage, 1),
            'available_hours': round(available_hours, 1),
            'allocated_hours': round(total_allocated_hours, 1),
            'capacity_hours': capacity_hours,
            'availability_status': availability_status,
            'can_take_more_work': can_take_more_work
        }
        
    except Exception as e:
        print(f"Error calculating resource availability: {e}")
        return {
            'utilization_percentage': 0.0,
            'available_hours': float(resource.get('capacity', 40)),
            'allocated_hours': 0.0,
            'capacity_hours': resource.get('capacity', 40),
            'availability_status': 'available',
            'can_take_more_work': True
        }

def calculate_budget_variance(project: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate budget variance and utilization for a project"""
    try:
        budget = float(project.get('budget', 0))
        actual_cost = float(project.get('actual_cost', 0))
        
        if budget <= 0:
            return {
                'budget_amount': budget,
                'actual_cost': actual_cost,
                'variance': actual_cost,
                'variance_percentage': 0.0,
                'utilization_percentage': 0.0,
                'status': 'no_budget'
            }
        
        variance = actual_cost - budget
        variance_percentage = (variance / budget) * 100
        utilization_percentage = (actual_cost / budget) * 100
        
        # Determine status
        if utilization_percentage >= 100:
            status = 'over_budget'
        elif utilization_percentage >= 90:
            status = 'critical'
        elif utilization_percentage >= 80:
            status = 'warning'
        else:
            status = 'on_track'
        
        return {
            'budget_amount': budget,
            'actual_cost': actual_cost,
            'variance': variance,
            'variance_percentage': round(variance_percentage, 2),
            'utilization_percentage': round(utilization_percentage, 2),
            'status': status
        }
        
    except Exception as e:
        print(f"Error calculating budget variance: {e}")
        return {
            'budget_amount': 0.0,
            'actual_cost': 0.0,
            'variance': 0.0,
            'variance_percentage': 0.0,
            'utilization_percentage': 0.0,
            'status': 'error'
        }

def check_budget_thresholds(project: Dict[str, Any], alert_rules: List[Dict[str, Any]]) -> List[BudgetAlert]:
    """Check if project budget exceeds any configured thresholds"""
    try:
        budget_info = calculate_budget_variance(project)
        alerts = []
        
        if budget_info['status'] == 'no_budget' or budget_info['status'] == 'error':
            return alerts
        
        current_percentage = budget_info['utilization_percentage']
        project_id = UUID(project['id'])
        
        # Check each alert rule
        for rule in alert_rules:
            # Skip inactive rules
            if not rule.get('is_active', True):
                continue
            
            # Check if rule applies to this project
            rule_project_id = rule.get('project_id')
            if rule_project_id and str(rule_project_id) != str(project_id):
                continue
            
            threshold = rule['threshold_percentage']
            
            # Check if threshold is exceeded
            if current_percentage >= threshold:
                alert_type = rule['alert_type']
                
                # Create alert message
                if alert_type == 'overrun':
                    message = f"Project '{project['name']}' has exceeded budget by {current_percentage - 100:.1f}% (${budget_info['actual_cost']:,.2f} of ${budget_info['budget_amount']:,.2f})"
                elif alert_type == 'critical':
                    message = f"Project '{project['name']}' is at {current_percentage:.1f}% of budget - immediate attention required (${budget_info['actual_cost']:,.2f} of ${budget_info['budget_amount']:,.2f})"
                else:  # warning
                    message = f"Project '{project['name']}' has reached {current_percentage:.1f}% of budget (${budget_info['actual_cost']:,.2f} of ${budget_info['budget_amount']:,.2f})"
                
                alert = BudgetAlert(
                    project_id=project_id,
                    alert_type=alert_type,
                    threshold_percentage=threshold,
                    current_percentage=current_percentage,
                    budget_amount=budget_info['budget_amount'],
                    actual_cost=budget_info['actual_cost'],
                    variance=budget_info['variance'],
                    message=message,
                    recipients=rule['recipients']
                )
                alerts.append(alert)
        
        return alerts
        
    except Exception as e:
        print(f"Error checking budget thresholds: {e}")
        return []

async def send_budget_alert_notification(alert: BudgetAlert) -> bool:
    """Send budget alert notification to recipients"""
    try:
        # In a real implementation, this would integrate with email service
        # For now, we'll log the alert and store it in the database
        print(f"🚨 BUDGET ALERT: {alert.alert_type.upper()}")
        print(f"   Project: {alert.project_id}")
        print(f"   Message: {alert.message}")
        print(f"   Recipients: {', '.join(alert.recipients)}")
        
        # Store alert in database
        if supabase:
            alert_data = {
                'project_id': str(alert.project_id),
                'alert_type': alert.alert_type,
                'threshold_percentage': alert.threshold_percentage,
                'current_percentage': alert.current_percentage,
                'budget_amount': alert.budget_amount,
                'actual_cost': alert.actual_cost,
                'variance': alert.variance,
                'message': alert.message,
                'recipients': alert.recipients,
                'is_resolved': False
            }
            
            response = supabase.table("budget_alerts").insert(alert_data).execute()
            if response.data:
                print(f"✅ Budget alert stored in database: {response.data[0]['id']}")
                return True
        
        return False
        
    except Exception as e:
        print(f"Error sending budget alert notification: {e}")
        return False

async def monitor_all_project_budgets() -> Dict[str, Any]:
    """Monitor all project budgets and generate alerts as needed"""
    try:
        if not supabase:
            return {"error": "Database not available"}
        
        # Get all active projects with budgets
        projects_response = supabase.table("projects").select("*").neq("budget", None).execute()
        projects = projects_response.data or []
        
        # Get all active alert rules
        rules_response = supabase.table("budget_alert_rules").select("*").eq("is_active", True).execute()
        alert_rules = rules_response.data or []
        
        if not alert_rules:
            return {"message": "No active alert rules configured", "projects_checked": len(projects)}
        
        total_alerts = 0
        alerts_by_type = {"warning": 0, "critical": 0, "overrun": 0}
        
        # Check each project
        for project in projects:
            alerts = check_budget_thresholds(project, alert_rules)
            
            for alert in alerts:
                # Send notification
                success = await send_budget_alert_notification(alert)
                if success:
                    total_alerts += 1
                    alerts_by_type[alert.alert_type] = alerts_by_type.get(alert.alert_type, 0) + 1
        
        return {
            "projects_checked": len(projects),
            "total_alerts_generated": total_alerts,
            "alerts_by_type": alerts_by_type,
            "active_rules": len(alert_rules)
        }
        
    except Exception as e:
        print(f"Error monitoring project budgets: {e}")
        return {"error": str(e)}

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
            "message": "Willkommen zur Orka PPM – mit agentic AI 🚀",
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

# Role Management Endpoints
@app.post("/roles/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(role: RoleCreate, current_user = Depends(require_permission(Permission.role_manage))):
    """Create a new role with specified permissions"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Validate permissions
        for perm in role.permissions:
            if not isinstance(perm, Permission):
                raise HTTPException(status_code=400, detail=f"Invalid permission: {perm}")
        
        role_data = {
            "name": role.name,
            "description": role.description,
            "permissions": [perm.value for perm in role.permissions],
            "is_active": role.is_active
        }
        
        response = supabase.table("roles").insert(role_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create role")
        
        # Clear RBAC cache since roles changed
        rbac.clear_all_cache()
        
        return convert_uuids(response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Create role error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to create role: {str(e)}")

@app.get("/roles/")
async def list_roles(
    is_active: Optional[bool] = Query(None),
    current_user = Depends(require_permission(Permission.role_manage))
):
    """Get all roles with optional filtering"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        query = supabase.table("roles").select("*")
        
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        response = query.order("created_at", desc=True).execute()
        return convert_uuids(response.data)
        
    except Exception as e:
        print(f"List roles error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get roles: {str(e)}")

@app.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(role_id: UUID, current_user = Depends(require_permission(Permission.role_manage))):
    """Get a specific role by ID"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        response = supabase.table("roles").select("*").eq("id", str(role_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Role not found")
        
        return convert_uuids(response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get role error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get role: {str(e)}")

@app.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(role_id: UUID, role_update: RoleUpdate, current_user = Depends(require_permission(Permission.role_manage))):
    """Update a role"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Only include non-None fields in the update
        update_data = {}
        if role_update.name is not None:
            update_data["name"] = role_update.name
        if role_update.description is not None:
            update_data["description"] = role_update.description
        if role_update.permissions is not None:
            # Validate permissions
            for perm in role_update.permissions:
                if not isinstance(perm, Permission):
                    raise HTTPException(status_code=400, detail=f"Invalid permission: {perm}")
            update_data["permissions"] = [perm.value for perm in role_update.permissions]
        if role_update.is_active is not None:
            update_data["is_active"] = role_update.is_active
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        response = supabase.table("roles").update(update_data).eq("id", str(role_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Clear RBAC cache since roles changed
        rbac.clear_all_cache()
        
        return convert_uuids(response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Update role error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to update role: {str(e)}")

@app.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(role_id: UUID, current_user = Depends(require_permission(Permission.role_manage))):
    """Delete a role"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Check if role is assigned to any users
        assignments_response = supabase.table("user_roles").select("id").eq("role_id", str(role_id)).execute()
        if assignments_response.data:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete role that is assigned to users. Remove assignments first."
            )
        
        response = supabase.table("roles").delete().eq("id", str(role_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Clear RBAC cache since roles changed
        rbac.clear_all_cache()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete role error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete role: {str(e)}")

# User Role Assignment Endpoints
@app.post("/users/{user_id}/roles/{role_id}", response_model=UserRoleResponse, status_code=status.HTTP_201_CREATED)
async def assign_role_to_user(
    user_id: UUID, 
    role_id: UUID, 
    current_user = Depends(require_permission(Permission.user_manage))
):
    """Assign a role to a user"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Verify role exists
        role_response = supabase.table("roles").select("*").eq("id", str(role_id)).execute()
        if not role_response.data:
            raise HTTPException(status_code=404, detail="Role not found")
        
        role = role_response.data[0]
        
        # Assign role using RBAC system
        success = await rbac.assign_role_to_user(str(user_id), str(role_id))
        if not success:
            raise HTTPException(status_code=400, detail="Failed to assign role to user")
        
        # Return the assignment details
        return {
            "id": f"{user_id}_{role_id}",
            "user_id": str(user_id),
            "role_id": str(role_id),
            "role_name": role["name"],
            "permissions": role["permissions"],
            "assigned_at": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Assign role error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to assign role: {str(e)}")

@app.delete("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role_from_user(
    user_id: UUID, 
    role_id: UUID, 
    current_user = Depends(require_permission(Permission.user_manage))
):
    """Remove a role from a user"""
    try:
        success = await rbac.remove_role_from_user(str(user_id), str(role_id))
        if not success:
            raise HTTPException(status_code=404, detail="Role assignment not found")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Remove role error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove role: {str(e)}")

@app.get("/users/{user_id}/roles")
async def get_user_roles(user_id: UUID, current_user = Depends(require_permission(Permission.user_manage))):
    """Get all roles assigned to a user"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        response = supabase.table("user_roles").select(
            "role_id, assigned_at, roles(id, name, description, permissions)"
        ).eq("user_id", str(user_id)).execute()
        
        user_roles = []
        for assignment in response.data or []:
            role_data = assignment.get("roles", {})
            user_roles.append({
                "id": f"{user_id}_{assignment['role_id']}",
                "user_id": str(user_id),
                "role_id": assignment["role_id"],
                "role_name": role_data.get("name", "Unknown"),
                "permissions": role_data.get("permissions", []),
                "assigned_at": assignment["assigned_at"]
            })
        
        return user_roles
        
    except Exception as e:
        print(f"Get user roles error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user roles: {str(e)}")

@app.get("/users/{user_id}/permissions")
async def get_user_permissions(user_id: UUID, current_user = Depends(require_permission(Permission.user_manage))):
    """Get all permissions for a user (aggregated from all roles)"""
    try:
        permissions = await rbac.get_user_permissions(str(user_id))
        return {
            "user_id": str(user_id),
            "permissions": [perm.value for perm in permissions],
            "total_permissions": len(permissions)
        }
        
    except Exception as e:
        print(f"Get user permissions error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user permissions: {str(e)}")

@app.get("/permissions")
async def list_all_permissions(current_user = Depends(require_permission(Permission.role_manage))):
    """Get all available permissions in the system"""
    try:
        permissions = []
        for perm in Permission:
            permissions.append({
                "name": perm.value,
                "description": perm.value.replace("_", " ").title()
            })
        
        return {
            "permissions": permissions,
            "total_permissions": len(permissions)
        }
        
    except Exception as e:
        print(f"List permissions error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get permissions: {str(e)}")

@app.post("/roles/initialize-defaults")
async def initialize_default_roles(current_user = Depends(require_permission(Permission.system_admin))):
    """Initialize default roles in the database"""
    try:
        success = await rbac.create_default_roles()
        if success:
            return {"message": "Default roles initialized successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to initialize default roles")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Initialize default roles error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize default roles: {str(e)}")

# Portfolio Endpoints
@app.post("/portfolios/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(portfolio: PortfolioCreate, current_user = Depends(require_permission(Permission.portfolio_create))):
    try:
        response = supabase.table("portfolios").insert(portfolio.dict()).execute()
        if not response.data:
            raise HTTPException(status_code=400, detail="Fehler beim Erstellen des Portfolios")
        
        return convert_uuids(response.data[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/portfolios/")
async def list_portfolios(current_user = Depends(require_permission(Permission.portfolio_read))):
    response = supabase.table("portfolios").select("*").execute()
    return convert_uuids(response.data)

@app.get("/portfolios/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(portfolio_id: UUID, current_user = Depends(require_permission(Permission.portfolio_read))):
    response = supabase.table("portfolios").select("*").eq("id", str(portfolio_id)).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return convert_uuids(response.data[0])

# Project Endpoints
@app.post("/projects/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate, current_user = Depends(require_permission(Permission.project_create))):
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
    portfolio_id: Optional[UUID] = Query(None),
    status: Optional[ProjectStatus] = Query(None),
    current_user = Depends(require_permission(Permission.project_read))
):
    query = supabase.table("projects").select("*")
    
    if portfolio_id:
        query = query.eq("portfolio_id", str(portfolio_id))
    if status:
        query = query.eq("status", status.value)
    
    response = query.execute()
    return convert_uuids(response.data)

@app.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID, current_user = Depends(require_permission(Permission.project_read))):
    response = supabase.table("projects").select("*").eq("id", str(project_id)).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Project not found")
    return convert_uuids(response.data[0])

# Dashboard endpoint
@app.get("/dashboard")
async def get_dashboard_data(current_user = Depends(require_permission(Permission.portfolio_read))):
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
async def get_portfolio_kpis(current_user = Depends(require_permission(Permission.portfolio_read))):
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
async def get_portfolio_trends(current_user = Depends(require_permission(Permission.portfolio_read))):
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
async def get_portfolio_metrics(current_user = Depends(require_permission(Permission.portfolio_read))):
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
@app.post("/resources/", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(resource: ResourceCreate, current_user = Depends(require_permission(Permission.resource_create))):
    """Create a new resource"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        resource_data = resource.dict()
        response = supabase.table("resources").insert(resource_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create resource")
        
        created_resource = response.data[0]
        
        # Calculate availability metrics
        availability_metrics = calculate_enhanced_resource_availability(created_resource)
        created_resource.update(availability_metrics)
        
        return convert_uuids(created_resource)
        
    except Exception as e:
        print(f"Create resource error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to create resource: {str(e)}")

@app.get("/resources/")
async def list_resources(current_user = Depends(require_permission(Permission.resource_read))):
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
                    "availability": 80,
                    "hourly_rate": 85,
                    "skills": ["React", "TypeScript", "Node.js", "Python"],
                    "location": "New York",
                    "current_projects": ["proj-1", "proj-2"],
                    "utilization_percentage": 80.0,
                    "available_hours": 8.0,
                    "allocated_hours": 32.0,
                    "capacity_hours": 40.0,
                    "availability_status": "mostly_allocated",
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
                    "availability": 100,
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
                    "availability": 50,
                    "hourly_rate": 75,
                    "skills": ["UI/UX Design", "Figma", "Adobe Creative Suite", "User Research"],
                    "location": "Remote",
                    "current_projects": ["proj-2", "proj-3"],
                    "utilization_percentage": 50.0,
                    "available_hours": 20.0,
                    "allocated_hours": 20.0,
                    "capacity_hours": 40.0,
                    "availability_status": "partially_allocated",
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
                    "availability": 100,
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
        
        # Calculate availability metrics for each resource
        enhanced_resources = []
        for resource in resources:
            availability_metrics = calculate_enhanced_resource_availability(resource)
            resource.update(availability_metrics)
            enhanced_resources.append(resource)
        
        return enhanced_resources
        
    except Exception as e:
        print(f"Resources error: {e}")
        raise HTTPException(status_code=500, detail=f"Resources data retrieval failed: {str(e)}")

@app.get("/resources/{resource_id}", response_model=ResourceResponse)
async def get_resource(resource_id: UUID, current_user = Depends(require_permission(Permission.resource_read))):
    """Get a specific resource by ID"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        response = supabase.table("resources").select("*").eq("id", str(resource_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        resource = convert_uuids(response.data[0])
        
        # Calculate availability metrics
        availability_metrics = calculate_enhanced_resource_availability(resource)
        resource.update(availability_metrics)
        
        return resource
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get resource error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get resource: {str(e)}")

@app.put("/resources/{resource_id}", response_model=ResourceResponse)
async def update_resource(resource_id: UUID, resource_update: ResourceUpdate, current_user = Depends(require_permission(Permission.resource_update))):
    """Update a resource"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Only include non-None fields in the update
        update_data = {k: v for k, v in resource_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        response = supabase.table("resources").update(update_data).eq("id", str(resource_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        updated_resource = convert_uuids(response.data[0])
        
        # Calculate availability metrics
        availability_metrics = calculate_enhanced_resource_availability(updated_resource)
        updated_resource.update(availability_metrics)
        
        return updated_resource
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Update resource error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to update resource: {str(e)}")

@app.delete("/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(resource_id: UUID, current_user = Depends(require_permission(Permission.resource_delete))):
    """Delete a resource"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        response = supabase.table("resources").delete().eq("id", str(resource_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete resource error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete resource: {str(e)}")

@app.post("/resources/search")
async def search_resources(search_request: ResourceSearchRequest, current_user = Depends(require_permission(Permission.resource_read))):
    """Search resources based on skills, capacity, availability, and other criteria"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Start with base query
        query = supabase.table("resources").select("*")
        
        # Apply filters
        if search_request.role:
            query = query.ilike("role", f"%{search_request.role}%")
        
        if search_request.location:
            query = query.ilike("location", f"%{search_request.location}%")
        
        if search_request.min_capacity:
            query = query.gte("capacity", search_request.min_capacity)
        
        if search_request.max_capacity:
            query = query.lte("capacity", search_request.max_capacity)
        
        if search_request.min_availability:
            query = query.gte("availability", search_request.min_availability)
        
        response = query.execute()
        resources = convert_uuids(response.data)
        
        # Filter by skills if specified
        if search_request.skills:
            filtered_resources = []
            for resource in resources:
                resource_skills = resource.get('skills', [])
                skill_match = calculate_advanced_skill_match_score(search_request.skills, resource_skills)
                
                if skill_match['match_score'] > 0:  # At least one skill matches
                    # Calculate availability metrics
                    availability_metrics = calculate_enhanced_resource_availability(resource)
                    resource.update(availability_metrics)
                    resource['skill_match_score'] = skill_match['match_score']
                    resource['matching_skills'] = skill_match['matching_skills']
                    filtered_resources.append(resource)
            
            # Sort by skill match score (descending)
            filtered_resources.sort(key=lambda x: x['skill_match_score'], reverse=True)
            return filtered_resources
        else:
            # Calculate availability metrics for all resources
            enhanced_resources = []
            for resource in resources:
                availability_metrics = calculate_enhanced_resource_availability(resource)
                resource.update(availability_metrics)
                enhanced_resources.append(resource)
            
            return enhanced_resources
        
    except Exception as e:
        print(f"Search resources error: {e}")
        raise HTTPException(status_code=500, detail=f"Resource search failed: {str(e)}")

@app.get("/resources/utilization/summary")
async def get_resource_utilization_summary(current_user = Depends(require_permission(Permission.resource_read))):
    """Get resource utilization summary for analytics"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Get all resources
        resources_response = supabase.table("resources").select("*").execute()
        resources = convert_uuids(resources_response.data)
        
        if not resources:
            # Return mock data if no resources exist
            return {
                "total_resources": 4,
                "available_resources": 2,
                "partially_allocated_resources": 1,
                "fully_allocated_resources": 1,
                "overallocated_resources": 0,
                "average_utilization": 75.6,
                "total_capacity_hours": 160,
                "total_allocated_hours": 137,
                "total_available_hours": 23
            }
        
        # Calculate utilization metrics
        total_resources = len(resources)
        available_count = 0
        partially_allocated_count = 0
        fully_allocated_count = 0
        overallocated_count = 0
        total_capacity = 0
        total_allocated = 0
        total_available = 0
        utilization_sum = 0
        
        for resource in resources:
            availability_metrics = calculate_enhanced_resource_availability(resource)
            
            total_capacity += availability_metrics['capacity_hours']
            total_allocated += availability_metrics['allocated_hours']
            total_available += availability_metrics['available_hours']
            utilization_sum += availability_metrics['utilization_percentage']
            
            status = availability_metrics['availability_status']
            if status == 'available':
                available_count += 1
            elif status == 'partially_allocated':
                partially_allocated_count += 1
            elif status == 'fully_allocated':
                fully_allocated_count += 1
            
            if availability_metrics['utilization_percentage'] > 100:
                overallocated_count += 1
        
        average_utilization = utilization_sum / total_resources if total_resources > 0 else 0
        
        return {
            "total_resources": total_resources,
            "available_resources": available_count,
            "partially_allocated_resources": partially_allocated_count,
            "fully_allocated_resources": fully_allocated_count,
            "overallocated_resources": overallocated_count,
            "average_utilization": round(average_utilization, 1),
            "total_capacity_hours": total_capacity,
            "total_allocated_hours": round(total_allocated, 1),
            "total_available_hours": round(total_available, 1)
        }
        
    except Exception as e:
        print(f"Resource utilization summary error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get utilization summary: {str(e)}")

@app.post("/resources/{resource_id}/allocate/{project_id}")
async def allocate_resource_to_project(
    resource_id: UUID, 
    project_id: UUID, 
    allocation_percentage: int = Query(..., ge=1, le=100),
    current_user = Depends(require_permission(Permission.resource_allocate))
):
    """Allocate a resource to a project with specified percentage"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Check if resource and project exist
        resource_response = supabase.table("resources").select("*").eq("id", str(resource_id)).execute()
        if not resource_response.data:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        project_response = supabase.table("projects").select("*").eq("id", str(project_id)).execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Create or update allocation
        allocation_data = {
            "resource_id": str(resource_id),
            "project_id": str(project_id),
            "allocation_percentage": allocation_percentage,
            "start_date": date.today().isoformat(),
            "role_in_project": "Team Member"
        }
        
        # Try to insert, if conflict then update
        try:
            response = supabase.table("project_resources").insert(allocation_data).execute()
        except Exception:
            # If insert fails due to unique constraint, update existing
            response = supabase.table("project_resources").update({
                "allocation_percentage": allocation_percentage
            }).eq("resource_id", str(resource_id)).eq("project_id", str(project_id)).execute()
        
        # Update resource's current_projects list
        resource = resource_response.data[0]
        current_projects = resource.get('current_projects', [])
        if str(project_id) not in current_projects:
            current_projects.append(str(project_id))
            supabase.table("resources").update({
                "current_projects": current_projects
            }).eq("id", str(resource_id)).execute()
        
        return {
            "message": "Resource allocated successfully",
            "resource_id": str(resource_id),
            "project_id": str(project_id),
            "allocation_percentage": allocation_percentage
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Resource allocation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to allocate resource: {str(e)}")

@app.delete("/resources/{resource_id}/allocate/{project_id}")
async def deallocate_resource_from_project(
    resource_id: UUID, 
    project_id: UUID, 
    current_user = Depends(require_permission(Permission.resource_allocate))
):
    """Remove resource allocation from a project"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Remove allocation
        response = supabase.table("project_resources").delete().eq(
            "resource_id", str(resource_id)
        ).eq("project_id", str(project_id)).execute()
        
        # Update resource's current_projects list
        resource_response = supabase.table("resources").select("current_projects").eq("id", str(resource_id)).execute()
        if resource_response.data:
            current_projects = resource_response.data[0].get('current_projects', [])
            if str(project_id) in current_projects:
                current_projects.remove(str(project_id))
                supabase.table("resources").update({
                    "current_projects": current_projects
                }).eq("id", str(resource_id)).execute()
        
        return {
            "message": "Resource deallocated successfully",
            "resource_id": str(resource_id),
            "project_id": str(project_id)
        }
        
    except Exception as e:
        print(f"Resource deallocation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to deallocate resource: {str(e)}")

# Budget Alert Endpoints
@app.post("/budget-alerts/rules/", response_model=BudgetAlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_budget_alert_rule(rule: BudgetAlertRuleCreate, current_user = Depends(require_permission(Permission.budget_alert_manage))):
    """Create a new budget alert rule"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Validate threshold percentage
        if rule.threshold_percentage <= 0 or rule.threshold_percentage > 200:
            raise HTTPException(status_code=400, detail="Threshold percentage must be between 0 and 200")
        
        # Validate alert type
        if rule.alert_type not in ['warning', 'critical', 'overrun']:
            raise HTTPException(status_code=400, detail="Alert type must be 'warning', 'critical', or 'overrun'")
        
        # Validate recipients
        if not rule.recipients:
            raise HTTPException(status_code=400, detail="At least one recipient email is required")
        
        # If project_id is specified, verify project exists
        if rule.project_id:
            project_response = supabase.table("projects").select("id").eq("id", str(rule.project_id)).execute()
            if not project_response.data:
                raise HTTPException(status_code=404, detail="Project not found")
        
        rule_data = rule.dict()
        if rule_data['project_id']:
            rule_data['project_id'] = str(rule_data['project_id'])
        
        response = supabase.table("budget_alert_rules").insert(rule_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create budget alert rule")
        
        return convert_uuids(response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Create budget alert rule error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to create budget alert rule: {str(e)}")

@app.get("/budget-alerts/rules/")
async def list_budget_alert_rules(
    project_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user = Depends(get_current_user)
):
    """Get all budget alert rules with optional filtering"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        query = supabase.table("budget_alert_rules").select("*")
        
        if project_id:
            query = query.eq("project_id", str(project_id))
        
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        response = query.order("created_at", desc=True).execute()
        return convert_uuids(response.data)
        
    except Exception as e:
        print(f"List budget alert rules error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get budget alert rules: {str(e)}")

@app.get("/budget-alerts/rules/{rule_id}", response_model=BudgetAlertRuleResponse)
async def get_budget_alert_rule(rule_id: UUID, current_user = Depends(get_current_user)):
    """Get a specific budget alert rule"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        response = supabase.table("budget_alert_rules").select("*").eq("id", str(rule_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Budget alert rule not found")
        
        return convert_uuids(response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get budget alert rule error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get budget alert rule: {str(e)}")

@app.put("/budget-alerts/rules/{rule_id}", response_model=BudgetAlertRuleResponse)
async def update_budget_alert_rule(rule_id: UUID, rule_update: BudgetAlertRuleCreate, current_user = Depends(get_current_user)):
    """Update a budget alert rule"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Validate threshold percentage
        if rule_update.threshold_percentage <= 0 or rule_update.threshold_percentage > 200:
            raise HTTPException(status_code=400, detail="Threshold percentage must be between 0 and 200")
        
        # Validate alert type
        if rule_update.alert_type not in ['warning', 'critical', 'overrun']:
            raise HTTPException(status_code=400, detail="Alert type must be 'warning', 'critical', or 'overrun'")
        
        # Validate recipients
        if not rule_update.recipients:
            raise HTTPException(status_code=400, detail="At least one recipient email is required")
        
        update_data = rule_update.dict()
        if update_data['project_id']:
            update_data['project_id'] = str(update_data['project_id'])
        
        response = supabase.table("budget_alert_rules").update(update_data).eq("id", str(rule_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Budget alert rule not found")
        
        return convert_uuids(response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Update budget alert rule error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to update budget alert rule: {str(e)}")

@app.delete("/budget-alerts/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget_alert_rule(rule_id: UUID, current_user = Depends(get_current_user)):
    """Delete a budget alert rule"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        response = supabase.table("budget_alert_rules").delete().eq("id", str(rule_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Budget alert rule not found")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete budget alert rule error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete budget alert rule: {str(e)}")

@app.get("/budget-alerts/")
async def list_budget_alerts(
    project_id: Optional[UUID] = Query(None),
    alert_type: Optional[str] = Query(None),
    is_resolved: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user = Depends(get_current_user)
):
    """Get budget alerts with optional filtering"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        query = supabase.table("budget_alerts").select("*")
        
        if project_id:
            query = query.eq("project_id", str(project_id))
        
        if alert_type:
            query = query.eq("alert_type", alert_type)
        
        if is_resolved is not None:
            query = query.eq("is_resolved", is_resolved)
        
        response = query.order("created_at", desc=True).limit(limit).execute()
        return convert_uuids(response.data)
        
    except Exception as e:
        print(f"List budget alerts error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get budget alerts: {str(e)}")

@app.post("/budget-alerts/monitor")
async def monitor_project_budgets(current_user = Depends(get_current_user)):
    """Manually trigger budget monitoring for all projects"""
    try:
        result = await monitor_all_project_budgets()
        return result
        
    except Exception as e:
        print(f"Monitor project budgets error: {e}")
        raise HTTPException(status_code=500, detail=f"Budget monitoring failed: {str(e)}")

@app.post("/budget-alerts/{alert_id}/resolve")
async def resolve_budget_alert(alert_id: UUID, current_user = Depends(get_current_user)):
    """Mark a budget alert as resolved"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        response = supabase.table("budget_alerts").update({
            "is_resolved": True,
            "resolved_at": datetime.now().isoformat()
        }).eq("id", str(alert_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Budget alert not found")
        
        return {"message": "Budget alert resolved successfully", "alert_id": str(alert_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Resolve budget alert error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resolve budget alert: {str(e)}")

@app.get("/budget-alerts/summary")
async def get_budget_alerts_summary(current_user = Depends(get_current_user)):
    """Get summary of budget alerts"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Get alert counts by type and status
        alerts_response = supabase.table("budget_alerts").select("alert_type, is_resolved").execute()
        alerts = alerts_response.data or []
        
        summary = {
            "total_alerts": len(alerts),
            "active_alerts": len([a for a in alerts if not a.get('is_resolved', False)]),
            "resolved_alerts": len([a for a in alerts if a.get('is_resolved', False)]),
            "by_type": {
                "warning": len([a for a in alerts if a.get('alert_type') == 'warning']),
                "critical": len([a for a in alerts if a.get('alert_type') == 'critical']),
                "overrun": len([a for a in alerts if a.get('alert_type') == 'overrun'])
            },
            "active_by_type": {
                "warning": len([a for a in alerts if a.get('alert_type') == 'warning' and not a.get('is_resolved', False)]),
                "critical": len([a for a in alerts if a.get('alert_type') == 'critical' and not a.get('is_resolved', False)]),
                "overrun": len([a for a in alerts if a.get('alert_type') == 'overrun' and not a.get('is_resolved', False)])
            }
        }
        
        # Get active rules count
        rules_response = supabase.table("budget_alert_rules").select("id").eq("is_active", True).execute()
        summary["active_rules"] = len(rules_response.data or [])
        
        return summary
        
    except Exception as e:
        print(f"Budget alerts summary error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get budget alerts summary: {str(e)}")

# Financial Tracking Endpoints
@app.post("/financial-tracking/", response_model=FinancialTrackingResponse, status_code=status.HTTP_201_CREATED)
async def create_financial_entry(entry: FinancialTrackingCreate, current_user = Depends(get_current_user)):
    """Create a new financial tracking entry"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Verify project exists
        project_response = supabase.table("projects").select("id").eq("id", str(entry.project_id)).execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        entry_data = entry.dict()
        entry_data['project_id'] = str(entry_data['project_id'])
        entry_data['recorded_by'] = current_user['user_id']
        
        response = supabase.table("financial_tracking").insert(entry_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create financial entry")
        
        # Update project actual_cost
        await update_project_actual_cost(entry.project_id)
        
        # Check for budget alerts after updating costs
        await check_project_budget_alerts(entry.project_id)
        
        return convert_uuids(response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Create financial entry error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to create financial entry: {str(e)}")

@app.get("/financial-tracking/")
async def list_financial_entries(
    project_id: Optional[UUID] = Query(None),
    category: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user = Depends(get_current_user)
):
    """Get financial tracking entries with optional filtering"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        query = supabase.table("financial_tracking").select("*")
        
        if project_id:
            query = query.eq("project_id", str(project_id))
        
        if category:
            query = query.eq("category", category)
        
        if start_date:
            query = query.gte("date_incurred", start_date.isoformat())
        
        if end_date:
            query = query.lte("date_incurred", end_date.isoformat())
        
        response = query.order("date_incurred", desc=True).execute()
        return convert_uuids(response.data)
        
    except Exception as e:
        print(f"List financial entries error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get financial entries: {str(e)}")

async def update_project_actual_cost(project_id: UUID):
    """Update project's actual_cost based on financial tracking entries"""
    try:
        if not supabase:
            return
        
        # Sum all actual amounts for the project
        response = supabase.table("financial_tracking").select("actual_amount").eq("project_id", str(project_id)).execute()
        
        total_actual = sum(float(entry.get('actual_amount', 0)) for entry in response.data or [])
        
        # Update project
        supabase.table("projects").update({"actual_cost": total_actual}).eq("id", str(project_id)).execute()
        
    except Exception as e:
        print(f"Error updating project actual cost: {e}")

async def check_project_budget_alerts(project_id: UUID):
    """Check budget alerts for a specific project after cost update"""
    try:
        if not supabase:
            return
        
        # Get project data
        project_response = supabase.table("projects").select("*").eq("id", str(project_id)).execute()
        if not project_response.data:
            return
        
        project = project_response.data[0]
        
        # Get active alert rules
        rules_response = supabase.table("budget_alert_rules").select("*").eq("is_active", True).execute()
        alert_rules = rules_response.data or []
        
        # Check thresholds and generate alerts
        alerts = check_budget_thresholds(project, alert_rules)
        
        for alert in alerts:
            await send_budget_alert_notification(alert)
        
    except Exception as e:
        print(f"Error checking project budget alerts: {e}")

# Risk Management Endpoints
@app.post("/risks/", response_model=RiskResponse, status_code=status.HTTP_201_CREATED)
async def create_risk(risk: RiskCreate, current_user = Depends(get_current_user)):
    """Create a new risk entry in the risk register"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Verify project exists
        project_response = supabase.table("projects").select("id").eq("id", str(risk.project_id)).execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Validate probability and impact ranges
        if not (0.0 <= risk.probability <= 1.0):
            raise HTTPException(status_code=400, detail="Probability must be between 0.0 and 1.0")
        
        if not (0.0 <= risk.impact <= 1.0):
            raise HTTPException(status_code=400, detail="Impact must be between 0.0 and 1.0")
        
        risk_data = risk.dict()
        risk_data['project_id'] = str(risk_data['project_id'])
        if risk_data.get('owner_id'):
            risk_data['owner_id'] = str(risk_data['owner_id'])
        
        response = supabase.table("risks").insert(risk_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create risk")
        
        return convert_uuids(response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Create risk error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to create risk: {str(e)}")

@app.get("/risks/")
async def list_risks(
    project_id: Optional[UUID] = Query(None),
    category: Optional[RiskCategory] = Query(None),
    status: Optional[RiskStatus] = Query(None),
    owner_id: Optional[UUID] = Query(None),
    current_user = Depends(get_current_user)
):
    """Get all risks with optional filtering"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        query = supabase.table("risks").select("*")
        
        if project_id:
            query = query.eq("project_id", str(project_id))
        
        if category:
            query = query.eq("category", category.value)
        
        if status:
            query = query.eq("status", status.value)
        
        if owner_id:
            query = query.eq("owner_id", str(owner_id))
        
        response = query.order("created_at", desc=True).execute()
        return convert_uuids(response.data)
        
    except Exception as e:
        print(f"List risks error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get risks: {str(e)}")

@app.get("/risks/{risk_id}", response_model=RiskResponse)
async def get_risk(risk_id: UUID, current_user = Depends(get_current_user)):
    """Get a specific risk by ID"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        response = supabase.table("risks").select("*").eq("id", str(risk_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Risk not found")
        
        return convert_uuids(response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get risk error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get risk: {str(e)}")

@app.put("/risks/{risk_id}", response_model=RiskResponse)
async def update_risk(risk_id: UUID, risk_update: RiskUpdate, current_user = Depends(get_current_user)):
    """Update a risk entry with audit trail maintenance"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Only include non-None fields in the update
        update_data = {k: v for k, v in risk_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Validate probability and impact if provided
        if 'probability' in update_data and not (0.0 <= update_data['probability'] <= 1.0):
            raise HTTPException(status_code=400, detail="Probability must be between 0.0 and 1.0")
        
        if 'impact' in update_data and not (0.0 <= update_data['impact'] <= 1.0):
            raise HTTPException(status_code=400, detail="Impact must be between 0.0 and 1.0")
        
        # Convert UUIDs to strings
        if 'owner_id' in update_data and update_data['owner_id']:
            update_data['owner_id'] = str(update_data['owner_id'])
        
        response = supabase.table("risks").update(update_data).eq("id", str(risk_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Risk not found")
        
        return convert_uuids(response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Update risk error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to update risk: {str(e)}")

@app.delete("/risks/{risk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_risk(risk_id: UUID, current_user = Depends(get_current_user)):
    """Delete a risk entry"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        response = supabase.table("risks").delete().eq("id", str(risk_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Risk not found")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete risk error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete risk: {str(e)}")

# Issue Management Endpoints
@app.post("/issues/", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
async def create_issue(issue: IssueCreate, current_user = Depends(get_current_user)):
    """Create a new issue entry in the issue register"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Verify project exists
        project_response = supabase.table("projects").select("id").eq("id", str(issue.project_id)).execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Verify risk exists if risk_id is provided
        if issue.risk_id:
            risk_response = supabase.table("risks").select("id").eq("id", str(issue.risk_id)).execute()
            if not risk_response.data:
                raise HTTPException(status_code=404, detail="Risk not found")
        
        issue_data = issue.dict()
        issue_data['project_id'] = str(issue_data['project_id'])
        if issue_data.get('risk_id'):
            issue_data['risk_id'] = str(issue_data['risk_id'])
        if issue_data.get('assigned_to'):
            issue_data['assigned_to'] = str(issue_data['assigned_to'])
        if issue_data.get('reporter_id'):
            issue_data['reporter_id'] = str(issue_data['reporter_id'])
        else:
            # Set current user as reporter if not specified
            issue_data['reporter_id'] = current_user['user_id']
        
        response = supabase.table("issues").insert(issue_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create issue")
        
        return convert_uuids(response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Create issue error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to create issue: {str(e)}")

@app.get("/issues/")
async def list_issues(
    project_id: Optional[UUID] = Query(None),
    risk_id: Optional[UUID] = Query(None),
    severity: Optional[IssueSeverity] = Query(None),
    status: Optional[IssueStatus] = Query(None),
    assigned_to: Optional[UUID] = Query(None),
    current_user = Depends(get_current_user)
):
    """Get all issues with optional filtering"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        query = supabase.table("issues").select("*")
        
        if project_id:
            query = query.eq("project_id", str(project_id))
        
        if risk_id:
            query = query.eq("risk_id", str(risk_id))
        
        if severity:
            query = query.eq("severity", severity.value)
        
        if status:
            query = query.eq("status", status.value)
        
        if assigned_to:
            query = query.eq("assigned_to", str(assigned_to))
        
        response = query.order("created_at", desc=True).execute()
        return convert_uuids(response.data)
        
    except Exception as e:
        print(f"List issues error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get issues: {str(e)}")

@app.get("/issues/{issue_id}", response_model=IssueResponse)
async def get_issue(issue_id: UUID, current_user = Depends(get_current_user)):
    """Get a specific issue by ID"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        response = supabase.table("issues").select("*").eq("id", str(issue_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        return convert_uuids(response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get issue error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get issue: {str(e)}")

@app.put("/issues/{issue_id}", response_model=IssueResponse)
async def update_issue(issue_id: UUID, issue_update: IssueUpdate, current_user = Depends(get_current_user)):
    """Update an issue entry with audit trail maintenance"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Only include non-None fields in the update
        update_data = {k: v for k, v in issue_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Convert UUIDs to strings
        if 'assigned_to' in update_data and update_data['assigned_to']:
            update_data['assigned_to'] = str(update_data['assigned_to'])
        
        # Set resolution_date when status changes to resolved or closed
        if 'status' in update_data and update_data['status'] in ['resolved', 'closed']:
            update_data['resolution_date'] = datetime.now().isoformat()
        
        response = supabase.table("issues").update(update_data).eq("id", str(issue_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        return convert_uuids(response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Update issue error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to update issue: {str(e)}")

@app.delete("/issues/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_issue(issue_id: UUID, current_user = Depends(get_current_user)):
    """Delete an issue entry"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        response = supabase.table("issues").delete().eq("id", str(issue_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete issue error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete issue: {str(e)}")

@app.post("/risks/{risk_id}/materialize", response_model=IssueResponse)
async def materialize_risk_to_issue(
    risk_id: UUID, 
    issue_data: IssueCreate,
    current_user = Depends(get_current_user)
):
    """Convert a risk into an issue (risk materialization) with proper linkage"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Verify risk exists
        risk_response = supabase.table("risks").select("*").eq("id", str(risk_id)).execute()
        if not risk_response.data:
            raise HTTPException(status_code=404, detail="Risk not found")
        
        risk = risk_response.data[0]
        
        # Create issue with risk linkage
        issue_create_data = issue_data.dict()
        issue_create_data['risk_id'] = str(risk_id)
        issue_create_data['project_id'] = risk['project_id']  # Ensure same project
        
        # Create the linked issue
        issue_response = await create_issue(IssueCreate(**issue_create_data), current_user)
        
        # Update risk status to indicate it has materialized
        await update_risk(
            UUID(risk_id), 
            RiskUpdate(status=RiskStatus.closed), 
            current_user
        )
        
        return issue_response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Risk materialization error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to materialize risk to issue: {str(e)}")

@app.get("/projects/{project_id}/risks-issues-summary")
async def get_project_risks_issues_summary(project_id: UUID, current_user = Depends(get_current_user)):
    """Get summary of risks and issues for a project"""
    try:
        if supabase is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Get risks summary
        risks_response = supabase.table("risks").select("category, status").eq("project_id", str(project_id)).execute()
        risks = risks_response.data or []
        
        # Get issues summary
        issues_response = supabase.table("issues").select("severity, status").eq("project_id", str(project_id)).execute()
        issues = issues_response.data or []
        
        # Calculate risk statistics
        risk_stats = {
            "total_risks": len(risks),
            "by_category": {},
            "by_status": {},
            "high_impact_risks": 0
        }
        
        for risk in risks:
            category = risk.get('category', 'unknown')
            status = risk.get('status', 'unknown')
            
            risk_stats["by_category"][category] = risk_stats["by_category"].get(category, 0) + 1
            risk_stats["by_status"][status] = risk_stats["by_status"].get(status, 0) + 1
        
        # Calculate issue statistics
        issue_stats = {
            "total_issues": len(issues),
            "by_severity": {},
            "by_status": {},
            "critical_issues": len([i for i in issues if i.get('severity') == 'critical'])
        }
        
        for issue in issues:
            severity = issue.get('severity', 'unknown')
            status = issue.get('status', 'unknown')
            
            issue_stats["by_severity"][severity] = issue_stats["by_severity"].get(severity, 0) + 1
            issue_stats["by_status"][status] = issue_stats["by_status"].get(status, 0) + 1
        
        return {
            "project_id": str(project_id),
            "risks": risk_stats,
            "issues": issue_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Project risks/issues summary error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get project risks/issues summary: {str(e)}")

# AI Endpoints - Real Implementation

# Financial Tracking Models
class BudgetAlertRule(BaseModel):
    project_id: Optional[UUID] = None  # None means applies to all projects
    threshold_percentage: float  # e.g., 80.0 for 80%
# Pydantic models for AI requests
class RAGQueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

class ResourceOptimizationRequest(BaseModel):
    project_id: Optional[str] = None

class RiskForecastRequest(BaseModel):
    project_id: Optional[str] = None

@app.post("/ai/rag-query")
async def process_rag_query(request: RAGQueryRequest, current_user = Depends(require_permission(Permission.ai_rag_query))):
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
async def optimize_resources(request: ResourceOptimizationRequest = None, current_user = Depends(require_permission(Permission.ai_resource_optimize))):
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
async def forecast_risks(request: RiskForecastRequest = None, current_user = Depends(require_permission(Permission.ai_risk_forecast))):
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
async def get_conversation_history(conversation_id: str, current_user = Depends(require_permission(Permission.ai_rag_query))):
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
async def get_ai_metrics(current_user = Depends(require_permission(Permission.ai_metrics_read))):
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