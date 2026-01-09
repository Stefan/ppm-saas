"""
Schedule Management Data Models
Provides Pydantic models for integrated master schedule system
"""

from enum import Enum
from datetime import date, datetime
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator

# =====================================================
# ENUMS
# =====================================================

class DependencyType(str, Enum):
    """Task dependency relationship types"""
    FINISH_TO_START = "finish_to_start"
    START_TO_START = "start_to_start"
    FINISH_TO_FINISH = "finish_to_finish"
    START_TO_FINISH = "start_to_finish"

class TaskStatus(str, Enum):
    """Task execution status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"

class MilestoneStatus(str, Enum):
    """Milestone achievement status"""
    PLANNED = "planned"
    AT_RISK = "at_risk"
    ACHIEVED = "achieved"
    MISSED = "missed"

# =====================================================
# BASE MODELS
# =====================================================

class ScheduleBase(BaseModel):
    """Base schedule model with common fields"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: date
    end_date: date
    
    @field_validator('end_date')
    @classmethod
    def end_date_must_be_after_start_date(cls, v, info):
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

class TaskBase(BaseModel):
    """Base task model with common fields"""
    wbs_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    planned_start_date: date
    planned_end_date: date
    duration_days: int = Field(..., ge=1)
    
    @field_validator('planned_end_date')
    @classmethod
    def planned_end_date_must_be_after_start_date(cls, v, info):
        if 'planned_start_date' in info.data and v < info.data['planned_start_date']:
            raise ValueError('planned_end_date must be after planned_start_date')
        return v

# =====================================================
# CREATE MODELS
# =====================================================

class ScheduleCreate(ScheduleBase):
    """Model for creating new schedules"""
    project_id: UUID

class TaskCreate(TaskBase):
    """Model for creating new tasks"""
    parent_task_id: Optional[UUID] = None
    planned_effort_hours: Optional[float] = Field(None, ge=0)
    deliverables: List[str] = Field(default_factory=list)
    acceptance_criteria: Optional[str] = None

class TaskDependencyCreate(BaseModel):
    """Model for creating task dependencies"""
    predecessor_task_id: UUID
    successor_task_id: UUID
    dependency_type: DependencyType = DependencyType.FINISH_TO_START
    lag_days: int = Field(default=0)
    
    @field_validator('successor_task_id')
    @classmethod
    def no_self_dependency(cls, v, info):
        if 'predecessor_task_id' in info.data and v == info.data['predecessor_task_id']:
            raise ValueError('Task cannot depend on itself')
        return v

class WBSElementCreate(BaseModel):
    """Model for creating WBS elements"""
    parent_element_id: Optional[UUID] = None
    wbs_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    work_package_manager: Optional[UUID] = None
    deliverable_description: Optional[str] = None
    acceptance_criteria: Optional[str] = None

class MilestoneCreate(BaseModel):
    """Model for creating milestones"""
    task_id: Optional[UUID] = None
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_date: date
    success_criteria: Optional[str] = None
    responsible_party: Optional[UUID] = None
    deliverables: List[str] = Field(default_factory=list)
    approval_required: bool = False

class ResourceAssignmentCreate(BaseModel):
    """Model for creating resource assignments"""
    resource_id: UUID
    allocation_percentage: int = Field(..., ge=1, le=100)
    planned_hours: Optional[float] = Field(None, ge=0)
    assignment_start_date: Optional[date] = None
    assignment_end_date: Optional[date] = None
    
    @field_validator('assignment_end_date')
    @classmethod
    def assignment_end_date_validation(cls, v, info):
        if v and 'assignment_start_date' in info.data and info.data['assignment_start_date'] and v < info.data['assignment_start_date']:
            raise ValueError('assignment_end_date must be after assignment_start_date')
        return v

class ScheduleBaselineCreate(BaseModel):
    """Model for creating schedule baselines"""
    baseline_name: str = Field(..., min_length=1, max_length=255)
    baseline_date: date
    description: Optional[str] = None
    baseline_data: Dict[str, Any]

# =====================================================
# UPDATE MODELS
# =====================================================

class ScheduleUpdate(BaseModel):
    """Model for updating schedules"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_dates(self):
        start_date = self.start_date
        end_date = self.end_date
        if start_date and end_date and end_date < start_date:
            raise ValueError('end_date must be after start_date')
        return self

class TaskUpdate(BaseModel):
    """Model for updating tasks"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    duration_days: Optional[int] = Field(None, ge=1)
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    status: Optional[TaskStatus] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    actual_effort_hours: Optional[float] = Field(None, ge=0)
    
    @model_validator(mode='after')
    def validate_dates(self):
        planned_start = self.planned_start_date
        planned_end = self.planned_end_date
        actual_start = self.actual_start_date
        actual_end = self.actual_end_date
        
        if planned_start and planned_end and planned_end < planned_start:
            raise ValueError('planned_end_date must be after planned_start_date')
        
        if actual_start and actual_end and actual_end < actual_start:
            raise ValueError('actual_end_date must be after actual_start_date')
        
        return self

