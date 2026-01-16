-- Knowledge Base RAG System Migration
-- Creates comprehensive RAG-enhanced help chat system with vector embeddings,
-- semantic search, multi-language support, and knowledge management

-- =====================================================
-- ENABLE PGVECTOR EXTENSION
-- =====================================================

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- =====================================================
-- KNOWLEDGE BASE TABLES
-- =====================================================

-- Feature categories enum type
DO $$ BEGIN
    CREATE TYPE feature_category AS ENUM (
        'dashboard',
        'resource_management',
        'financial_tracking',
        'risk_management',
        'monte_carlo',
        'pmr',
        'change_management',
        'schedule_management',
        'ai_features',
        'collaboration',
        'audit_trails',
        'user_management',
        'general'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Knowledge documents table - stores documentation with metadata
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category feature_category NOT NULL,
    keywords TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    access_control JSONB DEFAULT '{"requiredRoles": [], "isPublic": true}',
    version VARCHAR(50) DEFAULT '1.0.0',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure title is unique per category
    CONSTRAINT unique_document_title_category UNIQUE (title, category)
);

-- Vector chunks table - stores document chunks with embeddings
CREATE TABLE IF NOT EXISTS vector_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI text-embedding-3-small dimension
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure unique chunk index per document
    CONSTRAINT unique_document_chunk_index UNIQUE (document_id, chunk_index),
    
    -- Ensure chunk_index is non-negative
    CONSTRAINT positive_chunk_index CHECK (chunk_index >= 0)
);

-- Query logs table - tracks all RAG queries for analytics and monitoring
CREATE TABLE IF NOT EXISTS query_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    query TEXT NOT NULL,
    query_language VARCHAR(5) DEFAULT 'en',
    retrieved_chunks JSONB DEFAULT '[]',
    response TEXT,
    response_language VARCHAR(5) DEFAULT 'en',
    citations JSONB DEFAULT '[]',
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    processing_time_ms INTEGER CHECK (processing_time_ms >= 0),
    feedback VARCHAR(20) CHECK (feedback IN ('helpful', 'not_helpful', 'incorrect')),
    user_context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- PERFORMANCE INDEXES
-- =====================================================

