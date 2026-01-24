-- ============================================================================
-- Migration 034: Add Missing Columns to Commitments Table
-- Migration 035: Add Missing Columns to Actuals Table
-- Migration 036: Add Performance Indexes for ULTRA FAST Import
-- Copy this entire file and paste into Supabase SQL Editor, then click RUN
-- ============================================================================

-- ============================================================================
-- MIGRATION 034: COMMITMENTS TABLE
-- ============================================================================

-- Add all missing columns to commitments
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS po_line_text TEXT;
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS po_created_by VARCHAR(255);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS shopping_cart_number VARCHAR(100);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS document_currency_code VARCHAR(3);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS value_in_document_currency DECIMAL(15, 2);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS investment_profile VARCHAR(50);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS account_group_level1 VARCHAR(100);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS account_subgroup_level2 VARCHAR(100);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS account_level3 VARCHAR(100);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS change_date DATE;
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS purchase_requisition VARCHAR(100);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS procurement_plant VARCHAR(100);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS contract_number VARCHAR(100);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS joint_commodity_code VARCHAR(100);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS po_title TEXT;
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS version VARCHAR(50);
ALTER TABLE commitments ADD COLUMN IF NOT EXISTS fi_doc_no VARCHAR(50);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_commitments_po_created_by ON commitments(po_created_by);
CREATE INDEX IF NOT EXISTS idx_commitments_investment_profile ON commitments(investment_profile);
CREATE INDEX IF NOT EXISTS idx_commitments_contract_number ON commitments(contract_number);
CREATE INDEX IF NOT EXISTS idx_commitments_change_date ON commitments(change_date);
CREATE INDEX IF NOT EXISTS idx_commitments_fi_doc_no ON commitments(fi_doc_no);

-- Verify commitments columns were added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'commitments' 
  AND column_name IN (
    'po_line_text', 'po_created_by', 'shopping_cart_number',
    'document_currency_code', 'value_in_document_currency',
    'investment_profile', 'account_group_level1', 'account_subgroup_level2',
    'account_level3', 'change_date', 'purchase_requisition',
    'procurement_plant', 'contract_number', 'joint_commodity_code',
    'po_title', 'version', 'fi_doc_no'
  )
ORDER BY column_name;

-- Show total commitments column count (should be 45+)
SELECT COUNT(*) as total_commitments_columns 
FROM information_schema.columns 
WHERE table_name = 'commitments';

-- ============================================================================
-- MIGRATION 035: ACTUALS TABLE
-- ============================================================================

-- Add all missing columns to actuals
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS document_type_desc VARCHAR(500);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS po_no VARCHAR(50);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS po_line_no INTEGER;
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS vendor_invoice_no VARCHAR(100);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS project_description VARCHAR(500);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS wbs_description VARCHAR(500);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS gl_account VARCHAR(50);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS gl_account_desc VARCHAR(500);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS cost_center VARCHAR(50);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS cost_center_desc VARCHAR(500);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS product_desc VARCHAR(500);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS document_header_text TEXT;
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS payment_terms VARCHAR(100);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS net_due_date DATE;
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS creation_date DATE;
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS sap_invoice_no VARCHAR(100);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS investment_profile VARCHAR(50);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS account_group_level1 VARCHAR(100);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS account_subgroup_level2 VARCHAR(100);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS account_level3 VARCHAR(100);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS value_in_document_currency DECIMAL(15, 2);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS document_currency_code VARCHAR(3);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS quantity DECIMAL(15, 3);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS personnel_number VARCHAR(50);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS po_final_invoice_indicator VARCHAR(10);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS value_type VARCHAR(50);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS miro_invoice_no VARCHAR(100);
ALTER TABLE actuals ADD COLUMN IF NOT EXISTS goods_received_value DECIMAL(15, 2);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_actuals_po_no ON actuals(po_no);
CREATE INDEX IF NOT EXISTS idx_actuals_vendor_invoice_no ON actuals(vendor_invoice_no);
CREATE INDEX IF NOT EXISTS idx_actuals_gl_account ON actuals(gl_account);
CREATE INDEX IF NOT EXISTS idx_actuals_cost_center ON actuals(cost_center);
CREATE INDEX IF NOT EXISTS idx_actuals_investment_profile ON actuals(investment_profile);
CREATE INDEX IF NOT EXISTS idx_actuals_creation_date ON actuals(creation_date);
CREATE INDEX IF NOT EXISTS idx_actuals_sap_invoice_no ON actuals(sap_invoice_no);
CREATE INDEX IF NOT EXISTS idx_actuals_personnel_number ON actuals(personnel_number);

