"""
Quick diagnostic script to check commitments data in the database
"""

from config.database import supabase, service_supabase

def check_commitments():
    print("\n" + "="*80)
    print("CHECKING COMMITMENTS DATA")
    print("="*80)
    
    # Try with regular client
    print("\n1. Checking with regular Supabase client...")
    try:
        response = supabase.table("commitments").select("*", count="exact").limit(5).execute()
        print(f"   ✅ Query successful")
        print(f"   Total count: {response.count if hasattr(response, 'count') else 'unknown'}")
        print(f"   Records returned: {len(response.data or [])}")
        if response.data:
            print(f"   Sample record: {response.data[0]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Try with service role client (bypasses RLS)
    print("\n2. Checking with service role client (bypasses RLS)...")
    try:
        if service_supabase:
            response = service_supabase.table("commitments").select("*", count="exact").limit(5).execute()
            print(f"   ✅ Query successful")
            print(f"   Total count: {response.count if hasattr(response, 'count') else 'unknown'}")
            print(f"   Records returned: {len(response.data or [])}")
            if response.data:
                print(f"   Sample record: {response.data[0]}")
            else:
                print(f"   ⚠️  No records found - table is empty")
        else:
            print(f"   ⚠️  Service role client not available")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Check actuals too
    print("\n3. Checking actuals table...")
    try:
        if service_supabase:
            response = service_supabase.table("actuals").select("*", count="exact").limit(5).execute()
            print(f"   ✅ Query successful")
            print(f"   Total count: {response.count if hasattr(response, 'count') else 'unknown'}")
            print(f"   Records returned: {len(response.data or [])}")
            if response.data:
                print(f"   Sample record: {response.data[0]}")
            else:
                print(f"   ⚠️  No records found - table is empty")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "="*80)
    print("DIAGNOSIS COMPLETE")
    print("="*80)
    print("\nIf both tables are empty, you need to import data via CSV Import.")
    print("If service role shows data but regular client doesn't, check RLS policies.")
    print("\n")

if __name__ == "__main__":
    check_commitments()
