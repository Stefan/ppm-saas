"""
Property-Based Tests for Ingestion Update Propagation
Feature: ai-help-chat-knowledge-base
Tests Property 15 from the design document
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import List, Dict, Any
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ingestion_orchestrator import (
    IngestionOrchestrator,
    IngestionResult,
    IngestionStatus,
    IngestionError
)
from services.document_parser import DocumentParser, DocumentFormat
from services.text_chunker import TextChunker
from services.embedding_service import EmbeddingService, EmbeddingConfig
from services.vector_store import VectorStore, VectorChunk


# Test data strategies
@st.composite
def document_content_strategy(draw):
    """Generate valid document content"""
    # Generate title
    title = draw(st.text(min_size=10, max_size=100, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')
    )))
    assume(title.strip())
    
    # Generate paragraphs
    num_paragraphs = draw(st.integers(min_value=3, max_value=8))
    paragraphs = []
    
    for i in range(num_paragraphs):
        paragraph = draw(st.text(min_size=100, max_size=500, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')
        )))
        if paragraph.strip():
            paragraphs.append(paragraph.strip())
    
    # Ensure we have enough content
    assume(len(paragraphs) >= 2)
    
    content = f"# {title}\n\n" + "\n\n".join(paragraphs)
    
    return content


@st.composite
def document_update_strategy(draw):
    """Generate a document with original and updated content"""
    document_id = draw(st.text(min_size=10, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd')
    )))
    assume(document_id.strip())
    
    original_content = draw(document_content_strategy())
    updated_content = draw(document_content_strategy())
    
    # Ensure contents are different
    assume(original_content != updated_content)
    
    metadata = {
        "category": draw(st.sampled_from([
            "dashboard", "resource_management", "financial_tracking",
            "risk_management", "general"
        ])),
        "version": draw(st.text(min_size=3, max_size=10))
    }
    
    return {
        "document_id": document_id,
        "original_content": original_content,
        "updated_content": updated_content,
        "metadata": metadata
    }


# Mock fixtures - Synchronous versions
class MockVectorStore:
    """Mock vector store for testing - synchronous"""
    
    def __init__(self):
        self.chunks = {}  # document_id -> list of chunks
        self.deleted_documents = []
    
    async def upsert_chunks(self, chunks: List[VectorChunk]) -> None:
        """Store chunks in memory"""
        for chunk in chunks:
            if chunk.document_id not in self.chunks:
                self.chunks[chunk.document_id] = []
            
            # Remove existing chunk with same index
            self.chunks[chunk.document_id] = [
                c for c in self.chunks[chunk.document_id]
                if c.chunk_index != chunk.chunk_index
            ]
            
            # Add new chunk
            self.chunks[chunk.document_id].append(chunk)
    
    async def delete_by_document_id(self, document_id: str) -> int:
        """Delete chunks for a document"""
        if document_id in self.chunks:
            count = len(self.chunks[document_id])
            del self.chunks[document_id]
            self.deleted_documents.append(document_id)
            return count
        return 0
    
    async def get_chunks_by_document_id(self, document_id: str) -> List[VectorChunk]:
        """Get chunks for a document"""
        return self.chunks.get(document_id, [])


class MockEmbeddingService:
    """Mock embedding service for testing - synchronous"""
    
    def __init__(self):
        self.embedding_calls = []
    
    async def embed_batch_async(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings"""
        self.embedding_calls.append(texts)
        
        # Return mock embeddings (1536 dimensions)
        embeddings = []
        for text in texts:
            # Generate deterministic embedding based on text hash
            embedding = [float(hash(text + str(i)) % 100) / 100.0 for i in range(1536)]
            embeddings.append(embedding)
        
        return embeddings


