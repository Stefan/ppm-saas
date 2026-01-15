"""
Enhanced Project Monthly Report (PMR) - Pydantic Models
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from enum import Enum
from uuid import UUID, uuid4
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal

# Import base models
from .base import BaseResponse


class PMRStatus(str, Enum):
    """PMR report status"""
    draft = "draft"
    review = "review"
    approved = "approved"
    distributed = "distributed"


class PMRTemplateType(str, Enum):
    """PMR template types"""
    executive = "executive"
    technical = "technical"
    financial = "financial"
    custom = "custom"


class AIInsightType(str, Enum):
    """AI insight types"""
    prediction = "prediction"
    recommendation = "recommendation"
    alert = "alert"
    summary = "summary"


class AIInsightCategory(str, Enum):
    """AI insight categories"""
    budget = "budget"
    schedule = "schedule"
    resource = "resource"
    risk = "risk"
    quality = "quality"


class AIInsightPriority(str, Enum):
    """AI insight priority levels"""
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class EditSessionType(str, Enum):
    """Interactive edit session types"""
    chat = "chat"
    direct = "direct"
    collaborative = "collaborative"


class ExportFormat(str, Enum):
    """Export format types"""
    pdf = "pdf"
    excel = "excel"
    slides = "slides"
    word = "word"
    powerpoint = "powerpoint"


class ExportJobStatus(str, Enum):
    """Export job status"""
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


# Core PMR Models

class PMRReportBase(BaseModel):
    """Base PMR report model"""
    project_id: UUID
    report_month: date
    report_year: int
    template_id: UUID
    title: str
    executive_summary: Optional[str] = None
    ai_generated_insights: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Optional[Dict[str, Any]] = Field(default_factory=dict)
    visualizations: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    status: PMRStatus = PMRStatus.draft
    version: int = 1
    is_active: bool = True

    @validator('report_year')
    def validate_report_year(cls, v):
        current_year = datetime.now().year
        if v < 2020 or v > current_year + 5:
            raise ValueError(f'Report year must be between 2020 and {current_year + 5}')
        return v

    @validator('version')
    def validate_version(cls, v):
        if v < 1:
            raise ValueError('Version must be at least 1')
        return v


class PMRReportCreate(PMRReportBase):
    """PMR report creation model"""
    generated_by: UUID


class PMRReportUpdate(BaseModel):
    """PMR report update model"""
    title: Optional[str] = None
    executive_summary: Optional[str] = None
    sections: Optional[List[Dict[str, Any]]] = None
    metrics: Optional[Dict[str, Any]] = None
    visualizations: Optional[List[Dict[str, Any]]] = None
    status: Optional[PMRStatus] = None
    approved_by: Optional[UUID] = None


class PMRReport(PMRReportBase):
    """Complete PMR report model"""
    id: UUID
    generated_by: UUID
    approved_by: Optional[UUID] = None
    generated_at: datetime
    last_modified: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PMRReportResponse(BaseResponse):
    """PMR report API response model"""
    project_id: UUID
    report_month: date
    report_year: int
    template_id: UUID
    title: str
    executive_summary: Optional[str]
    ai_generated_insights: List[Dict[str, Any]]
    sections: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    visualizations: List[Dict[str, Any]]
    status: PMRStatus
    generated_by: UUID
    approved_by: Optional[UUID]
    generated_at: datetime
    last_modified: datetime
    version: int
    is_active: bool


# PMR Template Models

class PMRTemplateBase(BaseModel):
    """Base PMR template model"""
    name: str
    description: Optional[str] = None
    template_type: PMRTemplateType
    industry_focus: Optional[str] = None
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    default_metrics: Optional[List[str]] = Field(default_factory=list)
    ai_suggestions: Optional[Dict[str, Any]] = Field(default_factory=dict)
    branding_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    export_formats: List[ExportFormat] = Field(default_factory=list)
    is_public: bool = False
    usage_count: int = 0
    rating: Optional[Decimal] = None

    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 0 or v > 5):
            raise ValueError('Rating must be between 0 and 5')
        return v

    @validator('usage_count')
    def validate_usage_count(cls, v):
        if v < 0:
            raise ValueError('Usage count cannot be negative')
        return v


class PMRTemplateCreate(PMRTemplateBase):
    """PMR template creation model"""
    created_by: UUID
    organization_id: Optional[UUID] = None


class PMRTemplateUpdate(BaseModel):
    """PMR template update model"""
    name: Optional[str] = None
    description: Optional[str] = None
    sections: Optional[List[Dict[str, Any]]] = None
    default_metrics: Optional[List[str]] = None
    ai_suggestions: Optional[Dict[str, Any]] = None
    branding_config: Optional[Dict[str, Any]] = None
    export_formats: Optional[List[ExportFormat]] = None
    is_public: Optional[bool] = None
    rating: Optional[Decimal] = None


class PMRTemplate(PMRTemplateBase):
    """Complete PMR template model"""
    id: UUID
    created_by: UUID
    organization_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PMRTemplateResponse(BaseResponse):
    """PMR template API response model"""
    name: str
    description: Optional[str]
    template_type: PMRTemplateType
    industry_focus: Optional[str]
    sections: List[Dict[str, Any]]
    default_metrics: List[str]
    ai_suggestions: Dict[str, Any]
    branding_config: Dict[str, Any]
    export_formats: List[ExportFormat]
    is_public: bool
    created_by: UUID
    organization_id: Optional[UUID]
    usage_count: int
    rating: Optional[Decimal]


# AI Insight Models

class AIInsightBase(BaseModel):
    """Base AI insight model"""
    insight_type: AIInsightType
    category: AIInsightCategory
    title: str
    content: str
    confidence_score: Decimal = Field(ge=0.0, le=1.0)
    supporting_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    predicted_impact: Optional[str] = None
    recommended_actions: Optional[List[str]] = Field(default_factory=list)
    priority: AIInsightPriority = AIInsightPriority.medium
    validated: bool = False
    validation_notes: Optional[str] = None

    @validator('confidence_score')
    def validate_confidence_score(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError('Confidence score must be between 0.0 and 1.0')
        return v


class AIInsightCreate(AIInsightBase):
    """AI insight creation model"""
    report_id: UUID


class AIInsightUpdate(BaseModel):
    """AI insight update model"""
    title: Optional[str] = None
    content: Optional[str] = None
    confidence_score: Optional[Decimal] = None
    predicted_impact: Optional[str] = None
    recommended_actions: Optional[List[str]] = None
    priority: Optional[AIInsightPriority] = None
    validated: Optional[bool] = None
    validation_notes: Optional[str] = None


class AIInsight(AIInsightBase):
    """Complete AI insight model"""
    id: UUID
    report_id: UUID
    generated_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AIInsightResponse(BaseResponse):
    """AI insight API response model"""
    report_id: UUID
    insight_type: AIInsightType
    category: AIInsightCategory
    title: str
    content: str
    confidence_score: Decimal
    supporting_data: Dict[str, Any]
    predicted_impact: Optional[str]
    recommended_actions: List[str]
    priority: AIInsightPriority
    generated_at: datetime
    validated: bool
    validation_notes: Optional[str]


# Interactive Edit Session Models

class EditSessionBase(BaseModel):
    """Base edit session model"""
    session_type: EditSessionType = EditSessionType.chat
    chat_messages: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    changes_made: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    active_section: Optional[str] = None
    is_active: bool = True


class EditSessionCreate(EditSessionBase):
    """Edit session creation model"""
    report_id: UUID
    user_id: UUID


class EditSessionUpdate(BaseModel):
    """Edit session update model"""
    chat_messages: Optional[List[Dict[str, Any]]] = None
    changes_made: Optional[List[Dict[str, Any]]] = None
    active_section: Optional[str] = None
    is_active: Optional[bool] = None


class EditSession(EditSessionBase):
    """Complete edit session model"""
    id: UUID
    report_id: UUID
    user_id: UUID
    started_at: datetime
    last_activity: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EditSessionResponse(BaseResponse):
    """Edit session API response model"""
    report_id: UUID
    user_id: UUID
    session_type: EditSessionType
    chat_messages: List[Dict[str, Any]]
    changes_made: List[Dict[str, Any]]
    active_section: Optional[str]
    started_at: datetime
    last_activity: datetime
    is_active: bool


# Export Job Models

class ExportJobBase(BaseModel):
    """Base export job model"""
    export_format: ExportFormat
    template_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    export_options: Optional[Dict[str, Any]] = Field(default_factory=dict)
    status: ExportJobStatus = ExportJobStatus.queued
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None

    @validator('file_size')
    def validate_file_size(cls, v):
        if v is not None and v < 0:
            raise ValueError('File size cannot be negative')
        return v


class ExportJobCreate(ExportJobBase):
    """Export job creation model"""
    report_id: UUID
    requested_by: UUID


class ExportJobUpdate(BaseModel):
    """Export job update model"""
    status: Optional[ExportJobStatus] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None


class ExportJob(ExportJobBase):
    """Complete export job model"""
    id: UUID
    report_id: UUID
    requested_by: UUID
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExportJobResponse(BaseResponse):
    """Export job API response model"""
    report_id: UUID
    export_format: ExportFormat
    template_config: Dict[str, Any]
    status: ExportJobStatus
    file_url: Optional[str]
    file_size: Optional[int]
    export_options: Dict[str, Any]
    requested_by: UUID
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]


# Request/Response Models for API Operations

class PMRGenerationRequest(BaseModel):
    """Request model for PMR generation"""
    project_id: UUID
    report_month: date
    report_year: int
    template_id: UUID
    title: str
    description: Optional[str] = None
    include_ai_insights: bool = True
    include_monte_carlo: bool = False
    custom_sections: Optional[List[Dict[str, Any]]] = None

    @validator('report_year')
    def validate_report_year(cls, v):
        current_year = datetime.now().year
        if v < 2020 or v > current_year + 5:
            raise ValueError(f'Report year must be between 2020 and {current_year + 5}')
        return v


class ChatEditRequest(BaseModel):
    """Request model for chat-based editing"""
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

    @validator('message')
    def validate_message(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Message cannot be empty')
        if len(v) > 2000:
            raise ValueError('Message too long (max 2000 characters)')
        return v.strip()


class ChatEditResponse(BaseModel):
    """Response model for chat-based editing"""
    response: str
    changes_applied: List[Dict[str, Any]]
    session_id: str
    suggestions: Optional[List[Dict[str, Any]]] = None
    confidence: Decimal
    processing_time_ms: int


class SectionUpdateRequest(BaseModel):
    """Request model for section updates"""
    section_id: str
    content: Dict[str, Any]
    merge_strategy: str = "replace"  # "replace", "merge", "append"

    @validator('merge_strategy')
    def validate_merge_strategy(cls, v):
        if v not in ["replace", "merge", "append"]:
            raise ValueError('Merge strategy must be "replace", "merge", or "append"')
        return v


class SectionUpdateResponse(BaseModel):
    """Response model for section updates"""
    section_id: str
    updated_content: Dict[str, Any]
    version: int
    last_modified: datetime
    success: bool


class AISuggestionsRequest(BaseModel):
    """Request model for AI suggestions"""
    section: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    suggestion_type: str = "content"  # "content", "structure", "metrics", "visualizations"

    @validator('suggestion_type')
    def validate_suggestion_type(cls, v):
        if v not in ["content", "structure", "metrics", "visualizations"]:
            raise ValueError('Suggestion type must be one of: content, structure, metrics, visualizations')
        return v


class AISuggestionsResponse(BaseModel):
    """Response model for AI suggestions"""
    suggestions: List[Dict[str, Any]]
    confidence: Decimal
    applicable_sections: List[str]
    processing_time_ms: int


class ValidationRequest(BaseModel):
    """Request model for report validation"""
    validation_type: str = "accuracy"  # "accuracy", "completeness", "consistency"
    check_data_sources: bool = True
    include_recommendations: bool = True

    @validator('validation_type')
    def validate_validation_type(cls, v):
        if v not in ["accuracy", "completeness", "consistency"]:
            raise ValueError('Validation type must be one of: accuracy, completeness, consistency')
        return v


class ValidationResponse(BaseModel):
    """Response model for report validation"""
    is_valid: bool
    validation_score: Decimal
    issues_found: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    data_freshness: Dict[str, Any]
    validation_timestamp: datetime


class MonteCarloRequest(BaseModel):
    """Request model for Monte Carlo analysis"""
    analysis_type: str = "budget_variance"  # "budget_variance", "schedule_variance", "resource_risk"
    iterations: int = Field(default=1000, ge=100, le=10000)
    confidence_levels: List[Decimal] = Field(default=[0.5, 0.8, 0.95])
    parameters: Optional[Dict[str, Any]] = None

    @validator('analysis_type')
    def validate_analysis_type(cls, v):
        if v not in ["budget_variance", "schedule_variance", "resource_risk"]:
            raise ValueError('Analysis type must be one of: budget_variance, schedule_variance, resource_risk')
        return v

    @validator('confidence_levels')
    def validate_confidence_levels(cls, v):
        for level in v:
            if level <= 0 or level >= 1:
                raise ValueError('Confidence levels must be between 0 and 1')
        return sorted(v)


class MonteCarloResponse(BaseModel):
    """Response model for Monte Carlo analysis"""
    analysis_type: str
    iterations: int
    results: Dict[str, Any]
    confidence_intervals: Dict[str, Dict[str, Decimal]]
    risk_assessment: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    processing_time_ms: int
    generated_at: datetime


# Template AI Suggestions Models

class TemplateAISuggestionsRequest(BaseModel):
    """Request model for template AI suggestions"""
    project_type: Optional[str] = None
    industry: Optional[str] = None
    stakeholder_types: Optional[List[str]] = None
    reporting_frequency: str = "monthly"

    @validator('reporting_frequency')
    def validate_reporting_frequency(cls, v):
        if v not in ["weekly", "monthly", "quarterly", "annual"]:
            raise ValueError('Reporting frequency must be one of: weekly, monthly, quarterly, annual')
        return v


class TemplateAISuggestionsResponse(BaseModel):
    """Response model for template AI suggestions"""
    suggested_sections: List[Dict[str, Any]]
    recommended_metrics: List[Dict[str, Any]]
    visualization_suggestions: List[Dict[str, Any]]
    branding_recommendations: Dict[str, Any]
    confidence: Decimal
    reasoning: str


# Bulk Operations Models

class BulkReportGenerationRequest(BaseModel):
    """Request model for bulk report generation"""
    project_ids: List[UUID]
    report_month: date
    report_year: int
    template_id: UUID
    include_ai_insights: bool = True
    batch_size: int = Field(default=10, ge=1, le=50)

    @validator('project_ids')
    def validate_project_ids(cls, v):
        if len(v) == 0:
            raise ValueError('At least one project ID is required')
        if len(v) > 100:
            raise ValueError('Maximum 100 projects per batch')
        return v


class BulkReportGenerationResponse(BaseModel):
    """Response model for bulk report generation"""
    batch_id: str
    total_projects: int
    successful_reports: List[UUID]
    failed_reports: List[Dict[str, Any]]
    processing_time_ms: int
    estimated_completion: datetime


# ============================================================================
# ENHANCED PMR MODELS - AI-Powered, Collaborative, Real-Time
# ============================================================================

class ValidationStatus(str, Enum):
    """Validation status for AI insights"""
    pending = "pending"
    validated = "validated"
    rejected = "rejected"
    needs_review = "needs_review"


class SessionType(str, Enum):
    """Collaboration session types"""
    chat = "chat"
    direct = "direct"
    collaborative = "collaborative"


class ParticipantRole(str, Enum):
    """Collaboration participant roles"""
    owner = "owner"
    editor = "editor"
    commenter = "commenter"
    viewer = "viewer"


class ChangeEventType(str, Enum):
    """Types of change events in collaboration"""
    section_update = "section_update"
    content_edit = "content_edit"
    comment_added = "comment_added"
    insight_validated = "insight_validated"
    cursor_move = "cursor_move"


# Enhanced AI Insight Engine Models

class AIInsightEngine(BaseModel):
    """
    AI Insight Engine configuration and state
    Manages AI-powered insight generation with confidence scoring
    """
    engine_id: str = Field(default_factory=lambda: str(uuid4()))
    model_version: str = "gpt-4"
    temperature: Decimal = Field(default=Decimal("0.7"), ge=Decimal("0.0"), le=Decimal("2.0"))
    max_tokens: int = Field(default=2000, ge=100, le=4000)
    insight_categories_enabled: List[AIInsightCategory] = Field(
        default_factory=lambda: [
            AIInsightCategory.budget,
            AIInsightCategory.schedule,
            AIInsightCategory.resource,
            AIInsightCategory.risk,
            AIInsightCategory.quality
        ]
    )
    confidence_threshold: Decimal = Field(default=Decimal("0.7"), ge=Decimal("0.0"), le=Decimal("1.0"))
    max_insights_per_category: int = Field(default=5, ge=1, le=20)
    enable_predictions: bool = True
    enable_recommendations: bool = True
    enable_alerts: bool = True
    context_window_days: int = Field(default=90, ge=30, le=365)
    last_training_date: Optional[datetime] = None
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)

    @validator('temperature')
    def validate_temperature(cls, v):
        if v < Decimal("0.0") or v > Decimal("2.0"):
            raise ValueError('Temperature must be between 0.0 and 2.0')
        return v

    @validator('confidence_threshold')
    def validate_confidence_threshold(cls, v):
        if v < Decimal("0.0") or v > Decimal("1.0"):
            raise ValueError('Confidence threshold must be between 0.0 and 1.0')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "engine_id": "ai-engine-001",
                "model_version": "gpt-4",
                "temperature": 0.7,
                "confidence_threshold": 0.75,
                "enable_predictions": True
            }
        }


class EnhancedAIInsight(AIInsightBase):
    """
    Enhanced AI Insight with additional metadata and validation
    Extends base AI insight with real-time metrics and validation status
    """
    id: UUID = Field(default_factory=uuid4)
    report_id: UUID
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    validation_status: ValidationStatus = ValidationStatus.pending
    validated_by: Optional[UUID] = None
    validated_at: Optional[datetime] = None
    feedback_score: Optional[Decimal] = Field(default=None, ge=Decimal("0.0"), le=Decimal("5.0"))
    user_feedback: Optional[str] = None
    impact_score: Optional[Decimal] = Field(default=None, ge=Decimal("0.0"), le=Decimal("1.0"))
    related_insights: List[UUID] = Field(default_factory=list)
    data_sources: List[str] = Field(default_factory=list)
    refresh_frequency: Optional[str] = None  # "real-time", "hourly", "daily"
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('feedback_score')
    def validate_feedback_score(cls, v):
        if v is not None and (v < Decimal("0.0") or v > Decimal("5.0")):
            raise ValueError('Feedback score must be between 0.0 and 5.0')
        return v

    @validator('impact_score')
    def validate_impact_score(cls, v):
        if v is not None and (v < Decimal("0.0") or v > Decimal("1.0")):
            raise ValueError('Impact score must be between 0.0 and 1.0')
        return v

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "insight_type": "prediction",
                "category": "budget",
                "title": "Budget Variance Prediction",
                "content": "Project likely to finish 8% under budget",
                "confidence_score": 0.87,
                "validation_status": "validated",
                "impact_score": 0.75
            }
        }


# Collaboration Models

class CollaborationParticipant(BaseModel):
    """Participant in a collaboration session"""
    user_id: UUID
    user_name: str
    user_email: str
    role: ParticipantRole
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    is_online: bool = True
    current_section: Optional[str] = None
    cursor_position: Optional[int] = None
    color: Optional[str] = None  # For visual identification

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_name": "John Doe",
                "user_email": "john@example.com",
                "role": "editor",
                "is_online": True
            }
        }


class Comment(BaseModel):
    """Comment on a report section"""
    comment_id: UUID = Field(default_factory=uuid4)
    section_id: str
    user_id: UUID
    user_name: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    resolved: bool = False
    resolved_by: Optional[UUID] = None
    resolved_at: Optional[datetime] = None
    parent_comment_id: Optional[UUID] = None  # For threaded comments
    mentions: List[UUID] = Field(default_factory=list)
    attachments: List[Dict[str, Any]] = Field(default_factory=list)

    @validator('content')
    def validate_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Comment content cannot be empty')
        if len(v) > 5000:
            raise ValueError('Comment too long (max 5000 characters)')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "section_id": "executive_summary",
                "user_name": "Jane Smith",
                "content": "Consider adding more detail about the milestone",
                "resolved": False
            }
        }


class ChangeEvent(BaseModel):
    """Event representing a change in the report"""
    event_id: UUID = Field(default_factory=uuid4)
    event_type: ChangeEventType
    user_id: UUID
    user_name: str
    section_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    changes: Dict[str, Any] = Field(default_factory=dict)
    previous_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "section_update",
                "user_name": "John Doe",
                "section_id": "budget_analysis",
                "changes": {"content": "Updated budget forecast"}
            }
        }


class CollaborationSession(BaseModel):
    """
    Real-time collaboration session for Enhanced PMR
    Manages multi-user editing with conflict resolution
    """
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    report_id: UUID
    session_type: SessionType = SessionType.collaborative
    participants: List[CollaborationParticipant] = Field(default_factory=list)
    active_editors: List[str] = Field(default_factory=list)  # List of user_ids currently editing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    changes_log: List[ChangeEvent] = Field(default_factory=list)
    comments: List[Comment] = Field(default_factory=list)
    locked_sections: Dict[str, UUID] = Field(default_factory=dict)  # section_id -> user_id
    version_history: List[Dict[str, Any]] = Field(default_factory=list)
    conflict_resolution_strategy: str = "last_write_wins"  # "last_write_wins", "manual", "merge"
    max_participants: int = Field(default=10, ge=1, le=50)
    session_timeout_minutes: int = Field(default=60, ge=5, le=480)
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('conflict_resolution_strategy')
    def validate_conflict_resolution(cls, v):
        if v not in ["last_write_wins", "manual", "merge"]:
            raise ValueError('Conflict resolution strategy must be one of: last_write_wins, manual, merge')
        return v

    @validator('participants')
    def validate_max_participants(cls, v, values):
        max_participants = values.get('max_participants', 10)
        if len(v) > max_participants:
            raise ValueError(f'Cannot exceed {max_participants} participants')
        return v

    def add_participant(self, participant: CollaborationParticipant) -> bool:
        """Add a participant to the session"""
        if len(self.participants) >= self.max_participants:
            return False
        if any(p.user_id == participant.user_id for p in self.participants):
            return False
        self.participants.append(participant)
        self.last_activity = datetime.utcnow()
        return True

    def remove_participant(self, user_id: UUID) -> bool:
        """Remove a participant from the session"""
        initial_count = len(self.participants)
        self.participants = [p for p in self.participants if p.user_id != user_id]
        user_id_str = str(user_id)
        if user_id_str in self.active_editors:
            self.active_editors.remove(user_id_str)
        self.last_activity = datetime.utcnow()
        return len(self.participants) < initial_count

    def add_change_event(self, event: ChangeEvent) -> None:
        """Add a change event to the log"""
        self.changes_log.append(event)
        self.last_activity = datetime.utcnow()

    def add_comment(self, comment: Comment) -> None:
        """Add a comment to the session"""
        self.comments.append(comment)
        self.last_activity = datetime.utcnow()

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session-001",
                "report_id": "123e4567-e89b-12d3-a456-426614174000",
                "session_type": "collaborative",
                "max_participants": 10,
                "is_active": True
            }
        }


# Enhanced PMR Report Model

class MonteCarloResults(BaseModel):
    """Results from Monte Carlo analysis"""
    analysis_type: str
    iterations: int
    budget_completion: Optional[Dict[str, Decimal]] = None  # p50, p80, p95
    schedule_completion: Optional[Dict[str, Any]] = None  # p50, p80, p95 dates
    resource_utilization: Optional[Dict[str, Decimal]] = None
    risk_probability: Optional[Dict[str, Decimal]] = None
    confidence_intervals: Dict[str, Dict[str, Decimal]] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    parameters_used: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "analysis_type": "budget_variance",
                "iterations": 10000,
                "budget_completion": {"p50": 0.92, "p80": 0.96, "p95": 1.02},
                "confidence_intervals": {"budget": {"lower": 0.85, "upper": 1.05}}
            }
        }


class RealTimeMetrics(BaseModel):
    """Real-time metrics for Enhanced PMR"""
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    budget_utilization: Optional[Decimal] = None
    schedule_performance_index: Optional[Decimal] = None
    cost_performance_index: Optional[Decimal] = None
    risk_score: Optional[Decimal] = Field(default=None, ge=Decimal("0.0"), le=Decimal("1.0"))
    team_velocity: Optional[Decimal] = None
    quality_score: Optional[Decimal] = Field(default=None, ge=Decimal("0.0"), le=Decimal("1.0"))
    stakeholder_satisfaction: Optional[Decimal] = Field(default=None, ge=Decimal("0.0"), le=Decimal("5.0"))
    active_issues_count: Optional[int] = Field(default=0, ge=0)
    completed_milestones: Optional[int] = Field(default=0, ge=0)
    upcoming_milestones: Optional[int] = Field(default=0, ge=0)
    data_freshness_minutes: Optional[int] = None
    metrics_metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('risk_score', 'quality_score')
    def validate_score_range(cls, v):
        if v is not None and (v < Decimal("0.0") or v > Decimal("1.0")):
            raise ValueError('Score must be between 0.0 and 1.0')
        return v

    @validator('stakeholder_satisfaction')
    def validate_satisfaction(cls, v):
        if v is not None and (v < Decimal("0.0") or v > Decimal("5.0")):
            raise ValueError('Stakeholder satisfaction must be between 0.0 and 5.0')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "budget_utilization": 0.78,
                "schedule_performance_index": 1.12,
                "risk_score": 0.23,
                "active_issues_count": 5
            }
        }


class EnhancedPMRReport(PMRReportBase):
    """
    Enhanced PMR Report with AI capabilities, collaboration, and real-time metrics
    This is the main model for the "3x better than Cora" PMR feature
    """
    id: UUID = Field(default_factory=uuid4)
    
    # AI-powered features
    ai_insights: List[EnhancedAIInsight] = Field(default_factory=list)
    ai_insight_engine: Optional[AIInsightEngine] = None
    ai_generated_summary: Optional[str] = None
    ai_confidence_scores: Dict[str, Decimal] = Field(default_factory=dict)
    
    # Monte Carlo analysis
    monte_carlo_analysis: Optional[MonteCarloResults] = None
    monte_carlo_enabled: bool = False
    
    # Collaboration features
    collaboration_session: Optional[CollaborationSession] = None
    collaboration_enabled: bool = False
    
    # Export and template features
    export_history: List[Dict[str, Any]] = Field(default_factory=list)
    template_customizations: Dict[str, Any] = Field(default_factory=dict)
    
    # Real-time metrics
    real_time_metrics: Optional[RealTimeMetrics] = None
    metrics_refresh_interval_seconds: int = Field(default=300, ge=60, le=3600)
    
    # Enhanced metadata
    generated_by: UUID
    approved_by: Optional[UUID] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    last_ai_update: Optional[datetime] = None
    last_collaboration_activity: Optional[datetime] = None
    
    # Performance tracking
    generation_time_seconds: Optional[Decimal] = None
    ai_processing_time_seconds: Optional[Decimal] = None
    total_edits: int = Field(default=0, ge=0)
    total_collaborators: int = Field(default=0, ge=0)
    
    # Audit trail
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    audit_log: List[Dict[str, Any]] = Field(default_factory=list)

    @validator('metrics_refresh_interval_seconds')
    def validate_refresh_interval(cls, v):
        if v < 60 or v > 3600:
            raise ValueError('Metrics refresh interval must be between 60 and 3600 seconds')
        return v

    def add_ai_insight(self, insight: EnhancedAIInsight) -> None:
        """Add an AI insight to the report"""
        self.ai_insights.append(insight)
        self.last_ai_update = datetime.utcnow()
        self.last_modified = datetime.utcnow()

    def update_real_time_metrics(self, metrics: RealTimeMetrics) -> None:
        """Update real-time metrics"""
        self.real_time_metrics = metrics
        self.last_modified = datetime.utcnow()

    def start_collaboration_session(self, session: CollaborationSession) -> None:
        """Start a collaboration session"""
        self.collaboration_session = session
        self.collaboration_enabled = True
        self.last_collaboration_activity = datetime.utcnow()
        self.last_modified = datetime.utcnow()

    def end_collaboration_session(self) -> None:
        """End the current collaboration session"""
        if self.collaboration_session:
            self.collaboration_session.is_active = False
            self.collaboration_enabled = False
            self.last_modified = datetime.utcnow()

    def add_export_record(self, export_format: str, file_url: str, file_size: int) -> None:
        """Add an export record to history"""
        export_record = {
            "format": export_format,
            "file_url": file_url,
            "file_size": file_size,
            "exported_at": datetime.utcnow().isoformat(),
            "exported_by": str(self.generated_by)
        }
        self.export_history.append(export_record)
        self.last_modified = datetime.utcnow()

    def increment_edit_count(self) -> None:
        """Increment the total edit count"""
        self.total_edits += 1
        self.last_modified = datetime.utcnow()

    def add_audit_entry(self, action: str, user_id: UUID, details: Dict[str, Any]) -> None:
        """Add an entry to the audit log"""
        audit_entry = {
            "action": action,
            "user_id": str(user_id),
            "timestamp": datetime.utcnow().isoformat(),
            "details": details
        }
        self.audit_log.append(audit_entry)

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Project Alpha Monthly Report",
                "report_month": "2024-01-01",
                "report_year": 2024,
                "collaboration_enabled": True,
                "monte_carlo_enabled": True,
                "status": "approved"
            }
        }


# Request/Response Models for Enhanced PMR

class EnhancedPMRGenerationRequest(PMRGenerationRequest):
    """Enhanced request model for PMR generation with AI features"""
    enable_collaboration: bool = True
    enable_real_time_metrics: bool = True
    ai_insight_categories: Optional[List[AIInsightCategory]] = None
    monte_carlo_iterations: int = Field(default=1000, ge=100, le=10000)
    monte_carlo_confidence_levels: List[Decimal] = Field(default=[0.5, 0.8, 0.95])
    metrics_refresh_interval_seconds: int = Field(default=300, ge=60, le=3600)
    collaboration_max_participants: int = Field(default=10, ge=1, le=50)


class EnhancedPMRResponse(BaseResponse):
    """Enhanced PMR report API response model"""
    project_id: UUID
    title: str
    status: PMRStatus
    report_month: date
    report_year: int
    
    # AI features
    ai_insights: List[EnhancedAIInsight]
    ai_generated_summary: Optional[str]
    ai_confidence_scores: Dict[str, Decimal]
    
    # Monte Carlo
    monte_carlo_analysis: Optional[MonteCarloResults]
    
    # Collaboration
    collaboration_session: Optional[CollaborationSession]
    collaboration_enabled: bool
    
    # Real-time metrics
    real_time_metrics: Optional[RealTimeMetrics]
    
    # Metadata
    generated_by: UUID
    generated_at: datetime
    last_modified: datetime
    version: int
    total_edits: int
    total_collaborators: int


class CollaborationSessionCreate(BaseModel):
    """Request model for creating a collaboration session"""
    report_id: UUID
    session_type: SessionType = SessionType.collaborative
    max_participants: int = Field(default=10, ge=1, le=50)
    conflict_resolution_strategy: str = "last_write_wins"
    session_timeout_minutes: int = Field(default=60, ge=5, le=480)


class CollaborationSessionResponse(BaseResponse):
    """Response model for collaboration session"""
    session_id: str
    report_id: UUID
    session_type: SessionType
    participants: List[CollaborationParticipant]
    active_editors: List[str]
    started_at: datetime
    last_activity: datetime
    is_active: bool
    max_participants: int


class AddParticipantRequest(BaseModel):
    """Request model for adding a participant to a collaboration session"""
    user_id: UUID
    user_name: str
    user_email: str
    role: ParticipantRole = ParticipantRole.editor


class AddCommentRequest(BaseModel):
    """Request model for adding a comment"""
    section_id: str
    content: str
    parent_comment_id: Optional[UUID] = None
    mentions: List[UUID] = Field(default_factory=list)

    @validator('content')
    def validate_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Comment content cannot be empty')
        if len(v) > 5000:
            raise ValueError('Comment too long (max 5000 characters)')
        return v.strip()


class ResolveCommentRequest(BaseModel):
    """Request model for resolving a comment"""
    comment_id: UUID
    resolution_note: Optional[str] = None