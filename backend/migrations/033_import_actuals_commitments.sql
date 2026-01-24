-- Migration 033: Import Actuals and Commitments Enhancement
-- This migration enhances the existing actuals and commitments tables to support
-- the new import feature with project linking, anonymization, and audit logging.

-- ============================================================================
-- PART 1: Enhance 'actuals' table
-- Requirements: 8.1, 8.3, 8.4
-- ============================================================================

-- Add missing columns to actuals table if they don't exist
DO $$
BEGIN
    -- Add project_id column for foreign key to projects table
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'actuals' AND column_name = 'project_id') THEN
        ALTER TABLE actuals ADD COLUMN project_id UUID REFERENCES projects(id) ON DELETE SET NULL;
    END IF;
    
    -- Add project_nr column if it doesn't exist (may exist as project_nr already)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'actuals' AND column_name = 'project_nr') THEN
        ALTER TABLE actuals ADD COLUMN project_nr VARCHAR(50);
    END IF;
    
    -- Add vendor_description column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'actuals' AND column_name = 'vendor_description') THEN
        ALTER TABLE actuals ADD COLUMN vendor_description VARCHAR(500);
    END IF;
    
    -- Add document_date column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'actuals' AND column_name = 'document_date') THEN
        ALTER TABLE actuals ADD COLUMN document_date DATE;
    END IF;
    
    -- Add wbs_element column if it doesn't exist (may exist as wbs)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'actuals' AND column_name = 'wbs_element') THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'actuals' AND column_name = 'wbs') THEN
            ALTER TABLE actuals RENAME COLUMN wbs TO wbs_element;
        ELSE
            ALTER TABLE actuals ADD COLUMN wbs_element VARCHAR(100);
        END IF;
    END IF;
    
    -- Add amount column if it doesn't exist (may exist as invoice_amount)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'actuals' AND column_name = 'amount') THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'actuals' AND column_name = 'invoice_amount') THEN
            ALTER TABLE actuals RENAME COLUMN invoice_amount TO amount;
        ELSE
            ALTER TABLE actuals ADD COLUMN amount DECIMAL(15, 2) NOT NULL DEFAULT 0;
        END IF;
    END IF;
    
    -- Add currency column if it doesn't exist (may exist as currency_code)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'actuals' AND column_name = 'currency') THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'actuals' AND column_name = 'currency_code') THEN
            ALTER TABLE actuals RENAME COLUMN currency_code TO currency;
        ELSE
            ALTER TABLE actuals ADD COLUMN currency VARCHAR(3) DEFAULT 'EUR';
        END IF;
    END IF;
    
    -- Add item_text column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'actuals' AND column_name = 'item_text') THEN
        ALTER TABLE actuals ADD COLUMN item_text TEXT;
    END IF;
    
    -- Add document_type column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'actuals' AND column_name = 'document_type') THEN
        ALTER TABLE actuals ADD COLUMN document_type VARCHAR(50);
    END IF;
END $$;

-- Create unique constraint on fi_doc_no if it doesn't exist
-- First drop the old constraint if it exists (organization-based)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'actuals_fi_doc_no_organization_id_key') THEN
        ALTER TABLE actuals DROP CONSTRAINT actuals_fi_doc_no_organization_id_key;
    END IF;
END $$;

-- Add unique constraint on fi_doc_no only (without organization_id)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'unique_actuals_fi_doc_no') THEN
        -- Handle potential duplicates before adding constraint
        DELETE FROM actuals a1
        USING actuals a2
        WHERE a1.id > a2.id AND a1.fi_doc_no = a2.fi_doc_no;
        
        ALTER TABLE actuals ADD CONSTRAINT unique_actuals_fi_doc_no UNIQUE (fi_doc_no);
    END IF;
END $$;

-- Create indexes for actuals table
CREATE INDEX IF NOT EXISTS idx_actuals_project_id ON actuals(project_id);
CREATE INDEX IF NOT EXISTS idx_actuals_project_nr ON actuals(project_nr);
CREATE INDEX IF NOT EXISTS idx_actuals_posting_date ON actuals(posting_date);
CREATE INDEX IF NOT EXISTS idx_actuals_fi_doc_no ON actuals(fi_doc_no);

-- ============================================================================
-- PART 2: Enhance 'commitments' table
-- Requirements: 8.2, 8.3, 8.4
-- ============================================================================

-- Add missing columns to commitments table if they don't exist
DO $$
BEGIN
    -- Add project_id column for foreign key to projects table
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'commitments' AND column_name = 'project_id') THEN
        ALTER TABLE commitments ADD COLUMN project_id UUID REFERENCES projects(id) ON DELETE SET NULL;
    END IF;
    
    -- Add project_nr column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'commitments' AND column_name = 'project_nr') THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'commitments' AND column_name = 'project') THEN
            ALTER TABLE commitments RENAME COLUMN project TO project_nr;
        ELSE
            ALTER TABLE commitments ADD COLUMN project_nr VARCHAR(50);
        END IF;
    END IF;
    
    -- Add po_line_nr column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'commitments' AND column_name = 'po_line_nr') THEN
        ALTER TABLE commitments ADD COLUMN po_line_nr INTEGER DEFAULT 1;
    END IF;
    
    -- Add po_net_amount column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'commitments' AND column_name = 'po_net_amount') THEN
        ALTER TABLE commitments ADD COLUMN po_net_amount DECIMAL(15, 2) NOT NULL DEFAULT 0;
    END IF;
    
    -- Ensure currency column exists (may exist as currency_code)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'commitments' AND column_name = 'currency') THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'commitments' AND column_name = 'currency_code') THEN
            ALTER TABLE commitments RENAME COLUMN currency_code TO currency;
        ELSE
            ALTER TABLE commitments ADD COLUMN currency VARCHAR(3) DEFAULT 'EUR';
        END IF;
    END IF;