-- Knowledge documents indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_category ON knowledge_documents(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_keywords ON knowledge_documents USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_metadata ON knowledge_documents USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_created_at ON knowledge_documents(created_at);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_updated_at ON knowledge_documents(updated_at);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_version ON knowledge_documents(version);

-- Full-text search index for knowledge documents
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_search 
    ON knowledge_documents USING GIN(to_tsvector('english', title || ' ' || content));

-- Vector chunks indexes
CREATE INDEX IF NOT EXISTS idx_vector_chunks_document_id ON vector_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_vector_chunks_chunk_index ON vector_chunks(chunk_index);
CREATE INDEX IF NOT EXISTS idx_vector_chunks_metadata ON vector_chunks USING GIN(metadata);

-- Vector similarity search index (IVFFlat for efficient approximate nearest neighbor search)
CREATE INDEX IF NOT EXISTS idx_vector_chunks_embedding 
    ON vector_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Query logs indexes
CREATE INDEX IF NOT EXISTS idx_query_logs_user_id ON query_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_created_at ON query_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_query_logs_query_language ON query_logs(query_language);
CREATE INDEX IF NOT EXISTS idx_query_logs_confidence_score ON query_logs(confidence_score) WHERE confidence_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_query_logs_feedback ON query_logs(feedback) WHERE feedback IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_query_logs_user_context ON query_logs USING GIN(user_context);

-- =====================================================
-- TRIGGERS FOR UPDATED_AT TIMESTAMPS
-- =====================================================

-- Create or replace the update_updated_at_column function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to knowledge_documents table
CREATE TRIGGER update_knowledge_documents_updated_at 
    BEFORE UPDATE ON knowledge_documents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- KNOWLEDGE BASE FUNCTIONS
-- =====================================================

-- Function to perform semantic search on vector chunks
CREATE OR REPLACE FUNCTION semantic_search(
    query_embedding vector(1536),
    top_k INTEGER DEFAULT 5,
    filter_category feature_category DEFAULT NULL,
    filter_roles TEXT[] DEFAULT NULL
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    document_title VARCHAR(500),
    category feature_category,
    content TEXT,
    similarity FLOAT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        vc.id as chunk_id,
        vc.document_id,
        kd.title as document_title,
        kd.category,
        vc.content,
        1 - (vc.embedding <=> query_embedding) as similarity,
        vc.metadata
    FROM vector_chunks vc
    JOIN knowledge_documents kd ON vc.document_id = kd.id
    WHERE 
        (filter_category IS NULL OR kd.category = filter_category)
        AND (
            filter_roles IS NULL 
            OR (kd.access_control->>'isPublic')::BOOLEAN = true
            OR kd.access_control->'requiredRoles' ?| filter_roles
        )
    ORDER BY vc.embedding <=> query_embedding
    LIMIT top_k;
END;
$$ LANGUAGE plpgsql;

-- Function to get document statistics
CREATE OR REPLACE FUNCTION get_knowledge_base_stats()
RETURNS TABLE (
    total_documents BIGINT,
    total_chunks BIGINT,
    documents_by_category JSONB,
    avg_chunks_per_document NUMERIC,
    last_updated TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT kd.id) as total_documents,
        COUNT(vc.id) as total_chunks,
        jsonb_object_agg(
            kd.category::TEXT, 
            COUNT(DISTINCT kd.id)
        ) as documents_by_category,
        ROUND(COUNT(vc.id)::NUMERIC / NULLIF(COUNT(DISTINCT kd.id), 0), 2) as avg_chunks_per_document,
        MAX(kd.updated_at) as last_updated
    FROM knowledge_documents kd
    LEFT JOIN vector_chunks vc ON kd.id = vc.document_id
    GROUP BY ();
END;
$$ LANGUAGE plpgsql;

-- Function to get query analytics
CREATE OR REPLACE FUNCTION get_query_analytics(
    start_date TIMESTAMP WITH TIME ZONE DEFAULT NOW() - INTERVAL '30 days',
    end_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
)
RETURNS TABLE (
    total_queries BIGINT,
    avg_confidence NUMERIC,
    avg_processing_time_ms NUMERIC,
    feedback_distribution JSONB,
    top_languages TEXT[],
    queries_by_day JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_queries,
        ROUND(AVG(confidence_score), 3) as avg_confidence,
        ROUND(AVG(processing_time_ms), 2) as avg_processing_time_ms,
        jsonb_object_agg(
            COALESCE(feedback, 'no_feedback'),
            COUNT(*)
        ) FILTER (WHERE feedback IS NOT NULL OR feedback IS NULL) as feedback_distribution,
        ARRAY_AGG(DISTINCT query_language ORDER BY COUNT(*) DESC) as top_languages,
        jsonb_object_agg(
            DATE(created_at)::TEXT,
            COUNT(*)
        ) as queries_by_day
    FROM query_logs
    WHERE created_at BETWEEN start_date AND end_date
    GROUP BY ();
END;
$$ LANGUAGE plpgsql;

-- Function to identify documentation gaps
CREATE OR REPLACE FUNCTION identify_documentation_gaps(
    min_query_count INTEGER DEFAULT 5,
    days_back INTEGER DEFAULT 30
)
RETURNS TABLE (
    query_pattern TEXT,
    query_count BIGINT,
    avg_confidence NUMERIC,
    negative_feedback_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        LOWER(SUBSTRING(query FROM 1 FOR 100)) as query_pattern,
        COUNT(*) as query_count,
        ROUND(AVG(confidence_score), 3) as avg_confidence,
        ROUND(
            COUNT(CASE WHEN feedback = 'not_helpful' OR feedback = 'incorrect' THEN 1 END)::NUMERIC / 
            NULLIF(COUNT(*), 0) * 100, 1
        ) as negative_feedback_rate
    FROM query_logs
    WHERE created_at > NOW() - INTERVAL '1 day' * days_back
    AND (confidence_score < 0.7 OR feedback IN ('not_helpful', 'incorrect'))
    GROUP BY LOWER(SUBSTRING(query FROM 1 FOR 100))
    HAVING COUNT(*) >= min_query_count
    ORDER BY query_count DESC, avg_confidence ASC;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old query logs (privacy compliance)
CREATE OR REPLACE FUNCTION cleanup_old_query_logs(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete query logs older than retention period
    WITH deleted_logs AS (
        DELETE FROM query_logs 
        WHERE created_at < NOW() - INTERVAL '1 day' * retention_days
        RETURNING id
    )
    SELECT COUNT(*) INTO deleted_count FROM deleted_logs;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- View for knowledge documents with chunk counts
CREATE OR REPLACE VIEW v_knowledge_documents_with_chunks AS
SELECT 
    kd.id,
    kd.title,
    kd.category,
    kd.keywords,
    kd.version,
    kd.created_at,
    kd.updated_at,
    COUNT(vc.id) as chunk_count,
    kd.access_control
FROM knowledge_documents kd
LEFT JOIN vector_chunks vc ON kd.id = vc.document_id
GROUP BY kd.id, kd.title, kd.category, kd.keywords, kd.version, 
         kd.created_at, kd.updated_at, kd.access_control;

-- View for query logs with feedback metrics
CREATE OR REPLACE VIEW v_query_logs_with_metrics AS
SELECT 
    DATE_TRUNC('day', created_at) as query_date,
    query_language,
    COUNT(*) as query_count,
    AVG(confidence_score) as avg_confidence,
    AVG(processing_time_ms) as avg_processing_time_ms,
    COUNT(CASE WHEN feedback = 'helpful' THEN 1 END) as helpful_count,
    COUNT(CASE WHEN feedback = 'not_helpful' THEN 1 END) as not_helpful_count,
    COUNT(CASE WHEN feedback = 'incorrect' THEN 1 END) as incorrect_count
FROM query_logs
WHERE created_at > NOW() - INTERVAL '90 days'
GROUP BY DATE_TRUNC('day', created_at), query_language
ORDER BY query_date DESC;

-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

-- Enable RLS on knowledge base tables
ALTER TABLE knowledge_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE vector_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_logs ENABLE ROW LEVEL SECURITY;

-- Knowledge documents policies - all authenticated users can read
CREATE POLICY knowledge_documents_read_policy ON knowledge_documents
    FOR SELECT USING (
        auth.uid() IS NOT NULL
        AND (
            (access_control->>'isPublic')::BOOLEAN = true
            OR EXISTS (
                SELECT 1 FROM user_profiles up
                WHERE up.user_id = auth.uid()
                AND up.role::TEXT = ANY(
                    SELECT jsonb_array_elements_text(access_control->'requiredRoles')
                )
            )
        )
    );

-- Knowledge documents admin policies - admins can manage documents
CREATE POLICY knowledge_documents_admin_policy ON knowledge_documents
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_profiles up
            WHERE up.user_id = auth.uid()
            AND up.role IN ('admin', 'content_manager')
        )
    );

-- Vector chunks policies - follow document access control
CREATE POLICY vector_chunks_read_policy ON vector_chunks
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM knowledge_documents kd
            WHERE kd.id = vector_chunks.document_id
            AND (
                (kd.access_control->>'isPublic')::BOOLEAN = true
                OR EXISTS (
                    SELECT 1 FROM user_profiles up
                    WHERE up.user_id = auth.uid()
                    AND up.role::TEXT = ANY(
                        SELECT jsonb_array_elements_text(kd.access_control->'requiredRoles')
                    )
                )
            )
        )
    );

-- Vector chunks admin policies - admins can manage chunks
CREATE POLICY vector_chunks_admin_policy ON vector_chunks
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_profiles up
            WHERE up.user_id = auth.uid()
            AND up.role IN ('admin', 'content_manager')
        )
    );

