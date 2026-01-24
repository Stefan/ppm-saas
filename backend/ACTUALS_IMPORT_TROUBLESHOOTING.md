# Actuals Import Troubleshooting

## Status Check

✅ **Database Schema**: All columns exist and are correctly named
- fi_doc_no, posting_date, document_date ✅
- vendor, vendor_description ✅
- project_nr, project_id, wbs_element ✅
- amount, currency ✅
- item_text, document_type ✅

✅ **Pydantic Model**: ActualCreate model matches database schema

✅ **Import Service**: Insert logic looks correct

## What Could Be Wrong?

### 1. CSV File Format
The actuals CSV might have different column names than expected.

**Expected columns:**
- fi_doc_no (or FI Doc No)
- posting_date (or Posting Date)
- vendor (or Vendor)
- project_nr (or Project)
- amount (or Amount)
- currency (or Currency)

### 2. Missing Column Mappings
Check if `backend/routers/csv_import.py` has column mappings for actuals like it does for commitments.

### 3. Validation Errors
The CSV data might have:
- Invalid dates
- Invalid amounts
- Missing required fields

## How to Debug

### Step 1: Check the Error Message
What exact error are you seeing? Look for:
- "Could not find column" → Schema issue
- "Validation error" → Data format issue
- "Batch insert failed" → Database constraint issue

### Step 2: Check Backend Logs
```bash
tail -f backend/backend_new.log
```

Look for error messages during import.

### Step 3: Test with Sample Data
Create a minimal actuals CSV:

```csv
FI Doc No;Posting Date;Vendor;Vendor Description;Project;WBS Element;Amount;Currency;Item Text;Document Type
FI-001;2024-01-15;Vendor A;Vendor Description;P0001;WBS-001;1000.00;EUR;Test Item;Invoice
```

Try importing this to see if it works.

### Step 4: Check Column Mappings
Verify that `map_csv_columns()` in `csv_import.py` has mappings for actuals columns.

## Quick Fix

If the issue is missing column mappings, add them to `backend/routers/csv_import.py`:

```python
else:  # actuals
    column_mapping = {
        'FI Doc No': 'fi_doc_no',
        'Posting Date': 'posting_date',
        'Document Date': 'document_date',
        'Vendor': 'vendor',
        'Vendor Description': 'vendor_description',
        'Project': 'project_nr',
        'WBS Element': 'wbs_element',
        'Amount': 'amount',
        'Currency': 'currency',
        'Item Text': 'item_text',
        'Document Type': 'document_type',
    }
```

## Need More Info

Please provide:
1. The exact error message you're seeing
2. A sample of the actuals CSV file (first 3 rows)
3. Any error logs from the backend

This will help identify the exact issue!
