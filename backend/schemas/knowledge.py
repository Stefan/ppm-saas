"""
Knowledge Base Pydantic Schemas for API Validation
Defines request/response models for the RAG system API
"""

from pydantic import BaseModel, Field, validator, constr, confloat, conint
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class FeatureCategory(str, Enum):
    """Feature categories for knowledge documents"""
    DASHBOARD = "dashboard"
    RESOURCE_MANAGEMENT = "resource_management"
    FINANCIAL_TRACKING = "financial_tracking"
    RISK_MANAGEMENT = "risk_management"
    MONTE_CARLO = "monte_carlo"
    PMR = "pmr"
    CHANGE_MANAGEMENT = "change_management"
    SCHEDULE_MANAGEMENT = "schedule_management"
    AI_FEATURES = "ai_features"
    COLLABORATION = "collaboration"
    AUDIT_TRAILS = "audit_trails"
    USER_MANAGEMENT = "user_management"
    GENERAL = "general"


class FeedbackType(str, Enum):
    """Feedback types for query responses"""
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    INCORRECT = "incorrect"


# =====================================================
# ACCESS CONTROL SCHEMAS
# =====================================================

class AccessControl(BaseModel):
    """Access control settings for knowledge documents"""
    requiredRoles: List[str] = Field(default_factory=list, description="Roles required to access this document")
    isPublic: bool = Field(default=True, description="Whether document is publicly accessible")
    
    class Config:
        json_schema_extra = {
            "example": {
                "requiredRoles": ["admin", "manager"],
                "isPublic": False
            }
        }


# =====================================================
# KNOWLEDGE DOCUMENT SCHEMAS
# =====================================================

class KnowledgeDocumentBase(BaseModel):
    """Base schema for knowledge documents"""
    title: constr(min_length=1, max_length=500) = Field(..., description="Document title")
    content: constr(min_length=1) = Field(..., description="Document content")
    category: FeatureCategory = Field(..., description="Feature category")
    keywords: List[str] = Field(default_factory=list, description="Keywords for search")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    access_control: AccessControl = Field(default_factory=AccessControl, description="Access control settings")
    version: constr(min_length=1, max_length=50) = Field(default="1.0.0", description="Document version")


class KnowledgeDocumentCreate(KnowledgeDocumentBase):
    """Schema for creating a knowledge document"""
    pass


class KnowledgeDocumentUpdate(BaseModel):
    """Schema for updating a knowledge document"""
    title: Optional[constr(min_length=1, max_length=500)] = None
    content: Optional[constr(min_length=1)] = None
    category: Optional[FeatureCategory] = None
    keywords: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    access_control: Optional[AccessControl] = None
    version: Optional[constr(min_length=1, max_length=50)] = None


class KnowledgeDocumentResponse(KnowledgeDocumentBase):
    """Schema for knowledge document response"""
    id: str = Field(..., description="Document ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    chunk_count: Optional[int] = Field(None, description="Number of chunks")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Getting Started with Dashboard",
                "content": "The dashboard provides an overview of all your projects...",
                "category": "dashboard",
                "keywords": ["dashboard", "overview", "getting-started"],
                "metadata": {"author": "John Doe", "lastReviewed": "2024-01-15"},
                "access_control": {"requiredRoles": [], "isPublic": True},
                "version": "1.0.0",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z",
                "chunk_count": 5
            }
        }


# =====================================================
# VECTOR CHUNK SCHEMAS
# =====================================================

class VectorChunkBase(BaseModel):
    """Base schema for vector chunks"""
    document_id: str = Field(..., description="Parent document ID")
    chunk_index: conint(ge=0) = Field(..., description="Chunk index in document")
    content: constr(min_length=1) = Field(..., description="Chunk content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")


class VectorChunkCreate(VectorChunkBase):
    """Schema for creating a vector chunk"""
    embedding: List[float] = Field(..., description="Vector embedding (1536 dimensions)")
    
    @validator('embedding')
    def validate_embedding_dimension(cls, v):
        if len(v) != 1536:
            raise ValueError(f"Embedding must have 1536 dimensions, got {len(v)}")
        return v


class VectorChunkResponse(VectorChunkBase):
    """Schema for vector chunk response"""
    id: str = Field(..., description="Chunk ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    similarity: Optional[float] = Field(None, description="Similarity score (for search results)")
    
    class Config:
        from_attributes = True


# =====================================================
# QUERY AND RESPONSE SCHEMAS
# =====================================================

class Citation(BaseModel):
    """Citation for a response"""
    document_id: str = Field(..., description="Source document ID")
    document_title: str = Field(..., description="Source document title")
    category: FeatureCategory = Field(..., description="Document category")
    relevance_score: confloat(ge=0, le=1) = Field(..., description="Relevance score")
    chunk_content: Optional[str] = Field(None, description="Relevant chunk content")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "document_title": "Dashboard Overview",
                "category": "dashboard",
                "relevance_score": 0.92,
                "chunk_content": "The dashboard provides real-time insights..."
            }
        }


