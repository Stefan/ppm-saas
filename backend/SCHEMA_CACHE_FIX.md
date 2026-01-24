# Schema Cache Issue - Fix

## Problem
The columns exist in the database (verified ✅), but Supabase's PostgREST schema cache hasn't refreshed yet.

Error message:
```
Could not find the 'account_group_level1' column of 'commitments' in the schema cache
```

## Solution: Refresh Supabase Schema Cache

### Option 1: Wait (Easiest)
Wait 10-30 seconds and try the import again. The schema cache refreshes automatically.

### Option 2: Force Refresh via SQL
Run this in Supabase SQL Editor:

```sql
-- Force PostgREST to reload the schema cache
NOTIFY pgrst, 'reload schema';
```

### Option 3: Restart PostgREST (Supabase Dashboard)
1. Go to Supabase Dashboard
2. Settings → API
3. Click "Restart API" or wait for auto-refresh

### Option 4: Restart Your Backend Server
If you're running the backend locally:

```bash
# Stop the backend (Ctrl+C)
# Then restart:
cd backend
python main.py
```

### Option 5: Use Direct Database Connection (Workaround)
If the cache issue persists, we can bypass PostgREST by using a direct database connection.

## Quick Test

Try this command to verify the columns are accessible:

```bash
cd backend
python check_migration_status.py
```

If it shows ✅ for all columns, the database is fine - it's just a cache issue.

## Why This Happens

Supabase uses PostgREST as an API layer over PostgreSQL. When you add columns via SQL, PostgREST's schema cache needs to refresh to recognize the new columns. This usually happens automatically within seconds, but sometimes needs a manual refresh.

## After Fixing

Once the cache refreshes, try the import again. It should work!

Expected result:
- ~997 records imported successfully
- 6 duplicates detected
- ~93 validation errors
- All 35 columns populated
