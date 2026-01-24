-- Migration 037: Fix RLS policies for commitments and actuals tables
-- Allow authenticated users to read commitments and actuals data

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view commitments" ON commitments;
DROP POLICY IF EXISTS "Users can view actuals" ON actuals;
DROP POLICY IF EXISTS "Users can insert commitments" ON commitments;
DROP POLICY IF EXISTS "Users can insert actuals" ON actuals;

-- Enable RLS on both tables
ALTER TABLE commitments ENABLE ROW LEVEL SECURITY;
ALTER TABLE actuals ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read all commitments
CREATE POLICY "Users can view commitments"
ON commitments
FOR SELECT
TO authenticated
USING (true);

-- Allow authenticated users to read all actuals
CREATE POLICY "Users can view actuals"
ON actuals
FOR SELECT
TO authenticated
USING (true);

-- Allow service role to insert commitments (for imports)
CREATE POLICY "Service role can insert commitments"
ON commitments
FOR INSERT
TO service_role
WITH CHECK (true);

-- Allow service role to insert actuals (for imports)
CREATE POLICY "Service role can insert actuals"
ON actuals
FOR INSERT
TO service_role
WITH CHECK (true);

-- Allow users with data_import permission to insert (optional, for future use)
CREATE POLICY "Users with data_import can insert commitments"
ON commitments
FOR INSERT
TO authenticated
WITH CHECK (
  EXISTS (
    SELECT 1 FROM user_permissions up
    WHERE up.user_id = auth.uid()
    AND up.permission = 'data_import'
  )
);

CREATE POLICY "Users with data_import can insert actuals"
ON actuals
FOR INSERT
TO authenticated
WITH CHECK (
  EXISTS (
    SELECT 1 FROM user_permissions up
    WHERE up.user_id = auth.uid()
    AND up.permission = 'data_import'
  )
);
