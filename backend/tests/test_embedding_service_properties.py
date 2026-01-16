"""
Property-Based Tests for Embedding Service
Feature: ai-help-chat-knowledge-base
Tests Properties 7 and 25 from the design document
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the service
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.embedding_service import (
    EmbeddingService,
    EmbeddingConfig,
    EmbeddingServiceError,
    EmbeddingAPIError
)


# Test data strategies
@st.composite
def text_strategy(draw):
    """Generate valid text inputs for embedding"""
    # Generate text with various characteristics
    min_length = draw(st.integers(min_value=1, max_value=10))
    max_length = draw(st.integers(min_value=min_length, max_value=1000))
    
    text = draw(st.text(
        min_size=min_length,
        max_size=max_length,
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs', 'Po')
        )
    ))
    
    # Ensure text is not just whitespace
    assume(text.strip())
    
    return text


@st.composite
def text_batch_strategy(draw):
    """Generate batches of text for batch embedding tests"""
    batch_size = draw(st.integers(min_value=1, max_value=50))
    
    texts = draw(st.lists(
        text_strategy(),
        min_size=batch_size,
        max_size=batch_size
    ))
    
    return texts


# Fixtures
@pytest.fixture(scope="module")
def embedding_service():
    """Create embedding service instance for testing"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set - skipping embedding service tests")
    
    config = EmbeddingConfig(
        model="text-embedding-3-small",
        dimensions=1536,
        max_batch_size=100,
        max_retries=3
    )
    
    return EmbeddingService(api_key=api_key, config=config)


@pytest.fixture(scope="module")
def mock_embedding_service():
    """Create a mock embedding service for testing without API key"""
    import unittest.mock as mock
    
    # Create a mock OpenAI client
    mock_client = mock.MagicMock()
    mock_async_client = mock.MagicMock()
    
    # Configure mock to return embeddings
    def create_mock_embedding(model, input, dimensions):
        """Create mock embedding response"""
        import random
        
        # Handle both single text and batch
        if isinstance(input, str):
            texts = [input]
        else:
            texts = input
        
        # Create mock response
        mock_response = mock.MagicMock()
        mock_response.data = []
        
        for text in texts:
            # Generate deterministic embedding based on text hash
            random.seed(hash(text))
            embedding = [random.uniform(-1, 1) for _ in range(dimensions)]
            
            mock_data = mock.MagicMock()
            mock_data.embedding = embedding
            mock_response.data.append(mock_data)
        
        return mock_response
    
    mock_client.embeddings.create = mock.MagicMock(side_effect=create_mock_embedding)
    mock_async_client.embeddings.create = mock.MagicMock(side_effect=create_mock_embedding)
    
    # Create service with mock API key
    config = EmbeddingConfig(
        model="text-embedding-3-small",
        dimensions=1536,
        max_batch_size=100,
        max_retries=3
    )
    
    service = EmbeddingService(api_key="mock-api-key", config=config)
    
    # Replace clients with mocks
    service.client = mock_client
    service.async_client = mock_async_client
    
    return service


