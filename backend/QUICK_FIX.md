# QUICK FIX - Import Failed Error

## Error You're Seeing:
```
Could not find the 'account_group_level1' column of 'commitments' in the schema cache
```

## Why It Failed:
The new columns don't exist in the database yet. You need to add them first!

## Fix (2 minutes):

### 1️⃣ Open Supabase SQL Editor
Go to: https://app.supabase.com → Your Project → **SQL Editor**

### 2️⃣ Copy This SQL:
```sql
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
```

### 3️⃣ Paste and Click RUN

### 4️⃣ Wait for "Success" ✅

### 5️⃣ Try Import Again
Go back to your app and upload the CSV again. It should work now!

---

## Full SQL (with indexes):
If you want the complete version with performance indexes, use `backend/RUN_THIS_IN_SUPABASE.sql`

---

## Still Not Working?
- Wait 10 seconds for Supabase schema cache to refresh
- Or restart your backend server
- Check `backend/MIGRATION_INSTRUCTIONS.md` for detailed troubleshooting