@pytest.mark.property_test
class TestUpdatePropagationToVectorStore:
    """
    Property 15: Update Propagation to Vector Store
    Validates: Requirements 5.2
    
    For any Knowledge_Document that is updated, all associated chunks in the 
    Vector_Store must be regenerated with new embeddings.
    """
    
    @settings(max_examples=5, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(doc_update=document_update_strategy())
    @pytest.mark.asyncio
    async def test_update_regenerates_all_chunks(self, doc_update):
        """
        Test that document updates regenerate all chunks.
        
        Property: For any document update, all chunks must be regenerated
        and stored in the vector store with new embeddings.
        """
        # Create fresh instances for each test
        parser = DocumentParser()
        chunker = TextChunker(chunk_size=512, overlap=50)
        mock_vector_store = MockVectorStore()
        mock_embedding_service = MockEmbeddingService()
        
        orchestrator = IngestionOrchestrator(
            parser=parser,
            chunker=chunker,
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store
        )
        
        document_id = doc_update["document_id"]
        original_content = doc_update["original_content"]
        updated_content = doc_update["updated_content"]
        metadata = doc_update["metadata"]
        
        # Step 1: Ingest original document
        result1 = await orchestrator.ingest_document(
            document_id=document_id,
            content=original_content,
            format=DocumentFormat.MARKDOWN,
            metadata=metadata
        )
        
        # Verify original ingestion succeeded
        assert result1.success, \
            f"Original ingestion must succeed: {result1.error_message}"
        
        original_chunk_count = result1.chunks_created
        assert original_chunk_count > 0, \
            "Original ingestion must create chunks"
        
        # Verify chunks are in vector store
        original_chunks = await mock_vector_store.get_chunks_by_document_id(document_id)
        assert len(original_chunks) == original_chunk_count, \
            "Vector store must contain all original chunks"
        
        # Store original chunk contents for comparison
        original_chunk_contents = [chunk.content for chunk in original_chunks]
        original_embeddings = [chunk.embedding for chunk in original_chunks]
        
        # Step 2: Update document
        result2 = await orchestrator.update_document(
            document_id=document_id,
            content=updated_content,
            format=DocumentFormat.MARKDOWN,
            metadata=metadata
        )
        
        # Verify update succeeded
        assert result2.success, \
            f"Document update must succeed: {result2.error_message}"
        
        updated_chunk_count = result2.chunks_created
        assert updated_chunk_count > 0, \
            "Updated document must create chunks"
        
        # Step 3: Verify all chunks were regenerated
        updated_chunks = await mock_vector_store.get_chunks_by_document_id(document_id)
        
        assert len(updated_chunks) == updated_chunk_count, \
            "Vector store must contain all updated chunks"
        
        # Verify chunks are different from original
        updated_chunk_contents = [chunk.content for chunk in updated_chunks]
        updated_embeddings = [chunk.embedding for chunk in updated_chunks]
        
        # At least some content should be different (since we ensured different content)
        content_changed = updated_chunk_contents != original_chunk_contents
        assert content_changed, \
            "Updated chunks must have different content from original"
        
        # Embeddings should be regenerated (different from original)
        embeddings_changed = updated_embeddings != original_embeddings
        assert embeddings_changed, \
            "Updated chunks must have regenerated embeddings"
        
        # Verify embedding service was called for both ingestions
        assert len(mock_embedding_service.embedding_calls) >= 2, \
            "Embedding service must be called for both original and updated documents"
        
        # Verify old chunks were deleted
        assert document_id in mock_vector_store.deleted_documents, \
            "Old chunks must be deleted during update"
    
    @settings(max_examples=5, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(doc_update=document_update_strategy())
    @pytest.mark.asyncio
    async def test_update_preserves_document_id_and_indices(self, doc_update):
        """
        Test that document updates preserve document ID and maintain sequential indices.
        
        Property: For any document update, all new chunks must reference
        the same document ID and have sequential indices.
        """
        # Create fresh instances
        parser = DocumentParser()
        chunker = TextChunker(chunk_size=512, overlap=50)
        mock_vector_store = MockVectorStore()
        mock_embedding_service = MockEmbeddingService()
        
        orchestrator = IngestionOrchestrator(
            parser=parser,
            chunker=chunker,
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store
        )
        
        document_id = doc_update["document_id"]
        original_content = doc_update["original_content"]
        updated_content = doc_update["updated_content"]
        metadata = doc_update["metadata"]
        
        # Ingest original
        await orchestrator.ingest_document(
            document_id=document_id,
            content=original_content,
            format=DocumentFormat.MARKDOWN,
            metadata=metadata
        )
        
        # Update document
        result = await orchestrator.update_document(
            document_id=document_id,
            content=updated_content,
            format=DocumentFormat.MARKDOWN,
            metadata=metadata
        )
        
        assert result.success, "Update must succeed"
        
        # Verify all chunks have correct document ID
        updated_chunks = await mock_vector_store.get_chunks_by_document_id(document_id)
        
        for chunk in updated_chunks:
            assert chunk.document_id == document_id, \
                f"All chunks must reference document ID {document_id}"
        
        # Verify chunk indices are sequential
        chunk_indices = sorted([chunk.chunk_index for chunk in updated_chunks])
        expected_indices = list(range(len(updated_chunks)))
        assert chunk_indices == expected_indices, \
            f"Chunk indices must be sequential: expected {expected_indices}, got {chunk_indices}"
