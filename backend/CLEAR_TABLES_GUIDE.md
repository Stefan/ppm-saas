# Clear Tables Guide

Quick reference for clearing import data during testing.

## Clear Commitments Table

### Option 1: Python Script
```python
from config.database import service_supabase

# Delete all commitments
service_supabase.table("commitments").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
print("✅ Commitments table cleared")
```

### Option 2: SQL (Supabase SQL Editor)
```sql
DELETE FROM commitments;
```

### Option 3: SQL with Confirmation
```sql
-- Check count first
SELECT COUNT(*) FROM commitments;

-- Delete all
DELETE FROM commitments;

-- Verify
SELECT COUNT(*) FROM commitments;
```

## Clear Import Audit Logs

### Python
```python
from config.database import service_supabase

# Delete all import logs
service_supabase.table("import_audit_logs").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
print("✅ Import logs cleared")
```

### SQL
```sql
DELETE FROM import_audit_logs;
```

## Clear Both Tables at Once

### SQL
```sql
-- Clear commitments
DELETE FROM commitments;

-- Clear import logs
DELETE FROM import_audit_logs;

-- Verify
SELECT 
  (SELECT COUNT(*) FROM commitments) as commitments_count,
  (SELECT COUNT(*) FROM import_audit_logs) as logs_count;
```

## Clear Actuals Table (if needed)

### SQL
```sql
DELETE FROM actuals;
```

## Reset Auto-Generated Projects (if needed)

If you want to also clear auto-generated projects created during import:

```sql
-- Be careful! This will delete ALL projects
DELETE FROM projects WHERE project_nr LIKE 'C.%';

-- Or delete all projects
DELETE FROM projects;
```

## Quick Test Reset Script

Create `backend/reset_for_testing.py`:

```python
from config.database import service_supabase

print("Resetting database for testing...")

# Clear commitments
service_supabase.table("commitments").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
print("✅ Cleared commitments")

# Clear import logs
service_supabase.table("import_audit_logs").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
print("✅ Cleared import logs")

print("\n✅ Database reset complete - ready for fresh import!")
```

Run with:
```bash
cd backend
python reset_for_testing.py
```

## Notes

- **Service role client** bypasses RLS policies, so deletions work even with RLS enabled
- The `neq("id", "00000000-0000-0000-0000-000000000000")` filter is a workaround to delete all records (Supabase requires a filter)
- Always verify counts before and after deletion
- Consider backing up data before clearing in production environments
