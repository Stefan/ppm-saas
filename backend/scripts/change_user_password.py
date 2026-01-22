#!/usr/bin/env python3
"""
Change user password in Supabase
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def change_password(email: str, new_password: str):
    """Change password for a user"""
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_service_key:
        print("❌ Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in .env")
        return False
    
    try:
        # Create Supabase client with service role key (has admin privileges)
        supabase = create_client(supabase_url, supabase_service_key)
        
        print(f"🔍 Looking for user: {email}")
        
        # Get user by email
        response = supabase.auth.admin.list_users()
        users = [u for u in response if u.email == email]
        
        if not users:
            print(f"❌ User not found: {email}")
            return False
        
        user = users[0]
        user_id = user.id
        
        print(f"✅ Found user: {email} (ID: {user_id})")
        print(f"🔄 Updating password...")
        
        # Update user password using admin API
        supabase.auth.admin.update_user_by_id(
            user_id,
            {"password": new_password}
        )
        
        print(f"✅ Password updated successfully for {email}")
        print(f"\n📝 New credentials:")
        print(f"   Email: {email}")
        print(f"   Password: {new_password}")
        print(f"\n⚠️  Please save these credentials securely!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error changing password: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python change_user_password.py <email> <new_password>")
        print("\nExample:")
        print("  python change_user_password.py stefan.krause@gmail.com NewSecurePass123!")
        sys.exit(1)
    
    email = sys.argv[1]
    new_password = sys.argv[2]
    
    print("=" * 60)
    print("🔐 Change User Password")
    print("=" * 60)
    
    success = change_password(email, new_password)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Password change completed!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ Password change failed!")
        print("=" * 60)
        sys.exit(1)
