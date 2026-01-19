-- Migration 026: RAG Embeddings System
-- Creates the embeddings table and vector search infrastructure for RAG (Retrieval-Augmented Generation)
-- Requires pgvector extension for vector similarity search

-- Enable pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- Create embeddings table for storing content embeddings
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_type TEXT NOT NULL CHECK (content_type IN ('project', 'portfolio', 'resource', 'risk', 'issue', 'document', 'knowledge_base')),
    content_id TEXT NOT NULL,
    content_text TEXT NOT NULL,
    embedding vector(1536), -- OpenAI text-embedding-ada-002 dimension
    metadata JSONB DEFAULT '{}',
    organization_id UUID, -- For multi-tenancy support
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_content UNIQUE(content_type, content_id)
);

-- Create indexes for performance
-- IVFFlat index for fast approximate nearest neighbor search
CREATE INDEX IF NOT EXISTS embeddings_vector_idx ON embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100); -- Adjust lists based on dataset size

-- Index for content type filtering
CREATE INDEX IF NOT EXISTS embeddings_content_type_idx ON embeddings(content_type);

-- Index for organization filtering (multi-tenancy)
CREATE INDEX IF NOT EXISTS embeddings_organization_idx ON embeddings(organization_id);

-- Composite index for filtered vector search
CREATE INDEX IF NOT EXISTS embeddings_org_type_idx ON embeddings(organization_id, content_type);

-- Index for timestamp-based queries
CREATE INDEX IF NOT EXISTS embeddings_created_at_idx ON embeddings(created_at DESC);

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_embeddings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER embeddings_updated_at_trigger
    BEFORE UPDATE ON embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_embeddings_updated_at();

-- Create RPC function for vector similarity search
CREATE OR REPLACE FUNCTION vector_similarity_search(
    query_embedding vector(1536),
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

-- Create function to get embedding statistics
CREATE OR REPLACE FUNCTION get_embedding_stats(org_id UUID DEFAULT NULL)
RETURNS TABLE (
    content_type text,
    count bigint,
    avg_text_length float,
    latest_update timestamptz
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.content_type,
        COUNT(*)::bigint as count,
        AVG(LENGTH(e.content_text))::float as avg_text_length,
        MAX(e.updated_at) as latest_update
    FROM embeddings e
    WHERE org_id IS NULL OR e.organization_id = org_id
    GROUP BY e.content_type
    ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Create function to delete embeddings by content
CREATE OR REPLACE FUNCTION delete_content_embedding(
    p_content_type text,
    p_content_id text
)
RETURNS boolean AS $$
DECLARE
    deleted_count int;
BEGIN
    DELETE FROM embeddings 
    WHERE content_type = p_content_type 
    AND content_id = p_content_id;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count > 0;
END;
$$ LANGUAGE plpgsql;

-- Create function to batch delete embeddings
CREATE OR REPLACE FUNCTION batch_delete_embeddings(
    p_content_type text,
    p_content_ids text[]
)
RETURNS int AS $$
DECLARE
    deleted_count int;
BEGIN
    DELETE FROM embeddings 
    WHERE content_type = p_content_type 
    AND content_id = ANY(p_content_ids);
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON TABLE embeddings IS 'Stores vector embeddings for RAG (Retrieval-Augmented Generation) semantic search';
COMMENT ON COLUMN embeddings.content_type IS 'Type of content: project, portfolio, resource, risk, issue, document, knowledge_base';
COMMENT ON COLUMN embeddings.content_id IS 'ID of the content in its source table';
COMMENT ON COLUMN embeddings.content_text IS 'Text representation of the content used for embedding generation';
COMMENT ON COLUMN embeddings.embedding IS 'Vector embedding (1536 dimensions for OpenAI text-embedding-ada-002)';
COMMENT ON COLUMN embeddings.metadata IS 'Additional metadata about the content (name, status, etc.)';
COMMENT ON COLUMN embeddings.organization_id IS 'Organization ID for multi-tenancy filtering';

COMMENT ON FUNCTION vector_similarity_search IS 'Performs vector similarity search with optional filtering by content type and organization';
COMMENT ON FUNCTION get_embedding_stats IS 'Returns statistics about embeddings grouped by content type';
COMMENT ON FUNCTION delete_content_embedding IS 'Deletes a single embedding by content type and ID';
COMMENT ON FUNCTION batch_delete_embeddings IS 'Deletes multiple embeddings by content type and IDs';

-- Grant permissions (adjust based on your role setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON embeddings TO authenticated;
-- GRANT EXECUTE ON FUNCTION vector_similarity_search TO authenticated;
-- GRANT EXECUTE ON FUNCTION get_embedding_stats TO authenticated;
-- GRANT EXECUTE ON FUNCTION delete_content_embedding TO authenticated;
-- GRANT EXECUTE ON FUNCTION batch_delete_embeddings TO authenticated;
