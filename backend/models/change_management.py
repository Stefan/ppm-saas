"""
Data models for integrated change management system
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    SCOPE = "scope"
    SCHEDULE = "schedule"
    BUDGET = "budget"
    DESIGN = "design"
    REGULATORY = "regulatory"
    RESOURCE = "resource"
    QUALITY = "quality"
    SAFETY = "safety"
    EMERGENCY = "emergency"


class ChangeStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ON_HOLD = "on_hold"
    IMPLEMENTING = "implementing"
    IMPLEMENTED = "implemented"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class ApprovalDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_INFO = "needs_info"
    DELEGATED = "delegated"


class ChangeRequestCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10)
    justification: Optional[str] = None
    change_type: ChangeType
    priority: PriorityLevel = PriorityLevel.MEDIUM
    project_id: UUID
    required_by_date: Optional[date] = None
    
    # Impact estimates
    estimated_cost_impact: Optional[Decimal] = Field(None, ge=0)
    estimated_schedule_impact_days: Optional[int] = Field(None, ge=0)
    estimated_effort_hours: Optional[Decimal] = Field(None, ge=0)
    
    # Linkages
    affected_milestones: List[UUID] = Field(default_factory=list)
    affected_pos: List[UUID] = Field(default_factory=list)
    
    # Template usage
    template_id: Optional[UUID] = None
    template_data: Optional[Dict[str, Any]] = None


class ChangeRequestUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    justification: Optional[str] = None
    priority: Optional[PriorityLevel] = None
    required_by_date: Optional[date] = None
    estimated_cost_impact: Optional[Decimal] = Field(None, ge=0)
    estimated_schedule_impact_days: Optional[int] = Field(None, ge=0)
    estimated_effort_hours: Optional[Decimal] = Field(None, ge=0)


class ChangeRequestResponse(BaseModel):
    id: str
    change_number: str
    title: str
    description: str
    justification: Optional[str]
    change_type: str
    priority: str
    status: str
    
    # Requestor information
    requested_by: str
    requested_date: datetime
    required_by_date: Optional[date]
    
    # Project linkage
    project_id: str
    project_name: Optional[str]
    affected_milestones: List[Dict[str, Any]]
    affected_pos: List[Dict[str, Any]]
    
    # Impact data
    estimated_cost_impact: Optional[Decimal]
    estimated_schedule_impact_days: Optional[int]
    actual_cost_impact: Optional[Decimal]
    actual_schedule_impact_days: Optional[int]
    
    # Implementation tracking
    implementation_progress: Optional[int]
    implementation_start_date: Optional[date]
    implementation_end_date: Optional[date]
    
    # Approval status
    pending_approvals: List[Dict[str, Any]]
    approval_history: List[Dict[str, Any]]
    
    # Metadata
    version: int
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]


class ApprovalRequest(BaseModel):
    change_request_id: UUID
    approver_id: UUID
    step_number: int
    is_required: bool = True
    is_parallel: bool = False
    depends_on_step: Optional[int] = None
    due_date: Optional[datetime] = None


class ApprovalDecisionRequest(BaseModel):
    decision: ApprovalDecision
    comments: Optional[str] = None
    conditions: Optional[str] = None


class ChangeRequest(BaseModel):
    """Full change request model for internal use"""
    id: str
    change_number: str
    title: str
    description: str
    justification: Optional[str]
    change_type: ChangeType
    priority: PriorityLevel
    status: ChangeStatus
    
    # Requestor information
    requested_by: str
    requested_date: datetime
    required_by_date: Optional[date]
    
    # Project linkage
    project_id: str
    affected_milestones: List[str] = Field(default_factory=list)
    affected_pos: List[str] = Field(default_factory=list)
    
    # Impact estimates
    estimated_cost_impact: Optional[Decimal] = None
    estimated_schedule_impact_days: Optional[int] = None
    estimated_effort_hours: Optional[Decimal] = None
    
    # Actual impacts
    actual_cost_impact: Optional[Decimal] = None
    actual_schedule_impact_days: Optional[int] = None
    actual_effort_hours: Optional[Decimal] = None
    
    # Implementation tracking
    implementation_start_date: Optional[date] = None
    implementation_end_date: Optional[date] = None
    implementation_notes: Optional[str] = None
    
    # Metadata
    template_id: Optional[str] = None
    version: int = 1
    parent_change_id: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    closed_by: Optional[str] = None