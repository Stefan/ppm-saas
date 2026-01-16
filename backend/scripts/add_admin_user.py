#!/usr/bin/env python3
"""
Script to add admin role to a user in the database.

Usage:
    python scripts/add_admin_user.py <email>
    python scripts/add_admin_user.py --user-id <user_id>
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from config.database import supabase
from auth.rbac import UserRole, DEFAULT_ROLE_PERMISSIONS


def find_user_by_email(email: str):
    """Find user by email in auth.users table"""
    try:
        # Query Supabase auth users
        response = supabase.auth.admin.list_users()
        
        for user in response:
            if user.email == email:
                return user.id
        
        print(f"❌ User with email '{email}' not found")
        return None
    except Exception as e:
        print(f"❌ Error finding user: {e}")
        return None


def get_or_create_admin_role():
    """Get or create the admin role"""
    try:
        # Check if admin role exists
        response = supabase.table("roles").select("*").eq("name", "admin").execute()
        
        if response.data:
            print(f"✅ Admin role found: {response.data[0]['id']}")
            return response.data[0]['id']
        
        # Create admin role if it doesn't exist
        print("📝 Creating admin role...")
        admin_permissions = [perm.value for perm in DEFAULT_ROLE_PERMISSIONS[UserRole.admin]]
        
        # Use service role client for creating roles (bypasses RLS)
        from config.database import service_role_supabase
        
        if not service_role_supabase:
            print("❌ Service role client not available. Cannot create roles.")
            print("💡 Please create the admin role manually in Supabase SQL Editor")
            print("💡 See QUICK_FIX_ADMIN.sql for the SQL script")
            return None
        
        response = service_role_supabase.table("roles").insert({
            "name": "admin",
            "description": "Full system administrator with all permissions",
            "permissions": admin_permissions  # Supabase Python client handles JSONB conversion
        }).execute()
        
        if response.data:
            print(f"✅ Admin role created: {response.data[0]['id']}")
            return response.data[0]['id']
        else:
            print("❌ Failed to create admin role")
            return None
            
    except Exception as e:
        print(f"❌ Error getting/creating admin role: {e}")
        return None


def add_admin_role_to_user(user_id: str):
    """Add admin role to user"""
    try:
        # Get admin role ID
        admin_role_id = get_or_create_admin_role()
        if not admin_role_id:
            return False
        
        # Check if user already has admin role
        response = supabase.table("user_roles").select("*").eq(
            "user_id", user_id
        ).eq("role_id", admin_role_id).execute()
        
        if response.data:
            print(f"ℹ️  User already has admin role")
            return True
        
        # Add admin role to user
        print(f"📝 Adding admin role to user {user_id}...")
        response = supabase.table("user_roles").insert({
            "user_id": user_id,
            "role_id": admin_role_id
        }).execute()
        
        if response.data:
            print(f"✅ Admin role successfully added to user!")
            return True
        else:
            print("❌ Failed to add admin role to user")
            return False
            
    except Exception as e:
        print(f"❌ Error adding admin role: {e}")
        return False


def list_user_roles(user_id: str):
    """List all roles for a user"""
    try:
        response = supabase.table("user_roles").select(
            "*, roles(name, description)"
        ).eq("user_id", user_id).execute()
        
        if not response.data:
            print(f"ℹ️  User has no roles assigned")
            return
        
        print(f"\n📋 User roles:")
        for assignment in response.data:
            role = assignment.get("roles", {})
            print(f"  - {role.get('name')}: {role.get('description')}")
            
    except Exception as e:
        print(f"❌ Error listing user roles: {e}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/add_admin_user.py <email>")
        print("  python scripts/add_admin_user.py --user-id <user_id>")
        print("\nExamples:")
        print("  python scripts/add_admin_user.py user@example.com")
        print("  python scripts/add_admin_user.py --user-id bf1b1732-2449-4987-9fdb-fefa2a93b816")
        sys.exit(1)
    
    # Check Supabase connection
    if not supabase:
        print("❌ Supabase client not initialized. Check your .env file.")
        sys.exit(1)
    
    print("🚀 Admin User Setup")
    print("=" * 50)
    
    # Get user ID
    if sys.argv[1] == "--user-id":
        if len(sys.argv) < 3:
            print("❌ Please provide a user ID")
            sys.exit(1)
        user_id = sys.argv[2]
        print(f"📧 Using user ID: {user_id}")
    else:
        email = sys.argv[1]
        print(f"📧 Looking up user: {email}")
        user_id = find_user_by_email(email)
        if not user_id:
            sys.exit(1)
        print(f"✅ Found user ID: {user_id}")
    
    # Add admin role
    success = add_admin_role_to_user(user_id)
    
    if success:
        print("\n" + "=" * 50)
        print("✅ SUCCESS! User is now an admin")
        print("=" * 50)
        
        # List all roles
        list_user_roles(user_id)
        
        print("\n💡 Next steps:")
        print("  1. Refresh your browser")
        print("  2. Log out and log back in")
        print("  3. Visit http://localhost:3000/admin/performance")
        print("  4. You should now see real performance data!")
    else:
        print("\n❌ Failed to add admin role")
        sys.exit(1)


if __name__ == "__main__":
    main()
