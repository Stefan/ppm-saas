
-- Integrated Master Schedule System Tables
-- Execute this SQL in the Supabase SQL Editor

-- Create custom types
CREATE TYPE IF NOT EXISTS dependency_type AS ENUM (
    'finish_to_start',
    'start_to_start', 
    'finish_to_finish',
    'start_to_finish'
);

CREATE TYPE IF NOT EXISTS task_status AS ENUM (
    'not_started',
    'in_progress',
    'completed',
    'on_hold',
    'cancelled'
);

CREATE TYPE IF NOT EXISTS milestone_status AS ENUM (
    'planned',
    'at_risk',
    'achieved',
    'missed'
);

-- Main schedules table
CREATE TABLE IF NOT EXISTS schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    baseline_start_date DATE,
    baseline_end_date DATE,
    status VARCHAR(50) DEFAULT 'active',
    
    -- Schedule metadata
    created_by UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Performance tracking
    schedule_performance_index DECIMAL(5,3),
    schedule_variance_days INTEGER,
    
    CONSTRAINT schedules_date_check CHECK (end_date >= start_date)
);

-- Tasks table with WBS support
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
    created_by UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT tasks_date_check CHECK (planned_end_date >= planned_start_date),
    CONSTRAINT tasks_wbs_unique UNIQUE (schedule_id, wbs_code)
);

-- Task dependencies
CREATE TABLE IF NOT EXISTS task_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    predecessor_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    successor_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type dependency_type NOT NULL DEFAULT 'finish_to_start',
    lag_days INTEGER DEFAULT 0,
    
    created_by UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT no_self_dependency CHECK (predecessor_task_id != successor_task_id),
    CONSTRAINT unique_dependency UNIQUE (predecessor_task_id, successor_task_id)
);

-- WBS elements (for detailed work breakdown structure)
CREATE TABLE IF NOT EXISTS wbs_elements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
    parent_element_id UUID REFERENCES wbs_elements(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    
    -- WBS identification
    wbs_code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Hierarchy information
    level_number INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0,
    
    -- Work package information
    work_package_manager UUID REFERENCES auth.users(id),
    deliverable_description TEXT,
    acceptance_criteria TEXT,
    
    -- Progress rollup
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    
    created_by UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT wbs_elements_code_unique UNIQUE (schedule_id, wbs_code)
);

-- Schedule baselines for version control
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
    approved_by UUID REFERENCES auth.users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    
    created_by UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Resource assignments to tasks
CREATE TABLE IF NOT EXISTS task_resource_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    resource_id UUID NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
    
    -- Assignment details
    allocation_percentage INTEGER NOT NULL DEFAULT 100 CHECK (allocation_percentage > 0 AND allocation_percentage <= 100),
    planned_hours DECIMAL(8,2),
    actual_hours DECIMAL(8,2),
    
    -- Assignment period
    assignment_start_date DATE,
    assignment_end_date DATE,
    
    created_by UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_task_resource UNIQUE (task_id, resource_id)
);

-- Enhance existing milestones table
DO $$
BEGIN
    -- Add schedule_id column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'milestones' AND column_name = 'schedule_id') THEN
        ALTER TABLE milestones ADD COLUMN schedule_id UUID REFERENCES schedules(id) ON DELETE CASCADE;
    END IF;
    
    -- Add task_id column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'milestones' AND column_name = 'task_id') THEN
        ALTER TABLE milestones ADD COLUMN task_id UUID REFERENCES tasks(id) ON DELETE SET NULL;
    END IF;
    
    -- Add additional milestone fields
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'milestones' AND column_name = 'success_criteria') THEN
        ALTER TABLE milestones ADD COLUMN success_criteria TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'milestones' AND column_name = 'responsible_party') THEN
        ALTER TABLE milestones ADD COLUMN responsible_party UUID REFERENCES auth.users(id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'milestones' AND column_name = 'deliverables') THEN
        ALTER TABLE milestones ADD COLUMN deliverables JSONB DEFAULT '[]';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'milestones' AND column_name = 'approval_required') THEN
        ALTER TABLE milestones ADD COLUMN approval_required BOOLEAN DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'milestones' AND column_name = 'approved_by') THEN
        ALTER TABLE milestones ADD COLUMN approved_by UUID REFERENCES auth.users(id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'milestones' AND column_name = 'approved_at') THEN
        ALTER TABLE milestones ADD COLUMN approved_at TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;

-- Create performance indexes
CREATE INDEX IF NOT EXISTS idx_schedules_project_id ON schedules(project_id);
CREATE INDEX IF NOT EXISTS idx_schedules_status ON schedules(status);
CREATE INDEX IF NOT EXISTS idx_schedules_dates ON schedules(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_tasks_schedule_id ON tasks(schedule_id);
CREATE INDEX IF NOT EXISTS idx_tasks_parent_task_id ON tasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_wbs_code ON tasks(schedule_id, wbs_code);
CREATE INDEX IF NOT EXISTS idx_tasks_dates ON tasks(planned_start_date, planned_end_date);
CREATE INDEX IF NOT EXISTS idx_tasks_critical ON tasks(is_critical) WHERE is_critical = TRUE;
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

CREATE INDEX IF NOT EXISTS idx_task_dependencies_predecessor ON task_dependencies(predecessor_task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_successor ON task_dependencies(successor_task_id);

CREATE INDEX IF NOT EXISTS idx_wbs_elements_schedule_id ON wbs_elements(schedule_id);
CREATE INDEX IF NOT EXISTS idx_wbs_elements_parent ON wbs_elements(parent_element_id);
CREATE INDEX IF NOT EXISTS idx_wbs_elements_level ON wbs_elements(level_number);

CREATE INDEX IF NOT EXISTS idx_schedule_baselines_schedule_id ON schedule_baselines(schedule_id);
CREATE INDEX IF NOT EXISTS idx_task_resource_assignments_task ON task_resource_assignments(task_id);
CREATE INDEX IF NOT EXISTS idx_task_resource_assignments_resource ON task_resource_assignments(resource_id);

-- Apply updated_at triggers to new tables (assuming update_updated_at_column function exists)
CREATE TRIGGER update_schedules_updated_at BEFORE UPDATE ON schedules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_wbs_elements_updated_at BEFORE UPDATE ON wbs_elements FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_task_resource_assignments_updated_at BEFORE UPDATE ON task_resource_assignments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Apply audit triggers (assuming audit_trigger_function exists)
CREATE TRIGGER audit_schedules AFTER INSERT OR UPDATE OR DELETE ON schedules FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_tasks AFTER INSERT OR UPDATE OR DELETE ON tasks FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_task_dependencies AFTER INSERT OR UPDATE OR DELETE ON task_dependencies FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_wbs_elements AFTER INSERT OR UPDATE OR DELETE ON wbs_elements FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_schedule_baselines AFTER INSERT OR UPDATE OR DELETE ON schedule_baselines FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_task_resource_assignments AFTER INSERT OR UPDATE OR DELETE ON task_resource_assignments FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
