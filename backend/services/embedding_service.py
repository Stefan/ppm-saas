"""
Embedding Service for RAG Knowledge Base
Generates vector embeddings for text using OpenAI's text-embedding-3-small model
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
from openai import OpenAI, AsyncOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger(__name__)


class EmbeddingServiceError(Exception):
    """Base exception for embedding service errors"""
    pass


class EmbeddingAPIError(EmbeddingServiceError):
    """Exception for API-related errors"""
    pass


class EmbeddingConfig:
    """Configuration for embedding service"""
    
    def __init__(
        self,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536,
        max_batch_size: int = 100,
        max_retries: int = 3,
        retry_min_wait: int = 1,
        retry_max_wait: int = 10
    ):
        self.model = model
        self.dimensions = dimensions
        self.max_batch_size = max_batch_size
        self.max_retries = max_retries
        self.retry_min_wait = retry_min_wait
        self.retry_max_wait = retry_max_wait


class EmbeddingResult:
    """Result of an embedding operation"""
    
    def __init__(
        self,
        text: str,
        embedding: List[float],
        model: str,
        dimensions: int,
        processing_time_ms: int
    ):
        self.text = text
        self.embedding = embedding
        self.model = model
        self.dimensions = dimensions
        self.processing_time_ms = processing_time_ms
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "text": self.text,
            "embedding": self.embedding,
            "model": self.model,
            "dimensions": self.dimensions,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp.isoformat()
        }


class BatchEmbeddingResult:
    """Result of a batch embedding operation"""
    
    def __init__(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        model: str,
        dimensions: int,
        total_processing_time_ms: int,
        batch_size: int
    ):
        self.texts = texts
        self.embeddings = embeddings
        self.model = model
        self.dimensions = dimensions
        self.total_processing_time_ms = total_processing_time_ms
        self.batch_size = batch_size
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "texts": self.texts,
            "embeddings": self.embeddings,
            "model": self.model,
            "dimensions": self.dimensions,
            "total_processing_time_ms": self.total_processing_time_ms,
            "batch_size": self.batch_size,
            "timestamp": self.timestamp.isoformat()
        }


class EmbeddingService:
    """
    Service for generating vector embeddings using OpenAI API.
    
    Features:
    - Single text embedding generation
    - Efficient batch processing
    - Automatic retry logic with exponential backoff
    - Error handling and logging
    - Configurable model and dimensions
    """
    
    def __init__(self, api_key: str, config: Optional[EmbeddingConfig] = None):
        """
        Initialize the embedding service.
        
        Args:
            api_key: OpenAI API key
            config: Optional configuration object
        """
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        self.api_key = api_key
        self.config = config or EmbeddingConfig()
        
        # Initialize OpenAI clients
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)
        
        logger.info(
            f"EmbeddingService initialized with model={self.config.model}, "
            f"dimensions={self.config.dimensions}"
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding vector for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            EmbeddingAPIError: If API call fails after retries
            ValueError: If text is empty or invalid
        """
        start_time = datetime.now()
        
        # Validate input
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            logger.debug(f"Generating embedding for text (length={len(text)})")
            
            # Call OpenAI API
            response = self.client.embeddings.create(
                model=self.config.model,
                input=text,
                dimensions=self.config.dimensions
            )
            
            # Extract embedding
            embedding = response.data[0].embedding
            
            # Calculate processing time
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            logger.debug(
                f"Embedding generated successfully: "
                f"dimensions={len(embedding)}, time={processing_time}ms"
            )
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise EmbeddingAPIError(f"Embedding generation failed: {str(e)}") from e
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def embed_text_async(self, text: str) -> List[float]:
        """
        Generate embedding vector for a single text (async version).
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            EmbeddingAPIError: If API call fails after retries
            ValueError: If text is empty or invalid
        """
        start_time = datetime.now()
        
        # Validate input
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            logger.debug(f"Generating embedding for text (length={len(text)})")
            
            # Call OpenAI API asynchronously
            response = await self.async_client.embeddings.create(
                model=self.config.model,
                input=text,
                dimensions=self.config.dimensions
            )
            
            # Extract embedding
            embedding = response.data[0].embedding
            
            # Calculate processing time
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            logger.debug(
                f"Embedding generated successfully: "
                f"dimensions={len(embedding)}, time={processing_time}ms"
            )
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise EmbeddingAPIError(f"Embedding generation failed: {str(e)}") from e
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently in batch.
        
        This method processes texts in batches to optimize API usage and performance.
        Large batches are automatically split into smaller chunks.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding vectors, one for each input text
            
        Raises:
            EmbeddingAPIError: If API call fails after retries
            ValueError: If texts list is empty or contains invalid entries
        """
        start_time = datetime.now()
        
        # Validate input
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        # Filter out empty texts and log warning
        valid_texts = [t for t in texts if t and t.strip()]
        if len(valid_texts) < len(texts):
            logger.warning(
                f"Filtered out {len(texts) - len(valid_texts)} empty texts from batch"
            )
        
        if not valid_texts:
            raise ValueError("No valid texts to embed")
        
        try:
            logger.info(f"Generating embeddings for batch of {len(valid_texts)} texts")
            
            # Process in batches if needed
            all_embeddings = []
            
            for i in range(0, len(valid_texts), self.config.max_batch_size):
                batch = valid_texts[i:i + self.config.max_batch_size]
                
                logger.debug(
                    f"Processing batch {i // self.config.max_batch_size + 1}: "
                    f"{len(batch)} texts"
                )
                
                # Call OpenAI API with batch
                response = self.client.embeddings.create(
                    model=self.config.model,
                    input=batch,
                    dimensions=self.config.dimensions
                )
                
                # Extract embeddings in order
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            
            # Calculate processing time
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            logger.info(
                f"Batch embeddings generated successfully: "
                f"count={len(all_embeddings)}, time={processing_time}ms, "
                f"avg_time_per_text={processing_time / len(all_embeddings):.2f}ms"
            )
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise EmbeddingAPIError(f"Batch embedding generation failed: {str(e)}") from e
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def embed_batch_async(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently in batch (async version).
        
        This method processes texts in batches to optimize API usage and performance.
        Large batches are automatically split into smaller chunks.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding vectors, one for each input text
            
        Raises:
            EmbeddingAPIError: If API call fails after retries
            ValueError: If texts list is empty or contains invalid entries
        """
        start_time = datetime.now()
        
        # Validate input
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        # Filter out empty texts and log warning
        valid_texts = [t for t in texts if t and t.strip()]
        if len(valid_texts) < len(texts):
            logger.warning(
                f"Filtered out {len(texts) - len(valid_texts)} empty texts from batch"
            )
        
        if not valid_texts:
            raise ValueError("No valid texts to embed")
        
        try:
            logger.info(f"Generating embeddings for batch of {len(valid_texts)} texts")
            
            # Process in batches if needed
            all_embeddings = []
            
            for i in range(0, len(valid_texts), self.config.max_batch_size):
                batch = valid_texts[i:i + self.config.max_batch_size]
                
                logger.debug(
                    f"Processing batch {i // self.config.max_batch_size + 1}: "
                    f"{len(batch)} texts"
                )
                
                # Call OpenAI API with batch asynchronously
                response = await self.async_client.embeddings.create(
                    model=self.config.model,
                    input=batch,
                    dimensions=self.config.dimensions
                )
                
                # Extract embeddings in order
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            
            # Calculate processing time
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            logger.info(
                f"Batch embeddings generated successfully: "
                f"count={len(all_embeddings)}, time={processing_time}ms, "
                f"avg_time_per_text={processing_time / len(all_embeddings):.2f}ms"
            )
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise EmbeddingAPIError(f"Batch embedding generation failed: {str(e)}") from e
    
    def get_embedding_dimensions(self) -> int:
        """Get the configured embedding dimensions"""
        return self.config.dimensions
    
    def get_model_name(self) -> str:
        """Get the configured model name"""
        return self.config.model
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """
        Validate that an embedding has the correct dimensions.
        
        Args:
            embedding: Embedding vector to validate
            
        Returns:
            True if valid, False otherwise
        """
        return (
            isinstance(embedding, list) and
            len(embedding) == self.config.dimensions and
            all(isinstance(x, (int, float)) for x in embedding)
        )
