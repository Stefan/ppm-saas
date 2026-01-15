#!/usr/bin/env python3
"""
Verify Enhanced PMR Schema Migration
This script verifies that the Enhanced PMR schema has been properly applied.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_url():
    """Get database URL from environment variables."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        db_url = os.getenv('SUPABASE_DB_URL')
    if not db_url:
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'postgres')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        db_url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    
    return db_url


def verify_tables(engine) -> bool:
    """Verify that all required tables exist."""
    required_tables = [
        'pmr_templates',
        'pmr_reports',
        'ai_insights',
        'collaboration_sessions',
        'edit_sessions',
        'export_jobs',
        'pmr_collaboration',
        'pmr_distribution_log',
        'pmr_comments',
        'pmr_change_events'
    ]
    
    logger.info("\n" + "="*60)
    logger.info("Verifying Tables")
    logger.info("="*60)
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    all_exist = True
    for table in required_tables:
        if table in existing_tables:
            logger.info(f"✓ Table '{table}' exists")
        else:
            logger.error(f"✗ Table '{table}' is missing")
            all_exist = False
    
    return all_exist


def verify_indexes(engine) -> bool:
    """Verify that key indexes exist."""
    key_indexes = [
        ('pmr_reports', 'idx_pmr_reports_project_month'),
        ('pmr_reports', 'idx_pmr_reports_status'),
        ('pmr_reports', 'idx_pmr_reports_collaboration'),
        ('ai_insights', 'idx_ai_insights_report'),
        ('ai_insights', 'idx_ai_insights_confidence'),
        ('collaboration_sessions', 'idx_collaboration_sessions_report'),
        ('export_jobs', 'idx_export_jobs_status'),
    ]
    
    logger.info("\n" + "="*60)
    logger.info("Verifying Key Indexes")
    logger.info("="*60)
    
    all_exist = True
    with engine.connect() as conn:
        for table_name, index_name in key_indexes:
            query = text("""
                SELECT COUNT(*) 
                FROM pg_indexes 
                WHERE tablename = :table_name 
                AND indexname = :index_name
            """)
            result = conn.execute(query, {"table_name": table_name, "index_name": index_name})
            count = result.scalar()
            
            if count > 0:
                logger.info(f"✓ Index '{index_name}' on '{table_name}' exists")
            else:
                logger.error(f"✗ Index '{index_name}' on '{table_name}' is missing")
                all_exist = False
    
    return all_exist


def verify_views(engine) -> bool:
    """Verify that all required views exist."""
    required_views = [
        'pmr_dashboard_summary',
        'pmr_template_analytics',
        'active_edit_sessions',
        'active_collaboration_sessions',
        'export_jobs_status',
        'ai_insights_performance',
        'report_collaboration_activity'
    ]
    
    logger.info("\n" + "="*60)
    logger.info("Verifying Views")
    logger.info("="*60)
    
    all_exist = True
    with engine.connect() as conn:
        for view_name in required_views:
            query = text("""
                SELECT COUNT(*) 
                FROM information_schema.views 
                WHERE table_schema = 'public' 
                AND table_name = :view_name
            """)
            result = conn.execute(query, {"view_name": view_name})
            count = result.scalar()
            
            if count > 0:
                logger.info(f"✓ View '{view_name}' exists")
            else:
                logger.error(f"✗ View '{view_name}' is missing")
                all_exist = False
    
    return all_exist


def verify_functions(engine) -> bool:
    """Verify that all required functions exist."""
    required_functions = [
        'get_latest_pmr_report',
        'calculate_pmr_completeness',
        'cleanup_old_edit_sessions',
        'cleanup_old_collaboration_sessions',
        'get_active_collaborators',
        'get_unresolved_comments',
        'get_ai_insights_summary',
        'archive_old_pmr_reports',
        'get_export_job_statistics',
        'pmr_maintenance_job'
    ]
    
    logger.info("\n" + "="*60)
    logger.info("Verifying Functions")
    logger.info("="*60)
    
    all_exist = True
    with engine.connect() as conn:
        for function_name in required_functions:
            query = text("""
                SELECT COUNT(*) 
                FROM information_schema.routines 
                WHERE routine_schema = 'public' 
                AND routine_name = :function_name
            """)
            result = conn.execute(query, {"function_name": function_name})
            count = result.scalar()
            
            if count > 0:
                logger.info(f"✓ Function '{function_name}' exists")
            else:
                logger.error(f"✗ Function '{function_name}' is missing")
                all_exist = False
    
    return all_exist


