# Enhanced PMR Schema Migration Guide

## Overview

This migration (`021_enhanced_pmr_schema.sql`) creates a comprehensive database schema for the Enhanced Project Monthly Report (PMR) feature. The schema supports AI-powered insights, real-time collaboration, multi-format exports, and Monte Carlo analysis integration.

## Migration Contents

### Tables Created

1. **pmr_templates** - Template management with AI suggestions
2. **pmr_reports** - Enhanced PMR reports with AI and collaboration features
3. **ai_insights** - AI-generated insights with validation and feedback
4. **collaboration_sessions** - Real-time collaborative editing sessions
5. **edit_sessions** - Individual editing sessions with chat support
6. **export_jobs** - Multi-format export job management
7. **pmr_collaboration** - Collaboration activity audit log
8. **pmr_distribution_log** - Report distribution tracking
9. **pmr_comments** - Section-level comments with threading
10. **pmr_change_events** - Detailed change event tracking

### Views Created

1. **pmr_dashboard_summary** - Comprehensive project PMR overview
2. **pmr_template_analytics** - Template usage and performance metrics
3. **active_edit_sessions** - Currently active editing sessions
4. **active_collaboration_sessions** - Active collaborative sessions
5. **export_jobs_status** - Export job status and metrics
6. **ai_insights_performance** - AI insights performance analytics
7. **report_collaboration_activity** - Recent collaboration activity

### Functions Created

1. **get_latest_pmr_report(UUID)** - Get most recent report for a project
2. **calculate_pmr_completeness(UUID)** - Calculate report completeness score
3. **cleanup_old_edit_sessions(INTEGER)** - Archive old edit sessions
4. **cleanup_old_collaboration_sessions(INTEGER)** - Archive old collaboration sessions
5. **get_active_collaborators(UUID)** - Get active collaborators for a report
6. **get_unresolved_comments(UUID)** - Get unresolved comments for a report
7. **get_ai_insights_summary(UUID)** - Get AI insights summary by category
8. **archive_old_pmr_reports(INTEGER)** - Archive old distributed reports
9. **get_export_job_statistics(INTEGER)** - Get export job statistics
10. **pmr_maintenance_job()** - Scheduled maintenance job

### Features

- **Custom Types**: 12 PostgreSQL ENUM types for type safety
- **Indexes**: 50+ performance-optimized indexes
- **Triggers**: Automatic timestamp updates and business logic enforcement
- **RLS Policies**: Row-level security for all tables
- **Default Data**: Pre-configured templates for immediate use

## Prerequisites

- PostgreSQL 12 or higher
- Existing tables: `projects`, `auth.users`, `monte_carlo_simulations`
- Extensions: `uuid-ossp`, `pg_trgm`

## Installation

### Method 1: Using Python Script (Recommended)

```bash
# Navigate to backend directory
cd backend

# Ensure virtual environment is activated
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Run the migration script
python migrations/apply_enhanced_pmr_migration.py
```

### Method 2: Direct SQL Execution

```bash
# Using psql
psql -U your_username -d your_database -f migrations/021_enhanced_pmr_schema.sql

# Or using Supabase CLI
supabase db push
```

## Verification

After applying the migration, verify it was successful:

```bash
# Run verification script
python migrations/verify_enhanced_pmr_migration.py
```

The verification script checks:
- All tables exist
- Key indexes are created
- Views are accessible
- Functions are defined
- Triggers are active
- RLS policies are enabled
- Default data is inserted

## Post-Migration Steps

### 1. Update Application Models

Ensure your Pydantic models in `backend/models/pmr.py` match the schema:

```python
from models.pmr import (
    EnhancedPMRReport,
    AIInsight,
    CollaborationSession,
    ExportJob
)
```

### 2. Configure Environment Variables

Add any required environment variables for AI and export features:

```bash
# .env
OPENAI_API_KEY=your_api_key
EXPORT_STORAGE_PATH=/path/to/exports
MONTE_CARLO_ENABLED=true
```

### 3. Test Core Functionality

```python
# Test report creation
from services.enhanced_pmr_service import EnhancedPMRService

service = EnhancedPMRService()
report = await service.generate_enhanced_pmr(
    project_id=project_id,
    report_month=date(2024, 1, 1),
    include_ai_insights=True
)
```

## Schema Details

### Key Relationships

```
projects
    └── pmr_reports
            ├── ai_insights
            ├── collaboration_sessions
            │       ├── pmr_comments
            │       └── pmr_change_events
            ├── edit_sessions
            ├── export_jobs
            └── pmr_collaboration

pmr_templates
    └── pmr_reports

monte_carlo_simulations
    └── pmr_reports (optional)
```

### Important Fields

#### pmr_reports
- `ai_generated_insights`: JSONB array (deprecated, use ai_insights table)
- `ai_confidence_scores`: Confidence scores by section
- `monte_carlo_analysis`: Monte Carlo simulation results
- `real_time_metrics`: Current project metrics
- `collaboration_session_id`: Active collaboration session reference
- `total_edits`: Edit counter for analytics

#### ai_insights
- `confidence_score`: AI confidence (0.0-1.0)
- `validation_status`: pending, validated, rejected, needs_review
- `impact_score`: Estimated impact (0.0-1.0)
- `feedback_score`: User feedback (0.0-5.0)

#### collaboration_sessions
- `conflict_resolution_strategy`: last_write_wins, manual, merge
- `participants`: JSONB array of active participants
- `changes_log`: JSONB array of all changes
- `locked_sections`: JSONB object of section locks

