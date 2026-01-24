-- QUICK FIX: Allow all authenticated users to view commitments and actuals

-- Enable RLS
ALTER TABLE commitments ENABLE ROW LEVEL SECURITY;
ALTER TABLE actuals ENABLE ROW LEVEL SECURITY;

-- Drop existing restrictive policies
DROP POLICY IF EXISTS "Users can view commitments" ON commitments;
DROP POLICY IF EXISTS "Users can view actuals" ON actuals;

-- Create permissive read policies
CREATE POLICY "Users can view commitments"
ON commitments
FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Users can view actuals"
ON actuals
FOR SELECT
TO authenticated
USING (true);
