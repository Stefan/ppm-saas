-- Enhanced Project Monthly Report (PMR) Schema Migration
-- Migration: 021_enhanced_pmr_schema.sql
-- Description: Complete schema for AI-powered PMR system with interactive editing,
--              real-time collaboration, multi-format export, and Monte Carlo integration
-- Dependencies: Requires projects table, auth.users table, and Monte Carlo tables

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search optimization

-- ============================================================================
-- ENUMS AND TYPES
-- ============================================================================

-- Create custom types for better type safety
DO $$ BEGIN
    CREATE TYPE pmr_status AS ENUM ('draft', 'review', 'approved', 'distributed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE pmr_template_type AS ENUM ('executive', 'technical', 'financial', 'custom');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE ai_insight_type AS ENUM ('prediction', 'recommendation', 'alert', 'summary');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE ai_insight_category AS ENUM ('budget', 'schedule', 'resource', 'risk', 'quality');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE ai_insight_priority AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE validation_status AS ENUM ('pending', 'validated', 'rejected', 'needs_review');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE session_type AS ENUM ('chat', 'direct', 'collaborative');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;


DO $$ BEGIN
    CREATE TYPE participant_role AS ENUM ('owner', 'editor', 'commenter', 'viewer');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE export_format AS ENUM ('pdf', 'excel', 'slides', 'word', 'powerpoint');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE export_job_status AS ENUM ('queued', 'processing', 'completed', 'failed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE change_event_type AS ENUM ('section_update', 'content_edit', 'comment_added', 'insight_validated', 'cursor_move');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE collaboration_action_type AS ENUM ('view', 'edit', 'comment', 'approve', 'reject');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE distribution_method AS ENUM ('email', 'slack', 'teams', 'portal', 'download');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE distribution_status AS ENUM ('pending', 'sent', 'delivered', 'failed', 'bounced');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- TABLE CREATION (in dependency order)
-- ============================================================================

-- PMR Templates Table (must be created first due to foreign key dependencies)
CREATE TABLE IF NOT EXISTS pmr_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_type pmr_template_type NOT NULL,
    industry_focus VARCHAR(100),
    sections JSONB NOT NULL DEFAULT '[]',
    default_metrics JSONB DEFAULT '[]',
    ai_suggestions JSONB DEFAULT '{}',
    branding_config JSONB DEFAULT '{}',
    export_formats JSONB DEFAULT '[]',
    is_public BOOLEAN DEFAULT FALSE,
    created_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    organization_id UUID,
    usage_count INTEGER DEFAULT 0 CHECK (usage_count >= 0),
    rating DECIMAL(3,2) CHECK (rating >= 0.0 AND rating <= 5.0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


-- PMR Reports Table (Enhanced with AI and collaboration features)
CREATE TABLE IF NOT EXISTS pmr_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    report_month DATE NOT NULL,
    report_year INTEGER NOT NULL CHECK (report_year >= 2020 AND report_year <= 2030),
    template_id UUID NOT NULL REFERENCES pmr_templates(id) ON DELETE RESTRICT,
    title VARCHAR(255) NOT NULL,
    executive_summary TEXT,
    
    -- AI-powered features
    ai_generated_insights JSONB DEFAULT '[]',
    ai_generated_summary TEXT,
    ai_confidence_scores JSONB DEFAULT '{}',
    ai_insight_engine_config JSONB DEFAULT '{}',
    last_ai_update TIMESTAMP WITH TIME ZONE,
    ai_processing_time_seconds DECIMAL(10,3),
    
    -- Content and structure
    sections JSONB NOT NULL DEFAULT '[]',
    metrics JSONB DEFAULT '{}',
    visualizations JSONB DEFAULT '[]',
    
    -- Monte Carlo analysis
    monte_carlo_analysis JSONB,
    monte_carlo_enabled BOOLEAN DEFAULT FALSE,
    monte_carlo_simulation_id UUID REFERENCES monte_carlo_simulations(id) ON DELETE SET NULL,
    
    -- Collaboration features
    collaboration_enabled BOOLEAN DEFAULT FALSE,
    collaboration_session_id UUID,
    last_collaboration_activity TIMESTAMP WITH TIME ZONE,
    total_collaborators INTEGER DEFAULT 0 CHECK (total_collaborators >= 0),
    
    -- Export and template features
    export_history JSONB DEFAULT '[]',
    template_customizations JSONB DEFAULT '{}',
    
    -- Real-time metrics
    real_time_metrics JSONB,
    metrics_refresh_interval_seconds INTEGER DEFAULT 300 CHECK (metrics_refresh_interval_seconds >= 60 AND metrics_refresh_interval_seconds <= 3600),
    
    -- Status and workflow
    status pmr_status DEFAULT 'draft',
    generated_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE RESTRICT,
    approved_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    
    -- Timestamps
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Version control
    version INTEGER DEFAULT 1 CHECK (version >= 1),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Performance tracking
    generation_time_seconds DECIMAL(10,3),
    total_edits INTEGER DEFAULT 0 CHECK (total_edits >= 0),
    
    -- Audit trail
    audit_log JSONB DEFAULT '[]',
    
    UNIQUE(project_id, report_month, report_year, version)
);


-- AI Insights Table (Enhanced with validation and feedback)
CREATE TABLE IF NOT EXISTS ai_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES pmr_reports(id) ON DELETE CASCADE,
    
    -- Insight classification
    insight_type ai_insight_type NOT NULL,
    category ai_insight_category NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    
    -- Confidence and validation
    confidence_score DECIMAL(3,2) NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    validation_status validation_status DEFAULT 'pending',
    validated_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    validated_at TIMESTAMP WITH TIME ZONE,
    
    -- Supporting data and recommendations
    supporting_data JSONB DEFAULT '{}',
    predicted_impact TEXT,
    recommended_actions JSONB DEFAULT '[]',
    priority ai_insight_priority DEFAULT 'medium',
    
    -- User feedback
    feedback_score DECIMAL(3,2) CHECK (feedback_score >= 0.0 AND feedback_score <= 5.0),
    user_feedback TEXT,
    impact_score DECIMAL(3,2) CHECK (impact_score >= 0.0 AND impact_score <= 1.0),
    
    -- Relationships and metadata
    related_insights JSONB DEFAULT '[]',
    data_sources JSONB DEFAULT '[]',
    refresh_frequency VARCHAR(20), -- 'real-time', 'hourly', 'daily'
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Legacy fields for backward compatibility
    validated BOOLEAN GENERATED ALWAYS AS (validation_status = 'validated') STORED,
    validation_notes TEXT
);

-- Collaboration Sessions Table (for real-time collaborative editing)
CREATE TABLE IF NOT EXISTS collaboration_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    report_id UUID NOT NULL REFERENCES pmr_reports(id) ON DELETE CASCADE,
    
    -- Session configuration
    session_type session_type DEFAULT 'collaborative',
    max_participants INTEGER DEFAULT 10 CHECK (max_participants >= 1 AND max_participants <= 50),
    conflict_resolution_strategy VARCHAR(50) DEFAULT 'last_write_wins' CHECK (conflict_resolution_strategy IN ('last_write_wins', 'manual', 'merge')),
    session_timeout_minutes INTEGER DEFAULT 60 CHECK (session_timeout_minutes >= 5 AND session_timeout_minutes <= 480),
    
    -- Participants and activity
    participants JSONB DEFAULT '[]',
    active_editors JSONB DEFAULT '[]',
    locked_sections JSONB DEFAULT '{}',
    
    -- Change tracking
    changes_log JSONB DEFAULT '[]',
    comments JSONB DEFAULT '[]',
    version_history JSONB DEFAULT '[]',
    
    -- Session state
    is_active BOOLEAN DEFAULT TRUE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


-- Interactive Edit Sessions Table (for tracking individual editing sessions)
CREATE TABLE IF NOT EXISTS edit_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES pmr_reports(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Session details
    session_type session_type DEFAULT 'chat',
    chat_messages JSONB DEFAULT '[]',
    changes_made JSONB DEFAULT '[]',
    active_section VARCHAR(100),
    
    -- Session state
    is_active BOOLEAN DEFAULT TRUE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Export Jobs Table (for multi-format export management)
CREATE TABLE IF NOT EXISTS export_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES pmr_reports(id) ON DELETE CASCADE,
    
    -- Export configuration
    export_format export_format NOT NULL,
    template_config JSONB DEFAULT '{}',
    export_options JSONB DEFAULT '{}',
    
    -- Job status
    status export_job_status DEFAULT 'queued',
    file_url TEXT,
    file_size INTEGER CHECK (file_size >= 0),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0),
    
    -- User and timestamps
    requested_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE RESTRICT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- PMR Collaboration Activity Log (for tracking all collaboration actions)
CREATE TABLE IF NOT EXISTS pmr_collaboration (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES pmr_reports(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Action details
    action_type collaboration_action_type NOT NULL,
    section_id VARCHAR(100),
    change_description TEXT,
    change_data JSONB DEFAULT '{}',
    
    -- Timestamps
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- PMR Distribution Log Table (for tracking report distribution)
CREATE TABLE IF NOT EXISTS pmr_distribution_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES pmr_reports(id) ON DELETE CASCADE,
    
    -- Distribution details
    distribution_method distribution_method NOT NULL,
    recipient_type VARCHAR(50) NOT NULL CHECK (recipient_type IN ('user', 'group', 'external')),
    recipient_identifier VARCHAR(255) NOT NULL,
    
    -- Status tracking
    status distribution_status DEFAULT 'pending',
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


-- Comments Table (for section-level comments and discussions)
CREATE TABLE IF NOT EXISTS pmr_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    comment_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES pmr_reports(id) ON DELETE CASCADE,
    section_id VARCHAR(100) NOT NULL,
    
    -- Comment details
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    user_name VARCHAR(255) NOT NULL,
    content TEXT NOT NULL CHECK (LENGTH(content) > 0 AND LENGTH(content) <= 5000),
    
    -- Threading
    parent_comment_id UUID REFERENCES pmr_comments(comment_id) ON DELETE CASCADE,
    
    -- Resolution
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_note TEXT,
    
    -- Mentions and attachments
    mentions JSONB DEFAULT '[]',
    attachments JSONB DEFAULT '[]',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Change Events Table (for detailed change tracking)
CREATE TABLE IF NOT EXISTS pmr_change_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES pmr_reports(id) ON DELETE CASCADE,
    session_id UUID REFERENCES collaboration_sessions(id) ON DELETE SET NULL,
    
    -- Event details
    event_type change_event_type NOT NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    user_name VARCHAR(255) NOT NULL,
    section_id VARCHAR(100),
    
    -- Change data
    changes JSONB DEFAULT '{}',
    previous_value JSONB,
    new_value JSONB,
    metadata JSONB DEFAULT '{}',
    
    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- ============================================================================

-- PMR Reports Indexes
CREATE INDEX IF NOT EXISTS idx_pmr_reports_project_month ON pmr_reports(project_id, report_month DESC, report_year DESC);
CREATE INDEX IF NOT EXISTS idx_pmr_reports_status ON pmr_reports(status, generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_pmr_reports_template ON pmr_reports(template_id);
CREATE INDEX IF NOT EXISTS idx_pmr_reports_generated_by ON pmr_reports(generated_by);
CREATE INDEX IF NOT EXISTS idx_pmr_reports_active ON pmr_reports(project_id, is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_pmr_reports_year_month ON pmr_reports(report_year, report_month);
CREATE INDEX IF NOT EXISTS idx_pmr_reports_collaboration ON pmr_reports(collaboration_session_id) WHERE collaboration_enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_pmr_reports_monte_carlo ON pmr_reports(monte_carlo_simulation_id) WHERE monte_carlo_enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_pmr_reports_last_modified ON pmr_reports(last_modified DESC);

-- PMR Templates Indexes
CREATE INDEX IF NOT EXISTS idx_pmr_templates_type ON pmr_templates(template_type, is_public);
CREATE INDEX IF NOT EXISTS idx_pmr_templates_created_by ON pmr_templates(created_by);
CREATE INDEX IF NOT EXISTS idx_pmr_templates_organization ON pmr_templates(organization_id) WHERE organization_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_pmr_templates_usage ON pmr_templates(usage_count DESC, rating DESC);
CREATE INDEX IF NOT EXISTS idx_pmr_templates_public ON pmr_templates(is_public, template_type) WHERE is_public = TRUE;
CREATE INDEX IF NOT EXISTS idx_pmr_templates_name_trgm ON pmr_templates USING gin(name gin_trgm_ops);


-- AI Insights Indexes
CREATE INDEX IF NOT EXISTS idx_ai_insights_report ON ai_insights(report_id, priority DESC, generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_insights_type_category ON ai_insights(insight_type, category);
CREATE INDEX IF NOT EXISTS idx_ai_insights_confidence ON ai_insights(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_ai_insights_validated ON ai_insights(report_id, validation_status);
CREATE INDEX IF NOT EXISTS idx_ai_insights_priority ON ai_insights(priority, generated_at DESC) WHERE priority IN ('high', 'critical');
CREATE INDEX IF NOT EXISTS idx_ai_insights_expires ON ai_insights(expires_at) WHERE expires_at IS NOT NULL;

-- Collaboration Sessions Indexes
CREATE INDEX IF NOT EXISTS idx_collaboration_sessions_report ON collaboration_sessions(report_id, is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_collaboration_sessions_session_id ON collaboration_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_collaboration_sessions_active ON collaboration_sessions(is_active, last_activity DESC) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_collaboration_sessions_started ON collaboration_sessions(started_at DESC);

-- Edit Sessions Indexes
CREATE INDEX IF NOT EXISTS idx_edit_sessions_report ON edit_sessions(report_id, is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_edit_sessions_user ON edit_sessions(user_id, last_activity DESC);
CREATE INDEX IF NOT EXISTS idx_edit_sessions_active ON edit_sessions(is_active, last_activity DESC) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_edit_sessions_report_user ON edit_sessions(report_id, user_id);

-- Export Jobs Indexes
CREATE INDEX IF NOT EXISTS idx_export_jobs_report ON export_jobs(report_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_export_jobs_status ON export_jobs(status, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_export_jobs_requested_by ON export_jobs(requested_by, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_export_jobs_format ON export_jobs(export_format, status);
CREATE INDEX IF NOT EXISTS idx_export_jobs_pending ON export_jobs(status, started_at) WHERE status IN ('queued', 'processing');

-- Collaboration Activity Indexes
CREATE INDEX IF NOT EXISTS idx_pmr_collaboration_report ON pmr_collaboration(report_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_pmr_collaboration_user ON pmr_collaboration(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_pmr_collaboration_action ON pmr_collaboration(action_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_pmr_collaboration_section ON pmr_collaboration(report_id, section_id, timestamp DESC);

-- Distribution Log Indexes
CREATE INDEX IF NOT EXISTS idx_pmr_distribution_report ON pmr_distribution_log(report_id, sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_pmr_distribution_status ON pmr_distribution_log(status, sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_pmr_distribution_method ON pmr_distribution_log(distribution_method, status);
CREATE INDEX IF NOT EXISTS idx_pmr_distribution_recipient ON pmr_distribution_log(recipient_identifier, status);

-- Comments Indexes
CREATE INDEX IF NOT EXISTS idx_pmr_comments_report ON pmr_comments(report_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pmr_comments_section ON pmr_comments(report_id, section_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pmr_comments_user ON pmr_comments(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pmr_comments_unresolved ON pmr_comments(report_id, resolved) WHERE resolved = FALSE;
CREATE INDEX IF NOT EXISTS idx_pmr_comments_parent ON pmr_comments(parent_comment_id) WHERE parent_comment_id IS NOT NULL;

-- Change Events Indexes
CREATE INDEX IF NOT EXISTS idx_pmr_change_events_report ON pmr_change_events(report_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_pmr_change_events_session ON pmr_change_events(session_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_pmr_change_events_user ON pmr_change_events(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_pmr_change_events_type ON pmr_change_events(event_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_pmr_change_events_section ON pmr_change_events(report_id, section_id, timestamp DESC);


-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- ============================================================================

-- Create or replace the update function (reuse existing if available)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers to all PMR tables
DROP TRIGGER IF EXISTS update_pmr_reports_updated_at ON pmr_reports;
CREATE TRIGGER update_pmr_reports_updated_at 
    BEFORE UPDATE ON pmr_reports 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_pmr_templates_updated_at ON pmr_templates;
CREATE TRIGGER update_pmr_templates_updated_at 
    BEFORE UPDATE ON pmr_templates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_ai_insights_updated_at ON ai_insights;
CREATE TRIGGER update_ai_insights_updated_at 
    BEFORE UPDATE ON ai_insights 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_collaboration_sessions_updated_at ON collaboration_sessions;
CREATE TRIGGER update_collaboration_sessions_updated_at 
    BEFORE UPDATE ON collaboration_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_edit_sessions_updated_at ON edit_sessions;
CREATE TRIGGER update_edit_sessions_updated_at 
    BEFORE UPDATE ON edit_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_export_jobs_updated_at ON export_jobs;
CREATE TRIGGER update_export_jobs_updated_at 
    BEFORE UPDATE ON export_jobs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_pmr_distribution_log_updated_at ON pmr_distribution_log;
CREATE TRIGGER update_pmr_distribution_log_updated_at 
    BEFORE UPDATE ON pmr_distribution_log 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_pmr_comments_updated_at ON pmr_comments;
CREATE TRIGGER update_pmr_comments_updated_at 
    BEFORE UPDATE ON pmr_comments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update last_modified on pmr_reports when related data changes
CREATE OR REPLACE FUNCTION update_pmr_report_last_modified()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the parent report's last_modified timestamp
    UPDATE pmr_reports 
    SET last_modified = NOW() 
    WHERE id = COALESCE(NEW.report_id, OLD.report_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ language 'plpgsql';

-- Apply to related tables
DROP TRIGGER IF EXISTS update_pmr_report_on_insight_change ON ai_insights;
CREATE TRIGGER update_pmr_report_on_insight_change 
    AFTER INSERT OR UPDATE OR DELETE ON ai_insights 
    FOR EACH ROW EXECUTE FUNCTION update_pmr_report_last_modified();

DROP TRIGGER IF EXISTS update_pmr_report_on_collaboration_change ON pmr_collaboration;
CREATE TRIGGER update_pmr_report_on_collaboration_change 
    AFTER INSERT OR UPDATE ON pmr_collaboration 
    FOR EACH ROW EXECUTE FUNCTION update_pmr_report_last_modified();

DROP TRIGGER IF EXISTS update_pmr_report_on_comment_change ON pmr_comments;
CREATE TRIGGER update_pmr_report_on_comment_change 
    AFTER INSERT OR UPDATE ON pmr_comments 
    FOR EACH ROW EXECUTE FUNCTION update_pmr_report_last_modified();


-- Trigger to update template usage count
CREATE OR REPLACE FUNCTION update_template_usage_count()
RETURNS TRIGGER AS $$
BEGIN
    -- Increment usage count when a new report is created with this template
    IF TG_OP = 'INSERT' THEN
        UPDATE pmr_templates 
        SET usage_count = usage_count + 1 
        WHERE id = NEW.template_id;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_template_usage_on_report_create ON pmr_reports;
CREATE TRIGGER update_template_usage_on_report_create 
    AFTER INSERT ON pmr_reports 
    FOR EACH ROW EXECUTE FUNCTION update_template_usage_count();

-- Trigger to update edit session activity
CREATE OR REPLACE FUNCTION update_edit_session_activity()
RETURNS TRIGGER AS $$
BEGIN
    -- Update last_activity timestamp when session data changes
    NEW.last_activity = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_edit_session_activity_trigger ON edit_sessions;
CREATE TRIGGER update_edit_session_activity_trigger 
    BEFORE UPDATE ON edit_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_edit_session_activity();

-- Trigger to update collaboration session activity
CREATE OR REPLACE FUNCTION update_collaboration_session_activity()
RETURNS TRIGGER AS $$
BEGIN
    -- Update last_activity timestamp when session data changes
    NEW.last_activity = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_collaboration_session_activity_trigger ON collaboration_sessions;
CREATE TRIGGER update_collaboration_session_activity_trigger 
    BEFORE UPDATE ON collaboration_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_collaboration_session_activity();

-- Trigger to validate export job status transitions
CREATE OR REPLACE FUNCTION validate_export_job_status() 
RETURNS TRIGGER AS $$
DECLARE
    old_status export_job_status;
    new_status export_job_status;
BEGIN
    old_status := OLD.status;
    new_status := NEW.status;
    
    -- Allow any transition from queued
    IF old_status = 'queued' THEN
        RETURN NEW;
    END IF;
    
    -- Allow processing -> completed or failed
    IF old_status = 'processing' AND new_status IN ('completed', 'failed') THEN
        RETURN NEW;
    END IF;
    
    -- Allow failed -> queued (for retry)
    IF old_status = 'failed' AND new_status = 'queued' THEN
        RETURN NEW;
    END IF;
    
    -- Prevent invalid transitions
    IF old_status = 'completed' THEN
        RAISE EXCEPTION 'Cannot change status from % to %', old_status, new_status;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS validate_export_job_status_trigger ON export_jobs;
CREATE TRIGGER validate_export_job_status_trigger
    BEFORE UPDATE ON export_jobs
    FOR EACH ROW EXECUTE FUNCTION validate_export_job_status();

-- Trigger to increment total_edits on pmr_reports
CREATE OR REPLACE FUNCTION increment_report_edit_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' AND NEW.action_type = 'edit' THEN
        UPDATE pmr_reports 
        SET total_edits = total_edits + 1 
        WHERE id = NEW.report_id;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS increment_report_edit_count_trigger ON pmr_collaboration;
CREATE TRIGGER increment_report_edit_count_trigger 
    AFTER INSERT ON pmr_collaboration 
    FOR EACH ROW EXECUTE FUNCTION increment_report_edit_count();


-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Function to get the latest PMR report for a project
CREATE OR REPLACE FUNCTION get_latest_pmr_report(p_project_id UUID)
RETURNS TABLE (
    report_id UUID,
    report_month DATE,
    report_year INTEGER,
    title VARCHAR(255),
    status pmr_status,
    generated_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        r.report_month,
        r.report_year,
        r.title,
        r.status,
        r.generated_at
    FROM pmr_reports r
    WHERE r.project_id = p_project_id 
      AND r.is_active = TRUE
    ORDER BY r.report_year DESC, r.report_month DESC, r.version DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate PMR report completeness score
CREATE OR REPLACE FUNCTION calculate_pmr_completeness(p_report_id UUID)
RETURNS DECIMAL(3,2) AS $$
DECLARE
    total_sections INTEGER := 0;
    completed_sections INTEGER := 0;
    has_executive_summary BOOLEAN := FALSE;
    has_insights BOOLEAN := FALSE;
    has_monte_carlo BOOLEAN := FALSE;
    completeness_score DECIMAL(3,2);
BEGIN
    -- Check if report exists
    IF NOT EXISTS (SELECT 1 FROM pmr_reports WHERE id = p_report_id) THEN
        RETURN 0.0;
    END IF;
    
    -- Get report data
    SELECT 
        CASE WHEN executive_summary IS NOT NULL AND LENGTH(TRIM(executive_summary)) > 0 THEN TRUE ELSE FALSE END,
        CASE WHEN jsonb_array_length(ai_generated_insights) > 0 THEN TRUE ELSE FALSE END,
        CASE WHEN monte_carlo_analysis IS NOT NULL THEN TRUE ELSE FALSE END,
        jsonb_array_length(sections)
    INTO has_executive_summary, has_insights, has_monte_carlo, total_sections
    FROM pmr_reports 
    WHERE id = p_report_id;
    
    -- Count completed sections (sections with content)
    SELECT COUNT(*)
    INTO completed_sections
    FROM pmr_reports r,
         jsonb_array_elements(r.sections) AS section
    WHERE r.id = p_report_id
      AND jsonb_typeof(section->'content') = 'string'
      AND LENGTH(TRIM(section->>'content')) > 0;
    
    -- Calculate completeness score
    completeness_score := 0.0;
    
    -- Executive summary (25% weight)
    IF has_executive_summary THEN
        completeness_score := completeness_score + 0.25;
    END IF;
    
    -- AI insights (20% weight)
    IF has_insights THEN
        completeness_score := completeness_score + 0.20;
    END IF;
    
    -- Monte Carlo analysis (15% weight)
    IF has_monte_carlo THEN
        completeness_score := completeness_score + 0.15;
    END IF;
    
    -- Sections completion (40% weight)
    IF total_sections > 0 THEN
        completeness_score := completeness_score + (0.40 * completed_sections / total_sections);
    END IF;
    
    RETURN LEAST(completeness_score, 1.0);
END;
$$ LANGUAGE plpgsql;


-- Function to clean up old edit sessions
CREATE OR REPLACE FUNCTION cleanup_old_edit_sessions(p_days_old INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    sessions_cleaned INTEGER;
BEGIN
    -- Mark old inactive sessions as inactive and clean up data
    UPDATE edit_sessions 
    SET 
        is_active = FALSE,
        ended_at = COALESCE(ended_at, last_activity),
        chat_messages = '[]',
        changes_made = '[]'
    WHERE 
        last_activity < NOW() - INTERVAL '1 day' * p_days_old
        AND is_active = TRUE;
    
    GET DIAGNOSTICS sessions_cleaned = ROW_COUNT;
    
    RETURN sessions_cleaned;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old collaboration sessions
CREATE OR REPLACE FUNCTION cleanup_old_collaboration_sessions(p_hours_old INTEGER DEFAULT 24)
RETURNS INTEGER AS $$
DECLARE
    sessions_cleaned INTEGER;
BEGIN
    -- Mark old inactive sessions as inactive
    UPDATE collaboration_sessions 
    SET 
        is_active = FALSE,
        ended_at = COALESCE(ended_at, last_activity)
    WHERE 
        last_activity < NOW() - INTERVAL '1 hour' * p_hours_old
        AND is_active = TRUE;
    
    GET DIAGNOSTICS sessions_cleaned = ROW_COUNT;
    
    RETURN sessions_cleaned;
END;
$$ LANGUAGE plpgsql;

-- Function to get active collaborators for a report
CREATE OR REPLACE FUNCTION get_active_collaborators(p_report_id UUID)
RETURNS TABLE (
    user_id UUID,
    user_name VARCHAR(255),
    role participant_role,
    last_active TIMESTAMP WITH TIME ZONE,
    current_section VARCHAR(100)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (participant->>'user_id')::UUID,
        participant->>'user_name',
        (participant->>'role')::participant_role,
        (participant->>'last_active')::TIMESTAMP WITH TIME ZONE,
        participant->>'current_section'
    FROM collaboration_sessions cs,
         jsonb_array_elements(cs.participants) AS participant
    WHERE cs.report_id = p_report_id
      AND cs.is_active = TRUE
      AND (participant->>'is_online')::BOOLEAN = TRUE
    ORDER BY (participant->>'last_active')::TIMESTAMP WITH TIME ZONE DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get unresolved comments for a report
CREATE OR REPLACE FUNCTION get_unresolved_comments(p_report_id UUID)
RETURNS TABLE (
    comment_id UUID,
    section_id VARCHAR(100),
    user_name VARCHAR(255),
    content TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    reply_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.comment_id,
        c.section_id,
        c.user_name,
        c.content,
        c.created_at,
        (SELECT COUNT(*)::INTEGER 
         FROM pmr_comments replies 
         WHERE replies.parent_comment_id = c.comment_id) AS reply_count
    FROM pmr_comments c
    WHERE c.report_id = p_report_id
      AND c.resolved = FALSE
      AND c.parent_comment_id IS NULL
    ORDER BY c.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get AI insights summary for a report
CREATE OR REPLACE FUNCTION get_ai_insights_summary(p_report_id UUID)
RETURNS TABLE (
    category ai_insight_category,
    total_insights INTEGER,
    critical_insights INTEGER,
    high_priority_insights INTEGER,
    validated_insights INTEGER,
    avg_confidence DECIMAL(3,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ai.category,
        COUNT(*)::INTEGER AS total_insights,
        COUNT(*) FILTER (WHERE ai.priority = 'critical')::INTEGER AS critical_insights,
        COUNT(*) FILTER (WHERE ai.priority = 'high')::INTEGER AS high_priority_insights,
        COUNT(*) FILTER (WHERE ai.validation_status = 'validated')::INTEGER AS validated_insights,
        AVG(ai.confidence_score)::DECIMAL(3,2) AS avg_confidence
    FROM ai_insights ai
    WHERE ai.report_id = p_report_id
    GROUP BY ai.category
    ORDER BY critical_insights DESC, high_priority_insights DESC;
END;
$$ LANGUAGE plpgsql;


-- Function to archive old PMR reports
CREATE OR REPLACE FUNCTION archive_old_pmr_reports(p_months_old INTEGER DEFAULT 12)
RETURNS INTEGER AS $$
DECLARE
    reports_archived INTEGER;
BEGIN
    -- Mark old reports as inactive (soft delete)
    UPDATE pmr_reports 
    SET is_active = FALSE
    WHERE 
        report_month < NOW() - INTERVAL '1 month' * p_months_old
        AND is_active = TRUE
        AND status = 'distributed';
    
    GET DIAGNOSTICS reports_archived = ROW_COUNT;
    
    RETURN reports_archived;
END;
$$ LANGUAGE plpgsql;

-- Function to get export job statistics
CREATE OR REPLACE FUNCTION get_export_job_statistics(p_days INTEGER DEFAULT 30)
RETURNS TABLE (
    export_format export_format,
    total_jobs INTEGER,
    completed_jobs INTEGER,
    failed_jobs INTEGER,
    avg_processing_time_seconds DECIMAL(10,2),
    success_rate DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ej.export_format,
        COUNT(*)::INTEGER AS total_jobs,
        COUNT(*) FILTER (WHERE ej.status = 'completed')::INTEGER AS completed_jobs,
        COUNT(*) FILTER (WHERE ej.status = 'failed')::INTEGER AS failed_jobs,
        AVG(EXTRACT(EPOCH FROM (ej.completed_at - ej.started_at)))::DECIMAL(10,2) AS avg_processing_time_seconds,
        (COUNT(*) FILTER (WHERE ej.status = 'completed')::DECIMAL / NULLIF(COUNT(*), 0) * 100)::DECIMAL(5,2) AS success_rate
    FROM export_jobs ej
    WHERE ej.started_at >= NOW() - INTERVAL '1 day' * p_days
    GROUP BY ej.export_format
    ORDER BY total_jobs DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- PMR Dashboard Summary View
CREATE OR REPLACE VIEW pmr_dashboard_summary AS
SELECT 
    p.id as project_id,
    p.name as project_name,
    p.status as project_status,
    -- Latest report info
    latest_report.report_id,
    latest_report.report_month,
    latest_report.report_year,
    latest_report.title as latest_report_title,
    latest_report.status as report_status,
    latest_report.generated_at as report_generated_at,
    -- Report statistics
    report_stats.total_reports,
    report_stats.draft_reports,
    report_stats.approved_reports,
    -- Template info
    t.name as template_name,
    t.template_type,
    -- Insights summary
    insight_stats.total_insights,
    insight_stats.critical_insights,
    insight_stats.unvalidated_insights,
    -- Collaboration stats
    collab_stats.active_sessions,
    collab_stats.total_collaborators
FROM projects p
LEFT JOIN LATERAL (
    SELECT * FROM get_latest_pmr_report(p.id)
) latest_report ON TRUE
LEFT JOIN LATERAL (
    SELECT 
        COUNT(*)::INTEGER as total_reports,
        COUNT(*) FILTER (WHERE status = 'draft')::INTEGER as draft_reports,
        COUNT(*) FILTER (WHERE status = 'approved')::INTEGER as approved_reports
    FROM pmr_reports 
    WHERE project_id = p.id AND is_active = TRUE
) report_stats ON TRUE
LEFT JOIN pmr_reports r ON r.id = latest_report.report_id
LEFT JOIN pmr_templates t ON t.id = r.template_id
LEFT JOIN LATERAL (
    SELECT 
        COUNT(*)::INTEGER as total_insights,
        COUNT(*) FILTER (WHERE priority = 'critical')::INTEGER as critical_insights,
        COUNT(*) FILTER (WHERE validation_status = 'pending')::INTEGER as unvalidated_insights
    FROM ai_insights ai
    JOIN pmr_reports rep ON rep.id = ai.report_id
    WHERE rep.project_id = p.id AND rep.is_active = TRUE
) insight_stats ON TRUE
LEFT JOIN LATERAL (
    SELECT 
        COUNT(*)::INTEGER as active_sessions,
        SUM(jsonb_array_length(cs.participants))::INTEGER as total_collaborators
    FROM collaboration_sessions cs
    JOIN pmr_reports rep ON rep.id = cs.report_id
    WHERE rep.project_id = p.id AND cs.is_active = TRUE
) collab_stats ON TRUE;


-- PMR Template Usage Analytics View
CREATE OR REPLACE VIEW pmr_template_analytics AS
SELECT 
    t.id,
    t.name,
    t.template_type,
    t.industry_focus,
    t.usage_count,
    t.rating,
    t.is_public,
    t.created_by,
    u.email as creator_email,
    -- Usage statistics
    usage_stats.reports_this_month,
    usage_stats.reports_this_year,
    usage_stats.avg_completion_score,
    -- Rating statistics
    COALESCE(rating_stats.total_ratings, 0) as total_ratings,
    rating_stats.avg_rating
FROM pmr_templates t
LEFT JOIN auth.users u ON u.id = t.created_by
LEFT JOIN LATERAL (
    SELECT 
        COUNT(*) FILTER (WHERE DATE_TRUNC('month', generated_at) = DATE_TRUNC('month', NOW()))::INTEGER as reports_this_month,
        COUNT(*) FILTER (WHERE DATE_TRUNC('year', generated_at) = DATE_TRUNC('year', NOW()))::INTEGER as reports_this_year,
        AVG(calculate_pmr_completeness(r.id))::DECIMAL(3,2) as avg_completion_score
    FROM pmr_reports r
    WHERE r.template_id = t.id AND r.is_active = TRUE
) usage_stats ON TRUE
LEFT JOIN LATERAL (
    -- This would be extended if we had a separate ratings table
    SELECT 
        1 as total_ratings,
        t.rating as avg_rating
    WHERE t.rating IS NOT NULL
) rating_stats ON TRUE;

-- Active Edit Sessions View
CREATE OR REPLACE VIEW active_edit_sessions AS
SELECT 
    es.id as session_id,
    es.report_id,
    r.title as report_title,
    r.project_id,
    p.name as project_name,
    es.user_id,
    u.email as user_email,
    es.session_type,
    es.active_section,
    es.started_at,
    es.last_activity,
    -- Session activity metrics
    jsonb_array_length(es.chat_messages) as message_count,
    jsonb_array_length(es.changes_made) as changes_count,
    -- Time since last activity
    EXTRACT(EPOCH FROM (NOW() - es.last_activity))/60 as minutes_since_activity
FROM edit_sessions es
JOIN pmr_reports r ON r.id = es.report_id
JOIN projects p ON p.id = r.project_id
LEFT JOIN auth.users u ON u.id = es.user_id
WHERE es.is_active = TRUE
ORDER BY es.last_activity DESC;

-- Active Collaboration Sessions View
CREATE OR REPLACE VIEW active_collaboration_sessions AS
SELECT 
    cs.id,
    cs.session_id,
    cs.report_id,
    r.title as report_title,
    r.project_id,
    p.name as project_name,
    cs.session_type,
    jsonb_array_length(cs.participants) as participant_count,
    jsonb_array_length(cs.active_editors) as active_editor_count,
    jsonb_array_length(cs.changes_log) as total_changes,
    jsonb_array_length(cs.comments) as total_comments,
    cs.started_at,
    cs.last_activity,
    EXTRACT(EPOCH FROM (NOW() - cs.last_activity))/60 as minutes_since_activity
FROM collaboration_sessions cs
JOIN pmr_reports r ON r.id = cs.report_id
JOIN projects p ON p.id = r.project_id
WHERE cs.is_active = TRUE
ORDER BY cs.last_activity DESC;

-- Export Jobs Status View
CREATE OR REPLACE VIEW export_jobs_status AS
SELECT 
    ej.id as job_id,
    ej.report_id,
    r.title as report_title,
    r.project_id,
    p.name as project_name,
    ej.export_format,
    ej.status,
    ej.file_url,
    ej.file_size,
    ej.requested_by,
    u.email as requester_email,
    ej.started_at,
    ej.completed_at,
    ej.error_message,
    ej.retry_count,
    -- Processing time
    CASE 
        WHEN ej.completed_at IS NOT NULL THEN 
            EXTRACT(EPOCH FROM (ej.completed_at - ej.started_at))/60
        ELSE 
            EXTRACT(EPOCH FROM (NOW() - ej.started_at))/60
    END as processing_time_minutes
FROM export_jobs ej
JOIN pmr_reports r ON r.id = ej.report_id
JOIN projects p ON p.id = r.project_id
LEFT JOIN auth.users u ON u.id = ej.requested_by
ORDER BY ej.started_at DESC;


-- AI Insights Performance View
CREATE OR REPLACE VIEW ai_insights_performance AS
SELECT 
    r.project_id,
    p.name as project_name,
    ai.category,
    ai.insight_type,
    COUNT(*)::INTEGER as total_insights,
    AVG(ai.confidence_score)::DECIMAL(3,2) as avg_confidence,
    COUNT(*) FILTER (WHERE ai.validation_status = 'validated')::INTEGER as validated_count,
    COUNT(*) FILTER (WHERE ai.validation_status = 'rejected')::INTEGER as rejected_count,
    AVG(ai.feedback_score)::DECIMAL(3,2) as avg_feedback_score,
    COUNT(*) FILTER (WHERE ai.priority IN ('high', 'critical'))::INTEGER as high_priority_count
FROM ai_insights ai
JOIN pmr_reports r ON r.id = ai.report_id
JOIN projects p ON p.id = r.project_id
WHERE r.is_active = TRUE
GROUP BY r.project_id, p.name, ai.category, ai.insight_type
ORDER BY r.project_id, ai.category, total_insights DESC;

-- Report Collaboration Activity View
CREATE OR REPLACE VIEW report_collaboration_activity AS
SELECT 
    r.id as report_id,
    r.title as report_title,
    r.project_id,
    p.name as project_name,
    pc.user_id,
    u.email as user_email,
    pc.action_type,
    pc.section_id,
    pc.timestamp,
    pc.change_description
FROM pmr_collaboration pc
JOIN pmr_reports r ON r.id = pc.report_id
JOIN projects p ON p.id = r.project_id
LEFT JOIN auth.users u ON u.id = pc.user_id
WHERE r.is_active = TRUE
ORDER BY pc.timestamp DESC;

-- ============================================================================
-- INITIAL DATA SETUP
-- ============================================================================

-- Insert default PMR templates
INSERT INTO pmr_templates (
    name, 
    description, 
    template_type, 
    sections, 
    default_metrics, 
    export_formats, 
    is_public, 
    created_by
) 
SELECT
    'Executive Summary Template',
    'High-level executive summary template focusing on key metrics and strategic insights with AI-powered recommendations',
    'executive'::pmr_template_type,
    '[
        {"id": "executive_summary", "name": "Executive Summary", "required": true, "order": 1, "ai_enabled": true},
        {"id": "key_metrics", "name": "Key Performance Metrics", "required": true, "order": 2, "ai_enabled": true},
        {"id": "budget_status", "name": "Budget Status", "required": true, "order": 3, "ai_enabled": true},
        {"id": "schedule_status", "name": "Schedule Status", "required": true, "order": 4, "ai_enabled": true},
        {"id": "risks_issues", "name": "Key Risks and Issues", "required": true, "order": 5, "ai_enabled": true},
        {"id": "ai_insights", "name": "AI-Generated Insights", "required": false, "order": 6, "ai_enabled": true},
        {"id": "recommendations", "name": "Recommendations", "required": false, "order": 7, "ai_enabled": true}
    ]'::jsonb,
    '["budget_variance", "schedule_variance", "cost_performance_index", "schedule_performance_index", "percent_complete", "risk_score"]'::jsonb,
    '["pdf", "slides", "word"]'::jsonb,
    true,
    (SELECT id FROM auth.users ORDER BY created_at LIMIT 1)
WHERE NOT EXISTS (
    SELECT 1 FROM pmr_templates WHERE name = 'Executive Summary Template'
);

INSERT INTO pmr_templates (
    name, 
    description, 
    template_type, 
    sections, 
    default_metrics, 
    export_formats, 
    is_public, 
    created_by
) 
SELECT
    'Technical Project Report',
    'Detailed technical report template with comprehensive metrics and AI-powered analysis',
    'technical'::pmr_template_type,
    '[
        {"id": "executive_summary", "name": "Executive Summary", "required": true, "order": 1, "ai_enabled": true},
        {"id": "technical_progress", "name": "Technical Progress", "required": true, "order": 2, "ai_enabled": false},
        {"id": "quality_metrics", "name": "Quality Metrics", "required": true, "order": 3, "ai_enabled": true},
        {"id": "resource_utilization", "name": "Resource Utilization", "required": true, "order": 4, "ai_enabled": true},
        {"id": "technical_challenges", "name": "Technical Challenges", "required": true, "order": 5, "ai_enabled": true},
        {"id": "monte_carlo_analysis", "name": "Monte Carlo Risk Analysis", "required": false, "order": 6, "ai_enabled": true},
        {"id": "recommendations", "name": "Technical Recommendations", "required": false, "order": 7, "ai_enabled": true}
    ]'::jsonb,
    '["quality_score", "defect_density", "code_coverage", "technical_debt", "velocity", "resource_utilization"]'::jsonb,
    '["pdf", "excel", "word"]'::jsonb,
    true,
    (SELECT id FROM auth.users ORDER BY created_at LIMIT 1)
WHERE NOT EXISTS (
    SELECT 1 FROM pmr_templates WHERE name = 'Technical Project Report'
);


-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on all PMR tables
ALTER TABLE pmr_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE pmr_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE collaboration_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE edit_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE export_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE pmr_collaboration ENABLE ROW LEVEL SECURITY;
ALTER TABLE pmr_distribution_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE pmr_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE pmr_change_events ENABLE ROW LEVEL SECURITY;

-- PMR Templates Policies
CREATE POLICY "Users can view public templates" ON pmr_templates
    FOR SELECT USING (is_public = TRUE OR created_by = auth.uid());

CREATE POLICY "Users can create their own templates" ON pmr_templates
    FOR INSERT WITH CHECK (created_by = auth.uid());

CREATE POLICY "Users can update their own templates" ON pmr_templates
    FOR UPDATE USING (created_by = auth.uid());

CREATE POLICY "Users can delete their own templates" ON pmr_templates
    FOR DELETE USING (created_by = auth.uid());

-- PMR Reports Policies
CREATE POLICY "Users can view reports for their projects" ON pmr_reports
    FOR SELECT USING (
        project_id IN (
            SELECT id FROM projects WHERE created_by = auth.uid()
            UNION
            SELECT project_id FROM project_members WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create reports for their projects" ON pmr_reports
    FOR INSERT WITH CHECK (
        generated_by = auth.uid() AND
        project_id IN (
            SELECT id FROM projects WHERE created_by = auth.uid()
            UNION
            SELECT project_id FROM project_members WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update reports they generated" ON pmr_reports
    FOR UPDATE USING (
        generated_by = auth.uid() OR
        project_id IN (
            SELECT id FROM projects WHERE created_by = auth.uid()
        )
    );

-- AI Insights Policies
CREATE POLICY "Users can view insights for accessible reports" ON ai_insights
    FOR SELECT USING (
        report_id IN (
            SELECT id FROM pmr_reports WHERE 
            project_id IN (
                SELECT id FROM projects WHERE created_by = auth.uid()
                UNION
                SELECT project_id FROM project_members WHERE user_id = auth.uid()
            )
        )
    );

CREATE POLICY "System can manage AI insights" ON ai_insights
    FOR ALL USING (true);

-- Collaboration Sessions Policies
CREATE POLICY "Users can view collaboration sessions for accessible reports" ON collaboration_sessions
    FOR SELECT USING (
        report_id IN (
            SELECT id FROM pmr_reports WHERE 
            project_id IN (
                SELECT id FROM projects WHERE created_by = auth.uid()
                UNION
                SELECT project_id FROM project_members WHERE user_id = auth.uid()
            )
        )
    );

CREATE POLICY "Users can manage collaboration sessions" ON collaboration_sessions
    FOR ALL USING (
        report_id IN (
            SELECT id FROM pmr_reports WHERE 
            project_id IN (
                SELECT id FROM projects WHERE created_by = auth.uid()
                UNION
                SELECT project_id FROM project_members WHERE user_id = auth.uid()
            )
        )
    );

-- Edit Sessions Policies
CREATE POLICY "Users can view their own edit sessions" ON edit_sessions
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can create their own edit sessions" ON edit_sessions
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own edit sessions" ON edit_sessions
    FOR UPDATE USING (user_id = auth.uid());

-- Export Jobs Policies
CREATE POLICY "Users can view their export jobs" ON export_jobs
    FOR SELECT USING (requested_by = auth.uid());

CREATE POLICY "Users can create export jobs for accessible reports" ON export_jobs
    FOR INSERT WITH CHECK (
        requested_by = auth.uid() AND
        report_id IN (
            SELECT id FROM pmr_reports WHERE 
            project_id IN (
                SELECT id FROM projects WHERE created_by = auth.uid()
                UNION
                SELECT project_id FROM project_members WHERE user_id = auth.uid()
            )
        )
    );

-- PMR Collaboration Policies
CREATE POLICY "Users can view collaboration activity for accessible reports" ON pmr_collaboration
    FOR SELECT USING (
        report_id IN (
            SELECT id FROM pmr_reports WHERE 
            project_id IN (
                SELECT id FROM projects WHERE created_by = auth.uid()
                UNION
                SELECT project_id FROM project_members WHERE user_id = auth.uid()
            )
        )
    );

CREATE POLICY "Users can log their own collaboration activity" ON pmr_collaboration
    FOR INSERT WITH CHECK (user_id = auth.uid());

-- Comments Policies
CREATE POLICY "Users can view comments on accessible reports" ON pmr_comments
    FOR SELECT USING (
        report_id IN (
            SELECT id FROM pmr_reports WHERE 
            project_id IN (
                SELECT id FROM projects WHERE created_by = auth.uid()
                UNION
                SELECT project_id FROM project_members WHERE user_id = auth.uid()
            )
        )
    );

CREATE POLICY "Users can create comments on accessible reports" ON pmr_comments
    FOR INSERT WITH CHECK (
        user_id = auth.uid() AND
        report_id IN (
            SELECT id FROM pmr_reports WHERE 
            project_id IN (
                SELECT id FROM projects WHERE created_by = auth.uid()
                UNION
                SELECT project_id FROM project_members WHERE user_id = auth.uid()
            )
        )
    );

CREATE POLICY "Users can update their own comments" ON pmr_comments
    FOR UPDATE USING (user_id = auth.uid());

-- Change Events Policies
CREATE POLICY "Users can view change events for accessible reports" ON pmr_change_events
    FOR SELECT USING (
        report_id IN (
            SELECT id FROM pmr_reports WHERE 
            project_id IN (
                SELECT id FROM projects WHERE created_by = auth.uid()
                UNION
                SELECT project_id FROM project_members WHERE user_id = auth.uid()
            )
        )
    );

CREATE POLICY "Users can create change events" ON pmr_change_events
    FOR INSERT WITH CHECK (user_id = auth.uid());


-- ============================================================================
-- DOCUMENTATION COMMENTS
-- ============================================================================

COMMENT ON TABLE pmr_reports IS 'Enhanced AI-powered Project Monthly Reports with real-time collaboration, Monte Carlo analysis, and interactive editing capabilities';
COMMENT ON TABLE pmr_templates IS 'Intelligent template management system for PMR generation with AI suggestions and industry-specific configurations';
COMMENT ON TABLE ai_insights IS 'AI-generated insights and recommendations with confidence scoring, validation tracking, and user feedback';
COMMENT ON TABLE collaboration_sessions IS 'Real-time collaborative editing sessions with multi-user support, conflict resolution, and change tracking';
COMMENT ON TABLE edit_sessions IS 'Individual interactive editing sessions with chat-based AI assistance and change history';
COMMENT ON TABLE export_jobs IS 'Multi-format export job management with status tracking, retry logic, and file delivery';
COMMENT ON TABLE pmr_collaboration IS 'Comprehensive collaboration activity log for audit trail and analytics';
COMMENT ON TABLE pmr_distribution_log IS 'Distribution tracking for automated report delivery across multiple channels';
COMMENT ON TABLE pmr_comments IS 'Section-level comments and discussions with threading, mentions, and resolution tracking';
COMMENT ON TABLE pmr_change_events IS 'Detailed change event tracking for version control and audit purposes';

COMMENT ON VIEW pmr_dashboard_summary IS 'Comprehensive dashboard view of PMR status, insights, and collaboration across all projects';
COMMENT ON VIEW pmr_template_analytics IS 'Template usage analytics, performance metrics, and completion scores';
COMMENT ON VIEW active_edit_sessions IS 'Currently active individual editing sessions with activity metrics';
COMMENT ON VIEW active_collaboration_sessions IS 'Currently active collaborative editing sessions with participant counts and activity';
COMMENT ON VIEW export_jobs_status IS 'Export job status, processing metrics, and file delivery tracking';
COMMENT ON VIEW ai_insights_performance IS 'AI insights performance metrics including confidence, validation rates, and user feedback';
COMMENT ON VIEW report_collaboration_activity IS 'Recent collaboration activity across all reports for monitoring and analytics';

COMMENT ON FUNCTION get_latest_pmr_report(UUID) IS 'Retrieves the most recent active PMR report for a given project';
COMMENT ON FUNCTION calculate_pmr_completeness(UUID) IS 'Calculates completeness score (0.0-1.0) based on content, insights, and Monte Carlo analysis';
COMMENT ON FUNCTION cleanup_old_edit_sessions(INTEGER) IS 'Archives old inactive edit sessions to maintain database performance';
COMMENT ON FUNCTION cleanup_old_collaboration_sessions(INTEGER) IS 'Archives old inactive collaboration sessions to maintain database performance';
COMMENT ON FUNCTION get_active_collaborators(UUID) IS 'Returns list of currently active collaborators for a report';
COMMENT ON FUNCTION get_unresolved_comments(UUID) IS 'Returns all unresolved comments for a report with reply counts';
COMMENT ON FUNCTION get_ai_insights_summary(UUID) IS 'Returns summary statistics of AI insights by category for a report';
COMMENT ON FUNCTION archive_old_pmr_reports(INTEGER) IS 'Archives old distributed reports to reduce active dataset size';
COMMENT ON FUNCTION get_export_job_statistics(INTEGER) IS 'Returns export job statistics including success rates and processing times';

-- Column-level comments for key fields
COMMENT ON COLUMN pmr_reports.ai_generated_insights IS 'JSONB array of AI-generated insights (deprecated - use ai_insights table)';
COMMENT ON COLUMN pmr_reports.ai_confidence_scores IS 'JSONB object mapping section IDs to AI confidence scores';
COMMENT ON COLUMN pmr_reports.monte_carlo_analysis IS 'JSONB object containing Monte Carlo simulation results';
COMMENT ON COLUMN pmr_reports.real_time_metrics IS 'JSONB object containing current real-time project metrics';
COMMENT ON COLUMN pmr_reports.collaboration_session_id IS 'Reference to active collaboration session if collaboration is enabled';
COMMENT ON COLUMN pmr_reports.total_edits IS 'Counter for total number of edits made to this report';
COMMENT ON COLUMN pmr_reports.audit_log IS 'JSONB array of audit log entries for compliance and tracking';

COMMENT ON COLUMN ai_insights.confidence_score IS 'AI confidence score (0.0-1.0) indicating reliability of the insight';
COMMENT ON COLUMN ai_insights.validation_status IS 'Current validation status: pending, validated, rejected, or needs_review';
COMMENT ON COLUMN ai_insights.impact_score IS 'Estimated impact score (0.0-1.0) of implementing the insight';
COMMENT ON COLUMN ai_insights.feedback_score IS 'User feedback score (0.0-5.0) rating the usefulness of the insight';

COMMENT ON COLUMN collaboration_sessions.conflict_resolution_strategy IS 'Strategy for resolving edit conflicts: last_write_wins, manual, or merge';
COMMENT ON COLUMN collaboration_sessions.locked_sections IS 'JSONB object mapping section IDs to user IDs who have them locked';
COMMENT ON COLUMN collaboration_sessions.changes_log IS 'JSONB array of all changes made during the session';

COMMENT ON COLUMN export_jobs.retry_count IS 'Number of retry attempts for failed export jobs';
COMMENT ON COLUMN export_jobs.file_size IS 'Size of exported file in bytes';

-- ============================================================================
-- MAINTENANCE JOBS (Optional - for scheduled cleanup)
-- ============================================================================

-- Create a maintenance function that can be called by a scheduler
CREATE OR REPLACE FUNCTION pmr_maintenance_job()
RETURNS TABLE (
    task VARCHAR(100),
    items_processed INTEGER,
    execution_time_ms INTEGER
) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    sessions_cleaned INTEGER;
    collab_sessions_cleaned INTEGER;
    reports_archived INTEGER;
BEGIN
    -- Clean up old edit sessions (older than 30 days)
    start_time := clock_timestamp();
    sessions_cleaned := cleanup_old_edit_sessions(30);
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT 
        'cleanup_edit_sessions'::VARCHAR(100),
        sessions_cleaned,
        EXTRACT(MILLISECONDS FROM (end_time - start_time))::INTEGER;
    
    -- Clean up old collaboration sessions (older than 24 hours)
    start_time := clock_timestamp();
    collab_sessions_cleaned := cleanup_old_collaboration_sessions(24);
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT 
        'cleanup_collaboration_sessions'::VARCHAR(100),
        collab_sessions_cleaned,
        EXTRACT(MILLISECONDS FROM (end_time - start_time))::INTEGER;
    
    -- Archive old reports (older than 12 months)
    start_time := clock_timestamp();
    reports_archived := archive_old_pmr_reports(12);
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT 
        'archive_old_reports'::VARCHAR(100),
        reports_archived,
        EXTRACT(MILLISECONDS FROM (end_time - start_time))::INTEGER;
    
    RETURN;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION pmr_maintenance_job() IS 'Scheduled maintenance job for PMR system cleanup and archival';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Enhanced PMR Schema Migration (021) completed successfully';
    RAISE NOTICE 'Created tables: pmr_templates, pmr_reports, ai_insights, collaboration_sessions, edit_sessions, export_jobs, pmr_collaboration, pmr_distribution_log, pmr_comments, pmr_change_events';
    RAISE NOTICE 'Created views: pmr_dashboard_summary, pmr_template_analytics, active_edit_sessions, active_collaboration_sessions, export_jobs_status, ai_insights_performance, report_collaboration_activity';
    RAISE NOTICE 'Created functions: 10 utility functions for PMR operations';
    RAISE NOTICE 'Created indexes: 50+ performance-optimized indexes';
    RAISE NOTICE 'Enabled RLS policies for all PMR tables';
END $$;
