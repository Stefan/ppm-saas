"""
Knowledge Base Models for RAG System
Data models for knowledge documents, vector chunks, and query logs
"""

from datetime import datetime
from enum import Enum
import uuid


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


# Helper functions for working with the database models

def create_knowledge_document_dict(
    title: str,
    content: str,
    category: FeatureCategory,
    keywords: list[str] = None,
    metadata: dict = None,
    access_control: dict = None,
    version: str = "1.0.0"
) -> dict:
    """
    Create a dictionary for inserting a knowledge document
    
    Args:
        title: Document title
        content: Document content
        category: Feature category
        keywords: List of keywords (optional)
        metadata: Additional metadata (optional)
        access_control: Access control settings (optional)
        version: Document version (default: "1.0.0")
    
    Returns:
        Dictionary ready for database insertion
    """
    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "category": category.value if isinstance(category, FeatureCategory) else category,
        "keywords": keywords or [],
        "metadata": metadata or {},
        "access_control": access_control or {"requiredRoles": [], "isPublic": True},
        "version": version,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


def create_vector_chunk_dict(
    document_id: str,
    chunk_index: int,
    content: str,
    embedding: list[float],
    metadata: dict = None
) -> dict:
    """
    Create a dictionary for inserting a vector chunk
    
    Args:
        document_id: ID of the parent document
        chunk_index: Index of this chunk in the document
        content: Chunk content
        embedding: Vector embedding (1536 dimensions)
        metadata: Additional metadata (optional)
    
    Returns:
        Dictionary ready for database insertion
    """
    return {
        "id": str(uuid.uuid4()),
        "document_id": document_id,
        "chunk_index": chunk_index,
        "content": content,
        "embedding": embedding,
        "metadata": metadata or {},
        "created_at": datetime.utcnow().isoformat()
    }


def create_query_log_dict(
    query: str,
    user_id: str = None,
    query_language: str = "en",
    retrieved_chunks: list = None,
    response: str = None,
    response_language: str = "en",
    citations: list = None,
    confidence_score: float = None,
    processing_time_ms: int = None,
    feedback: str = None,
    user_context: dict = None
) -> dict:
    """
    Create a dictionary for inserting a query log
    
    Args:
        query: User query text
        user_id: ID of the user (optional)
        query_language: Language of the query (default: "en")
        retrieved_chunks: List of retrieved chunks (optional)
        response: Generated response (optional)
        response_language: Language of the response (default: "en")
        citations: List of citations (optional)
        confidence_score: Confidence score 0-1 (optional)
        processing_time_ms: Processing time in milliseconds (optional)
        feedback: User feedback (optional)
        user_context: User context information (optional)
    
    Returns:
        Dictionary ready for database insertion
    """
    return {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "query": query,
        "query_language": query_language,
        "retrieved_chunks": retrieved_chunks or [],
        "response": response,
        "response_language": response_language,
        "citations": citations or [],
        "confidence_score": confidence_score,
        "processing_time_ms": processing_time_ms,
        "feedback": feedback,
        "user_context": user_context or {},
        "created_at": datetime.utcnow().isoformat()
    }