## Performance Considerations

### Indexes

The migration creates indexes for:
- Project and date-based queries
- Status and workflow filtering
- User-based lookups
- Full-text search on template names
- Time-based queries for sessions and events

### Maintenance

Run the maintenance job periodically:

```sql
-- Run maintenance (can be scheduled)
SELECT * FROM pmr_maintenance_job();
```

This will:
- Clean up old edit sessions (>30 days)
- Clean up old collaboration sessions (>24 hours)
- Archive old reports (>12 months)

### Query Optimization

Use the provided views for common queries:

```sql
-- Dashboard data
SELECT * FROM pmr_dashboard_summary WHERE project_id = 'xxx';

-- Template analytics
SELECT * FROM pmr_template_analytics ORDER BY usage_count DESC;

-- Active sessions
SELECT * FROM active_collaboration_sessions;
```

## Security

### Row Level Security (RLS)

All tables have RLS enabled with policies for:
- Users can view reports for their projects
- Users can edit their own content
- System can manage AI-generated content
- Collaboration based on project membership

### Audit Trail

All changes are tracked in:
- `pmr_collaboration` - User actions
- `pmr_change_events` - Detailed changes
- `audit_log` field in pmr_reports

## Troubleshooting

### Migration Fails

1. **Missing dependencies**:
   ```sql
   -- Check if required tables exist
   SELECT tablename FROM pg_tables 
   WHERE tablename IN ('projects', 'monte_carlo_simulations');
   ```

2. **Permission errors**:
   ```sql
   -- Grant necessary permissions
   GRANT ALL ON SCHEMA public TO your_user;
   ```

3. **Extension errors**:
   ```sql
   -- Install required extensions
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   CREATE EXTENSION IF NOT EXISTS "pg_trgm";
   ```

### Verification Fails

Check specific components:

```sql
-- Check tables
SELECT tablename FROM pg_tables WHERE tablename LIKE 'pmr_%';

-- Check views
SELECT viewname FROM pg_views WHERE viewname LIKE 'pmr_%';

-- Check functions
SELECT routine_name FROM information_schema.routines 
WHERE routine_name LIKE '%pmr%';
```

## Rollback

If you need to rollback the migration:

```sql
-- Drop all PMR tables (in reverse dependency order)
DROP TABLE IF EXISTS pmr_change_events CASCADE;
DROP TABLE IF EXISTS pmr_comments CASCADE;
DROP TABLE IF EXISTS pmr_distribution_log CASCADE;
DROP TABLE IF EXISTS pmr_collaboration CASCADE;
DROP TABLE IF EXISTS export_jobs CASCADE;
DROP TABLE IF EXISTS edit_sessions CASCADE;
DROP TABLE IF EXISTS collaboration_sessions CASCADE;
DROP TABLE IF EXISTS ai_insights CASCADE;
DROP TABLE IF EXISTS pmr_reports CASCADE;
DROP TABLE IF EXISTS pmr_templates CASCADE;

-- Drop views
DROP VIEW IF EXISTS report_collaboration_activity CASCADE;
DROP VIEW IF EXISTS ai_insights_performance CASCADE;
DROP VIEW IF EXISTS export_jobs_status CASCADE;
DROP VIEW IF EXISTS active_collaboration_sessions CASCADE;
DROP VIEW IF EXISTS active_edit_sessions CASCADE;
DROP VIEW IF EXISTS pmr_template_analytics CASCADE;
DROP VIEW IF EXISTS pmr_dashboard_summary CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS pmr_maintenance_job() CASCADE;
DROP FUNCTION IF EXISTS get_export_job_statistics(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS archive_old_pmr_reports(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS get_ai_insights_summary(UUID) CASCADE;
DROP FUNCTION IF EXISTS get_unresolved_comments(UUID) CASCADE;
DROP FUNCTION IF EXISTS get_active_collaborators(UUID) CASCADE;
DROP FUNCTION IF EXISTS cleanup_old_collaboration_sessions(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS cleanup_old_edit_sessions(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS calculate_pmr_completeness(UUID) CASCADE;
DROP FUNCTION IF EXISTS get_latest_pmr_report(UUID) CASCADE;

-- Drop types
DROP TYPE IF EXISTS distribution_status CASCADE;
DROP TYPE IF EXISTS distribution_method CASCADE;
DROP TYPE IF EXISTS collaboration_action_type CASCADE;
DROP TYPE IF EXISTS change_event_type CASCADE;
DROP TYPE IF EXISTS export_job_status CASCADE;
DROP TYPE IF EXISTS export_format CASCADE;
DROP TYPE IF EXISTS participant_role CASCADE;
DROP TYPE IF EXISTS session_type CASCADE;
DROP TYPE IF EXISTS validation_status CASCADE;
DROP TYPE IF EXISTS ai_insight_priority CASCADE;
DROP TYPE IF EXISTS ai_insight_category CASCADE;
DROP TYPE IF EXISTS ai_insight_type CASCADE;
DROP TYPE IF EXISTS pmr_template_type CASCADE;
DROP TYPE IF EXISTS pmr_status CASCADE;
```

## Support

For issues or questions:
1. Check the verification output for specific errors
2. Review the migration SQL file for details
3. Check application logs for runtime errors
4. Consult the Enhanced PMR feature specification

## Version History

- **v1.0** (2024-01-15): Initial enhanced PMR schema with full feature set
  - AI insights with validation
  - Real-time collaboration
  - Multi-format exports
  - Monte Carlo integration
  - Comprehensive audit trail