-- Query logs policies - users can only access their own logs
CREATE POLICY query_logs_user_policy ON query_logs
    FOR SELECT USING (auth.uid() = user_id);

-- Query logs admin policies - admins can view all logs
CREATE POLICY query_logs_admin_policy ON query_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_profiles up
            WHERE up.user_id = auth.uid()
            AND up.role = 'admin'
        )
    );

-- =====================================================
-- COMMENTS AND DOCUMENTATION
-- =====================================================

COMMENT ON TABLE knowledge_documents IS 'Knowledge base documents with metadata and access control';
COMMENT ON TABLE vector_chunks IS 'Document chunks with vector embeddings for semantic search';
COMMENT ON TABLE query_logs IS 'RAG query logs for analytics and monitoring';

COMMENT ON FUNCTION semantic_search(vector(1536), INTEGER, feature_category, TEXT[]) IS 'Performs semantic similarity search on vector chunks';
COMMENT ON FUNCTION get_knowledge_base_stats() IS 'Returns knowledge base statistics and metrics';
COMMENT ON FUNCTION get_query_analytics(TIMESTAMP WITH TIME ZONE, TIMESTAMP WITH TIME ZONE) IS 'Returns query analytics for specified date range';
COMMENT ON FUNCTION identify_documentation_gaps(INTEGER, INTEGER) IS 'Identifies potential documentation gaps based on low-confidence queries';
COMMENT ON FUNCTION cleanup_old_query_logs(INTEGER) IS 'Removes old query logs for privacy compliance';

COMMENT ON VIEW v_knowledge_documents_with_chunks IS 'Knowledge documents with chunk counts';
COMMENT ON VIEW v_query_logs_with_metrics IS 'Query logs with aggregated feedback metrics';

-- =====================================================
-- INITIAL DATA SETUP
-- =====================================================

-- Update table statistics for query optimization
ANALYZE knowledge_documents;
ANALYZE vector_chunks;
ANALYZE query_logs;

COMMIT;
