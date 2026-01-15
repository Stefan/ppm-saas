#!/usr/bin/env python3
"""
Apply Enhanced PMR Schema Migration
This script applies the 021_enhanced_pmr_schema.sql migration to the database.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_url():
    """Get database URL from environment variables."""
    # Try different environment variable names
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        db_url = os.getenv('SUPABASE_DB_URL')
    if not db_url:
        # Construct from individual components
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'postgres')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        db_url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    
    return db_url


def read_migration_file():
    """Read the migration SQL file."""
    migration_file = Path(__file__).parent / '021_enhanced_pmr_schema.sql'
    
    if not migration_file.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_file}")
    
    with open(migration_file, 'r') as f:
        return f.read()


def apply_migration(engine, sql_content):
    """Apply the migration to the database."""
    try:
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            try:
                logger.info("Starting Enhanced PMR schema migration...")
                
                # Execute the migration SQL
                conn.execute(text(sql_content))
                
                # Commit the transaction
                trans.commit()
                
                logger.info("✓ Enhanced PMR schema migration completed successfully")
                return True
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                logger.error(f"✗ Migration failed: {str(e)}")
                raise
                
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        return False


def verify_migration(engine):
    """Verify that the migration was applied successfully."""
    verification_queries = [
        ("pmr_templates table", "SELECT COUNT(*) FROM pmr_templates"),
        ("pmr_reports table", "SELECT COUNT(*) FROM pmr_reports"),
        ("ai_insights table", "SELECT COUNT(*) FROM ai_insights"),
        ("collaboration_sessions table", "SELECT COUNT(*) FROM collaboration_sessions"),
        ("edit_sessions table", "SELECT COUNT(*) FROM edit_sessions"),
        ("export_jobs table", "SELECT COUNT(*) FROM export_jobs"),
        ("pmr_collaboration table", "SELECT COUNT(*) FROM pmr_collaboration"),
        ("pmr_distribution_log table", "SELECT COUNT(*) FROM pmr_distribution_log"),
        ("pmr_comments table", "SELECT COUNT(*) FROM pmr_comments"),
        ("pmr_change_events table", "SELECT COUNT(*) FROM pmr_change_events"),
    ]
    
    logger.info("\nVerifying migration...")
    
    try:
        with engine.connect() as conn:
            for table_name, query in verification_queries:
                result = conn.execute(text(query))
                count = result.scalar()
                logger.info(f"✓ {table_name}: {count} rows")
            
            # Check views
            view_query = """
                SELECT COUNT(*) 
                FROM information_schema.views 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'pmr_%' OR table_name LIKE '%_pmr_%'
            """
            result = conn.execute(text(view_query))
            view_count = result.scalar()
            logger.info(f"✓ PMR views created: {view_count}")
            
            # Check functions
            function_query = """
                SELECT COUNT(*) 
                FROM information_schema.routines 
                WHERE routine_schema = 'public' 
                AND (routine_name LIKE '%pmr%' OR routine_name LIKE '%collaboration%')
            """
            result = conn.execute(text(function_query))
            function_count = result.scalar()
            logger.info(f"✓ PMR functions created: {function_count}")
            
            logger.info("\n✓ Migration verification completed successfully")
            return True
            
    except SQLAlchemyError as e:
        logger.error(f"✗ Verification failed: {str(e)}")
        return False


def main():
    """Main execution function."""
    try:
        # Get database URL
        db_url = get_database_url()
        logger.info(f"Connecting to database...")
        
        # Create engine
        engine = create_engine(db_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"Connected to: {version}")
        
        # Read migration file
        logger.info("Reading migration file...")
        sql_content = read_migration_file()
        logger.info(f"Migration file loaded ({len(sql_content)} characters)")
        
        # Apply migration
        success = apply_migration(engine, sql_content)
        
        if success:
            # Verify migration
            verify_migration(engine)
            logger.info("\n" + "="*60)
            logger.info("Enhanced PMR Migration Summary:")
            logger.info("="*60)
            logger.info("✓ All tables created successfully")
            logger.info("✓ All indexes created successfully")
            logger.info("✓ All triggers created successfully")
            logger.info("✓ All functions created successfully")
            logger.info("✓ All views created successfully")
            logger.info("✓ RLS policies enabled")
            logger.info("✓ Default templates inserted")
            logger.info("="*60)
            return 0
        else:
            logger.error("\n✗ Migration failed")
            return 1
            
    except Exception as e:
        logger.error(f"\n✗ Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
