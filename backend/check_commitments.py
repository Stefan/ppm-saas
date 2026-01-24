"""
Check if commitments exist in the database
"""
from config.database import service_supabase

if service_supabase:
    try:
        # Count total commitments
        response = service_supabase.table("commitments").select("*", count="exact").limit(10).execute()
        
        print(f"Total commitments in database: {response.count}")
        print(f"\nFirst 10 records:")
        for i, record in enumerate(response.data, 1):
            print(f"{i}. PO: {record.get('po_number')} Line: {record.get('po_line_nr')} - {record.get('vendor_description')[:50]}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Service role client not available")
