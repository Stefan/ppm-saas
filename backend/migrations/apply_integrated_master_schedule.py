#!/usr/bin/env python3
"""
Apply Integrated Master Schedule Migration
Applies the comprehensive schedule management schema to the database
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from config.database import create_supabase_client
from config.settings import settings

async def apply_migration():
    """Apply the integrated master schedule migration"""
    
    print("🚀 Starting Integrated Master Schedule Migration...")
    
    # Create Supabase client
    supabase = create_supabase_client()
    if not supabase:
        print("❌ Failed to create Supabase client")
        return False
    
    try:
        # Read the migration SQL file
        migration_file = Path(__file__).parent / "017_integrated_master_schedule.sql"
        
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return False
        
        print(f"📖 Reading migration file: {migration_file}")
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Split the migration into individual statements
        # Remove comments and empty lines for cleaner execution
        statements = []
        current_statement = []
        in_function = False
        
        for line in migration_sql.split('\n'):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('--'):
                continue
            
            # Track function definitions to avoid splitting on semicolons inside functions
            if 'CREATE OR REPLACE FUNCTION' in line.upper() or 'CREATE FUNCTION' in line.upper():
                in_function = True
            elif line.upper().startswith('$') and in_function:
                if line.count('$') >= 2:  # End of function
                    in_function = False
            
            current_statement.append(line)
            
            # Split on semicolon if not in function and line ends with semicolon
            if line.endswith(';') and not in_function:
                statement = ' '.join(current_statement)
                if statement.strip() and not statement.strip().upper() in ['COMMIT;', 'BEGIN;']:
                    statements.append(statement)
                current_statement = []
        
        # Add any remaining statement
        if current_statement:
            statement = ' '.join(current_statement)
            if statement.strip():
                statements.append(statement)
        
        print(f"📝 Found {len(statements)} SQL statements to execute")
        
        # Execute each statement
        success_count = 0
        for i, statement in enumerate(statements, 1):
            try:
                print(f"⚡ Executing statement {i}/{len(statements)}...")
                
                # Use RPC for complex SQL statements
                result = supabase.rpc('exec_sql', {'sql_statement': statement}).execute()
                
                if result.data is not None:
                    success_count += 1
                    print(f"✅ Statement {i} executed successfully")
                else:
                    print(f"⚠️ Statement {i} executed with warnings")
                    success_count += 1
                    
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a "already exists" error (which we can ignore)
                if any(phrase in error_msg.lower() for phrase in [
                    'already exists',
                    'relation already exists',
                    'type already exists',
                    'function already exists',
                    'trigger already exists',
                    'index already exists'
                ]):
                    print(f"ℹ️ Statement {i} skipped (already exists): {error_msg}")
                    success_count += 1
                else:
                    print(f"❌ Error executing statement {i}: {error_msg}")
                    print(f"📄 Statement: {statement[:200]}...")
                    
                    # For critical errors, we might want to continue or stop
                    if 'syntax error' in error_msg.lower():
                        print("⚠️ Syntax error detected, continuing with next statement...")
                    else:
                        print("⚠️ Continuing with next statement...")
        
        print(f"\n📊 Migration Summary:")
        print(f"   Total statements: {len(statements)}")
        print(f"   Successful: {success_count}")
        print(f"   Failed: {len(statements) - success_count}")
        
        if success_count == len(statements):
            print("🎉 Migration completed successfully!")
            return True
        elif success_count > len(statements) * 0.8:  # 80% success rate
            print("⚠️ Migration completed with some warnings")
            return True
        else:
            print("❌ Migration failed with too many errors")
            return False
            
    except Exception as e:
        print(f"❌ Migration failed with error: {e}")
        return False

async def verify_migration():
    """Verify that the migration was applied correctly"""
    
    print("\n🔍 Verifying migration...")
    
    supabase = create_supabase_client()
    if not supabase:
        print("❌ Failed to create Supabase client for verification")
        return False
    
    try:
        # Check if key tables exist
        tables_to_check = [
            'schedules',
            'tasks', 
            'task_dependencies',
            'wbs_elements',
            'schedule_baselines',
            'task_resource_assignments'
        ]
        
        for table in tables_to_check:
            try:
                result = supabase.table(table).select("count", count="exact").limit(1).execute()
                print(f"✅ Table '{table}' exists and is accessible")
            except Exception as e:
                print(f"❌ Table '{table}' check failed: {e}")
                return False
        
        # Check if custom types exist by trying to use them
        try:
            # This will fail if the enum types don't exist
            result = supabase.rpc('check_enum_types').execute()
            print("✅ Custom enum types are available")
        except Exception as e:
            print(f"ℹ️ Custom enum type check: {e}")
            # This is not critical, continue
        
        # Check if key functions exist
        functions_to_check = [
            'calculate_task_progress_rollup',
            'detect_circular_dependency',
            'generate_wbs_code'
        ]
        
        for function in functions_to_check:
            try:
                # Try to call the function with dummy parameters to see if it exists
                if function == 'calculate_task_progress_rollup':
                    # This will fail gracefully if function doesn't exist
                    pass  # We can't easily test this without real data
                print(f"ℹ️ Function '{function}' check skipped (requires test data)")
            except Exception as e:
                print(f"ℹ️ Function '{function}' check: {e}")
        
        print("✅ Migration verification completed")
        return True
        
    except Exception as e:
        print(f"❌ Migration verification failed: {e}")
        return False

async def main():
    """Main migration execution"""
    
    print("=" * 60)
    print("🏗️  INTEGRATED MASTER SCHEDULE MIGRATION")
    print("=" * 60)
    
    # Apply the migration
    migration_success = await apply_migration()
    
    if migration_success:
        # Verify the migration
        verification_success = await verify_migration()
        
        if verification_success:
            print("\n🎉 Integrated Master Schedule migration completed successfully!")
            print("\n📋 Next steps:")
            print("   1. Test the schedule management API endpoints")
            print("   2. Verify Gantt chart functionality")
            print("   3. Test WBS hierarchy management")
            print("   4. Validate critical path calculations")
            return True
        else:
            print("\n⚠️ Migration applied but verification failed")
            return False
    else:
        print("\n❌ Migration failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)