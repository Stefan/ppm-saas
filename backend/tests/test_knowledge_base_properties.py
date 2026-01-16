"""
Property-Based Tests for Knowledge Base RAG System
Tests universal correctness properties for knowledge documents and vector chunks

Feature: ai-help-chat-knowledge-base
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
from datetime import datetime
from typing import List, Dict, Any
import uuid

# Import models and schemas
from models.knowledge import (
    FeatureCategory,
    create_knowledge_document_dict,
    create_vector_chunk_dict
)
from schemas.knowledge import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentResponse,
    AccessControl,
    VectorChunkCreate
)


# =====================================================
# HYPOTHESIS STRATEGIES
# =====================================================

@composite
def feature_category_strategy(draw):
    """Generate random feature categories"""
    return draw(st.sampled_from(list(FeatureCategory)))


@composite
def access_control_strategy(draw):
    """Generate random access control settings"""
    roles = draw(st.lists(
        st.sampled_from(['admin', 'manager', 'user', 'viewer', 'content_manager']),
        min_size=0,
        max_size=3,
        unique=True
    ))
    is_public = draw(st.booleans())
    return AccessControl(requiredRoles=roles, isPublic=is_public)


@composite
def knowledge_document_strategy(draw):
    """Generate random knowledge documents"""
    title = draw(st.text(min_size=1, max_size=500, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))))
    content = draw(st.text(min_size=1, max_size=5000, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))))
    category = draw(feature_category_strategy())
    keywords = draw(st.lists(
        st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        min_size=0,
        max_size=10,
        unique=True
    ))
    
    # Generate metadata
    metadata = {
        "author": draw(st.text(min_size=1, max_size=100)),
        "lastReviewed": draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31))).isoformat(),
        "version": draw(st.text(min_size=1, max_size=20))
    }
    
    access_control = draw(access_control_strategy())
    version = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'P'))))
    
    return KnowledgeDocumentCreate(
        title=title,
        content=content,
        category=category,
        keywords=keywords,
        metadata=metadata,
        access_control=access_control,
        version=version
    )


@composite
def embedding_vector_strategy(draw):
    """Generate random embedding vectors with 1536 dimensions"""
    return draw(st.lists(
        st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        min_size=1536,
        max_size=1536
    ))


@composite
def vector_chunk_strategy(draw):
    """Generate random vector chunks"""
    document_id = str(uuid.uuid4())
    chunk_index = draw(st.integers(min_value=0, max_value=1000))
    content = draw(st.text(min_size=1, max_size=2000, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))))
    embedding = draw(embedding_vector_strategy())
    metadata = {
        "document_title": draw(st.text(min_size=1, max_size=200)),
        "category": draw(feature_category_strategy()).value,
        "section": draw(st.text(min_size=1, max_size=100))
    }
    
    return VectorChunkCreate(
        document_id=document_id,
        chunk_index=chunk_index,
        content=content,
        embedding=embedding,
        metadata=metadata
    )


# =====================================================
# PROPERTY 1: DOCUMENT METADATA COMPLETENESS
# Feature: ai-help-chat-knowledge-base, Property 1: Document Metadata Completeness
# Validates: Requirements 1.2
# =====================================================

@given(doc=knowledge_document_strategy())
@settings(max_examples=100)
def test_property_1_document_metadata_completeness(doc: KnowledgeDocumentCreate):
    """
    Property 1: Document Metadata Completeness
    
    For any Knowledge_Document created in the system, it must contain all required 
    metadata fields (category, keywords, lastUpdated, version) with non-null values.
    
    Validates: Requirements 1.2
    """
    # Verify all required fields are present and non-null
    assert doc.title is not None, "Title must not be None"
    assert doc.content is not None, "Content must not be None"
    assert doc.category is not None, "Category must not be None"
    assert doc.keywords is not None, "Keywords must not be None"
    assert doc.metadata is not None, "Metadata must not be None"
    assert doc.access_control is not None, "Access control must not be None"
    assert doc.version is not None, "Version must not be None"
    
    # Verify title is not empty
    assert len(doc.title.strip()) > 0, "Title must not be empty"
    
    # Verify content is not empty
    assert len(doc.content.strip()) > 0, "Content must not be empty"
    
    # Verify category is a valid FeatureCategory
    assert hasattr(doc.category, 'value'), "Category must be an enum with a value attribute"
    assert doc.category.value in [
        "dashboard", "resource_management", "financial_tracking", "risk_management",
        "monte_carlo", "pmr", "change_management", "schedule_management",
        "ai_features", "collaboration", "audit_trails", "user_management", "general"
    ], f"Category value {doc.category.value} must be a valid feature category"
    
    # Verify keywords is a list
    assert isinstance(doc.keywords, list), "Keywords must be a list"
    
    # Verify metadata is a dictionary
    assert isinstance(doc.metadata, dict), "Metadata must be a dictionary"
    
    # Verify access_control is an AccessControl object
    assert isinstance(doc.access_control, AccessControl), "Access control must be an AccessControl object"
    
    # Verify version is not empty
    assert len(doc.version.strip()) > 0, "Version must not be empty"
    
    # Create document dict to verify it can be created
    doc_dict = create_knowledge_document_dict(
        title=doc.title,
        content=doc.content,
        category=doc.category,
        keywords=doc.keywords,
        metadata=doc.metadata,
        access_control=doc.access_control.model_dump(),
        version=doc.version
    )
    
    # Verify the created dict has all required fields
    assert "id" in doc_dict, "Document dict must have id"
    assert "title" in doc_dict, "Document dict must have title"
    assert "content" in doc_dict, "Document dict must have content"
    assert "category" in doc_dict, "Document dict must have category"
    assert "keywords" in doc_dict, "Document dict must have keywords"
    assert "metadata" in doc_dict, "Document dict must have metadata"
    assert "access_control" in doc_dict, "Document dict must have access_control"
    assert "version" in doc_dict, "Document dict must have version"
    assert "created_at" in doc_dict, "Document dict must have created_at"
    assert "updated_at" in doc_dict, "Document dict must have updated_at"


# =====================================================
# PROPERTY 2: VALID CATEGORY ASSIGNMENT
# Feature: ai-help-chat-knowledge-base, Property 2: Valid Category Assignment
# Validates: Requirements 1.3
# =====================================================

@given(doc=knowledge_document_strategy())
@settings(max_examples=100)
def test_property_2_valid_category_assignment(doc: KnowledgeDocumentCreate):
    """
    Property 2: Valid Category Assignment
    
    For any Knowledge_Document stored in the Knowledge_Base, its category must be 
    one of the defined FeatureCategory enum values.
    
    Validates: Requirements 1.3
    """
    # Verify category is a valid FeatureCategory enum value
    assert hasattr(doc.category, 'value'), "Category must be an enum with a value attribute"
    
    # Verify category is one of the defined values
    valid_category_values = [
        "dashboard", "resource_management", "financial_tracking", "risk_management",
        "monte_carlo", "pmr", "change_management", "schedule_management",
        "ai_features", "collaboration", "audit_trails", "user_management", "general"
    ]
    
    assert doc.category.value in valid_category_values, f"Category {doc.category.value} must be one of the defined FeatureCategory values"
    
    # Verify category value is a string when converted
    category_value = doc.category.value if isinstance(doc.category, FeatureCategory) else doc.category
    assert isinstance(category_value, str), "Category value must be a string"
    
    # Verify category value is not empty
    assert len(category_value) > 0, "Category value must not be empty"
    
    # Verify category value matches one of the expected string values
    expected_values = [
        "dashboard", "resource_management", "financial_tracking", "risk_management",
        "monte_carlo", "pmr", "change_management", "schedule_management",
        "ai_features", "collaboration", "audit_trails", "user_management", "general"
    ]
    assert category_value in expected_values, f"Category value {category_value} must be one of the expected values"
    
    # Create document dict and verify category is preserved correctly
    doc_dict = create_knowledge_document_dict(
        title=doc.title,
        content=doc.content,
        category=doc.category,
        keywords=doc.keywords,
        metadata=doc.metadata,
        access_control=doc.access_control.model_dump(),
        version=doc.version
    )
    
    # Verify category in dict is a valid string value
    assert doc_dict["category"] in expected_values, "Category in document dict must be a valid string value"


# =====================================================
# ADDITIONAL PROPERTY TESTS FOR VECTOR CHUNKS
# =====================================================

@given(chunk=vector_chunk_strategy())
@settings(max_examples=100)
def test_vector_chunk_embedding_dimension(chunk: VectorChunkCreate):
    """
    Property: Vector Chunk Embedding Dimension
    
    For any vector chunk created, the embedding must have exactly 1536 dimensions
    (OpenAI text-embedding-3-small dimension).
    """
    # Verify embedding has exactly 1536 dimensions
    assert len(chunk.embedding) == 1536, f"Embedding must have 1536 dimensions, got {len(chunk.embedding)}"
    
    # Verify all embedding values are floats
    assert all(isinstance(v, float) for v in chunk.embedding), "All embedding values must be floats"
    
    # Verify no NaN or infinity values
    assert all(not (v != v) for v in chunk.embedding), "Embedding must not contain NaN values"  # NaN check
    assert all(abs(v) != float('inf') for v in chunk.embedding), "Embedding must not contain infinity values"


@given(chunk=vector_chunk_strategy())
@settings(max_examples=100)
def test_vector_chunk_index_non_negative(chunk: VectorChunkCreate):
    """
    Property: Vector Chunk Index Non-Negative
    
    For any vector chunk created, the chunk_index must be non-negative.
    """
    # Verify chunk_index is non-negative
    assert chunk.chunk_index >= 0, f"Chunk index must be non-negative, got {chunk.chunk_index}"
    
    # Verify chunk_index is an integer
    assert isinstance(chunk.chunk_index, int), "Chunk index must be an integer"


@given(chunk=vector_chunk_strategy())
@settings(max_examples=100)
def test_vector_chunk_content_not_empty(chunk: VectorChunkCreate):
    """
    Property: Vector Chunk Content Not Empty
    
    For any vector chunk created, the content must not be empty.
    """
    # Verify content is not None
    assert chunk.content is not None, "Chunk content must not be None"
    
    # Verify content is not empty after stripping whitespace
    assert len(chunk.content.strip()) > 0, "Chunk content must not be empty"
    
    # Verify content is a string
    assert isinstance(chunk.content, str), "Chunk content must be a string"


@given(doc=knowledge_document_strategy())
@settings(max_examples=100)
def test_access_control_structure(doc: KnowledgeDocumentCreate):
    """
    Property: Access Control Structure
    
    For any knowledge document, the access_control must have the correct structure
    with requiredRoles (list) and isPublic (boolean).
    """
    # Verify access_control is an AccessControl object
    assert isinstance(doc.access_control, AccessControl), "Access control must be an AccessControl object"
    
    # Verify requiredRoles is a list
    assert isinstance(doc.access_control.requiredRoles, list), "requiredRoles must be a list"
    
    # Verify all roles are strings
    assert all(isinstance(role, str) for role in doc.access_control.requiredRoles), "All roles must be strings"
    
    # Verify isPublic is a boolean
    assert isinstance(doc.access_control.isPublic, bool), "isPublic must be a boolean"
    
    # Verify access_control can be converted to dict
    access_dict = doc.access_control.model_dump()
    assert "requiredRoles" in access_dict, "Access control dict must have requiredRoles"
    assert "isPublic" in access_dict, "Access control dict must have isPublic"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
