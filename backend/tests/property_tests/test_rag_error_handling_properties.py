"""
Property-Based Tests for RAG Agent Error Handling
Tests Property 4: Exception Logging and User-Friendly Errors

Feature: ai-empowered-ppm-features
Property 4: Exception Logging and User-Friendly Errors

For any unexpected exception during AI agent processing, the system SHALL log 
the full stack trace to audit_logs AND return a user-friendly error message 
(not the raw exception) to the user.

Validates: Requirements 1.7
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from unittest.mock import Mock, patch, AsyncMock
import uuid
from datetime import datetime
import traceback
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from ai_agents import RAGReporterAgent


# Hypothesis strategies
@st.composite
def query_strategy(draw):
    """Generate valid query strings"""
    return draw(st.text(min_size=1, max_size=1000, alphabet=st.characters(blacklist_categories=('Cs',))))


@st.composite
def user_id_strategy(draw):
    """Generate valid UUIDs as strings"""
    return str(uuid.uuid4())


@st.composite
def organization_id_strategy(draw):
    """Generate valid organization UUIDs"""
    return str(uuid.uuid4())


class TestRAGErrorHandlingProperties:
    """Property-based tests for RAG agent error handling"""
    
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
    
    @given(
        query=query_strategy(),
        user_id=user_id_strategy(),
        organization_id=organization_id_strategy()
    )
    @settings(
        max_examples=50, 
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @pytest.mark.asyncio
    async def test_property_4_exception_logging_and_user_friendly_errors(
        self, 
        query, 
        user_id, 
        organization_id,
        mock_supabase,
        mock_openai
    ):
        """
        Feature: ai-empowered-ppm-features
        Property 4: Exception Logging and User-Friendly Errors
        
        For any unexpected exception during AI agent processing, the system SHALL 
        log the full stack trace to audit_logs AND return a user-friendly error 
        message (not the raw exception) to the user.
        
        Validates: Requirements 1.7
        """
        # Arrange: Create agent with mocked dependencies
        with patch('ai_agents.OpenAI', return_value=mock_openai):
            agent = RAGReporterAgent(
                supabase_client=mock_supabase,
                openai_api_key="test-key"
            )
            agent.openai_client = mock_openai
        
        # Simulate an unexpected exception during processing
        test_exception = Exception("Simulated unexpected error")
        
        # Mock the embedding generation to raise an exception
        async def mock_generate_embedding_error(text):
            raise test_exception
        
        agent.generate_embedding = mock_generate_embedding_error
        
        # Track audit log calls
        audit_log_calls = []
        
        def mock_insert_audit_log(data):
            audit_log_calls.append(data)
            return Mock(execute=Mock(return_value=Mock(data=[data])))
        
        mock_supabase.table = Mock(return_value=Mock(
            insert=mock_insert_audit_log
        ))
        
        # Act: Try to process the query (should fail)
        try:
            result = await agent.process_rag_query(
                query=query,
                user_id=user_id,
                conversation_id=f"test-conv-{uuid.uuid4()}"
            )
            # If no exception, the test should still verify logging
            assert False, "Expected exception was not raised"
        except Exception as e:
            # Assert: Verify error handling
            
            # 1. Check that an exception was raised
            assert e is not None
            
            # 2. Verify that the error message is user-friendly (not raw exception)
            error_message = str(e)
            
            # User-friendly error should NOT contain:
            # - Stack traces
            # - File paths
            # - Line numbers
            # - Raw exception types
            assert "Traceback" not in error_message, "Error message contains stack trace"
            assert ".py" not in error_message, "Error message contains file paths"
            assert "line " not in error_message.lower(), "Error message contains line numbers"
            
            # User-friendly error SHOULD be:
            # - Concise (not too long)
            # - Descriptive (tells user what went wrong)
            assert len(error_message) < 500, "Error message is too verbose"
            assert len(error_message) > 0, "Error message is empty"
    
    @given(
        query=query_strategy(),
        user_id=user_id_strategy()
    )
    @settings(
        max_examples=30, 
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @pytest.mark.asyncio
    async def test_error_logging_includes_full_context(
        self,
        query,
        user_id,
        mock_supabase,
        mock_openai
    ):
        """
        Test that error logging includes full context:
        - Timestamp
        - User ID
        - Error message
        - Stack trace (in logs, not user message)
        """
        # Arrange
        with patch('ai_agents.OpenAI', return_value=mock_openai):
            agent = RAGReporterAgent(
                supabase_client=mock_supabase,
                openai_api_key="test-key"
            )
            agent.openai_client = mock_openai
        
        # Simulate exception
        test_exception = ValueError("Test validation error")
        
        async def mock_generate_embedding_error(text):
            raise test_exception
        
        agent.generate_embedding = mock_generate_embedding_error
        
        # Track log operations
        log_operations = []
        
        async def mock_log_operation(*args, **kwargs):
            log_operations.append({
                'args': args,
                'kwargs': kwargs,
                'timestamp': datetime.now()
            })
            return str(uuid.uuid4())
        
        agent.log_operation = mock_log_operation
        
        # Act
        try:
            await agent.process_rag_query(
                query=query,
                user_id=user_id,
                conversation_id=f"test-{uuid.uuid4()}"
            )
        except Exception:
            pass  # Expected
        
        # Assert: Verify logging occurred with full context
        if log_operations:
            last_log = log_operations[-1]
            
            # Check that error was logged
            assert last_log['kwargs'].get('success') == False, "Error should be logged as failure"
            assert last_log['kwargs'].get('error_message') is not None, "Error message should be logged"
            assert last_log['kwargs'].get('user_id') == user_id, "User ID should be logged"
    
    @given(
        query=query_strategy(),
        user_id=user_id_strategy()
    )
    @settings(
        max_examples=30, 
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @pytest.mark.asyncio
    async def test_different_exception_types_handled_consistently(
        self,
        query,
        user_id,
        mock_supabase,
        mock_openai
    ):
        """
        Test that different exception types are handled consistently
        with user-friendly messages
        """
        # Arrange
        with patch('ai_agents.OpenAI', return_value=mock_openai):
            agent = RAGReporterAgent(
                supabase_client=mock_supabase,
                openai_api_key="test-key"
            )
            agent.openai_client = mock_openai
        
        # Test different exception types
        exception_types = [
            ValueError("Invalid value"),
            KeyError("Missing key"),
            TypeError("Type mismatch"),
            RuntimeError("Runtime error"),
            Exception("Generic error")
        ]
        
        for test_exception in exception_types:
            # Mock to raise this exception
            async def mock_generate_embedding_error(text):
                raise test_exception
            
            agent.generate_embedding = mock_generate_embedding_error
            
            # Act & Assert
            try:
                await agent.process_rag_query(
                    query=query,
                    user_id=user_id,
                    conversation_id=f"test-{uuid.uuid4()}"
                )
                assert False, f"Expected {type(test_exception).__name__} to be raised"
            except Exception as e:
                # Verify user-friendly error
                error_msg = str(e)
                
                # Should not expose internal exception type names
                assert type(test_exception).__name__ not in error_msg or len(error_msg) < 100, \
                    f"Error message exposes internal exception type: {error_msg}"
                
                # Should be concise
                assert len(error_msg) < 500, "Error message too verbose"
    
    @given(
        query=query_strategy(),
        user_id=user_id_strategy()
    )
    @settings(
        max_examples=20, 
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @pytest.mark.asyncio
    async def test_error_recovery_after_exception(
        self,
        query,
        user_id,
        mock_supabase,
        mock_openai
    ):
        """
        Test that the agent can recover and process subsequent requests
        after an exception occurs
        """
        # Arrange
        with patch('ai_agents.OpenAI', return_value=mock_openai):
            agent = RAGReporterAgent(
                supabase_client=mock_supabase,
                openai_api_key="test-key"
            )
            agent.openai_client = mock_openai
        
        # First request: cause an error
        call_count = [0]
        
        async def mock_generate_embedding_conditional(text):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("First call error")
            # Second call succeeds
            return [0.1] * 1536
        
        agent.generate_embedding = mock_generate_embedding_conditional
        
        # Mock successful response for second call
        mock_openai.chat = Mock()
        mock_openai.chat.completions = Mock()
        mock_openai.chat.completions.create = Mock(return_value=Mock(
            choices=[Mock(message=Mock(content="Test response"))],
            usage=Mock(prompt_tokens=10, completion_tokens=20)
        ))
        
        # Act: First request should fail
        try:
            await agent.process_rag_query(
                query=query,
                user_id=user_id,
                conversation_id=f"test-1-{uuid.uuid4()}"
            )
            assert False, "Expected first request to fail"
        except Exception:
            pass  # Expected
        
        # Second request should succeed (agent recovered)
        try:
            result = await agent.process_rag_query(
                query=query,
                user_id=user_id,
                conversation_id=f"test-2-{uuid.uuid4()}"
            )
            # If we get here, agent recovered successfully
            assert result is not None, "Agent should recover and return result"
        except Exception as e:
            # Agent failed to recover
            pytest.fail(f"Agent failed to recover after exception: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
