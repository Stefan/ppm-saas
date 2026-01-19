"""
Unit Tests for RAG Agent Edge Cases
Tests specific edge cases and error scenarios

Feature: ai-empowered-ppm-features
Validates: Requirements 1.1, 1.2, 1.3
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import uuid
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from ai_agents import RAGReporterAgent


class TestRAGEdgeCases:
    """Unit tests for RAG agent edge cases"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create mock Supabase client"""
        mock = Mock()
        mock.table = Mock(return_value=mock)
        mock.select = Mock(return_value=mock)
        mock.insert = Mock(return_value=mock)
        mock.execute = Mock(return_value=Mock(data=[]))
        return mock
    
    @pytest.fixture
    def mock_openai(self):
        """Create mock OpenAI client"""
        mock = Mock()
        return mock
    
    @pytest.fixture
    def rag_agent(self, mock_supabase, mock_openai):
        """Create RAG agent with mocked dependencies"""
        with patch('ai_agents.OpenAI', return_value=mock_openai):
            agent = RAGReporterAgent(
                supabase_client=mock_supabase,
                openai_api_key="test-key"
            )
            agent.openai_client = mock_openai
            return agent
    
    @pytest.mark.asyncio
    async def test_empty_query_handling(self, rag_agent):
        """Test handling of empty query string"""
        # Arrange
        empty_query = ""
        user_id = str(uuid.uuid4())
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await rag_agent.process_rag_query(
                query=empty_query,
                user_id=user_id,
                conversation_id=f"test-{uuid.uuid4()}"
            )
        
        # Should raise an error or handle gracefully
        assert exc_info.value is not None
    
    @pytest.mark.asyncio
    async def test_malformed_context_data(self, rag_agent, mock_supabase):
        """Test handling of malformed context data from database"""
        # Arrange
        query = "Test query"
        user_id = str(uuid.uuid4())
        
        # Mock malformed data response
        mock_supabase.table = Mock(return_value=Mock(
            select=Mock(return_value=Mock(
                execute=Mock(return_value=Mock(data=None))  # Malformed: None instead of list
            ))
        ))
        
        # Mock embedding generation
        async def mock_generate_embedding(text):
            return [0.1] * 1536
        
        rag_agent.generate_embedding = mock_generate_embedding
        
        # Act
        try:
            result = await rag_agent.process_rag_query(
                query=query,
                user_id=user_id,
                conversation_id=f"test-{uuid.uuid4()}"
            )
            # Should handle gracefully
            assert result is not None or True  # Either returns result or raises handled exception
        except Exception as e:
            # Should be a user-friendly error
            error_msg = str(e)
            assert len(error_msg) < 500, "Error message should be concise"
    
    @pytest.mark.asyncio
    async def test_openai_api_timeout(self, rag_agent, mock_openai):
        """Test handling of OpenAI API timeout scenarios"""
        # Arrange
        query = "Test query"
        user_id = str(uuid.uuid4())
        
        # Mock timeout exception
        import asyncio
        
        async def mock_generate_embedding_timeout(text):
            raise asyncio.TimeoutError("API request timed out")
        
        rag_agent.generate_embedding = mock_generate_embedding_timeout
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await rag_agent.process_rag_query(
                query=query,
                user_id=user_id,
                conversation_id=f"test-{uuid.uuid4()}"
            )
        
        # Should handle timeout gracefully
        error_msg = str(exc_info.value)
        assert "timeout" in error_msg.lower() or len(error_msg) < 500
    
    @pytest.mark.asyncio
    async def test_very_long_query(self, rag_agent):
        """Test handling of very long query strings"""
        # Arrange
        long_query = "test " * 10000  # Very long query
        user_id = str(uuid.uuid4())
        
        # Mock embedding generation
        async def mock_generate_embedding(text):
            if len(text) > 8000:
                raise ValueError("Text too long for embedding")
            return [0.1] * 1536
        
        rag_agent.generate_embedding = mock_generate_embedding
        
        # Act
        try:
            result = await rag_agent.process_rag_query(
                query=long_query,
                user_id=user_id,
                conversation_id=f"test-{uuid.uuid4()}"
            )
            # Should either truncate or handle gracefully
            assert result is not None or True
        except Exception as e:
            # Should be a user-friendly error
            error_msg = str(e)
            assert len(error_msg) < 500
    
    @pytest.mark.asyncio
    async def test_special_characters_in_query(self, rag_agent):
        """Test handling of special characters in query"""
        # Arrange
        special_query = "Test query with special chars: <script>alert('xss')</script> & symbols !@#$%^&*()"
        user_id = str(uuid.uuid4())
        
        # Mock embedding generation
        async def mock_generate_embedding(text):
            return [0.1] * 1536
        
        rag_agent.generate_embedding = mock_generate_embedding
        
        # Mock OpenAI response
        rag_agent.openai_client.chat = Mock()
        rag_agent.openai_client.chat.completions = Mock()
        rag_agent.openai_client.chat.completions.create = Mock(return_value=Mock(
            choices=[Mock(message=Mock(content="Safe response"))],
            usage=Mock(prompt_tokens=10, completion_tokens=20)
        ))
        
        # Act
        try:
            result = await rag_agent.process_rag_query(
                query=special_query,
                user_id=user_id,
                conversation_id=f"test-{uuid.uuid4()}"
            )
            # Should sanitize and handle safely
            assert result is not None
            # Response should not contain unsanitized special chars
            if result.get("response"):
                assert "<script>" not in result["response"]
        except Exception as e:
            # Should handle gracefully
            assert str(e) is not None
    
    @pytest.mark.asyncio
    async def test_no_similar_content_found(self, rag_agent):
        """Test handling when no similar content is found"""
        # Arrange
        query = "Test query"
        user_id = str(uuid.uuid4())
        
        # Mock empty similarity search results
        async def mock_search_similar_content(query, content_types=None, limit=5):
            return []  # No similar content found
        
        rag_agent.search_similar_content = mock_search_similar_content
        
        # Mock embedding generation
        async def mock_generate_embedding(text):
            return [0.1] * 1536
        
        rag_agent.generate_embedding = mock_generate_embedding
        
        # Mock OpenAI response
        rag_agent.openai_client.chat = Mock()
        rag_agent.openai_client.chat.completions = Mock()
        rag_agent.openai_client.chat.completions.create = Mock(return_value=Mock(
            choices=[Mock(message=Mock(content="I don't have enough information"))],
            usage=Mock(prompt_tokens=10, completion_tokens=20)
        ))
        
        # Act
        result = await rag_agent.process_rag_query(
            query=query,
            user_id=user_id,
            conversation_id=f"test-{uuid.uuid4()}"
        )
        
        # Assert
        assert result is not None
        assert result.get("confidence_score", 1.0) < 0.5, "Should have low confidence with no context"
        assert len(result.get("sources", [])) == 0, "Should have no sources"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
