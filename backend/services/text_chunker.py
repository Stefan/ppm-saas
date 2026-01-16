"""
Text Chunker Service for RAG Knowledge Base
Splits documents into optimal chunks for embedding and retrieval
"""

import logging
import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ChunkingError(Exception):
    """Base exception for chunking errors"""
    pass


@dataclass
class Chunk:
    """Represents a text chunk with metadata"""
    content: str
    chunk_index: int
    token_count: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary representation"""
        return {
            "content": self.content,
            "chunk_index": self.chunk_index,
            "token_count": self.token_count,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "metadata": self.metadata
        }


class TextChunker:
    """
    Service for splitting documents into optimal chunks for embedding.
    
    Features:
    - Token-based chunking with configurable size and overlap
    - Semantic boundary preservation (paragraphs, sections)
    - Accurate token counting using tiktoken
    - Metadata preservation for each chunk
    """
    
    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
        encoding_name: str = "cl100k_base"
    ):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Target chunk size in tokens (default 512)
            overlap: Number of overlapping tokens between chunks (default 50)
            encoding_name: Tiktoken encoding name (default cl100k_base for GPT-4)
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        
        if overlap < 0:
            raise ValueError("overlap cannot be negative")
        
        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size")
        
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.encoding_name = encoding_name
        
        # Initialize tiktoken encoder
        try:
            import tiktoken
            self.encoder = tiktoken.get_encoding(encoding_name)
        except ImportError:
            logger.warning(
                "tiktoken not installed, falling back to approximate token counting. "
                "Install with: pip install tiktoken"
            )
            self.encoder = None
        except Exception as e:
            logger.warning(f"Failed to initialize tiktoken encoder: {e}. Using approximation.")
            self.encoder = None
        
        logger.info(
            f"TextChunker initialized: chunk_size={chunk_size}, "
            f"overlap={overlap}, encoding={encoding_name}"
        )
    
    def chunk_text(
        self,
        text: str,
        preserve_boundaries: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """
        Split text into chunks.
        
        Args:
            text: Input text to chunk
            preserve_boundaries: If True, try to preserve semantic boundaries
            metadata: Optional metadata to attach to all chunks
            
        Returns:
            List of Chunk objects
            
        Raises:
            ChunkingError: If chunking fails
        """
        if not text or not text.strip():
            raise ChunkingError("Text cannot be empty")
        
        if preserve_boundaries:
            return self.chunk_by_semantic_boundaries(text, metadata)
        else:
            return self.chunk_by_tokens(text, metadata)
    
    def chunk_by_tokens(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """
        Split text into chunks by token count with overlap.
        
        This method:
        1. Encodes text into tokens
        2. Splits into chunks of target size
        3. Adds overlap between adjacent chunks
        4. Decodes back to text
        
        Args:
            text: Input text to chunk
            metadata: Optional metadata to attach to all chunks
            
        Returns:
            List of Chunk objects with specified size and overlap
        """
        if not text or not text.strip():
            raise ChunkingError("Text cannot be empty")
        
        logger.debug(
            f"Chunking text by tokens: length={len(text)}, "
            f"chunk_size={self.chunk_size}, overlap={self.overlap}"
        )
        
        # Encode text to tokens
        if self.encoder:
            tokens = self.encoder.encode(text)
        else:
            # Fallback: approximate tokens (1 token ≈ 4 characters)
            tokens = self._approximate_tokens(text)
        
        total_tokens = len(tokens)
        logger.debug(f"Total tokens: {total_tokens}")
        
        chunks = []
        chunk_index = 0
        start_token = 0
        
        while start_token < total_tokens:
            # Calculate end token for this chunk
            end_token = min(start_token + self.chunk_size, total_tokens)
            
            # Extract chunk tokens
            chunk_tokens = tokens[start_token:end_token]
            
            # Decode tokens back to text
            if self.encoder:
                chunk_text = self.encoder.decode(chunk_tokens)
            else:
                # Fallback: use character-based approximation
                chars_per_token = len(text) / total_tokens
                start_char = int(start_token * chars_per_token)
                end_char = int(end_token * chars_per_token)
                chunk_text = text[start_char:end_char]
            
            # Calculate character positions (approximate for token-based)
            start_char = text.find(chunk_text[:50]) if len(chunk_text) >= 50 else 0
            if start_char == -1:
                start_char = 0
            end_char = start_char + len(chunk_text)
            
            # Create chunk
            chunk = Chunk(
                content=chunk_text.strip(),
                chunk_index=chunk_index,
                token_count=len(chunk_tokens),
                start_char=start_char,
                end_char=end_char,
                metadata=metadata.copy() if metadata else {}
            )
            
            chunks.append(chunk)
            
            # Move to next chunk with overlap
            start_token = end_token - self.overlap
            chunk_index += 1
            
            # Prevent infinite loop
            if start_token >= total_tokens:
                break
        
        logger.info(f"Created {len(chunks)} chunks from text")
        
        return chunks
    
    def chunk_by_semantic_boundaries(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """
        Split text at natural boundaries (paragraphs, sections) while respecting token limits.
        
        This method:
        1. Splits text into paragraphs
        2. Groups paragraphs into chunks that fit within token limit
        3. Preserves paragraph boundaries when possible
        4. Falls back to token-based splitting for oversized paragraphs
        
        Args:
            text: Input text to chunk
            metadata: Optional metadata to attach to all chunks
            
        Returns:
            List of Chunk objects preserving semantic boundaries
        """
        if not text or not text.strip():
            raise ChunkingError("Text cannot be empty")
        
        logger.debug(
            f"Chunking text by semantic boundaries: length={len(text)}, "
            f"chunk_size={self.chunk_size}"
        )
        
        # Split into paragraphs (double newline or more)
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        logger.debug(f"Found {len(paragraphs)} paragraphs")
        
        chunks = []
        chunk_index = 0
        current_chunk_text = []
        current_chunk_tokens = 0
        current_start_char = 0
        
        for para_idx, paragraph in enumerate(paragraphs):
            para_tokens = self._count_tokens(paragraph)
            
            # If single paragraph exceeds chunk size, split it
            if para_tokens > self.chunk_size:
                # Save current chunk if it has content
                if current_chunk_text:
                    chunk_text = '\n\n'.join(current_chunk_text)
                    chunk = self._create_chunk(
                        chunk_text,
                        chunk_index,
                        current_chunk_tokens,
                        current_start_char,
                        metadata
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    current_chunk_text = []
                    current_chunk_tokens = 0
                
                # Split oversized paragraph using token-based chunking
                para_chunks = self.chunk_by_tokens(paragraph, metadata)
                for para_chunk in para_chunks:
                    para_chunk.chunk_index = chunk_index
                    para_chunk.start_char = text.find(para_chunk.content, current_start_char)
                    if para_chunk.start_char == -1:
                        para_chunk.start_char = current_start_char
                    para_chunk.end_char = para_chunk.start_char + len(para_chunk.content)
                    chunks.append(para_chunk)
                    chunk_index += 1
                    current_start_char = para_chunk.end_char
                
                continue
            
            # Check if adding this paragraph would exceed chunk size
            if current_chunk_tokens + para_tokens > self.chunk_size and current_chunk_text:
                # Save current chunk
                chunk_text = '\n\n'.join(current_chunk_text)
                chunk = self._create_chunk(
                    chunk_text,
                    chunk_index,
                    current_chunk_tokens,
                    current_start_char,
                    metadata
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # Start new chunk with overlap
                # Include last paragraph from previous chunk for overlap
                if len(current_chunk_text) > 0:
                    overlap_text = current_chunk_text[-1]
                    overlap_tokens = self._count_tokens(overlap_text)
                    
                    if overlap_tokens <= self.overlap:
                        current_chunk_text = [overlap_text]
                        current_chunk_tokens = overlap_tokens
                    else:
                        current_chunk_text = []
                        current_chunk_tokens = 0
                else:
                    current_chunk_text = []
                    current_chunk_tokens = 0
                
                current_start_char = text.find(paragraph, current_start_char)
                if current_start_char == -1:
                    current_start_char = 0
            
            # Add paragraph to current chunk
            current_chunk_text.append(paragraph)
            current_chunk_tokens += para_tokens
        
        # Add final chunk if it has content
        if current_chunk_text:
            chunk_text = '\n\n'.join(current_chunk_text)
            chunk = self._create_chunk(
                chunk_text,
                chunk_index,
                current_chunk_tokens,
                current_start_char,
                metadata
            )
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} chunks preserving semantic boundaries")
        
        return chunks
    
    def _create_chunk(
        self,
        text: str,
        chunk_index: int,
        token_count: int,
        start_char: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Chunk:
        """Helper method to create a Chunk object"""
        return Chunk(
            content=text.strip(),
            chunk_index=chunk_index,
            token_count=token_count,
            start_char=start_char,
            end_char=start_char + len(text),
            metadata=metadata.copy() if metadata else {}
        )
    
    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken or approximation.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        if not text:
            return 0
        
        if self.encoder:
            return len(self.encoder.encode(text))
        else:
            # Fallback: approximate (1 token ≈ 4 characters)
            return len(text) // 4
    
    def _approximate_tokens(self, text: str) -> List[int]:
        """
        Approximate token list when tiktoken is not available.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of pseudo-token IDs (character indices)
        """
        # Simple approximation: treat every 4 characters as a token
        return list(range(0, len(text), 4))
    
    def validate_chunks(self, chunks: List[Chunk]) -> bool:
        """
        Validate that chunks meet requirements.
        
        Checks:
        - All chunks have content
        - Token counts are within bounds (200-1000)
        - Chunk indices are sequential
        - Overlaps exist between adjacent chunks
        
        Args:
            chunks: List of chunks to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not chunks:
            return False
        
        for i, chunk in enumerate(chunks):
            # Check content exists
            if not chunk.content or not chunk.content.strip():
                logger.warning(f"Chunk {i} has empty content")
                return False
            
            # Check token count bounds (200-1000 as per requirements)
            if chunk.token_count < 200 or chunk.token_count > 1000:
                # Allow last chunk to be smaller
                if i == len(chunks) - 1 and chunk.token_count < 200:
                    pass  # Last chunk can be smaller
                else:
                    logger.warning(
                        f"Chunk {i} token count out of bounds: {chunk.token_count}"
                    )
                    return False
            
            # Check sequential indices
            if chunk.chunk_index != i:
                logger.warning(
                    f"Chunk index mismatch: expected {i}, got {chunk.chunk_index}"
                )
                return False
        
        # Check overlaps between adjacent chunks
        for i in range(len(chunks) - 1):
            current = chunks[i]
            next_chunk = chunks[i + 1]
            
            # Check if there's any overlap in content
            # (last part of current should appear in beginning of next)
            current_end = current.content[-100:] if len(current.content) > 100 else current.content
            next_start = next_chunk.content[:100] if len(next_chunk.content) > 100 else next_chunk.content
            
            # Simple overlap check: some words should match
            current_words = set(current_end.split())
            next_words = set(next_start.split())
            overlap_words = current_words & next_words
            
            if not overlap_words and self.overlap > 0:
                logger.warning(f"No overlap detected between chunks {i} and {i+1}")
                # Don't fail validation, just warn
        
        return True
