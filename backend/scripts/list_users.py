#!/usr/bin/env python3
"""
List all users in Supabase
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def list_users():
    """List all users in Supabase"""
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_service_key:
        print("❌ Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in .env")
        return False
    
    try:
        # Create Supabase client with service role key
        supabase = create_client(supabase_url, supabase_service_key)
        
        print("🔍 Fetching users from Supabase...")
        
        # Get all users
        response = supabase.auth.admin.list_users()
        
        if not response:
            print("📭 No users found")
            return True
        
        print(f"\n✅ Found {len(response)} user(s):\n")
        print("=" * 100)
        
        for i, user in enumerate(response, 1):
            email = user.email
            user_id = user.id
            created_at = user.created_at
            last_sign_in = getattr(user, 'last_sign_in_at', 'Never')
            
            # Get user metadata
            user_metadata = getattr(user, 'user_metadata', {})
            role = user_metadata.get('role', 'user')
            
            print(f"\n{i}. User Details:")
            print(f"   Email:          {email}")
            print(f"   User ID:        {user_id}")
            print(f"   Role:           {role}")
            print(f"   Created:        {created_at}")
            print(f"   Last Sign In:   {last_sign_in}")
            print("-" * 100)
        
        return True
        
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 100)
    print("👥 Supabase Users List")
    print("=" * 100)
    
    success = list_users()
    
    if success:
        print("\n" + "=" * 100)
        print("✅ User list completed!")
        print("=" * 100)
        sys.exit(0)
    else:
        print("\n" + "=" * 100)
        print("❌ Failed to list users!")
        print("=" * 100)
        sys.exit(1)
