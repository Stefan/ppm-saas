-- Migration 027: Update Embedding Dimension for Local Models
-- Changes embedding column from vector(1536) to vector(384) for sentence-transformers compatibility

-- Drop existing indexes that depend on the embedding column
DROP INDEX IF EXISTS embeddings_vector_idx;

-- Alter the embedding column to support 384 dimensions (all-MiniLM-L6-v2)
ALTER TABLE embeddings ALTER COLUMN embedding TYPE vector(384);

-- Recreate the IVFFlat index for fast approximate nearest neighbor search
CREATE INDEX embeddings_vector_idx ON embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Update the vector_similarity_search function to use vector(384)
CREATE OR REPLACE FUNCTION vector_similarity_search(
    query_embedding vector(384),  -- Changed from 1536 to 384
    content_types text[] DEFAULT NULL,
    org_id UUID DEFAULT NULL,
    similarity_limit int DEFAULT 10,
    similarity_threshold float DEFAULT 0.0
)
RETURNS TABLE (
    content_type text,
    content_id text,
    content_text text,
    metadata jsonb,
    similarity_score float,
    created_at timestamptz
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.content_type,
        e.content_id,
        e.content_text,
        e.metadata,
        (1 - (e.embedding <=> query_embedding))::float as similarity_score,
        e.created_at
    FROM embeddings e
    WHERE 
        (content_types IS NULL OR e.content_type = ANY(content_types))
        AND (org_id IS NULL OR e.organization_id = org_id)
        AND (1 - (e.embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY e.embedding <=> query_embedding
    LIMIT similarity_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- Update comments
COMMENT ON COLUMN embeddings.embedding IS 'Vector embedding (384 dimensions for sentence-transformers all-MiniLM-L6-v2)';
COMMENT ON FUNCTION vector_similarity_search IS 'Performs vector similarity search with 384-dimensional embeddings';