class UserContext(BaseModel):
    """User context for query processing"""
    user_id: Optional[str] = Field(None, description="User ID")
    role: Optional[str] = Field(None, description="User role")
    language: str = Field(default="en", description="User language")
    current_page: Optional[str] = Field(None, description="Current page/feature")
    current_feature: Optional[str] = Field(None, description="Current feature context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "role": "manager",
                "language": "en",
                "current_page": "/dashboard",
                "current_feature": "dashboard"
            }
        }


class ChatQuery(BaseModel):
    """Schema for chat query request"""
    query: constr(min_length=1, max_length=2000) = Field(..., description="User query")
    user_context: UserContext = Field(default_factory=UserContext, description="User context")
    conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="Previous messages")
    top_k: conint(ge=1, le=20) = Field(default=5, description="Number of chunks to retrieve")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "How do I create a new project?",
                "user_context": {
                    "user_id": "user123",
                    "role": "manager",
                    "language": "en",
                    "current_page": "/projects"
                },
                "conversation_history": [],
                "top_k": 5
            }
        }


class ChatResponse(BaseModel):
    """Schema for chat response"""
    message: str = Field(..., description="Generated response")
    citations: List[Citation] = Field(default_factory=list, description="Source citations")
    confidence: confloat(ge=0, le=1) = Field(..., description="Response confidence score")
    processing_time_ms: conint(ge=0) = Field(..., description="Processing time in milliseconds")
    query_id: str = Field(..., description="Query log ID for feedback")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "To create a new project, navigate to the Projects page and click the 'New Project' button...",
                "citations": [
                    {
                        "document_id": "123e4567-e89b-12d3-a456-426614174000",
                        "document_title": "Project Management Guide",
                        "category": "dashboard",
                        "relevance_score": 0.95
                    }
                ],
                "confidence": 0.92,
                "processing_time_ms": 1250,
                "query_id": "query123"
            }
        }


class FeedbackRequest(BaseModel):
    """Schema for submitting feedback on a response"""
    query_id: str = Field(..., description="Query log ID")
    feedback: FeedbackType = Field(..., description="Feedback type")
    feedback_text: Optional[str] = Field(None, description="Optional feedback text")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "query123",
                "feedback": "helpful",
                "feedback_text": "This answered my question perfectly!"
            }
        }


# =====================================================
# QUERY LOG SCHEMAS
# =====================================================

class QueryLogResponse(BaseModel):
    """Schema for query log response"""
    id: str = Field(..., description="Log ID")
    user_id: Optional[str] = Field(None, description="User ID")
    query: str = Field(..., description="User query")
    query_language: str = Field(..., description="Query language")
    response: Optional[str] = Field(None, description="Generated response")
    response_language: str = Field(..., description="Response language")
    citations: List[Citation] = Field(default_factory=list, description="Citations")
    confidence_score: Optional[float] = Field(None, description="Confidence score")
    processing_time_ms: Optional[int] = Field(None, description="Processing time")
    feedback: Optional[FeedbackType] = Field(None, description="User feedback")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


# =====================================================
# ANALYTICS SCHEMAS
# =====================================================

class KnowledgeBaseStats(BaseModel):
    """Schema for knowledge base statistics"""
    total_documents: int = Field(..., description="Total number of documents")
    total_chunks: int = Field(..., description="Total number of chunks")
    documents_by_category: Dict[str, int] = Field(..., description="Documents per category")
    avg_chunks_per_document: float = Field(..., description="Average chunks per document")
    last_updated: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_documents": 150,
                "total_chunks": 750,
                "documents_by_category": {
                    "dashboard": 20,
                    "resource_management": 25,
                    "financial_tracking": 18
                },
                "avg_chunks_per_document": 5.0,
                "last_updated": "2024-01-15T10:00:00Z"
            }
        }


class QueryAnalytics(BaseModel):
    """Schema for query analytics"""
    total_queries: int = Field(..., description="Total number of queries")
    avg_confidence: float = Field(..., description="Average confidence score")
    avg_processing_time_ms: float = Field(..., description="Average processing time")
    feedback_distribution: Dict[str, int] = Field(..., description="Feedback distribution")
    top_languages: List[str] = Field(..., description="Most used languages")
    queries_by_day: Dict[str, int] = Field(..., description="Queries per day")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_queries": 1250,
                "avg_confidence": 0.87,
                "avg_processing_time_ms": 1450.5,
                "feedback_distribution": {
                    "helpful": 850,
                    "not_helpful": 120,
                    "incorrect": 30,
                    "no_feedback": 250
                },
                "top_languages": ["en", "de", "fr"],
                "queries_by_day": {
                    "2024-01-15": 45,
                    "2024-01-14": 52
                }
            }
        }


class DocumentationGap(BaseModel):
    """Schema for documentation gap"""
    query_pattern: str = Field(..., description="Query pattern")
    query_count: int = Field(..., description="Number of similar queries")
    avg_confidence: float = Field(..., description="Average confidence score")
    negative_feedback_rate: float = Field(..., description="Negative feedback rate (%)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query_pattern": "how to export reports",
                "query_count": 15,
                "avg_confidence": 0.45,
                "negative_feedback_rate": 60.0
            }
        }