class TaskProgressUpdate(BaseModel):
    """Model for updating task progress"""
    progress_percentage: int = Field(..., ge=0, le=100)
    status: TaskStatus
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    actual_effort_hours: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None
    
    @field_validator('actual_end_date')
    @classmethod
    def actual_end_date_validation(cls, v, info):
        if v and 'actual_start_date' in info.data and info.data['actual_start_date'] and v < info.data['actual_start_date']:
            raise ValueError('actual_end_date must be after actual_start_date')
        return v

# =====================================================
# RESPONSE MODELS
# =====================================================

class ScheduleResponse(BaseModel):
    """Response model for schedules"""
    id: str
    project_id: str
    name: str
    description: Optional[str]
    start_date: date
    end_date: date
    baseline_start_date: Optional[date]
    baseline_end_date: Optional[date]
    status: str
    schedule_performance_index: Optional[float]
    schedule_variance_days: Optional[int]
    created_by: str
    created_at: datetime
    updated_at: datetime

class TaskResponse(BaseModel):
    """Response model for tasks"""
    id: str
    schedule_id: str
    parent_task_id: Optional[str]
    wbs_code: str
    name: str
    description: Optional[str]
    planned_start_date: date
    planned_end_date: date
    actual_start_date: Optional[date]
    actual_end_date: Optional[date]
    duration_days: int
    baseline_start_date: Optional[date]
    baseline_end_date: Optional[date]
    baseline_duration_days: Optional[int]
    progress_percentage: int
    status: str
    planned_effort_hours: Optional[float]
    actual_effort_hours: Optional[float]
    remaining_effort_hours: Optional[float]
    is_critical: bool
    total_float_days: int
    free_float_days: int
    early_start_date: Optional[date]
    early_finish_date: Optional[date]
    late_start_date: Optional[date]
    late_finish_date: Optional[date]
    deliverables: List[str]
    acceptance_criteria: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime

class TaskDependencyResponse(BaseModel):
    """Response model for task dependencies"""
    id: str
    predecessor_task_id: str
    successor_task_id: str
    dependency_type: str
    lag_days: int
    created_by: str
    created_at: datetime

class WBSElementResponse(BaseModel):
    """Response model for WBS elements"""
    id: str
    schedule_id: str
    parent_element_id: Optional[str]
    task_id: Optional[str]
    wbs_code: str
    name: str
    description: Optional[str]
    level_number: int
    sort_order: int
    work_package_manager: Optional[str]
    deliverable_description: Optional[str]
    acceptance_criteria: Optional[str]
    progress_percentage: int
    created_by: str
    created_at: datetime
    updated_at: datetime

class MilestoneResponse(BaseModel):
    """Response model for milestones"""
    id: str
    project_id: str
    schedule_id: Optional[str]
    task_id: Optional[str]
    name: str
    description: Optional[str]
    target_date: date
    actual_date: Optional[date]
    status: str
    success_criteria: Optional[str]
    responsible_party: Optional[str]
    deliverables: List[str]
    approval_required: bool
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    progress_percentage: int
    created_by: str
    created_at: datetime
    updated_at: datetime

class ResourceAssignmentResponse(BaseModel):
    """Response model for resource assignments"""
    id: str
    task_id: str
    resource_id: str
    allocation_percentage: int
    planned_hours: Optional[float]
    actual_hours: Optional[float]
    assignment_start_date: Optional[date]
    assignment_end_date: Optional[date]
    created_by: str
    created_at: datetime
    updated_at: datetime

class ScheduleBaselineResponse(BaseModel):
    """Response model for schedule baselines"""
    id: str
    schedule_id: str
    baseline_name: str
    baseline_date: date
    description: Optional[str]
    baseline_data: Dict[str, Any]
    is_approved: bool
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_by: str
    created_at: datetime

# =====================================================
# COMPLEX RESPONSE MODELS
# =====================================================

class ScheduleWithTasksResponse(BaseModel):
    """Response model for schedule with all related data"""
    schedule: ScheduleResponse
    tasks: List[TaskResponse]
    dependencies: List[TaskDependencyResponse]
    milestones: List[MilestoneResponse]
    critical_path: List[str]

