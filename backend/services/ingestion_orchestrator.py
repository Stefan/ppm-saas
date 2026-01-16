"""
Ingestion Orchestrator Service for RAG Knowledge Base
Coordinates the document ingestion pipeline: parse → chunk → embed → store
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from services.document_parser import DocumentParser, DocumentFormat, ParsingError
from services.text_chunker import TextChunker, ChunkingError
from services.embedding_service import EmbeddingService, EmbeddingServiceError
from services.vector_store import VectorStore, VectorChunk, VectorStoreError

logger = logging.getLogger(__name__)


class IngestionStatus(str, Enum):
    """Status of ingestion operation"""
    PENDING = "pending"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestionError(Exception):
    """Base exception for ingestion errors"""
    pass


@dataclass
class IngestionProgress:
    """Progress tracking for ingestion operation"""
    document_id: str
    status: IngestionStatus
    current_stage: str
    progress_percentage: float
    chunks_processed: int
    total_chunks: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "document_id": self.document_id,
            "status": self.status.value,
            "current_stage": self.current_stage,
            "progress_percentage": self.progress_percentage,
            "chunks_processed": self.chunks_processed,
            "total_chunks": self.total_chunks,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class IngestionResult:
    """Result of document ingestion operation"""
    document_id: str
    success: bool
    chunks_created: int
    processing_time_ms: int
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "document_id": self.document_id,
            "success": self.success,
            "chunks_created": self.chunks_created,
            "processing_time_ms": self.processing_time_ms,
            "error_message": self.error_message,
            "metadata": self.metadata or {}
        }


class IngestionOrchestrator:
    """
    Orchestrates the document ingestion pipeline.
    
    Pipeline stages:
    1. Parse: Extract text and structure from document
    2. Chunk: Split document into optimal chunks
    3. Embed: Generate vector embeddings for chunks
    4. Store: Save chunks and embeddings to vector store
    
    Features:
    - Transaction handling for atomicity
    - Progress tracking for long-running operations
    - Error handling with rollback on failure
    - Support for document updates with re-indexing
    """
    
    def __init__(
        self,
        parser: DocumentParser,
        chunker: TextChunker,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        db_connection: Any = None
    ):
        """
        Initialize the ingestion orchestrator.
        
        Args:
            parser: Document parser service
            chunker: Text chunker service
            embedding_service: Embedding generation service
            vector_store: Vector store service
            db_connection: Database connection for transactions
        """
        self.parser = parser
        self.chunker = chunker
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.db = db_connection
        
        # Progress tracking
        self._progress_trackers: Dict[str, IngestionProgress] = {}
        
        logger.info("IngestionOrchestrator initialized")
    
    async def ingest_document(
        self,
        document_id: str,
        content: str,
        format: DocumentFormat = DocumentFormat.PLAIN_TEXT,
        metadata: Optional[Dict[str, Any]] = None,
        preserve_boundaries: bool = True
    ) -> IngestionResult:
        """
        Ingest a document through the full pipeline.
        
        This method coordinates all stages of ingestion:
        1. Parse document to extract text
        2. Chunk text into optimal sizes
        3. Generate embeddings for chunks
        4. Store chunks in vector database
        
        The operation is atomic - if any stage fails, all changes are rolled back.
        
        Args:
            document_id: Unique identifier for the document
            content: Raw document content
            format: Document format (markdown, json, plain_text)
            metadata: Optional metadata to attach to chunks
            preserve_boundaries: Whether to preserve semantic boundaries when chunking
            
        Returns:
            IngestionResult with operation details
            
        Raises:
            IngestionError: If ingestion fails at any stage
        """
        start_time = datetime.now()
        
        # Initialize progress tracking
        progress = IngestionProgress(
            document_id=document_id,
            status=IngestionStatus.PENDING,
            current_stage="Initializing",
            progress_percentage=0.0,
            chunks_processed=0,
            total_chunks=0,
            started_at=start_time
        )
        self._progress_trackers[document_id] = progress
        
        try:
            logger.info(f"Starting ingestion for document: {document_id}")
            
            # Stage 1: Parse document
            progress.status = IngestionStatus.PARSING
            progress.current_stage = "Parsing document"
            progress.progress_percentage = 10.0
            
            logger.debug(f"[{document_id}] Stage 1: Parsing document")
            
            try:
                parsed_doc = self.parser.parse(content, format)
            except ParsingError as e:
                raise IngestionError(f"Document parsing failed: {str(e)}") from e
            
            logger.info(
                f"[{document_id}] Document parsed successfully: "
                f"length={len(parsed_doc.content)}, format={format}"
            )
            
            # Stage 2: Chunk text
            progress.status = IngestionStatus.CHUNKING
            progress.current_stage = "Chunking text"
            progress.progress_percentage = 30.0
            
            logger.debug(f"[{document_id}] Stage 2: Chunking text")
            
            try:
                # Prepare chunk metadata
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    "document_title": parsed_doc.title,
                    "format": format.value
                })
                
                chunks = self.chunker.chunk_text(
                    parsed_doc.content,
                    preserve_boundaries=preserve_boundaries,
                    metadata=chunk_metadata
                )
            except ChunkingError as e:
                raise IngestionError(f"Text chunking failed: {str(e)}") from e
            
            progress.total_chunks = len(chunks)
            
            logger.info(
                f"[{document_id}] Text chunked successfully: "
                f"{len(chunks)} chunks created"
            )
            
            # Stage 3: Generate embeddings
            progress.status = IngestionStatus.EMBEDDING
            progress.current_stage = "Generating embeddings"
            progress.progress_percentage = 50.0
            
            logger.debug(f"[{document_id}] Stage 3: Generating embeddings")
            
            try:
                # Extract chunk texts for batch embedding
                chunk_texts = [chunk.content for chunk in chunks]
                
                # Generate embeddings in batch for efficiency
                embeddings = await self.embedding_service.embed_batch_async(chunk_texts)
                
            except EmbeddingServiceError as e:
                raise IngestionError(f"Embedding generation failed: {str(e)}") from e
            
            logger.info(
                f"[{document_id}] Embeddings generated successfully: "
                f"{len(embeddings)} embeddings"
            )
            
            # Stage 4: Store in vector database
            progress.status = IngestionStatus.STORING
            progress.current_stage = "Storing in vector database"
            progress.progress_percentage = 80.0
            
            logger.debug(f"[{document_id}] Stage 4: Storing in vector database")
            
            try:
                # Create VectorChunk objects
                vector_chunks = []
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    vector_chunk = VectorChunk(
                        document_id=document_id,
                        chunk_index=i,
                        content=chunk.content,
                        embedding=embedding,
                        metadata=chunk.metadata
                    )
                    vector_chunks.append(vector_chunk)
                    
                    # Update progress
                    progress.chunks_processed = i + 1
                    progress.progress_percentage = 80.0 + (15.0 * (i + 1) / len(chunks))
                
                # Store chunks in vector database
                await self.vector_store.upsert_chunks(vector_chunks)
                
            except VectorStoreError as e:
                raise IngestionError(f"Vector store operation failed: {str(e)}") from e
            
            # Complete
            progress.status = IngestionStatus.COMPLETED
            progress.current_stage = "Completed"
            progress.progress_percentage = 100.0
            progress.completed_at = datetime.now()
            
            processing_time = int((progress.completed_at - start_time).total_seconds() * 1000)
            
            logger.info(
                f"[{document_id}] Ingestion completed successfully: "
                f"{len(chunks)} chunks, {processing_time}ms"
            )
            
            return IngestionResult(
                document_id=document_id,
                success=True,
                chunks_created=len(chunks),
                processing_time_ms=processing_time,
                metadata={
                    "format": format.value,
                    "title": parsed_doc.title,
                    "total_chunks": len(chunks)
                }
            )
            
        except Exception as e:
            # Mark as failed
            progress.status = IngestionStatus.FAILED
            progress.error_message = str(e)
            progress.completed_at = datetime.now()
            
            processing_time = int((progress.completed_at - start_time).total_seconds() * 1000)
            
            logger.error(f"[{document_id}] Ingestion failed: {e}")
            
            # Attempt rollback - delete any chunks that were created
            try:
                await self._rollback_ingestion(document_id)
            except Exception as rollback_error:
                logger.error(f"[{document_id}] Rollback failed: {rollback_error}")
            
            return IngestionResult(
                document_id=document_id,
                success=False,
                chunks_created=0,
                processing_time_ms=processing_time,
                error_message=str(e)
            )
    
    async def update_document(
        self,
        document_id: str,
        content: str,
        format: DocumentFormat = DocumentFormat.PLAIN_TEXT,
        metadata: Optional[Dict[str, Any]] = None,
        preserve_boundaries: bool = True
    ) -> IngestionResult:
        """
        Update an existing document with re-indexing.
        
        This method:
        1. Deletes all existing chunks for the document
        2. Re-ingests the document with new content
        
        The operation is atomic - if re-ingestion fails, the old chunks remain.
        
        Args:
            document_id: ID of document to update
            content: New document content
            format: Document format
            metadata: Optional metadata
            preserve_boundaries: Whether to preserve semantic boundaries
            
        Returns:
            IngestionResult with operation details
            
        Raises:
            IngestionError: If update fails
        """
        logger.info(f"Updating document: {document_id}")
        
        try:
            # Step 1: Delete existing chunks
            logger.debug(f"[{document_id}] Deleting existing chunks")
            deleted_count = await self.vector_store.delete_by_document_id(document_id)
            logger.info(f"[{document_id}] Deleted {deleted_count} existing chunks")
            
            # Step 2: Re-ingest document
            logger.debug(f"[{document_id}] Re-ingesting document")
            result = await self.ingest_document(
                document_id=document_id,
                content=content,
                format=format,
                metadata=metadata,
                preserve_boundaries=preserve_boundaries
            )
            
            if result.success:
                logger.info(
                    f"[{document_id}] Document updated successfully: "
                    f"{deleted_count} old chunks deleted, {result.chunks_created} new chunks created"
                )
            else:
                logger.error(f"[{document_id}] Document update failed: {result.error_message}")
            
            return result
            
        except Exception as e:
            logger.error(f"[{document_id}] Document update failed: {e}")
            raise IngestionError(f"Document update failed: {str(e)}") from e
    
    async def _rollback_ingestion(self, document_id: str) -> None:
        """
        Rollback ingestion by deleting all chunks for a document.
        
        Args:
            document_id: ID of document to rollback
        """
        logger.warning(f"[{document_id}] Rolling back ingestion")
        
        try:
            deleted_count = await self.vector_store.delete_by_document_id(document_id)
            logger.info(f"[{document_id}] Rollback completed: {deleted_count} chunks deleted")
        except Exception as e:
            logger.error(f"[{document_id}] Rollback failed: {e}")
            raise
    
    def get_progress(self, document_id: str) -> Optional[IngestionProgress]:
        """
        Get progress for a document ingestion.
        
        Args:
            document_id: ID of document
            
        Returns:
            IngestionProgress object or None if not found
        """
        return self._progress_trackers.get(document_id)
    
    def clear_progress(self, document_id: str) -> None:
        """
        Clear progress tracking for a document.
        
        Args:
            document_id: ID of document
        """
        if document_id in self._progress_trackers:
            del self._progress_trackers[document_id]
    
    async def batch_ingest_documents(
        self,
        documents: List[Dict[str, Any]],
        continue_on_error: bool = True
    ) -> List[IngestionResult]:
        """
        Ingest multiple documents in batch.
        
        Args:
            documents: List of document dicts with keys: id, content, format, metadata
            continue_on_error: Whether to continue if one document fails
            
        Returns:
            List of IngestionResult objects
        """
        logger.info(f"Starting batch ingestion: {len(documents)} documents")
        
        results = []
        
        for i, doc in enumerate(documents):
            document_id = doc.get('id')
            content = doc.get('content')
            format = doc.get('format', DocumentFormat.PLAIN_TEXT)
            metadata = doc.get('metadata')
            
            logger.info(f"Batch ingestion [{i+1}/{len(documents)}]: {document_id}")
            
            try:
                result = await self.ingest_document(
                    document_id=document_id,
                    content=content,
                    format=format,
                    metadata=metadata
                )
                results.append(result)
                
                if not result.success and not continue_on_error:
                    logger.error(f"Batch ingestion stopped due to error: {result.error_message}")
                    break
                    
            except Exception as e:
                logger.error(f"Batch ingestion error for {document_id}: {e}")
                
                results.append(IngestionResult(
                    document_id=document_id,
                    success=False,
                    chunks_created=0,
                    processing_time_ms=0,
                    error_message=str(e)
                ))
                
                if not continue_on_error:
                    break
        
        successful = sum(1 for r in results if r.success)
        logger.info(
            f"Batch ingestion completed: {successful}/{len(documents)} successful"
        )
        
        return results