def verify_triggers(engine) -> bool:
    """Verify that key triggers exist."""
    key_triggers = [
        ('pmr_reports', 'update_pmr_reports_updated_at'),
        ('ai_insights', 'update_pmr_report_on_insight_change'),
        ('pmr_reports', 'update_template_usage_on_report_create'),
        ('export_jobs', 'validate_export_job_status_trigger'),
    ]
    
    logger.info("\n" + "="*60)
    logger.info("Verifying Key Triggers")
    logger.info("="*60)
    
    all_exist = True
    with engine.connect() as conn:
        for table_name, trigger_name in key_triggers:
            query = text("""
                SELECT COUNT(*) 
                FROM information_schema.triggers 
                WHERE event_object_table = :table_name 
                AND trigger_name = :trigger_name
            """)
            result = conn.execute(query, {"table_name": table_name, "trigger_name": trigger_name})
            count = result.scalar()
            
            if count > 0:
                logger.info(f"✓ Trigger '{trigger_name}' on '{table_name}' exists")
            else:
                logger.error(f"✗ Trigger '{trigger_name}' on '{table_name}' is missing")
                all_exist = False
    
    return all_exist


def verify_rls_policies(engine) -> bool:
    """Verify that RLS is enabled on key tables."""
    rls_tables = [
        'pmr_templates',
        'pmr_reports',
        'ai_insights',
        'collaboration_sessions',
        'edit_sessions',
        'export_jobs'
    ]
    
    logger.info("\n" + "="*60)
    logger.info("Verifying RLS Policies")
    logger.info("="*60)
    
    all_enabled = True
    with engine.connect() as conn:
        for table_name in rls_tables:
            query = text("""
                SELECT relrowsecurity 
                FROM pg_class 
                WHERE relname = :table_name
            """)
            result = conn.execute(query, {"table_name": table_name})
            row = result.fetchone()
            
            if row and row[0]:
                logger.info(f"✓ RLS enabled on '{table_name}'")
            else:
                logger.error(f"✗ RLS not enabled on '{table_name}'")
                all_enabled = False
    
    return all_enabled


def verify_default_data(engine) -> bool:
    """Verify that default templates were inserted."""
    logger.info("\n" + "="*60)
    logger.info("Verifying Default Data")
    logger.info("="*60)
    
    with engine.connect() as conn:
        query = text("SELECT COUNT(*) FROM pmr_templates WHERE is_public = TRUE")
        result = conn.execute(query)
        count = result.scalar()
        
        if count >= 2:
            logger.info(f"✓ Default templates exist ({count} public templates)")
            return True
        else:
            logger.warning(f"⚠ Expected at least 2 default templates, found {count}")
            return False


def main():
    """Main verification function."""
    try:
        # Get database URL
        db_url = get_database_url()
        logger.info("Connecting to database...")
        
        # Create engine
        engine = create_engine(db_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"Connected to: {version}\n")
        
        # Run all verifications
        results = {
            "Tables": verify_tables(engine),
            "Indexes": verify_indexes(engine),
            "Views": verify_views(engine),
            "Functions": verify_functions(engine),
            "Triggers": verify_triggers(engine),
            "RLS Policies": verify_rls_policies(engine),
            "Default Data": verify_default_data(engine)
        }
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("Verification Summary")
        logger.info("="*60)
        
        all_passed = True
        for category, passed in results.items():
            status = "✓ PASSED" if passed else "✗ FAILED"
            logger.info(f"{category}: {status}")
            if not passed:
                all_passed = False
        
        logger.info("="*60)
        
        if all_passed:
            logger.info("\n✓ All verifications passed successfully!")
            return 0
        else:
            logger.error("\n✗ Some verifications failed. Please review the errors above.")
            return 1
            
    except Exception as e:
        logger.error(f"\n✗ Verification error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
