-- Setup Admin Role and Assign to User
-- Run this in Supabase SQL Editor

-- Step 1: Disable RLS temporarily (if needed)
-- ALTER TABLE roles DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_roles DISABLE ROW LEVEL SECURITY;

-- Step 2: Create admin role (if not exists)
INSERT INTO roles (name, description, permissions)
VALUES (
  'admin',
  'Full system administrator with all permissions',
  ARRAY[
    'portfolio_create', 'portfolio_read', 'portfolio_update', 'portfolio_delete',
    'project_create', 'project_read', 'project_update', 'project_delete',
    'resource_create', 'resource_read', 'resource_update', 'resource_delete', 'resource_allocate',
    'financial_read', 'financial_create', 'financial_update', 'financial_delete', 'budget_alert_manage',
    'risk_create', 'risk_read', 'risk_update', 'risk_delete',
    'issue_create', 'issue_read', 'issue_update', 'issue_delete',
    'ai_rag_query', 'ai_resource_optimize', 'ai_risk_forecast', 'ai_metrics_read',
    'user_manage', 'role_manage', 'admin_read', 'admin_update', 'admin_delete', 'system_admin', 'data_import',
    'pmr_create', 'pmr_read', 'pmr_update', 'pmr_delete', 'pmr_approve', 'pmr_export', 'pmr_collaborate', 'pmr_ai_insights', 'pmr_template_manage', 'pmr_audit_read',
    'shareable_url_create', 'shareable_url_read', 'shareable_url_revoke', 'shareable_url_manage',
    'simulation_run', 'simulation_read', 'simulation_delete', 'simulation_manage',
    'scenario_create', 'scenario_read', 'scenario_update', 'scenario_delete', 'scenario_compare',
    'change_create', 'change_read', 'change_update', 'change_delete', 'change_approve', 'change_implement', 'change_audit_read',
    'po_breakdown_import', 'po_breakdown_create', 'po_breakdown_read', 'po_breakdown_update', 'po_breakdown_delete',
    'report_generate', 'report_read', 'report_template_create', 'report_template_manage',
    'audit:read', 'audit:export'
  ]
)
ON CONFLICT (name) DO UPDATE
SET permissions = EXCLUDED.permissions,
    description = EXCLUDED.description;

-- Step 3: Find your user ID
-- Replace 'your-email@example.com' with your actual email
SELECT id, email, created_at 
FROM auth.users 
WHERE email = 'your-email@example.com';

-- Step 4: Assign admin role to user
-- Replace 'YOUR-USER-ID-HERE' with the ID from Step 3
INSERT INTO user_roles (user_id, role_id)
VALUES (
  'YOUR-USER-ID-HERE',  -- Replace with your user ID
  (SELECT id FROM roles WHERE name = 'admin')
)
ON CONFLICT (user_id, role_id) DO NOTHING;

-- Step 5: Verify the assignment
SELECT 
  ur.user_id,
  au.email,
  r.name as role_name,
  r.description
FROM user_roles ur
JOIN auth.users au ON ur.user_id = au.id
JOIN roles r ON ur.role_id = r.id
WHERE au.email = 'your-email@example.com';

-- Step 6: Re-enable RLS (if you disabled it)
-- ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;

-- Optional: Create RLS policies to allow authenticated users to read roles
CREATE POLICY "Allow authenticated users to read roles"
ON roles FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Allow authenticated users to read their own role assignments"
ON user_roles FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Optional: Allow service role to manage roles
CREATE POLICY "Allow service role to manage roles"
ON roles FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Allow service role to manage user roles"
ON user_roles FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
