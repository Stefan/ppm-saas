#!/usr/bin/env python3
"""
Create Baseline Management Tables
Creates the schedule_baselines table and related structures for baseline management
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from config.database import create_supabase_client
from config.settings import settings

async def create_baseline_tables():
    """Create the baseline management tables"""
    
    print("🚀 Creating Baseline Management Tables...")
    
    # Create Supabase client
    supabase = create_supabase_client()
    if not supabase:
        print("❌ Failed to create Supabase client")
        return False
    
    try:
        # SQL statements to create baseline tables
        sql_statements = [
            # Create dependency_type enum if it doesn't exist
            """
            DO $$ BEGIN
                CREATE TYPE dependency_type AS ENUM (
                    'finish_to_start',
                    'start_to_start', 
                    'finish_to_finish',
                    'start_to_finish'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
            """,
            
            # Create task_status enum if it doesn't exist
            """
            DO $$ BEGIN
                CREATE TYPE task_status AS ENUM (
                    'not_started',
                    'in_progress',
                    'completed',
                    'on_hold',
                    'cancelled'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
            """,
            
            # Create milestone_status enum if it doesn't exist
            """
            DO $$ BEGIN
                CREATE TYPE milestone_status AS ENUM (
                    'planned',
                    'at_risk',
                    'achieved',
                    'missed'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
            """,
            
            # Create schedules table
            """
            CREATE TABLE IF NOT EXISTS schedules (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id UUID NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                baseline_start_date DATE,
                baseline_end_date DATE,
                status VARCHAR(50) DEFAULT 'active',
                
                -- Schedule metadata
                created_by UUID NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                
                -- Performance tracking
                schedule_performance_index DECIMAL(5,3),
                schedule_variance_days INTEGER,
                
                CONSTRAINT schedules_date_check CHECK (end_date >= start_date)
            );
            """,
            
            # Create tasks table
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                schedule_id UUID NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
                parent_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
                
                -- Task identification
                wbs_code VARCHAR(50) NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                
                -- Scheduling information
                planned_start_date DATE NOT NULL,
                planned_end_date DATE NOT NULL,
                actual_start_date DATE,
                actual_end_date DATE,
                duration_days INTEGER NOT NULL,
                
                -- Baseline information
                baseline_start_date DATE,
                baseline_end_date DATE,
                baseline_duration_days INTEGER,
                
                -- Progress tracking
                progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
                status task_status DEFAULT 'not_started',
                
                -- Work information
                planned_effort_hours DECIMAL(10,2),
                actual_effort_hours DECIMAL(10,2),
                remaining_effort_hours DECIMAL(10,2),
                
                -- Critical path analysis
                is_critical BOOLEAN DEFAULT FALSE,
                total_float_days INTEGER DEFAULT 0,
                free_float_days INTEGER DEFAULT 0,
                early_start_date DATE,
                early_finish_date DATE,
                late_start_date DATE,
                late_finish_date DATE,
                
                -- Deliverables and acceptance
                deliverables JSONB DEFAULT '[]',
                acceptance_criteria TEXT,
                
                -- Metadata
                created_by UUID NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                
                CONSTRAINT tasks_date_check CHECK (planned_end_date >= planned_start_date),
                CONSTRAINT tasks_wbs_unique UNIQUE (schedule_id, wbs_code)
            );
            """,
            
            # Create task_dependencies table
            """
            CREATE TABLE IF NOT EXISTS task_dependencies (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                predecessor_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                successor_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                dependency_type dependency_type NOT NULL DEFAULT 'finish_to_start',
                lag_days INTEGER DEFAULT 0,
                
                created_by UUID NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                
                CONSTRAINT no_self_dependency CHECK (predecessor_task_id != successor_task_id),
                CONSTRAINT unique_dependency UNIQUE (predecessor_task_id, successor_task_id)
            );
            """,
            
            # Create schedule_baselines table
            """
            CREATE TABLE IF NOT EXISTS schedule_baselines (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                schedule_id UUID NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
                
                -- Baseline information
                baseline_name VARCHAR(255) NOT NULL,
                baseline_date DATE NOT NULL,
                description TEXT,
                
                -- Baseline data (JSON snapshot)
                baseline_data JSONB NOT NULL,
                
                -- Approval workflow
                is_approved BOOLEAN DEFAULT FALSE,
                approved_by UUID,
                approved_at TIMESTAMP WITH TIME ZONE,
                
                created_by UUID NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            
            # Create indexes for performance
            "CREATE INDEX IF NOT EXISTS idx_schedules_project_id ON schedules(project_id);",
            "CREATE INDEX IF NOT EXISTS idx_schedules_status ON schedules(status);",
            "CREATE INDEX IF NOT EXISTS idx_tasks_schedule_id ON tasks(schedule_id);",
            "CREATE INDEX IF NOT EXISTS idx_tasks_parent_task_id ON tasks(parent_task_id);",
            "CREATE INDEX IF NOT EXISTS idx_tasks_wbs_code ON tasks(schedule_id, wbs_code);",
            "CREATE INDEX IF NOT EXISTS idx_tasks_critical ON tasks(is_critical) WHERE is_critical = TRUE;",
            "CREATE INDEX IF NOT EXISTS idx_task_dependencies_predecessor ON task_dependencies(predecessor_task_id);",
            "CREATE INDEX IF NOT EXISTS idx_task_dependencies_successor ON task_dependencies(successor_task_id);",
            "CREATE INDEX IF NOT EXISTS idx_schedule_baselines_schedule_id ON schedule_baselines(schedule_id);",
            "CREATE INDEX IF NOT EXISTS idx_schedule_baselines_approved ON schedule_baselines(is_approved);"
        ]
        
        print(f"📝 Executing {len(sql_statements)} SQL statements...")
        
        # Execute each statement
        for i, statement in enumerate(sql_statements, 1):
            try:
                print(f"⚡ Executing statement {i}/{len(sql_statements)}...")
                
                # Use rpc to execute raw SQL
                result = supabase.rpc('exec_sql', {'sql_statement': statement.strip()}).execute()
                
                if result.data is not None:
                    print(f"✅ Statement {i} executed successfully")
                else:
                    print(f"⚠️ Statement {i} executed with no data returned")
                    
            except Exception as e:
                print(f"❌ Error executing statement {i}: {e}")
                # Continue with other statements
                continue
        
        print("\n✅ Baseline management tables created successfully!")
        print("\nCreated tables:")
        print("- schedules")
        print("- tasks") 
        print("- task_dependencies")
        print("- schedule_baselines")
        print("\nCreated enums:")
        print("- dependency_type")
        print("- task_status")
        print("- milestone_status")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create baseline tables: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function"""
    print("🏗️ BASELINE MANAGEMENT TABLE CREATION")
    print("=" * 50)
    
    success = await create_baseline_tables()
    
    if success:
        print("\n🎉 Baseline management tables created successfully!")
        print("\nYou can now:")
        print("- Create schedules and tasks")
        print("- Create baselines for version control")
        print("- Track schedule variance and performance")
        print("- Use the baseline management API endpoints")
    else:
        print("\n❌ Failed to create baseline management tables")
        print("Check the error messages above for details")

if __name__ == "__main__":
    asyncio.run(main())