#!/usr/bin/env python3
"""
Verify Import Actuals and Commitments Migration

This script verifies that the import actuals and commitments schema migration
(033_import_actuals_commitments.sql) has been applied successfully.

Usage:
    python verify_import_actuals_commitments_migration.py
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client, Client


def load_env():
    """Load environment variables from .env files."""
    for env_file in [".env", ".env.local"]:
        env_path = Path(__file__).parent.parent / env_file
        if env_path.exists():
            print(f"Loading environment from {env_path}")
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key.strip(), value.strip())


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


def check_table_exists(client: Client, table_name: str) -> bool:
    """Check if a table exists by attempting to query it."""
    try:
        client.table(table_name).select("*").limit(1).execute()
        return True
    except Exception:
        return False


def check_column_exists(client: Client, table_name: str, column_name: str) -> bool:
    """Check if a column exists by attempting to select it."""
    try:
        client.table(table_name).select(column_name).limit(1).execute()
        return True
    except Exception:
        return False


def verify_actuals_table(client: Client) -> Tuple[bool, List[str]]:
    """Verify the actuals table has all required columns."""
    required_columns = [
        "id", "fi_doc_no", "posting_date", "document_date", "vendor",
        "vendor_description", "project_id", "project_nr", "wbs_element",
        "amount", "currency", "item_text", "document_type", "created_at", "updated_at"
    ]
    
    missing = []
    if not check_table_exists(client, "actuals"):
        return False, ["Table 'actuals' does not exist"]
    
    for col in required_columns:
        if not check_column_exists(client, "actuals", col):
            missing.append(f"Column '{col}' missing from actuals table")
    
    return len(missing) == 0, missing


def verify_commitments_table(client: Client) -> Tuple[bool, List[str]]:
    """Verify the commitments table has all required columns."""
    required_columns = [
        "id", "po_number", "po_date", "vendor", "vendor_description",
        "project_id", "project_nr", "wbs_element", "po_net_amount",
        "total_amount", "currency", "po_status", "po_line_nr",
        "delivery_date", "created_at", "updated_at"
    ]
    
    missing = []
    if not check_table_exists(client, "commitments"):
        return False, ["Table 'commitments' does not exist"]
    
    for col in required_columns:
        if not check_column_exists(client, "commitments", col):
            missing.append(f"Column '{col}' missing from commitments table")
    
    return len(missing) == 0, missing


def verify_import_audit_logs_table(client: Client) -> Tuple[bool, List[str]]:
    """Verify the import_audit_logs table has all required columns."""
    required_columns = [
        "id", "import_id", "user_id", "import_type", "total_records",
        "success_count", "duplicate_count", "error_count", "status",
        "errors", "created_at", "completed_at"
    ]
    
    missing = []
    if not check_table_exists(client, "import_audit_logs"):
        return False, ["Table 'import_audit_logs' does not exist"]
    
    for col in required_columns:
        if not check_column_exists(client, "import_audit_logs", col):
            missing.append(f"Column '{col}' missing from import_audit_logs table")
    
    return len(missing) == 0, missing


def main():
    """Main entry point."""
    print("=" * 70)
    print("Import Actuals and Commitments Migration Verification")
    print("=" * 70)
    
    load_env()
    
    try:
        print("\nConnecting to Supabase...")
        client = get_supabase_client()
        print("✓ Connected to Supabase")
        
        all_passed = True
        
        # Verify actuals table
        print("\n" + "-" * 70)
        print("Verifying 'actuals' table (Requirements 8.1, 8.3, 8.4)...")
        print("-" * 70)
        passed, issues = verify_actuals_table(client)
        if passed:
            print("✓ actuals table: All columns present")
        else:
            all_passed = False
            for issue in issues:
                print(f"✗ {issue}")
        
        # Verify commitments table
        print("\n" + "-" * 70)
        print("Verifying 'commitments' table (Requirements 8.2, 8.3, 8.4)...")
        print("-" * 70)
        passed, issues = verify_commitments_table(client)
        if passed:
            print("✓ commitments table: All columns present")
        else:
            all_passed = False
            for issue in issues:
                print(f"✗ {issue}")
        
        # Verify import_audit_logs table
        print("\n" + "-" * 70)
        print("Verifying 'import_audit_logs' table (Requirements 8.5, 10.1, 10.2)...")
        print("-" * 70)
        passed, issues = verify_import_audit_logs_table(client)
        if passed:
            print("✓ import_audit_logs table: All columns present")
        else:
            all_passed = False
            for issue in issues:
                print(f"✗ {issue}")
        
        # Summary
        print("\n" + "=" * 70)
        if all_passed:
            print("✓ MIGRATION VERIFICATION PASSED")
            print("  All tables and columns are present.")
        else:
            print("✗ MIGRATION VERIFICATION FAILED")
            print("  Some tables or columns are missing.")
            print("\n  To apply the migration:")
            print("  1. Open the Supabase SQL Editor")
            print("  2. Copy the contents of 033_import_actuals_commitments.sql")
            print("  3. Execute the SQL")
        print("=" * 70)
        
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