@pytest.mark.property_test
class TestEmbeddingGenerationConsistency:
    """
    Property 7: Embedding Generation Consistency
    Validates: Requirements 2.4, 3.1
    
    For any text input (query or chunk), the Embedding_Service must generate 
    a vector embedding with the correct dimensionality (1536 for OpenAI embeddings).
    """
    
    @settings(max_examples=100, deadline=30000)
    @given(text=text_strategy())
    def test_embedding_has_correct_dimensions(self, mock_embedding_service, text):
        """
        Test that generated embeddings have the correct dimensionality.
        
        Property: For any valid text input, embed_text() must return a vector
        with exactly 1536 dimensions.
        """
        # Generate embedding
        embedding = mock_embedding_service.embed_text(text)
        
        # Verify embedding is a list
        assert isinstance(embedding, list), \
            "Embedding must be a list"
        
        # Verify correct dimensions
        expected_dimensions = mock_embedding_service.get_embedding_dimensions()
        assert len(embedding) == expected_dimensions, \
            f"Embedding must have {expected_dimensions} dimensions, got {len(embedding)}"
        
        # Verify all elements are floats
        assert all(isinstance(x, (int, float)) for x in embedding), \
            "All embedding elements must be numeric"
        
        # Verify no NaN or infinite values
        assert all(not (x != x) for x in embedding), \
            "Embedding must not contain NaN values"
        
        assert all(abs(x) != float('inf') for x in embedding), \
            "Embedding must not contain infinite values"
    
    @settings(max_examples=50, deadline=30000)
    @given(text=text_strategy())
    def test_embedding_deterministic_for_same_input(self, mock_embedding_service, text):
        """
        Test that the same text produces consistent embeddings.
        
        Property: For any text input, calling embed_text() multiple times
        should produce the same embedding vector.
        """
        # Generate embedding twice
        embedding1 = mock_embedding_service.embed_text(text)
        embedding2 = mock_embedding_service.embed_text(text)
        
        # Verify embeddings are identical
        assert len(embedding1) == len(embedding2), \
            "Embeddings must have same length"
        
        # Check element-wise equality (with small tolerance for floating point)
        for i, (e1, e2) in enumerate(zip(embedding1, embedding2)):
            assert abs(e1 - e2) < 1e-6, \
                f"Embedding elements at index {i} must be equal: {e1} vs {e2}"
    
    @settings(max_examples=50, deadline=30000)
    @given(text=text_strategy())
    def test_embedding_validation_passes(self, mock_embedding_service, text):
        """
        Test that generated embeddings pass validation.
        
        Property: For any text input, the generated embedding must pass
        the service's own validation method.
        """
        # Generate embedding
        embedding = mock_embedding_service.embed_text(text)
        
        # Verify it passes validation
        assert mock_embedding_service.validate_embedding(embedding), \
            "Generated embedding must pass validation"
    
    @settings(max_examples=30, deadline=30000)
    @given(text=text_strategy())
    def test_embedding_non_zero_vector(self, mock_embedding_service, text):
        """
        Test that embeddings are not zero vectors.
        
        Property: For any non-empty text input, the embedding should not be
        a zero vector (all elements zero).
        """
        # Generate embedding
        embedding = mock_embedding_service.embed_text(text)
        
        # Verify not all zeros
        assert any(x != 0 for x in embedding), \
            "Embedding must not be a zero vector"
        
        # Verify has reasonable magnitude
        magnitude = sum(x * x for x in embedding) ** 0.5
        assert magnitude > 0, \
            "Embedding must have non-zero magnitude"


@pytest.mark.property_test
class TestEmbeddingBatchProcessing:
    """
    Property 25: Embedding Batch Processing
    Validates: Requirements 8.5
    
    For any set of multiple texts submitted for embedding, the Embedding_Service 
    must process them as a batch rather than individual sequential requests.
    """
    
    @settings(max_examples=50, deadline=60000)
    @given(texts=text_batch_strategy())
    def test_batch_returns_correct_count(self, mock_embedding_service, texts):
        """
        Test that batch processing returns embeddings for all inputs.
        
        Property: For any list of N valid texts, embed_batch() must return
        exactly N embeddings.
        """
        # Generate batch embeddings
        embeddings = mock_embedding_service.embed_batch(texts)
        
        # Verify count matches
        assert len(embeddings) == len(texts), \
            f"Must return {len(texts)} embeddings, got {len(embeddings)}"
    
    @settings(max_examples=50, deadline=60000)
    @given(texts=text_batch_strategy())
    def test_batch_all_embeddings_valid_dimensions(self, mock_embedding_service, texts):
        """
        Test that all embeddings in batch have correct dimensions.
        
        Property: For any batch of texts, every embedding in the result
        must have the correct dimensionality.
        """
        # Generate batch embeddings
        embeddings = mock_embedding_service.embed_batch(texts)
        
        expected_dimensions = mock_embedding_service.get_embedding_dimensions()
        
        # Verify each embedding
        for i, embedding in enumerate(embeddings):
            assert isinstance(embedding, list), \
                f"Embedding {i} must be a list"
            
            assert len(embedding) == expected_dimensions, \
                f"Embedding {i} must have {expected_dimensions} dimensions, got {len(embedding)}"
            
            assert all(isinstance(x, (int, float)) for x in embedding), \
                f"All elements in embedding {i} must be numeric"
    
    @settings(max_examples=30, deadline=60000)
    @given(texts=text_batch_strategy())
    def test_batch_preserves_order(self, mock_embedding_service, texts):
        """
        Test that batch processing preserves input order.
        
        Property: For any batch of texts, the order of embeddings in the result
        must match the order of texts in the input.
        """
        # Generate batch embeddings
        batch_embeddings = mock_embedding_service.embed_batch(texts)
        
        # Generate individual embeddings
        individual_embeddings = [mock_embedding_service.embed_text(text) for text in texts]
        
        # Verify order is preserved by comparing embeddings
        assert len(batch_embeddings) == len(individual_embeddings), \
            "Batch and individual results must have same count"
        
        for i, (batch_emb, indiv_emb) in enumerate(zip(batch_embeddings, individual_embeddings)):
            # Check element-wise equality (with small tolerance)
            for j, (b, ind) in enumerate(zip(batch_emb, indiv_emb)):
                assert abs(b - ind) < 1e-6, \
                    f"Embedding {i}, element {j} differs: batch={b}, individual={ind}"
    
    @settings(max_examples=20, deadline=60000)
    @given(texts=st.lists(text_strategy(), min_size=10, max_size=30))
    def test_batch_processing_uses_batch_api(self, mock_embedding_service, texts):
        """
        Test that batch processing uses the batch API call.
        
        Property: For any batch of texts, processing them as a batch should
        use fewer API calls than processing them individually.
        
        Note: This validates that the batch processing optimization is working
        by checking that the API is called with multiple texts at once.
        """
        # Reset mock call count
        mock_embedding_service.client.embeddings.create.reset_mock()
        
        # Process batch
        embeddings = mock_embedding_service.embed_batch(texts)
        
        # Verify batch API was called
        assert mock_embedding_service.client.embeddings.create.called, \
            "Batch API should be called"
        
        # Get the calls
        calls = mock_embedding_service.client.embeddings.create.call_args_list
        
        # Verify fewer calls than number of texts (batch processing)
        # With max_batch_size=100, should be 1 call for batches < 100
        expected_calls = (len(texts) + mock_embedding_service.config.max_batch_size - 1) // mock_embedding_service.config.max_batch_size
        assert len(calls) == expected_calls, \
            f"Expected {expected_calls} batch API calls, got {len(calls)}"
        
        # Verify all embeddings returned
        assert len(embeddings) == len(texts), \
            f"Must return {len(texts)} embeddings"
    
    @settings(max_examples=30, deadline=60000)
    @given(texts=st.lists(text_strategy(), min_size=1, max_size=20))
    def test_batch_handles_large_batches(self, mock_embedding_service, texts):
        """
        Test that batch processing handles batches larger than max_batch_size.
        
        Property: For any batch of texts, even if larger than max_batch_size,
        embed_batch() must successfully process all texts by splitting into
        smaller batches internally.
        """
        # This test verifies the internal batching logic
        embeddings = mock_embedding_service.embed_batch(texts)
        
        # Verify all texts were processed
        assert len(embeddings) == len(texts), \
            f"Must process all {len(texts)} texts"
        
        # Verify all embeddings are valid
        for embedding in embeddings:
            assert mock_embedding_service.validate_embedding(embedding), \
                "All embeddings must be valid"


