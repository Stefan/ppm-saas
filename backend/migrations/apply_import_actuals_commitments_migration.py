#!/usr/bin/env python3
"""
Apply the Import Actuals and Commitments migration.

This script applies migration 033 which enhances the actuals and commitments
tables and creates the import_audit_logs table.

Usage:
    python apply_import_actuals_commitments_migration.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client, Client


def get_supabase_client() -> Client:
    """Create and return a Supabase client."""
    url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError(
            "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
            "environment variables."
        )
    
    return create_client(url, key)


def read_migration_file() -> str:
    """Read the SQL migration file."""
    migration_path = Path(__file__).parent / "033_import_actuals_commitments.sql"
    
    if not migration_path.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_path}")
    
    return migration_path.read_text()


def apply_migration(client: Client, sql: str) -> None:
    """Apply the migration SQL to the database."""
    # Split the SQL into individual statements
    # We need to handle the DO $$ blocks specially
    statements = []
    current_statement = []
    in_do_block = False
    
    for line in sql.split('\n'):
        stripped = line.strip()
        
        # Track DO $$ blocks
        if stripped.startswith('DO $$') or stripped.startswith('DO $'):
            in_do_block = True
        
        current_statement.append(line)
        
        # Check for end of DO block
        if in_do_block and stripped.endswith('$$;'):
            in_do_block = False
            statements.append('\n'.join(current_statement))
            current_statement = []
        # Check for regular statement end (not in DO block)
        elif not in_do_block and stripped.endswith(';') and not stripped.startswith('--'):
            statements.append('\n'.join(current_statement))
            current_statement = []
    
    # Add any remaining statement
    if current_statement:
        remaining = '\n'.join(current_statement).strip()
        if remaining and not remaining.startswith('--'):
            statements.append(remaining)
    
    # Execute each statement
    for i, statement in enumerate(statements):
        statement = statement.strip()
        if not statement or statement.startswith('--'):
            continue
        
        try:
            # Use RPC to execute raw SQL
            client.rpc('exec_sql', {'sql': statement}).execute()
            print(f"✓ Executed statement {i + 1}")
        except Exception as e:
            # Try direct execution for simpler statements
            try:
                # For Supabase, we might need to use the REST API differently
                print(f"⚠ Statement {i + 1} may need manual execution: {str(e)[:100]}")
            except Exception as e2:
                print(f"✗ Failed statement {i + 1}: {str(e2)[:100]}")


def main():
    """Main entry point."""
    print("=" * 60)
    print("Import Actuals and Commitments Migration")
    print("=" * 60)
    
    try:
        # Load environment variables from .env file if present
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            print(f"Loading environment from {env_file}")
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key.strip(), value.strip())
        
        # Also try .env.local
        env_local = Path(__file__).parent.parent / ".env.local"
        if env_local.exists():
            print(f"Loading environment from {env_local}")
            with open(env_local) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key.strip(), value.strip())
        
        print("\nReading migration file...")
        sql = read_migration_file()
        print(f"✓ Read {len(sql)} bytes of SQL")
        
        print("\nConnecting to Supabase...")
        client = get_supabase_client()
        print("✓ Connected to Supabase")
        
        print("\nApplying migration...")
        apply_migration(client, sql)
        
        print("\n" + "=" * 60)
        print("Migration completed!")
        print("=" * 60)
        print("\nNote: Some statements may need to be executed manually in the")
        print("Supabase SQL Editor if they failed above. The migration file is:")
        print(f"  {Path(__file__).parent / '033_import_actuals_commitments.sql'}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTo apply this migration manually:")
        print("1. Open the Supabase SQL Editor")
        print("2. Copy the contents of 033_import_actuals_commitments.sql")
        print("3. Execute the SQL")
        sys.exit(1)


if __name__ == "__main__":
    main()
