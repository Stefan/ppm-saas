# Migration 034 - Quick Start Guide

## What This Does
Adds 17 missing columns to the `commitments` table so all 35 CSV columns are imported (instead of just 12).

## Quick Steps

### 1. Run the Migration
Copy the SQL from `migrations/034_add_missing_commitment_columns.sql` and run it in Supabase SQL Editor.

**Or use this shortened version:**

```sql
-- Add all missing columns at once
ALTER TABLE commitments 
  ADD COLUMN IF NOT EXISTS po_line_text TEXT,
  ADD COLUMN IF NOT EXISTS po_created_by VARCHAR(255),
  ADD COLUMN IF NOT EXISTS shopping_cart_number VARCHAR(100),
  ADD COLUMN IF NOT EXISTS document_currency_code VARCHAR(3),
  ADD COLUMN IF NOT EXISTS value_in_document_currency DECIMAL(15, 2),
  ADD COLUMN IF NOT EXISTS investment_profile VARCHAR(50),
  ADD COLUMN IF NOT EXISTS account_group_level1 VARCHAR(100),
  ADD COLUMN IF NOT EXISTS account_subgroup_level2 VARCHAR(100),
  ADD COLUMN IF NOT EXISTS account_level3 VARCHAR(100),
  ADD COLUMN IF NOT EXISTS change_date DATE,
  ADD COLUMN IF NOT EXISTS purchase_requisition VARCHAR(100),
  ADD COLUMN IF NOT EXISTS procurement_plant VARCHAR(100),
  ADD COLUMN IF NOT EXISTS contract_number VARCHAR(100),
  ADD COLUMN IF NOT EXISTS joint_commodity_code VARCHAR(100),
  ADD COLUMN IF NOT EXISTS po_title TEXT,
  ADD COLUMN IF NOT EXISTS version VARCHAR(50),
  ADD COLUMN IF NOT EXISTS fi_doc_no VARCHAR(50);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_commitments_po_created_by ON commitments(po_created_by);
CREATE INDEX IF NOT EXISTS idx_commitments_investment_profile ON commitments(investment_profile);
CREATE INDEX IF NOT EXISTS idx_commitments_contract_number ON commitments(contract_number);
CREATE INDEX IF NOT EXISTS idx_commitments_change_date ON commitments(change_date);
CREATE INDEX IF NOT EXISTS idx_commitments_fi_doc_no ON commitments(fi_doc_no);
```

### 2. Verify
```sql
SELECT COUNT(*) FROM information_schema.columns 
WHERE table_name = 'commitments';
```
Should return **45+** columns (was ~28 before).

### 3. Test Import
Upload your CSV file via the frontend CSV Import tab. All 35 columns should now be imported.

## What Changed
- ✅ Database: Added 17 columns + 5 indexes
- ✅ Pydantic Model: Extended with 17 optional fields
- ✅ CSV Mapping: Added mappings for all new columns
- ✅ Import Service: Populates all new fields

## Rollback (if needed)
```sql
ALTER TABLE commitments 
  DROP COLUMN IF EXISTS po_line_text,
  DROP COLUMN IF EXISTS po_created_by,
  DROP COLUMN IF EXISTS shopping_cart_number,
  DROP COLUMN IF EXISTS document_currency_code,
  DROP COLUMN IF EXISTS value_in_document_currency,
  DROP COLUMN IF EXISTS investment_profile,
  DROP COLUMN IF EXISTS account_group_level1,
  DROP COLUMN IF EXISTS account_subgroup_level2,
  DROP COLUMN IF EXISTS account_level3,
  DROP COLUMN IF EXISTS change_date,
  DROP COLUMN IF EXISTS purchase_requisition,
  DROP COLUMN IF EXISTS procurement_plant,
  DROP COLUMN IF EXISTS contract_number,
  DROP COLUMN IF EXISTS joint_commodity_code,
  DROP COLUMN IF EXISTS po_title,
  DROP COLUMN IF EXISTS version,
  DROP COLUMN IF EXISTS fi_doc_no;
```

## Done!
Your import system now captures all CSV data.