class TaskHierarchyResponse(BaseModel):
    """Response model for task hierarchy"""
    id: str
    schedule_id: str
    parent_task_id: Optional[str]
    wbs_code: str
    name: str
    planned_start_date: date
    planned_end_date: date
    progress_percentage: int
    status: str
    is_critical: bool
    level: int
    path: str
    children: List['TaskHierarchyResponse'] = []

# Enable forward references
TaskHierarchyResponse.update_forward_refs()

class CriticalPathResult(BaseModel):
    """Response model for critical path analysis"""
    critical_tasks: List[str]
    project_duration_days: int
    critical_path_length: float
    schedule_risk_factors: List[str]

class FloatCalculation(BaseModel):
    """Response model for float calculations"""
    task_id: str
    total_float_days: int
    free_float_days: int
    early_start_date: date
    early_finish_date: date
    late_start_date: date
    late_finish_date: date

class ScheduleRecalculationResult(BaseModel):
    """Response model for schedule recalculation"""
    schedule_id: str
    affected_tasks: List[str]
    critical_path_changed: bool
    new_critical_path: List[str]
    recalculation_timestamp: datetime

class WBSHierarchy(BaseModel):
    """Response model for WBS hierarchy"""
    schedule_id: str
    elements: List[WBSElementResponse]
    max_depth: int

class WBSValidationResult(BaseModel):
    """Response model for WBS validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class CircularDependency(BaseModel):
    """Response model for circular dependency detection"""
    task_ids: List[str]
    dependency_chain: List[str]

class ScheduleDateCalculation(BaseModel):
    """Response model for schedule date calculations"""
    schedule_id: str
    calculated_tasks: List[str]
    calculation_timestamp: datetime
    errors: List[str]

# =====================================================
# ANALYTICS AND REPORTING MODELS
# =====================================================

class ScheduleSummary(BaseModel):
    """Response model for schedule summary"""
    id: str
    project_id: str
    name: str
    description: Optional[str]
    start_date: date
    end_date: date
    status: str
    schedule_performance_index: Optional[float]
    schedule_variance_days: Optional[int]
    total_tasks: int
    completed_tasks: int
    critical_tasks: int
    avg_progress: Optional[int]
    created_at: datetime
    updated_at: datetime

class ResourceUtilizationReport(BaseModel):
    """Response model for resource utilization"""
    resource_id: str
    resource_name: str
    total_allocation: int
    assignments: List[ResourceAssignmentResponse]
    utilization_percentage: float
    conflicts: List[str]

class SchedulePerformanceMetrics(BaseModel):
    """Response model for schedule performance"""
    schedule_id: str
    schedule_performance_index: float
    schedule_variance_days: int
    earned_value_metrics: Dict[str, float]
    trend_analysis: Dict[str, Any]
    risk_indicators: List[str]

# =====================================================
# FILTER AND QUERY MODELS
# =====================================================

class ScheduleFilter(BaseModel):
    """Model for filtering schedules"""
    project_id: Optional[UUID] = None
    status: Optional[str] = None
    start_date_from: Optional[date] = None
    start_date_to: Optional[date] = None
    created_by: Optional[UUID] = None

class TaskFilter(BaseModel):
    """Model for filtering tasks"""
    schedule_id: Optional[UUID] = None
    parent_task_id: Optional[UUID] = None
    status: Optional[TaskStatus] = None
    is_critical: Optional[bool] = None
    progress_min: Optional[int] = Field(None, ge=0, le=100)
    progress_max: Optional[int] = Field(None, ge=0, le=100)
    assigned_to: Optional[UUID] = None

class PaginationParams(BaseModel):
    """Model for pagination parameters"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=1000)
    sort_by: Optional[str] = None
    sort_order: Optional[str] = Field(default="asc", pattern="^(asc|desc)$")

# =====================================================
# CONFIGURATION MODELS
# =====================================================

class GanttRenderOptions(BaseModel):
    """Model for Gantt chart rendering options"""
    time_scale: str = Field(default="week", pattern="^(day|week|month|quarter)$")
    show_critical_path: bool = True
    show_dependencies: bool = True
    show_progress: bool = True
    show_baselines: bool = False
    date_format: str = "YYYY-MM-DD"
    theme: str = "default"

class ScheduleExportOptions(BaseModel):
    """Model for schedule export options"""
    format: str = Field(..., pattern="^(ms_project|primavera|csv|pdf)$")
    include_dependencies: bool = True
    include_resources: bool = True
    include_baselines: bool = False
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None