END $$;

-- Create unique constraint on (po_number, po_line_nr) if it doesn't exist
-- First drop the old constraint if it exists (organization-based)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'commitments_po_number_organization_id_key') THEN
        ALTER TABLE commitments DROP CONSTRAINT commitments_po_number_organization_id_key;
    END IF;
END $$;

-- Add unique constraint on (po_number, po_line_nr)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'unique_commitments_po_line') THEN
        -- Handle potential duplicates before adding constraint
        DELETE FROM commitments c1
        USING commitments c2
        WHERE c1.id > c2.id 
          AND c1.po_number = c2.po_number 
          AND COALESCE(c1.po_line_nr, 1) = COALESCE(c2.po_line_nr, 1);
        
        ALTER TABLE commitments ADD CONSTRAINT unique_commitments_po_line UNIQUE (po_number, po_line_nr);
    END IF;
END $$;

-- Create indexes for commitments table
CREATE INDEX IF NOT EXISTS idx_commitments_project_id ON commitments(project_id);
CREATE INDEX IF NOT EXISTS idx_commitments_project_nr ON commitments(project_nr);
CREATE INDEX IF NOT EXISTS idx_commitments_po_date ON commitments(po_date);
CREATE INDEX IF NOT EXISTS idx_commitments_po_number ON commitments(po_number);

-- ============================================================================
-- PART 3: Create 'import_audit_logs' table
-- Requirements: 8.5, 10.1, 10.2
-- ============================================================================

CREATE TABLE IF NOT EXISTS import_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    import_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    import_type VARCHAR(20) NOT NULL,
    total_records INTEGER NOT NULL DEFAULT 0,
    success_count INTEGER NOT NULL DEFAULT 0,
    duplicate_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    errors JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Check constraints for import_type and status
    CONSTRAINT valid_import_audit_type CHECK (import_type IN ('actuals', 'commitments')),
    CONSTRAINT valid_import_audit_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'partial'))
);

-- Create indexes for import_audit_logs table
CREATE INDEX IF NOT EXISTS idx_import_audit_logs_user_id ON import_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_import_audit_logs_import_type ON import_audit_logs(import_type);
CREATE INDEX IF NOT EXISTS idx_import_audit_logs_created_at ON import_audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_import_audit_logs_status ON import_audit_logs(status);

-- ============================================================================
-- PART 4: Enable Row Level Security
-- ============================================================================

-- Enable RLS on import_audit_logs
ALTER TABLE import_audit_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for import_audit_logs
DROP POLICY IF EXISTS "Users can view their own import audit logs" ON import_audit_logs;
CREATE POLICY "Users can view their own import audit logs" ON import_audit_logs 
    FOR SELECT USING (
        user_id = auth.uid()::text OR 
        EXISTS (
            SELECT 1 FROM user_roles ur 
            JOIN roles r ON ur.role_id = r.id 
            WHERE ur.user_id = auth.uid() AND r.name IN ('admin', 'manager')
        )
    );

DROP POLICY IF EXISTS "Users can create import audit logs" ON import_audit_logs;
CREATE POLICY "Users can create import audit logs" ON import_audit_logs 
    FOR INSERT WITH CHECK (user_id = auth.uid()::text);

DROP POLICY IF EXISTS "System can update import audit logs" ON import_audit_logs;
CREATE POLICY "System can update import audit logs" ON import_audit_logs 
    FOR UPDATE USING (true);

-- ============================================================================
-- PART 5: Add triggers for updated_at
-- ============================================================================

-- Apply updated_at trigger to actuals if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_actuals_updated_at') THEN
        CREATE TRIGGER update_actuals_updated_at 
            BEFORE UPDATE ON actuals 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Apply updated_at trigger to commitments if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_commitments_updated_at') THEN
        CREATE TRIGGER update_commitments_updated_at 
            BEFORE UPDATE ON commitments 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- ============================================================================
-- PART 6: Comments for documentation
-- ============================================================================

COMMENT ON TABLE import_audit_logs IS 'Audit trail for import operations (actuals and commitments)';
COMMENT ON COLUMN import_audit_logs.import_id IS 'Unique identifier for the import operation';
COMMENT ON COLUMN import_audit_logs.user_id IS 'User who initiated the import';
COMMENT ON COLUMN import_audit_logs.import_type IS 'Type of import: actuals or commitments';
COMMENT ON COLUMN import_audit_logs.total_records IS 'Total number of records in the import file';
COMMENT ON COLUMN import_audit_logs.success_count IS 'Number of successfully imported records';
COMMENT ON COLUMN import_audit_logs.duplicate_count IS 'Number of duplicate records skipped';
COMMENT ON COLUMN import_audit_logs.error_count IS 'Number of records with errors';
COMMENT ON COLUMN import_audit_logs.status IS 'Import status: pending, processing, completed, failed, partial';
COMMENT ON COLUMN import_audit_logs.errors IS 'JSON array of error details with row numbers and field names';

COMMENT ON COLUMN actuals.project_id IS 'Foreign key to projects table for project linking';
COMMENT ON COLUMN actuals.project_nr IS 'Project number (may be anonymized)';
COMMENT ON COLUMN actuals.fi_doc_no IS 'Financial document number (unique identifier)';
COMMENT ON COLUMN actuals.amount IS 'Transaction amount';

COMMENT ON COLUMN commitments.project_id IS 'Foreign key to projects table for project linking';
COMMENT ON COLUMN commitments.project_nr IS 'Project number (may be anonymized)';
COMMENT ON COLUMN commitments.po_number IS 'Purchase order number';
COMMENT ON COLUMN commitments.po_line_nr IS 'Purchase order line number';