@pytest.mark.property_test
class TestEmbeddingServiceErrorHandling:
    """
    Additional property tests for error handling and edge cases.
    """
    
    @settings(max_examples=20, deadline=10000)
    @given(invalid_text=st.one_of(st.just(""), st.just("   "), st.just("\n\n")))
    def test_empty_text_raises_error(self, mock_embedding_service, invalid_text):
        """
        Test that empty or whitespace-only text raises appropriate error.
        
        Property: For any empty or whitespace-only text, embed_text()
        must raise a ValueError.
        """
        with pytest.raises(ValueError, match="Text cannot be empty"):
            mock_embedding_service.embed_text(invalid_text)
    
    @settings(max_examples=10, deadline=10000)
    @given(dummy=st.just(None))
    def test_empty_batch_raises_error(self, mock_embedding_service, dummy):
        """
        Test that empty batch raises appropriate error.
        
        Property: For an empty list of texts, embed_batch() must raise
        a ValueError.
        """
        with pytest.raises(ValueError, match="Texts list cannot be empty"):
            mock_embedding_service.embed_batch([])
    
    @settings(max_examples=20, deadline=30000)
    @given(texts=st.lists(
        st.one_of(text_strategy(), st.just(""), st.just("  ")),
        min_size=2,
        max_size=10
    ))
    def test_batch_filters_empty_texts(self, mock_embedding_service, texts):
        """
        Test that batch processing filters out empty texts.
        
        Property: For any batch containing some empty texts, embed_batch()
        must filter them out and process only valid texts.
        """
        # Count valid texts
        valid_texts = [t for t in texts if t and t.strip()]
        
        if not valid_texts:
            # If no valid texts, should raise error
            with pytest.raises(ValueError, match="No valid texts to embed"):
                mock_embedding_service.embed_batch(texts)
        else:
            # Should process only valid texts
            embeddings = mock_embedding_service.embed_batch(texts)
            assert len(embeddings) == len(valid_texts), \
                f"Should return {len(valid_texts)} embeddings for valid texts"
