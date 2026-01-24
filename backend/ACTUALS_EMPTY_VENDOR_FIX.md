# Actuals Empty Vendor Fix - Summary

## Problem
Actuals import was failing with validation error:
```
String should have at least 1 character
```

This occurred on rows 1, 4, 8, 9, 10, etc. where the `Vendor` field was empty.

## Root Cause
The `ActualCreate` Pydantic model defined `vendor` as a required field with `min_length=1`:

```python
vendor: str = Field(..., description="Vendor name", min_length=1, max_length=255)
```

But the CSV data has many rows with empty vendor fields.

## Solution
Changed `vendor` from required to optional in the `ActualCreate` model:

```python
vendor: Optional[str] = Field(None, description="Vendor name", max_length=255)
```

Also updated the `anonymize_actual()` method to handle empty vendor fields gracefully.

## Changes Made

### 1. `backend/models/imports.py`
```python
# Before:
vendor: str = Field(..., description="Vendor name", min_length=1, max_length=255)

# After:
vendor: Optional[str] = Field(None, description="Vendor name", max_length=255)
```

### 2. `backend/services/anonymizer.py`
Updated to check if vendor is present and not empty before anonymizing:

```python
# Anonymize vendor name (if present and not empty)
if "vendor" in anonymized and anonymized["vendor"]:
    anonymized["vendor"] = self.anonymize_vendor(anonymized["vendor"])
```

## Result

Now the import will:
- ✅ Accept records with empty vendor fields
- ✅ Store `NULL` in the database for empty vendors
- ✅ Only anonymize vendor when it's present and not empty
- ✅ Continue processing all valid records

## Expected Import Results

For `data/Combined_Actuals_DIA_UATNEW_short.csv` (999 records):
- **Before fix:** 505 imported, 492 errors (empty vendor validation)
- **After fix:** ~999 imported (or close to it, depending on other validation issues)

## Files Modified

1. `backend/models/imports.py` - Made vendor optional
2. `backend/services/anonymizer.py` - Handle empty vendor gracefully

## Testing

Try the import again:
1. Restart backend (if running)
2. Upload `data/Combined_Actuals_DIA_UATNEW_short.csv`
3. Should import successfully with minimal errors

## Note

Empty vendor fields are valid in financial systems when:
- Internal transfers
- System-generated entries
- Certain types of adjustments
- Missing data in source system

Making vendor optional is the correct approach for real-world data.