-- Verify actuals columns were added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'actuals' 
  AND column_name IN (
    'document_type_desc', 'po_no', 'po_line_no', 'vendor_invoice_no',
    'project_description', 'wbs_description', 'gl_account', 'gl_account_desc',
    'cost_center', 'cost_center_desc', 'product_desc', 'document_header_text',
    'payment_terms', 'net_due_date', 'creation_date', 'sap_invoice_no',
    'investment_profile', 'account_group_level1', 'account_subgroup_level2',
    'account_level3', 'value_in_document_currency', 'document_currency_code',
    'quantity', 'personnel_number', 'po_final_invoice_indicator', 'value_type',
    'miro_invoice_no', 'goods_received_value'
  )
ORDER BY column_name;

-- Show total actuals column count (should be 39+)
SELECT COUNT(*) as total_actuals_columns 
FROM information_schema.columns 
WHERE table_name = 'actuals';

-- ============================================================================
-- SUMMARY
-- ============================================================================
SELECT 
  'commitments' as table_name,
  COUNT(*) as total_columns
FROM information_schema.columns 
WHERE table_name = 'commitments'
UNION ALL
SELECT 
  'actuals' as table_name,
  COUNT(*) as total_columns
FROM information_schema.columns 
WHERE table_name = 'actuals';


-- ============================================================================
-- MIGRATION 036: PERFORMANCE INDEXES FOR ULTRA FAST IMPORT
-- ============================================================================

-- ACTUALS TABLE INDEXES (CRITICAL for import speed)
CREATE INDEX IF NOT EXISTS idx_actuals_fi_doc_no_fast 
ON actuals(fi_doc_no) 
WHERE fi_doc_no IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_actuals_project_wbs 
ON actuals(project_nr, wbs_element) 
WHERE project_nr IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_actuals_posting_date 
ON actuals(posting_date DESC) 
WHERE posting_date IS NOT NULL;

-- COMMITMENTS TABLE INDEXES (CRITICAL for import speed)
CREATE INDEX IF NOT EXISTS idx_commitments_po_composite_fast 
ON commitments(po_number, po_line_nr) 
WHERE po_number IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_commitments_po_number_fast 
ON commitments(po_number) 
WHERE po_number IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_commitments_project_wbs 
ON commitments(project_nr, wbs_element) 
WHERE project_nr IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_commitments_po_date 
ON commitments(po_date DESC) 
WHERE po_date IS NOT NULL;

-- PROJECTS TABLE INDEXES (CRITICAL for project cache)
CREATE INDEX IF NOT EXISTS idx_projects_name_fast 
ON projects(name) 
WHERE name IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_projects_status 
ON projects(status) 
WHERE status IS NOT NULL;

-- IMPORT AUDIT LOGS INDEXES
CREATE INDEX IF NOT EXISTS idx_import_audit_user_created 
ON import_audit_logs(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_import_audit_type_created 
ON import_audit_logs(import_type, created_at DESC);

-- Update statistics for query optimizer
ANALYZE actuals;
ANALYZE commitments;
ANALYZE projects;
ANALYZE import_audit_logs;

-- Verify performance indexes were created
SELECT 
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('actuals', 'commitments', 'projects')
  AND indexname LIKE '%_fast'
ORDER BY tablename, indexname;
