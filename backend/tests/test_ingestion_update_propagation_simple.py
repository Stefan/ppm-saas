"""
Simplified Tests for Ingestion Update Propagation
Feature: ai-help-chat-knowledge-base
Tests Property 15 from the design document

Note: This is a simplified synchronous version since hypothesis doesn't support async tests well.
"""

import pytest
from typing import List
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ingestion_orchestrator import IngestionOrchestrator
from services.document_parser import DocumentParser, DocumentFormat
from services.text_chunker import TextChunker
from services.vector_store import VectorChunk


# Mock classes
class MockVectorStore:
    """Mock vector store for testing"""
    
    def __init__(self):
        self.chunks = {}
        self.deleted_documents = []
    
    async def upsert_chunks(self, chunks: List[VectorChunk]) -> None:
        for chunk in chunks:
            if chunk.document_id not in self.chunks:
                self.chunks[chunk.document_id] = []
            self.chunks[chunk.document_id] = [
                c for c in self.chunks[chunk.document_id]
                if c.chunk_index != chunk.chunk_index
            ]
            self.chunks[chunk.document_id].append(chunk)
    
    async def delete_by_document_id(self, document_id: str) -> int:
        if document_id in self.chunks:
            count = len(self.chunks[document_id])
            del self.chunks[document_id]
            self.deleted_documents.append(document_id)
            return count
        return 0
    
    async def get_chunks_by_document_id(self, document_id: str) -> List[VectorChunk]:
        return self.chunks.get(document_id, [])


class MockEmbeddingService:
    """Mock embedding service"""
    
    def __init__(self):
        self.embedding_calls = []
    
    async def embed_batch_async(self, texts: List[str]) -> List[List[float]]:
        self.embedding_calls.append(texts)
        embeddings = []
        for text in texts:
            embedding = [float(hash(text + str(i)) % 100) / 100.0 for i in range(1536)]
            embeddings.append(embedding)
        return embeddings


@pytest.mark.asyncio
class TestUpdatePropagationToVectorStore:
    """
    Property 15: Update Propagation to Vector Store
    Validates: Requirements 5.2
    
    For any Knowledge_Document that is updated, all associated chunks in the 
    Vector_Store must be regenerated with new embeddings.
    """
    
    async def test_update_regenerates_all_chunks(self):
        """
        Test that document updates regenerate all chunks.
        
        Property: For any document update, all chunks must be regenerated
        and stored in the vector store with new embeddings.
        """
        # Setup
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
        
        document_id = "test-doc-123"
        original_content = """# Original Document

This is the original content of the document. It contains several paragraphs
that will be chunked and embedded.

## Section 1

This is the first section with some content about features and functionality.
The content is long enough to create multiple chunks.

## Section 2

This is the second section with different content. It discusses various aspects
of the system and provides detailed information.
"""
        
        updated_content = """# Updated Document

This is the UPDATED content of the document. It has been modified significantly
and contains different information.

## New Section A

This is a completely new section with fresh content about updated features.
The information here is different from the original.

## New Section B

Another new section with updated details and explanations. This content
is entirely different from what was there before.
"""
        
        metadata = {"category": "dashboard", "version": "1.0"}
        
        # Step 1: Ingest original document
        result1 = await orchestrator.ingest_document(
            document_id=document_id,
            content=original_content,
            format=DocumentFormat.MARKDOWN,
            metadata=metadata
        )
        
        assert result1.success, f"Original ingestion must succeed: {result1.error_message}"
        assert result1.chunks_created > 0, "Original ingestion must create chunks"
        
        original_chunks = await mock_vector_store.get_chunks_by_document_id(document_id)
        assert len(original_chunks) == result1.chunks_created
        
        original_chunk_contents = [chunk.content for chunk in original_chunks]
        original_embeddings = [chunk.embedding for chunk in original_chunks]
        
        # Step 2: Update document
        result2 = await orchestrator.update_document(
            document_id=document_id,
            content=updated_content,
            format=DocumentFormat.MARKDOWN,
            metadata=metadata
        )
        
        assert result2.success, f"Document update must succeed: {result2.error_message}"
        assert result2.chunks_created > 0, "Updated document must create chunks"
        
        # Step 3: Verify all chunks were regenerated
        updated_chunks = await mock_vector_store.get_chunks_by_document_id(document_id)
        assert len(updated_chunks) == result2.chunks_created
        
        updated_chunk_contents = [chunk.content for chunk in updated_chunks]
        updated_embeddings = [chunk.embedding for chunk in updated_chunks]
        
        # Verify chunks are different
        assert updated_chunk_contents != original_chunk_contents, \
            "Updated chunks must have different content"
        
        assert updated_embeddings != original_embeddings, \
            "Updated chunks must have regenerated embeddings"
        
        # Verify embedding service was called twice
        assert len(mock_embedding_service.embedding_calls) >= 2, \
            "Embedding service must be called for both ingestions"
        
        # Verify old chunks were deleted
        assert document_id in mock_vector_store.deleted_documents, \
            "Old chunks must be deleted during update"
    
    async def test_update_preserves_document_id_and_indices(self):
        """
        Test that document updates preserve document ID and maintain sequential indices.
        """
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
        
        document_id = "test-doc-456"
        original_content = "# Original\n\nSome content here that is original."
        updated_content = "# Updated\n\nSome content here that is updated and different."
        metadata = {"category": "general", "version": "1.0"}
        
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
            f"Chunk indices must be sequential"
