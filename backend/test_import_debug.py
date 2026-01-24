"""
Debug script to test commitment import with actual CSV data
"""
import asyncio
import csv
from config.database import service_supabase
from services.actuals_commitments_import import ActualsCommitmentsImportService

async def test_import():
    # Read a few rows from the CSV
    with open('../data/Combined_Commitments_DIA_UATNEW_short.csv', 'r', encoding='utf-8') as f:
        # Detect delimiter
        first_line = f.readline()
        delimiter = ';' if ';' in first_line else ','
        f.seek(0)
        
        reader = csv.DictReader(f, delimiter=delimiter)
        rows = list(reader)[:5]  # Just test with 5 rows
    
    print(f"Read {len(rows)} rows from CSV")
    print(f"First row keys: {list(rows[0].keys())}")
    print(f"First row sample: {rows[0]}")
    
    # Map columns
    from routers.csv_import import map_csv_columns
    mapped_rows = map_csv_columns(rows, 'commitments')
    
    print(f"\nMapped first row: {mapped_rows[0]}")
    
    # Try import with service role client
    if not service_supabase:
        print("\n❌ Service role client not available!")
        print("Make sure SUPABASE_SERVICE_ROLE_KEY is set in .env")
        return
    
    service = ActualsCommitmentsImportService(service_supabase, "test-user")
    result = await service.import_commitments(mapped_rows, anonymize=False)
    
    print(f"\nImport Result:")
    print(f"  Success: {result.success}")
    print(f"  Total: {result.total_records}")
    print(f"  Imported: {result.success_count}")
    print(f"  Duplicates: {result.duplicate_count}")
    print(f"  Errors: {result.error_count}")
    
    if result.errors:
        print(f"\nFirst 5 errors:")
        for err in result.errors[:5]:
            print(f"  Row {err.row}: {err.field} = {err.value} -> {err.error}")
    
    if result.success_count > 0:
        print(f"\n✅ Successfully imported {result.success_count} records!")

if __name__ == "__main__":
    asyncio.run(test_import())
