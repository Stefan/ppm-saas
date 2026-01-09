"""
Unit Tests for Help Content Management Service
Tests content embedding, search functionality, versioning, and updates
Requirements: 2.1, 2.3, 2.4
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime
from typing import List, Dict, Any

# Import the service and models
from services.help_content_service import HelpContentService
from models.help_content import (
    HelpContent, HelpContentCreate, HelpContentUpdate, HelpContentSearch,
    HelpContentSearchResult, HelpContentSearchResponse, ContentEmbedding,
    ContentVersion, ContentType, ReviewStatus, Language
)


@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    mock_client = Mock()
    mock_table = Mock()
    mock_client.table.return_value = mock_table
    mock_client.rpc.return_value = Mock()
    return mock_client

@pytest.fixture
def mock_openai():
    """Mock OpenAI client"""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3] * 512)]  # Mock 1536-dim embedding
    mock_client.embeddings.create.return_value = mock_response
    return mock_client

@pytest.fixture
def help_content_service(mock_supabase, mock_openai):
    """Create HelpContentService instance with mocked dependencies"""
    with patch('services.help_content_service.OpenAI', return_value=mock_openai):
        service = HelpContentService(mock_supabase, "test-api-key")
        service.openai_client = mock_openai
        return service

@pytest.fixture
def sample_content_create():
    """Sample content creation data"""
    return HelpContentCreate(
        content_type=ContentType.guide,
        title="Test Guide",
        content="This is a comprehensive test guide for PPM platform features.",
        tags=["test", "guide", "ppm"],
        language=Language.en,
        slug="test-guide",
        meta_description="Test guide for PPM platform",
        keywords=["test", "guide", "ppm", "platform"]
    )

@pytest.fixture
def sample_content():
    """Sample help content"""
    return HelpContent(
        id=uuid4(),
        content_type=ContentType.guide,
        title="Test Guide",
        content="This is a comprehensive test guide for PPM platform features.",
        tags=["test", "guide", "ppm"],
        language=Language.en,
        slug="test-guide",
        meta_description="Test guide for PPM platform",
        keywords=["test", "guide", "ppm", "platform"],
        version=1,
        is_active=True,
        review_status=ReviewStatus.approved,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


class TestHelpContentService:
    """Test suite for Help Content Service"""


class TestContentEmbeddingFunctionality:
    """Test content embedding generation and management"""
    
    @pytest.mark.asyncio
    async def test_generate_content_embedding_success(self, help_content_service, sample_content, mock_openai):
        """Test successful embedding generation for content"""
        # Requirements: 2.1 - Context_Aware_Assistant SHALL integrate with existing RAG system
        
        # Mock successful embedding generation
        mock_embedding_response = Mock()
        mock_embedding_response.data = [Mock(embedding=[0.1, 0.2, 0.3] * 512)]
        mock_openai.embeddings.create.return_value = mock_embedding_response
        
        # Mock successful database upsert
        mock_upsert = Mock()
        mock_upsert.execute.return_value = Mock(data=[{"id": "test-id"}])
        help_content_service.supabase.table.return_value.upsert.return_value = mock_upsert
        
        # Test embedding generation
        await help_content_service._generate_content_embedding(sample_content)
        
        # Verify OpenAI API was called with correct parameters
        mock_openai.embeddings.create.assert_called_once()
        call_args = mock_openai.embeddings.create.call_args
        assert call_args[1]['model'] == "text-embedding-ada-002"
        assert sample_content.title in call_args[1]['input']
        assert sample_content.content in call_args[1]['input']
        
        # Verify embedding was stored in database
        help_content_service.supabase.table.assert_called_with("embeddings")
        mock_upsert.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_content_embedding_truncation(self, help_content_service, sample_content, mock_openai):
        """Test embedding generation with content truncation for long content"""
        # Requirements: 2.1 - Handle content length limits
        
        # Create content with very long text
        long_content = sample_content.model_copy()  # Use model_copy instead of deprecated copy
        long_content.content = "A" * 10000  # Exceeds max_content_length
        
        mock_embedding_response = Mock()
        mock_embedding_response.data = [Mock(embedding=[0.1, 0.2, 0.3] * 512)]
        mock_openai.embeddings.create.return_value = mock_embedding_response
        
        mock_upsert = Mock()
        mock_upsert.execute.return_value = Mock(data=[{"id": "test-id"}])
        help_content_service.supabase.table.return_value.upsert.return_value = mock_upsert
        
        await help_content_service._generate_content_embedding(long_content)
        
        # Verify content was truncated
        call_args = mock_openai.embeddings.create.call_args
        input_text = call_args[1]['input']
        assert len(input_text) <= help_content_service.max_content_length
    
    @pytest.mark.asyncio
    async def test_generate_content_embedding_error_handling(self, help_content_service, sample_content, mock_openai):
        """Test embedding generation error handling"""
        # Requirements: 2.1 - Handle embedding generation failures gracefully
        
        # Mock OpenAI API failure
        mock_openai.embeddings.create.side_effect = Exception("API Error")
        
        # Should not raise exception, but log error
        await help_content_service._generate_content_embedding(sample_content)
        
        # Verify OpenAI was called despite error
        mock_openai.embeddings.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_regenerate_embeddings_success(self, help_content_service, mock_openai):
        """Test bulk embedding regeneration"""
        # Requirements: 2.3 - Content search and retrieval functionality
        
        # Mock database response with content
        mock_content_data = [
            {
                "id": str(uuid4()),
                "title": "Test Guide 1",
                "content": "Content 1",
                "content_type": "guide",
                "tags": ["test"],
                "language": "en",
                "version": 1,
                "is_active": True,
                "review_status": "approved",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "title": "Test Guide 2", 
                "content": "Content 2",
                "content_type": "faq",
                "tags": ["test"],
                "language": "en",
                "version": 1,
                "is_active": True,
                "review_status": "approved",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
        
        mock_response = Mock()
        mock_response.data = mock_content_data
        mock_select = Mock()
        mock_select.eq.return_value.execute.return_value = mock_response
        help_content_service.supabase.table.return_value.select.return_value = mock_select
        
        # Mock successful embedding generation
        mock_embedding_response = Mock()
        mock_embedding_response.data = [Mock(embedding=[0.1, 0.2, 0.3] * 512)]
        mock_openai.embeddings.create.return_value = mock_embedding_response
        
        mock_upsert = Mock()
        mock_upsert.execute.return_value = Mock(data=[{"id": "test-id"}])
        help_content_service.supabase.table.return_value.upsert.return_value = mock_upsert
        
        # Test regeneration
        result = await help_content_service.regenerate_embeddings([ContentType.guide])
        
        # Verify results
        assert result["processed"] == 2
        assert result["errors"] == 0
        
        # Verify OpenAI was called for each content item
        assert mock_openai.embeddings.create.call_count == 2
    
    @pytest.mark.asyncio
    async def test_regenerate_embeddings_with_errors(self, help_content_service, mock_openai):
        """Test embedding regeneration with some failures"""
        # Requirements: 2.3 - Handle partial failures in bulk operations
        
        mock_content_data = [
            {
                "id": str(uuid4()),
                "title": "Test Guide 1",
                "content": "Content 1",
                "content_type": "guide",
                "tags": ["test"],
                "language": "en",
                "version": 1,
                "is_active": True,
                "review_status": "approved",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
        
        mock_response = Mock()
        mock_response.data = mock_content_data
        mock_select = Mock()
        mock_select.eq.return_value.execute.return_value = mock_response
        help_content_service.supabase.table.return_value.select.return_value = mock_select
        
        # Mock OpenAI failure
        mock_openai.embeddings.create.side_effect = Exception("API Error")
        
        result = await help_content_service.regenerate_embeddings()
        
        # Verify error handling
        assert result["processed"] == 0
        assert result["errors"] == 1


class TestContentSearchFunctionality:
    """Test content search and retrieval functionality"""
    
    @pytest.mark.asyncio
    async def test_vector_search_success(self, help_content_service, mock_openai):
        """Test successful vector similarity search"""
        # Requirements: 2.3 - Content search and retrieval functionality
        
        # Mock query embedding generation
        mock_embedding_response = Mock()
        mock_embedding_response.data = [Mock(embedding=[0.1, 0.2, 0.3] * 512)]
        mock_openai.embeddings.create.return_value = mock_embedding_response
        
        # Mock RPC search results
        mock_search_results = [
            {
                "id": str(uuid4()),
                "title": "Test Guide",
                "content": "Test content",
                "content_type": "guide",
                "tags": ["test"],
                "language": "en",
                "version": 1,
                "is_active": True,
                "review_status": "approved",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "similarity_score": 0.85
            }
        ]
        
        mock_rpc = Mock()
        mock_rpc.execute.return_value = Mock(data=mock_search_results)
        help_content_service.supabase.rpc.return_value = mock_rpc
        
        # Test search
        search_params = HelpContentSearch(
            query="test query",
            content_types=[ContentType.guide],
            languages=[Language.en],
            limit=10
        )
        
        results = await help_content_service._vector_search(search_params)
        
        # Verify results
        assert len(results) == 1
        assert isinstance(results[0], HelpContentSearchResult)
        assert results[0].similarity_score == 0.85
        assert results[0].content.title == "Test Guide"
        
        # Verify OpenAI embedding generation was called
        mock_openai.embeddings.create.assert_called_once_with(
            model="text-embedding-ada-002",
            input="test query"
        )
        
        # Verify RPC was called with correct parameters
        help_content_service.supabase.rpc.assert_called_once_with(
            'help_content_vector_search',
            {
                'query_embedding': [0.1, 0.2, 0.3] * 512,
                'content_types': ['guide'],
                'languages': ['en'],
                'tags': [],
                'is_active': True,
                'similarity_limit': 10,
                'offset_count': 0
            }
        )
    
    @pytest.mark.asyncio
    async def test_fallback_vector_search(self, help_content_service, mock_openai):
        """Test fallback vector search when RPC is not available"""
        # Requirements: 2.3 - Fallback search functionality
        
        # Mock query embedding generation
        mock_embedding_response = Mock()
        mock_embedding_response.data = [Mock(embedding=[0.1, 0.2, 0.3] * 512)]
        mock_openai.embeddings.create.return_value = mock_embedding_response
        
        # Mock RPC failure (triggers fallback)
        help_content_service.supabase.rpc.side_effect = Exception("RPC not available")
        
        # Mock embeddings table response for fallback
        mock_embeddings_data = [
            {
                "content_id": str(uuid4()),
                "embedding": [0.2, 0.3, 0.4] * 512,  # Similar to query
                "content_type": "help_content"
            }
        ]
        
        mock_embeddings_select = Mock()
        mock_embeddings_select.execute.return_value = Mock(data=mock_embeddings_data)
        
        # Mock content table response
        mock_content_data = [
            {
                "id": mock_embeddings_data[0]["content_id"],
                "title": "Fallback Test Guide",
                "content": "Fallback test content",
                "content_type": "guide",
                "tags": ["test"],
                "language": "en",
                "version": 1,
                "is_active": True,
                "review_status": "approved",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
        
        mock_content_select = Mock()
        mock_content_select.execute.return_value = Mock(data=mock_content_data)
        
        # Configure table mocks
        def table_side_effect(table_name):
            if table_name == "embeddings":
                mock_table = Mock()
                mock_table.select.return_value.eq.return_value = mock_embeddings_select
                return mock_table
            elif table_name == "help_content":
                mock_table = Mock()
                mock_table.select.return_value.in_.return_value = mock_content_select
                return mock_table
            return Mock()
        
        help_content_service.supabase.table.side_effect = table_side_effect
        
        # Test fallback search
        search_params = HelpContentSearch(query="test query", limit=5)
        query_embedding = [0.1, 0.2, 0.3] * 512
        
        results = await help_content_service._fallback_vector_search(query_embedding, search_params)
        
        # Verify fallback results
        assert len(results) == 1
        assert results[0].content.title == "Fallback Test Guide"
        assert results[0].similarity_score is not None
        assert 0.0 <= results[0].similarity_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_filter_search(self, help_content_service):
        """Test filtered search without vector similarity"""
        # Requirements: 2.3 - Basic filtering functionality
        
        # Mock database response
        mock_content_data = [
            {
                "id": str(uuid4()),
                "title": "Filtered Guide",
                "content": "Filtered content",
                "content_type": "guide",
                "tags": ["test", "filter"],
                "language": "en",
                "version": 1,
                "is_active": True,
                "review_status": "approved",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
        
        mock_query_builder = Mock()
        mock_query_builder.in_.return_value = mock_query_builder
        mock_query_builder.eq.return_value = mock_query_builder
        mock_query_builder.overlaps.return_value = mock_query_builder
        mock_query_builder.range.return_value = mock_query_builder
        mock_query_builder.execute.return_value = Mock(data=mock_content_data)
        
        help_content_service.supabase.table.return_value.select.return_value = mock_query_builder
        
        # Test filter search
        search_params = HelpContentSearch(
            content_types=[ContentType.guide],
            languages=[Language.en],
            tags=["test"],
            is_active=True,
            limit=10,
            offset=0
        )
        
        results = await help_content_service._filter_search(search_params)
        
        # Verify results
        assert len(results) == 1
        assert results[0].content.title == "Filtered Guide"
        assert results[0].similarity_score is None  # No similarity in filter search
        
        # Verify query builder was called with filters
        mock_query_builder.in_.assert_any_call("content_type", ["guide"])
        mock_query_builder.in_.assert_any_call("language", ["en"])
        mock_query_builder.eq.assert_called_with("is_active", True)
        mock_query_builder.overlaps.assert_called_with("tags", ["test"])
        mock_query_builder.range.assert_called_with(0, 9)
    
    @pytest.mark.asyncio
    async def test_search_content_with_query(self, help_content_service, mock_openai):
        """Test complete search functionality with query"""
        # Requirements: 2.3 - Complete search integration
        
        # Mock embedding generation
        mock_embedding_response = Mock()
        mock_embedding_response.data = [Mock(embedding=[0.1, 0.2, 0.3] * 512)]
        mock_openai.embeddings.create.return_value = mock_embedding_response
        
        # Mock vector search results
        mock_search_results = [
            {
                "id": str(uuid4()),
                "title": "Search Result",
                "content": "Search content",
                "content_type": "guide",
                "tags": ["search"],
                "language": "en",
                "version": 1,
                "is_active": True,
                "review_status": "approved",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "similarity_score": 0.9
            }
        ]
        
        mock_rpc = Mock()
        mock_rpc.execute.return_value = Mock(data=mock_search_results)
        help_content_service.supabase.rpc.return_value = mock_rpc
        
        # Mock count query
        mock_count_response = Mock()
        mock_count_response.count = 1
        mock_count_query = Mock()
        mock_count_query.execute.return_value = mock_count_response
        help_content_service.supabase.table.return_value.select.return_value = mock_count_query
        
        # Test search
        search_params = HelpContentSearch(query="test search", limit=10)
        response = await help_content_service.search_content(search_params)
        
        # Verify response
        assert isinstance(response, HelpContentSearchResponse)
        assert len(response.results) == 1
        assert response.total_count == 1
        assert response.has_more is False
        assert response.results[0].similarity_score == 0.9
    
    def test_calculate_cosine_similarity(self, help_content_service):
        """Test cosine similarity calculation"""
        # Requirements: 2.3 - Vector similarity calculation
        
        # Test identical vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = help_content_service._calculate_cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 0.001
        
        # Test orthogonal vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = help_content_service._calculate_cosine_similarity(vec1, vec2)
        assert abs(similarity - 0.0) < 0.001
        
        # Test opposite vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]
        similarity = help_content_service._calculate_cosine_similarity(vec1, vec2)
        assert abs(similarity - (-1.0)) < 0.001
        
        # Test zero vectors
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = help_content_service._calculate_cosine_similarity(vec1, vec2)
        assert similarity == 0.0


class TestContentVersioning:
    """Test content versioning and update functionality"""
    
    @pytest.mark.asyncio
    async def test_create_content_with_versioning(self, help_content_service, sample_content_create, mock_openai):
        """Test content creation with initial version record"""
        # Requirements: 2.4 - Content versioning and update mechanisms
        
        # Mock database insert response
        content_id = uuid4()
        mock_insert_data = {
            "id": str(content_id),
            "content_type": sample_content_create.content_type.value,
            "title": sample_content_create.title,
            "content": sample_content_create.content,
            "tags": sample_content_create.tags,
            "language": sample_content_create.language.value,
            "slug": sample_content_create.slug,
            "version": 1,
            "is_active": False,
            "review_status": "draft",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        mock_insert = Mock()
        mock_insert.execute.return_value = Mock(data=[mock_insert_data])
        help_content_service.supabase.table.return_value.insert.return_value = mock_insert
        
        # Mock version record creation
        mock_version_insert = Mock()
        mock_version_insert.execute.return_value = Mock(data=[{"id": "version-id"}])
        
        def table_side_effect(table_name):
            if table_name == "help_content":
                mock_table = Mock()
                mock_table.insert.return_value = mock_insert
                return mock_table
            elif table_name == "help_content_versions":
                mock_table = Mock()
                mock_table.insert.return_value = mock_version_insert
                return mock_table
            return Mock()
        
        help_content_service.supabase.table.side_effect = table_side_effect
        
        # Mock embedding generation
        mock_embedding_response = Mock()
        mock_embedding_response.data = [Mock(embedding=[0.1, 0.2, 0.3] * 512)]
        mock_openai.embeddings.create.return_value = mock_embedding_response
        
        # Test content creation
        result = await help_content_service.create_content(sample_content_create, "user-123")
        
        # Verify content was created
        assert isinstance(result, HelpContent)
        assert result.title == sample_content_create.title
        assert result.version == 1
        
        # Verify version record was created
        mock_version_insert.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_content_with_version_tracking(self, help_content_service, mock_openai):
        """Test content update with version increment and change tracking"""
        # Requirements: 2.4 - Content versioning and update mechanisms
        
        content_id = uuid4()
        
        # Mock existing content
        existing_content = {
            "id": str(content_id),
            "title": "Original Title",
            "content": "Original content",
            "content_type": "guide",  # Add missing required field
            "tags": ["original"],
            "language": "en",  # Add missing required field
            "version": 1,
            "is_active": True,  # Add missing required field
            "review_status": "approved",  # Add missing required field
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Mock updated content
        updated_content = {
            "id": str(content_id),
            "title": "Updated Title",
            "content": "Updated content with new information",
            "content_type": "guide",  # Add missing required field
            "tags": ["updated"],
            "language": "en",  # Add missing required field
            "version": 2,  # Version incremented
            "is_active": True,  # Add missing required field
            "review_status": "approved",  # Add missing required field
            "created_at": existing_content["created_at"],
            "updated_at": datetime.now().isoformat()
        }
        
        # Mock database responses
        mock_select = Mock()
        mock_select.execute.return_value = Mock(data=[existing_content])
        
        mock_update = Mock()
        mock_update.execute.return_value = Mock(data=[updated_content])
        
        mock_version_insert = Mock()
        mock_version_insert.execute.return_value = Mock(data=[{"id": "version-id"}])
        
        def table_side_effect(table_name):
            if table_name == "help_content":
                mock_table = Mock()
                mock_table.select.return_value.eq.return_value = mock_select
                mock_table.update.return_value.eq.return_value = mock_update
                return mock_table
            elif table_name == "help_content_versions":
                mock_table = Mock()
                mock_table.insert.return_value = mock_version_insert
                return mock_table
            return Mock()
        
        help_content_service.supabase.table.side_effect = table_side_effect
        
        # Mock embedding generation
        mock_embedding_response = Mock()
        mock_embedding_response.data = [Mock(embedding=[0.1, 0.2, 0.3] * 512)]
        mock_openai.embeddings.create.return_value = mock_embedding_response
        
        # Test content update
        update_data = HelpContentUpdate(
            title="Updated Title",
            content="Updated content with new information",
            tags=["updated"]
        )
        
        result = await help_content_service.update_content(content_id, update_data, "user-123")
        
        # Verify content was updated
        assert isinstance(result, HelpContent)
        assert result.title == "Updated Title"
        assert result.version == 2
        
        # Verify version record was created with change summary
        mock_version_insert.execute.assert_called_once()
        
        # Verify embedding regeneration was triggered
        mock_openai.embeddings.create.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_content_no_changes(self, help_content_service):
        """Test content update with no actual changes"""
        # Requirements: 2.4 - Handle updates with no changes
        
        content_id = uuid4()
        
        # Mock existing content
        existing_content = {
            "id": str(content_id),
            "title": "Same Title",
            "content": "Same content",
            "content_type": "guide",  # Add missing required field
            "tags": ["same"],
            "language": "en",  # Add missing required field
            "version": 1,
            "is_active": True,  # Add missing required field
            "review_status": "approved",  # Add missing required field
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        mock_select = Mock()
        mock_select.execute.return_value = Mock(data=[existing_content])
        
        help_content_service.supabase.table.return_value.select.return_value.eq.return_value = mock_select
        
        # Test update with same data
        update_data = HelpContentUpdate(
            title="Same Title",  # No change
            content="Same content"  # No change
        )
        
        result = await help_content_service.update_content(content_id, update_data, "user-123")
        
        # Verify no database update was performed
        assert isinstance(result, HelpContent)
        assert result.title == "Same Title"
        assert result.version == 1  # Version not incremented
    
    @pytest.mark.asyncio
    async def test_get_content_versions(self, help_content_service):
        """Test retrieving content version history"""
        # Requirements: 2.4 - Content versioning and update mechanisms
        
        content_id = uuid4()
        
        # Mock version history
        user_uuid = str(uuid4())  # Use valid UUID for created_by
        mock_versions = [
            {
                "id": str(uuid4()),
                "content_id": str(content_id),
                "version_number": 2,
                "title": "Updated Title",
                "content": "Updated content",
                "changes_summary": "Title and content updated",
                "created_by": user_uuid,  # Use UUID instead of string
                "created_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "content_id": str(content_id),
                "version_number": 1,
                "title": "Original Title",
                "content": "Original content",
                "changes_summary": "Initial version",
                "created_by": user_uuid,  # Use UUID instead of string
                "created_at": datetime.now().isoformat()
            }
        ]
        
        mock_select = Mock()
        mock_select.order.return_value.execute.return_value = Mock(data=mock_versions)
        help_content_service.supabase.table.return_value.select.return_value.eq.return_value = mock_select
        
        # Test version retrieval
        versions = await help_content_service.get_content_versions(content_id)
        
        # Verify versions
        assert len(versions) == 2
        assert all(isinstance(v, ContentVersion) for v in versions)
        assert versions[0].version_number == 2  # Most recent first
        assert versions[1].version_number == 1
        assert versions[0].changes_summary == "Title and content updated"
    
    @pytest.mark.asyncio
    async def test_create_version_record(self, help_content_service, sample_content):
        """Test version record creation"""
        # Requirements: 2.4 - Version tracking functionality
        
        mock_insert = Mock()
        mock_insert.execute.return_value = Mock(data=[{"id": "version-id"}])
        help_content_service.supabase.table.return_value.insert.return_value = mock_insert
        
        # Test version record creation
        await help_content_service._create_version_record(
            sample_content, 
            "Test changes summary", 
            "user-123"
        )
        
        # Verify version record was inserted
        mock_insert.execute.assert_called_once()
        
        # Verify insert data
        call_args = help_content_service.supabase.table.return_value.insert.call_args
        version_data = call_args[0][0]
        
        assert version_data["content_id"] == str(sample_content.id)
        assert version_data["version_number"] == sample_content.version
        assert version_data["title"] == sample_content.title
        assert version_data["content"] == sample_content.content
        assert version_data["changes_summary"] == "Test changes summary"
        assert version_data["created_by"] == "user-123"


class TestContentManagementIntegration:
    """Test integrated content management functionality"""
    
    @pytest.mark.asyncio
    async def test_get_content_by_id(self, help_content_service):
        """Test retrieving content by ID"""
        # Requirements: 2.3 - Content retrieval functionality
        
        content_id = uuid4()
        mock_content_data = {
            "id": str(content_id),
            "title": "Retrieved Content",
            "content": "Retrieved content text",
            "content_type": "guide",
            "tags": ["retrieved"],
            "language": "en",
            "version": 1,
            "is_active": True,
            "review_status": "approved",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        mock_select = Mock()
        mock_select.execute.return_value = Mock(data=[mock_content_data])
        help_content_service.supabase.table.return_value.select.return_value.eq.return_value = mock_select
        
        # Test content retrieval
        result = await help_content_service.get_content(content_id)
        
        # Verify result
        assert isinstance(result, HelpContent)
        assert result.id == content_id
        assert result.title == "Retrieved Content"
    
    @pytest.mark.asyncio
    async def test_get_content_by_slug(self, help_content_service):
        """Test retrieving content by slug and language"""
        # Requirements: 2.3 - Content retrieval by slug
        
        mock_content_data = {
            "id": str(uuid4()),
            "title": "Slug Content",
            "content": "Content retrieved by slug",
            "content_type": "guide",
            "tags": ["slug"],
            "language": "en",
            "slug": "test-slug",
            "version": 1,
            "is_active": True,
            "review_status": "approved",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        mock_select = Mock()
        mock_select.eq.return_value.execute.return_value = Mock(data=[mock_content_data])
        help_content_service.supabase.table.return_value.select.return_value.eq.return_value = mock_select
        
        # Test content retrieval by slug
        result = await help_content_service.get_content_by_slug("test-slug", Language.en)
        
        # Verify result
        assert isinstance(result, HelpContent)
        assert result.slug == "test-slug"
        assert result.language == Language.en
    
    def test_generate_slug(self, help_content_service):
        """Test slug generation from titles"""
        # Requirements: 2.4 - URL-friendly slug generation
        
        test_cases = [
            ("How to Create a Project", "how-to-create-a-project"),
            ("Budget Management & Tracking!", "budget-management-tracking"),
            ("Getting Started with PPM Platform", "getting-started-with-ppm-platform"),
            ("FAQ: Common Issues", "faq-common-issues"),
            ("   Spaces   and   Tabs   ", "spaces-and-tabs")
        ]
        
        for title, expected_slug in test_cases:
            slug = help_content_service._generate_slug(title)
            assert slug == expected_slug
            assert slug.islower()
            assert ' ' not in slug
            assert slug.replace('-', '').replace('_', '').isalnum()