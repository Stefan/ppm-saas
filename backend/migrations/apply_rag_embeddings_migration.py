#!/usr/bin/env python3
"""
Apply RAG Embeddings System Migration
Creates the embeddings table and vector search infrastructure
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_migration():
    """Apply the RAG embeddings system migration"""
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        return False
    
    print("🔄 Connecting to Supabase...")
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Read migration file
    migration_file = Path(__file__).parent / "026_rag_embeddings_system.sql"
    
    if not migration_file.exists():
        print(f"❌ Error: Migration file not found: {migration_file}")
        return False
    
    print(f"📖 Reading migration file: {migration_file.name}")
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    # Split into individual statements (simple split by semicolon)
    # Note: This is a simple approach and may not work for complex SQL
    statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]
    
    print(f"📝 Found {len(statements)} SQL statements to execute")
    
    # Execute each statement
    success_count = 0
    error_count = 0
    
    for i, statement in enumerate(statements, 1):
        # Skip comments and empty statements
        if not statement or statement.startswith('--'):
            continue
        
        try:
            # For CREATE EXTENSION, CREATE TABLE, CREATE INDEX, CREATE FUNCTION
            # we need to use the SQL editor or RPC
            print(f"⏳ Executing statement {i}/{len(statements)}...")
            
            # Try to execute via RPC (if available)
            try:
                result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                print(f"✅ Statement {i} executed successfully")
                success_count += 1
            except Exception as rpc_error:
                # If RPC doesn't exist, we need to execute via SQL editor
                # This is a limitation - Supabase client doesn't support arbitrary SQL
                print(f"⚠️  Statement {i} requires manual execution via Supabase SQL Editor")
                print(f"   Statement preview: {statement[:100]}...")
                error_count += 1
                
        except Exception as e:
            print(f"❌ Error executing statement {i}: {str(e)}")
            print(f"   Statement: {statement[:200]}...")
            error_count += 1
    
    print("\n" + "="*60)
    print(f"✅ Successfully executed: {success_count} statements")
    if error_count > 0:
        print(f"⚠️  Requires manual execution: {error_count} statements")
        print("\n📋 MANUAL STEPS REQUIRED:")
        print("1. Open Supabase Dashboard → SQL Editor")
        print("2. Copy the contents of 026_rag_embeddings_system.sql")
        print("3. Paste and execute in the SQL Editor")
        print("4. Verify the embeddings table was created")
    print("="*60)
    
    return error_count == 0

def verify_migration():
    """Verify the migration was applied successfully"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        return False
    
    print("\n🔍 Verifying migration...")
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # Try to query the embeddings table
        result = supabase.table("embeddings").select("id").limit(1).execute()
        print("✅ Embeddings table exists and is accessible")
        
        # Try to call the vector_similarity_search function
        try:
            # Create a dummy embedding vector (1536 dimensions of zeros)
            dummy_embedding = [0.0] * 1536
            result = supabase.rpc('vector_similarity_search', {
                'query_embedding': dummy_embedding,
                'similarity_limit': 1
            }).execute()
            print("✅ vector_similarity_search function is available")
        except Exception as e:
            print(f"⚠️  vector_similarity_search function not available: {str(e)}")
            return False
        
        # Try to call get_embedding_stats
        try:
            result = supabase.rpc('get_embedding_stats', {}).execute()
            print("✅ get_embedding_stats function is available")
        except Exception as e:
            print(f"⚠️  get_embedding_stats function not available: {str(e)}")
            return False
        
        print("\n✅ Migration verification successful!")
        return True
        
    except Exception as e:
        print(f"❌ Migration verification failed: {str(e)}")
        print("\n📋 Please apply the migration manually:")
        print("1. Open Supabase Dashboard → SQL Editor")
        print("2. Copy the contents of 026_rag_embeddings_system.sql")
        print("3. Paste and execute in the SQL Editor")
        return False

if __name__ == "__main__":
    print("="*60)
    print("RAG Embeddings System Migration")
    print("="*60)
    
    # Apply migration
    success = apply_migration()
    
    if success:
        # Verify migration
        verify_migration()
    else:
        print("\n⚠️  Migration requires manual execution via Supabase SQL Editor")
        print("   See instructions above")
    
    print("\n" + "="*60)
    print("Migration process complete")
    print("="*60)
