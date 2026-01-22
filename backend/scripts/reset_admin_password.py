#!/usr/bin/env python3
"""
Reset admin password with a secure generated password
"""

import sys
import os
import secrets
import string
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_secure_password(length=16):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password

def reset_password(email: str, new_password: str = None):
    """Reset password for a user"""
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_service_key:
        print("❌ Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in .env")
        return False, None
    
    # Generate password if not provided
    if not new_password:
        new_password = generate_secure_password()
        print(f"🔐 Generated secure password: {new_password}")
    
    try:
        # Create Supabase client with service role key
        supabase = create_client(supabase_url, supabase_service_key)
        
        print(f"🔍 Looking for user: {email}")
        
        # Get user by email
        response = supabase.auth.admin.list_users()
        users = [u for u in response if u.email == email]
        
        if not users:
            print(f"❌ User not found: {email}")
            return False, None
        
        user = users[0]
        user_id = user.id
        
        print(f"✅ Found user: {email} (ID: {user_id})")
        print(f"🔄 Updating password...")
        
        # Update user password using admin API
        supabase.auth.admin.update_user_by_id(
            user_id,
            {"password": new_password}
        )
        
        print(f"✅ Password updated successfully!")
        
        return True, new_password
        
    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        import traceback
        traceback.print_exc()
        return False, None

if __name__ == "__main__":
    print("=" * 80)
    print("🔐 Reset Admin Password")
    print("=" * 80)
    
    # Default admin email
    email = "stefan.krause@gmail.com"
    
    # Check if custom password provided
    new_password = None
    if len(sys.argv) > 1:
        new_password = sys.argv[1]
        print(f"📝 Using provided password")
    else:
        print(f"🎲 Generating secure random password...")
    
    success, password = reset_password(email, new_password)
    
    if success:
        print("\n" + "=" * 80)
        print("✅ PASSWORD RESET SUCCESSFUL!")
        print("=" * 80)
        print(f"\n📝 NEW LOGIN CREDENTIALS:")
        print(f"   Email:    {email}")
        print(f"   Password: {password}")
        print(f"\n⚠️  IMPORTANT: Save these credentials securely!")
        print(f"⚠️  This password will NOT be shown again!")
        print("\n" + "=" * 80)
        
        # Save to file
        credentials_file = backend_dir / "PRODUCTION_ADMIN_CREDENTIALS.txt"
        with open(credentials_file, "w") as f:
            f.write(f"Production Admin Credentials\n")
            f.write(f"============================\n\n")
            f.write(f"Email:    {email}\n")
            f.write(f"Password: {password}\n")
            f.write(f"\nGenerated: {__import__('datetime').datetime.now().isoformat()}\n")
        
        print(f"💾 Credentials saved to: {credentials_file}")
        print(f"⚠️  Keep this file secure and delete after saving elsewhere!")
        print("=" * 80)
        
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("❌ Password reset failed!")
        print("=" * 80)
        sys.exit(1)
