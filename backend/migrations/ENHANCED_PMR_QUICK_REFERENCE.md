# Enhanced PMR Schema - Quick Reference

## Quick Start

```bash
# Apply migration
cd backend
python migrations/apply_enhanced_pmr_migration.py

# Verify migration
python migrations/verify_enhanced_pmr_migration.py
```

## Core Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `pmr_templates` | Report templates | name, template_type, sections, is_public |
| `pmr_reports` | PMR reports | project_id, title, status, ai_generated_insights |
| `ai_insights` | AI insights | report_id, insight_type, confidence_score, validation_status |
| `collaboration_sessions` | Real-time collab | report_id, participants, changes_log, is_active |
| `edit_sessions` | Individual edits | report_id, user_id, chat_messages, changes_made |
| `export_jobs` | Export tracking | report_id, export_format, status, file_url |

## Common Queries

### Get Latest Report
```sql
SELECT * FROM get_latest_pmr_report('project-uuid');
```

### Calculate Completeness
```sql
SELECT calculate_pmr_completeness('report-uuid');
```

### Get Active Collaborators
```sql
SELECT * FROM get_active_collaborators('report-uuid');
```

### Get Unresolved Comments
```sql
SELECT * FROM get_unresolved_comments('report-uuid');
```

### Get AI Insights Summary
```sql
SELECT * FROM get_ai_insights_summary('report-uuid');
```

## Useful Views

### Dashboard Summary
```sql
SELECT * FROM pmr_dashboard_summary 
WHERE project_id = 'project-uuid';
```

### Active Sessions
```sql
SELECT * FROM active_collaboration_sessions;
SELECT * FROM active_edit_sessions;
```

### Export Status
```sql
SELECT * FROM export_jobs_status 
WHERE report_id = 'report-uuid';
```

### AI Performance
```sql
SELECT * FROM ai_insights_performance 
WHERE project_id = 'project-uuid';
```

## Maintenance

### Run Maintenance Job
```sql
SELECT * FROM pmr_maintenance_job();
```

### Manual Cleanup
```sql
-- Clean old edit sessions (30+ days)
SELECT cleanup_old_edit_sessions(30);

-- Clean old collaboration sessions (24+ hours)
SELECT cleanup_old_collaboration_sessions(24);

-- Archive old reports (12+ months)
SELECT archive_old_pmr_reports(12);
```

## Status Values

### Report Status
- `draft` - Being edited
- `review` - Under review
- `approved` - Approved
- `distributed` - Sent out

### Insight Validation
- `pending` - Not yet validated
- `validated` - Confirmed accurate
- `rejected` - Marked as incorrect
- `needs_review` - Requires attention

### Export Job Status
- `queued` - Waiting to process
- `processing` - Currently exporting
- `completed` - Successfully exported
- `failed` - Export failed

## JSONB Fields

### pmr_reports.sections
```json
[
  {
    "id": "executive_summary",
    "name": "Executive Summary",
    "content": "...",
    "order": 1,
    "ai_enabled": true
  }
]
```

### pmr_reports.ai_confidence_scores
```json
{
  "executive_summary": 0.92,
  "budget_analysis": 0.87,
  "risk_assessment": 0.95
}
```

### collaboration_sessions.participants
```json
[
  {
    "user_id": "uuid",
    "user_name": "John Doe",
    "role": "editor",
    "is_online": true,
    "current_section": "executive_summary"
  }
]
```

## Indexes

Key indexes for performance:
- `idx_pmr_reports_project_month` - Project + date queries
- `idx_pmr_reports_status` - Status filtering
- `idx_ai_insights_report` - Insight lookups
- `idx_collaboration_sessions_report` - Active sessions
- `idx_export_jobs_status` - Export tracking

## Security

All tables have RLS enabled. Access based on:
- Project membership
- User ownership
- Collaboration participation

## Integration

### With Pydantic Models
```python
from models.pmr import (
    EnhancedPMRReport,
    AIInsight,
    CollaborationSession,
    ExportJob
)
```

### With Services
```python
from services.enhanced_pmr_service import EnhancedPMRService
from services.ai_insights_engine import AIInsightsEngine
from services.collaboration_service import CollaborationService
```

## Troubleshooting

### Check Table Exists
```sql
SELECT tablename FROM pg_tables 
WHERE tablename = 'pmr_reports';
```

### Check RLS Enabled
```sql
SELECT relname, relrowsecurity 
FROM pg_class 
WHERE relname LIKE 'pmr_%';
```

### Check Indexes
```sql
SELECT indexname FROM pg_indexes 
WHERE tablename = 'pmr_reports';
```

### Check Functions
```sql
SELECT routine_name FROM information_schema.routines 
WHERE routine_name LIKE '%pmr%';
```

## Performance Tips

1. Use views for complex queries
2. Leverage indexes for filtering
3. Run maintenance job regularly
4. Archive old data periodically
5. Monitor active session counts

## Default Templates

Two templates are pre-installed:
1. **Executive Summary Template** - High-level overview
2. **Technical Project Report** - Detailed technical metrics

Access via:
```sql
SELECT * FROM pmr_templates WHERE is_public = TRUE;
```
