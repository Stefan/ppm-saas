# How to Apply the Database Migration

## The Problem
The import failed because the new columns don't exist in the database yet. You need to add them first.

## Solution: Run SQL in Supabase

### Step 1: Open Supabase SQL Editor
1. Go to your Supabase project dashboard
2. Click on **SQL Editor** in the left sidebar (or go to the SQL tab)

### Step 2: Copy the SQL
Open the file `backend/RUN_THIS_IN_SUPABASE.sql` and copy ALL the contents.

Or copy this:

```sql
-- Add all missing columns
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS po_line_text TEXT;
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS po_created_by VARCHAR(255);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS shopping_cart_number VARCHAR(100);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS document_currency_code VARCHAR(3);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS value_in_document_currency DECIMAL(15, 2);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS investment_profile VARCHAR(50);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS account_group_level1 VARCHAR(100);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS account_subgroup_level2 VARCHAR(100);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS account_level3 VARCHAR(100);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS change_date DATE;
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS purchase_requisition VARCHAR(100);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS procurement_plant VARCHAR(100);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS contract_number VARCHAR(100);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS joint_commodity_code VARCHAR(100);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS po_title TEXT;
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS version VARCHAR(50);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS fi_doc_no VARCHAR(50);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_commitments_po_created_by ON commitments(po_created_by);
CREATE INDEX IF NOT EXISTS idx_commitments_investment_profile ON commitments(investment_profile);
CREATE INDEX IF NOT EXISTS idx_commitments_contract_number ON commitments(contract_number);
CREATE INDEX IF NOT EXISTS idx_commitments_change_date ON commitments(change_date);
CREATE INDEX IF NOT EXISTS idx_commitments_fi_doc_no ON commitments(fi_doc_no);
```

### Step 3: Paste and Run
1. Paste the SQL into the SQL Editor
2. Click the **RUN** button (or press Cmd/Ctrl + Enter)
3. Wait for "Success" message

### Step 4: Verify
You should see output showing:
- 17 new columns added
- 5 indexes created
- Total column count: 45+

### Step 5: Try Import Again
Now go back to your application and try the CSV import again. It should work!

## Alternative: Use psql (if you have database access)

```bash
psql "postgresql://postgres:[YOUR-PASSWORD]@[YOUR-HOST]:5432/postgres" -f backend/RUN_THIS_IN_SUPABASE.sql
```

## Troubleshooting

### "Permission denied"
→ Make sure you're logged in as the database owner or have ALTER TABLE permissions

### "Column already exists"
→ That's fine! The `IF NOT EXISTS` clause prevents errors. The migration is idempotent.

### "Table 'commitments' does not exist"
→ Check that you're connected to the correct database

### Still getting import errors after migration?
→ Restart your backend server to clear the schema cache:
```bash
# Stop the backend
# Start it again
cd backend
python main.py
```

Or in Supabase, the schema cache should refresh automatically within a few seconds.

## What This Does

Adds 17 new columns to capture all CSV data:
- po_line_text, po_created_by, shopping_cart_number
- document_currency_code, value_in_document_currency
- investment_profile, account_group_level1/2/3
- change_date, purchase_requisition, procurement_plant
- contract_number, joint_commodity_code, po_title
- version, fi_doc_no

After this migration:
- **Before:** 12/35 CSV columns imported (34%)
- **After:** 35/35 CSV columns imported (100%)
