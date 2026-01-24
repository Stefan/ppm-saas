#!/usr/bin/env python3
"""
Script to create a test user for E2E testing.

This script creates a test user with admin privileges for Playwright E2E tests.
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from config.database import supabase, service_supabase
from auth.rbac import UserRole, DEFAULT_ROLE_PERMISSIONS


def create_test_user():
    """Create a test user for E2E testing"""
    # Test user credentials
    email = "test-e2e@orkivo.com"
    password = "TestPassword123!"
    
    try:
        print("🧪 Creating Test User for E2E Tests")
        print("=" * 50)
        print(f"📧 Email: {email}")
        
        # Check Supabase connection
        if not service_supabase:
            print("❌ Service role Supabase client not initialized.")
            print("💡 Make sure SUPABASE_SERVICE_ROLE_KEY is set in your .env file")
            return False
        
        # Step 1: Check if user already exists
        print("\n📝 Step 1: Checking if user already exists...")
        try:
            # Try to get user by email
            users_response = service_supabase.auth.admin.list_users()
            existing_user = None
            
            if users_response:
                for user in users_response:
                    if hasattr(user, 'email') and user.email == email:
                        existing_user = user
                        break
            
            if existing_user:
                print(f"ℹ️  User already exists: {existing_user.id}")
                user_id = existing_user.id
            else:
                # Create new user
                print("📝 Creating new user in Supabase Auth...")
                auth_response = service_supabase.auth.admin.create_user({
                    "email": email,
                    "password": password,
                    "email_confirm": True  # Auto-confirm email
                })
                
                if not auth_response or not auth_response.user:
                    print("❌ Failed to create user in Supabase Auth")
                    return False
                
                user_id = auth_response.user.id
                print(f"✅ User created in Auth: {user_id}")
            
        except Exception as e:
            print(f"❌ Error with user creation: {e}")
            return False
        
        # Step 2: Create or update user profile
        print("\n📝 Step 2: Setting up user profile...")
        try:
            # Check if profile exists
            profile_check = service_supabase.table("user_profiles").select("*").eq("user_id", user_id).execute()
            
            if profile_check.data:
                print("ℹ️  User profile already exists, updating...")
                profile_response = service_supabase.table("user_profiles").update({
                    "role": "admin",
                    "is_active": True
                }).eq("user_id", user_id).execute()
            else:
                print("📝 Creating user profile...")
                profile_data = {
                    "user_id": user_id,
                    "role": "admin",
                    "is_active": True
                }
                profile_response = service_supabase.table("user_profiles").insert(profile_data).execute()
            
            print(f"✅ User profile configured")
                
        except Exception as e:
            print(f"⚠️  Error with user profile: {e}")
            print("   Continuing with role assignment...")
        
        # Step 3: Get or create admin role
        print("\n📝 Step 3: Setting up admin role...")
        try:
            # Check if admin role exists
            role_response = service_supabase.table("roles").select("*").eq("name", "admin").execute()
            
            if role_response.data:
                admin_role_id = role_response.data[0]['id']
                print(f"✅ Admin role found: {admin_role_id}")
            else:
                # Create admin role
                print("📝 Creating admin role...")
                admin_permissions = [perm.value for perm in DEFAULT_ROLE_PERMISSIONS[UserRole.admin]]
                
                role_create_response = service_supabase.table("roles").insert({
                    "name": "admin",
                    "description": "Full system administrator with all permissions",
                    "permissions": admin_permissions
                }).execute()
                
                if role_create_response.data:
                    admin_role_id = role_create_response.data[0]['id']
                    print(f"✅ Admin role created: {admin_role_id}")
                else:
                    print("❌ Failed to create admin role")
                    return False
            
        except Exception as e:
            print(f"❌ Error with admin role: {e}")
            return False
        
        # Step 4: Assign admin role to user
        print("\n📝 Step 4: Assigning admin role to user...")
        try:
            # Check if user already has admin role
            existing_assignment = service_supabase.table("user_roles").select("*").eq(
                "user_id", user_id
            ).eq("role_id", admin_role_id).execute()
            
            if existing_assignment.data:
                print("ℹ️  User already has admin role")
            else:
                # Assign admin role
                assignment_response = service_supabase.table("user_roles").insert({
                    "user_id": user_id,
                    "role_id": admin_role_id
                }).execute()
                
                if assignment_response.data:
                    print(f"✅ Admin role assigned to user")
                else:
                    print("❌ Failed to assign admin role")
                    return False
                    
        except Exception as e:
            print(f"⚠️  Error assigning admin role: {e}")
            print("   User might already have the role")
        
        # Success!
        print("\n" + "=" * 50)
        print("✅ SUCCESS! Test user is ready")
        print("=" * 50)
        print(f"\n📧 Email: {email}")
        print(f"🔑 Password: {password}")
        print(f"🆔 User ID: {user_id}")
        print("\n💡 This user can be used for E2E tests")
        print("  Credentials are stored in .env.test")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("\n" + "=" * 50)
    print("  Test User Setup Script")
    print("=" * 50 + "\n")
    
    success = create_test_user()
    
    if not success:
        print("\n❌ Failed to create test user")
        sys.exit(1)
    
    print("\n✅ Test user setup complete!")
    print("   You can now run Playwright tests with:")
    print("   npx playwright test")


if __name__ == "__main__":
    main()
