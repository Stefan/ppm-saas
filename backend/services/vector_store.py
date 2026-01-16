"""
Vector Store Service for RAG Knowledge Base
Handles storage and retrieval of vector embeddings using PostgreSQL with pgvector
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class VectorStoreError(Exception):
    """Base exception for vector store errors"""
    pass


class SearchResult:
    """Result from similarity search"""
    
    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        chunk_index: int,
        content: str,
        similarity_score: float,
        metadata: Dict[str, Any]
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.content = content
        self.similarity_score = similarity_score
        self.metadata = metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "similarity_score": self.similarity_score,
            "metadata": self.metadata
        }


class VectorChunk:
    """Represents a chunk stored in the vector database"""
    
    def __init__(
        self,
        document_id: str,
        chunk_index: int,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        chunk_id: Optional[str] = None
    ):
        self.chunk_id = chunk_id or str(uuid.uuid4())
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.content = content
        self.embedding = embedding
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.chunk_id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "embedding": self.embedding,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class VectorStore:
    """
    Interface for vector database operations using PostgreSQL with pgvector.
    
    Features:
    - Insert/update chunks with embeddings
    - Similarity search using cosine distance
    - Cascade deletion by document ID
    - Metadata filtering
    """
    
    def __init__(self, db_connection):
        """
        Initialize the vector store.
        
        Args:
            db_connection: Database connection (asyncpg connection or SQLAlchemy session)
        """
        self.db = db_connection
        logger.info("VectorStore initialized")
    
    async def upsert_chunks(self, chunks: List[VectorChunk]) -> None:
        """
        Insert or update chunks in the vector store.
        
        This method handles both new insertions and updates of existing chunks.
        Uses ON CONFLICT to handle duplicates.
        
        Args:
            chunks: List of VectorChunk objects to upsert
            
        Raises:
            VectorStoreError: If upsert operation fails
        """
        if not chunks:
            logger.warning("No chunks to upsert")
            return
        
        try:
            logger.info(f"Upserting {len(chunks)} chunks to vector store")
            
            # Prepare batch insert/update
            for chunk in chunks:
                # Validate embedding dimensions
                if not chunk.embedding or len(chunk.embedding) != 1536:
                    raise VectorStoreError(
                        f"Invalid embedding dimensions for chunk {chunk.chunk_id}: "
                        f"expected 1536, got {len(chunk.embedding) if chunk.embedding else 0}"
                    )
                
                # Insert or update chunk
                query = """
                    INSERT INTO vector_chunks (id, document_id, chunk_index, content, embedding, metadata, created_at)
                    VALUES ($1, $2, $3, $4, $5::vector, $6, $7)
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata
                """
                
                await self.db.execute(
                    query,
                    chunk.chunk_id,
                    chunk.document_id,
                    chunk.chunk_index,
                    chunk.content,
                    chunk.embedding,
                    chunk.metadata,
                    chunk.created_at
                )
            
            logger.info(f"Successfully upserted {len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Failed to upsert chunks: {e}")
            raise VectorStoreError(f"Chunk upsert failed: {str(e)}") from e
    
    async def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Find most similar chunks to query embedding using cosine similarity.
        
        Args:
            query_embedding: Query vector embedding
            top_k: Number of results to return (default 5)
            filter_metadata: Optional metadata filters (e.g., {"category": "dashboard"})
            
        Returns:
            List of SearchResult objects ordered by similarity (highest first)
            
        Raises:
            VectorStoreError: If search operation fails
        """
        if not query_embedding or len(query_embedding) != 1536:
            raise VectorStoreError(
                f"Invalid query embedding dimensions: "
                f"expected 1536, got {len(query_embedding) if query_embedding else 0}"
            )
        
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        
        try:
            logger.debug(f"Performing similarity search: top_k={top_k}")
            
            # Build query with optional metadata filtering
            query = """
                SELECT 
                    id,
                    document_id,
                    chunk_index,
                    content,
                    metadata,
                    1 - (embedding <=> $1::vector) as similarity_score
                FROM vector_chunks
            """
            
            params = [query_embedding]
            
            # Add metadata filters if provided
            if filter_metadata:
                conditions = []
                for key, value in filter_metadata.items():
                    params.append(value)
                    conditions.append(f"metadata->>'{key}' = ${len(params)}")
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            # Order by similarity and limit
            query += f" ORDER BY similarity_score DESC LIMIT {top_k}"
            
            # Execute query
            rows = await self.db.fetch(query, *params)
            
            # Convert to SearchResult objects
            results = []
            for row in rows:
                result = SearchResult(
                    chunk_id=row['id'],
                    document_id=row['document_id'],
                    chunk_index=row['chunk_index'],
                    content=row['content'],
                    similarity_score=float(row['similarity_score']),
                    metadata=row['metadata']
                )
                results.append(result)
            
            logger.info(f"Found {len(results)} similar chunks")
            
            return results
            
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            raise VectorStoreError(f"Similarity search failed: {str(e)}") from e
    
    async def delete_by_document_id(self, document_id: str) -> int:
        """
        Remove all chunks for a document (cascade deletion).
        
        Args:
            document_id: ID of the document whose chunks should be deleted
            
        Returns:
            Number of chunks deleted
            
        Raises:
            VectorStoreError: If deletion fails
        """
        if not document_id:
            raise ValueError("document_id cannot be empty")
        
        try:
            logger.info(f"Deleting all chunks for document: {document_id}")
            
            # Delete chunks
            query = "DELETE FROM vector_chunks WHERE document_id = $1"
            result = await self.db.execute(query, document_id)
            
            # Extract number of deleted rows
            # Result format: "DELETE N" where N is the count
            deleted_count = int(result.split()[-1]) if result else 0
            
            logger.info(f"Deleted {deleted_count} chunks for document {document_id}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete chunks for document {document_id}: {e}")
            raise VectorStoreError(f"Chunk deletion failed: {str(e)}") from e
    
    async def get_chunks_by_document_id(self, document_id: str) -> List[VectorChunk]:
        """
        Retrieve all chunks for a specific document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            List of VectorChunk objects
            
        Raises:
            VectorStoreError: If retrieval fails
        """
        if not document_id:
            raise ValueError("document_id cannot be empty")
        
        try:
            logger.debug(f"Retrieving chunks for document: {document_id}")
            
            query = """
                SELECT id, document_id, chunk_index, content, embedding, metadata, created_at
                FROM vector_chunks
                WHERE document_id = $1
                ORDER BY chunk_index
            """
            
            rows = await self.db.fetch(query, document_id)
            
            chunks = []
            for row in rows:
                chunk = VectorChunk(
                    chunk_id=row['id'],
                    document_id=row['document_id'],
                    chunk_index=row['chunk_index'],
                    content=row['content'],
                    embedding=row['embedding'],
                    metadata=row['metadata']
                )
                chunk.created_at = row['created_at']
                chunks.append(chunk)
            
            logger.debug(f"Retrieved {len(chunks)} chunks for document {document_id}")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to retrieve chunks for document {document_id}: {e}")
            raise VectorStoreError(f"Chunk retrieval failed: {str(e)}") from e
    
    async def count_chunks(self, document_id: Optional[str] = None) -> int:
        """
        Count total chunks in the vector store.
        
        Args:
            document_id: Optional document ID to count chunks for specific document
            
        Returns:
            Number of chunks
        """
        try:
            if document_id:
                query = "SELECT COUNT(*) FROM vector_chunks WHERE document_id = $1"
                result = await self.db.fetchval(query, document_id)
            else:
                query = "SELECT COUNT(*) FROM vector_chunks"
                result = await self.db.fetchval(query)
            
            return result or 0
            
        except Exception as e:
            logger.error(f"Failed to count chunks: {e}")
            return 0
