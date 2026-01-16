#!/usr/bin/env python3
"""
Script to check authentication status and list users.

Usage:
    python scripts/check_auth_status.py
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from config.database import supabase
from config.settings import settings


def list_all_users():
    """List all users in the system"""
    try:
        print("\n👥 Users in Supabase Auth:")
        print("-" * 80)
        
        # Try to list users using admin API
        try:
            response = supabase.auth.admin.list_users()
            
            if not response:
                print("  No users found or unable to access admin API")
                return []
            
            users = []
            for user in response:
                print(f"\n  📧 Email: {user.email}")
                print(f"     ID: {user.id}")
                print(f"     Created: {user.created_at}")
                print(f"     Last Sign In: {user.last_sign_in_at or 'Never'}")
                users.append(user)
            
            return users
            
        except Exception as e:
            print(f"  ⚠️  Cannot access admin API: {e}")
            print(f"  💡 This is normal if you don't have service role key")
            return []
            
    except Exception as e:
        print(f"  ❌ Error listing users: {e}")
        return []


def list_roles():
    """List all roles in the system"""
    try:
        print("\n🎭 Roles in Database:")
        print("-" * 80)
        
        response = supabase.table("roles").select("*").execute()
        
        if not response.data:
            print("  No roles found")
            return []
        
        for role in response.data:
            print(f"\n  📋 Role: {role['name']}")
            print(f"     ID: {role['id']}")
            print(f"     Description: {role.get('description', 'N/A')}")
            print(f"     Permissions: {len(role.get('permissions', []))} permissions")
        
        return response.data
        
    except Exception as e:
        print(f"  ❌ Error listing roles: {e}")
        return []


def list_user_role_assignments():
    """List all user-role assignments"""
    try:
        print("\n🔗 User-Role Assignments:")
        print("-" * 80)
        
        response = supabase.table("user_roles").select(
            "*, roles(name, description)"
        ).execute()
        
        if not response.data:
            print("  No role assignments found")
            return []
        
        for assignment in response.data:
            role = assignment.get("roles", {})
            print(f"\n  User ID: {assignment['user_id']}")
            print(f"  Role: {role.get('name', 'Unknown')}")
            print(f"  Description: {role.get('description', 'N/A')}")
        
        return response.data
        
    except Exception as e:
        print(f"  ❌ Error listing role assignments: {e}")
        return []


def check_environment():
    """Check environment configuration"""
    print("\n🔍 Environment Configuration:")
    print("-" * 80)
    print(f"  Environment: {settings.environment}")
    print(f"  Base URL: {settings.base_url}")
    print(f"  SUPABASE_URL: {'✅ Set' if settings.SUPABASE_URL else '❌ Not set'}")
    print(f"  SUPABASE_ANON_KEY: {'✅ Set' if settings.SUPABASE_ANON_KEY else '❌ Not set'}")
    print(f"  SUPABASE_SERVICE_ROLE_KEY: {'✅ Set' if settings.SUPABASE_SERVICE_ROLE_KEY else '❌ Not set'}")
    print(f"  OPENAI_API_KEY: {'✅ Set' if settings.OPENAI_API_KEY else '❌ Not set'}")


def check_development_mode():
    """Check if development mode is active"""
    print("\n🔧 Development Mode:")
    print("-" * 80)
    
    # Check if auth dependencies.py has development fallback
    try:
        from auth.dependencies import get_current_user
        print("  ✅ Development mode is ACTIVE")
        print("  💡 Default user ID: 00000000-0000-0000-0000-000000000001")
        print("  💡 This user automatically gets admin permissions")
        print("\n  📝 How it works:")
        print("     - If no auth token is provided, uses default dev user")
        print("     - Default dev user gets all admin permissions")
        print("     - This allows testing without Supabase auth")
    except Exception as e:
        print(f"  ❌ Error checking development mode: {e}")


def main():
    """Main function"""
    print("=" * 80)
    print("🔐 Authentication Status Check")
    print("=" * 80)
    
    # Check Supabase connection
    if not supabase:
        print("\n❌ Supabase client not initialized")
        print("💡 Check your .env file for SUPABASE_URL and SUPABASE_ANON_KEY")
        sys.exit(1)
    
    print("\n✅ Supabase client initialized")
    
    # Check environment
    check_environment()
    
    # Check development mode
    check_development_mode()
    
    # List users
    users = list_all_users()
    
    # List roles
    roles = list_roles()
    
    # List role assignments
    assignments = list_user_role_assignments()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Summary:")
    print("=" * 80)
    print(f"  Users: {len(users)}")
    print(f"  Roles: {len(roles)}")
    print(f"  Role Assignments: {len(assignments)}")
    
    if not assignments and users:
        print("\n⚠️  WARNING: You have users but no role assignments!")
        print("💡 Use add_admin_user.py to assign admin role to a user")
    
    print("\n💡 Next steps:")
    print("  1. To add admin role to a user:")
    print("     python scripts/add_admin_user.py <email>")
    print("\n  2. To use development mode (no auth required):")
    print("     - Just start the backend with ./start-dev.sh")
    print("     - Default dev user gets admin permissions automatically")
    print("\n  3. To disable Vercel auth and use Supabase auth:")
    print("     - See AUTH_SETUP_GUIDE.md for instructions")


if __name__ == "__main__":
    main()
