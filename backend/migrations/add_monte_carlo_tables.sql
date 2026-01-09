-- Migration: Add Monte Carlo Risk Simulation Tables
-- Created: 2025-01-09
-- Description: Add tables to support Monte Carlo risk simulation functionality

-- Monte Carlo Simulations table
CREATE TABLE IF NOT EXISTS monte_carlo_simulations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Simulation configuration
    iteration_count INTEGER NOT NULL DEFAULT 10000,
    random_seed INTEGER,
    convergence_threshold DECIMAL(10, 6) DEFAULT 0.001,
    
    -- Execution metadata
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, running, completed, failed
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    execution_time DECIMAL(10, 3), -- seconds
    
    -- Results summary (for quick access)
    results_summary JSONB,
    
    -- Convergence metrics
    converged BOOLEAN DEFAULT FALSE,
    convergence_iteration INTEGER,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Monte Carlo Scenarios table
CREATE TABLE IF NOT EXISTS monte_carlo_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id UUID REFERENCES monte_carlo_simulations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Scenario configuration
    is_baseline BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Risk modifications (stored as JSONB)
    risk_modifications JSONB,
    
    -- Scenario results (if simulation has been run)
    results_data JSONB,
    
    -- Audit fields
    created_by UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Monte Carlo Risk Configurations table
CREATE TABLE IF NOT EXISTS monte_carlo_risk_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id UUID NOT NULL REFERENCES monte_carlo_simulations(id) ON DELETE CASCADE,
    risk_id UUID REFERENCES risks(id) ON DELETE CASCADE,
    
    -- Risk configuration for simulation
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    impact_type VARCHAR(50) NOT NULL, -- cost, schedule, quality, etc.
    
    -- Probability distribution configuration
    distribution_type VARCHAR(50) NOT NULL, -- normal, triangular, uniform, beta, lognormal
    distribution_parameters JSONB NOT NULL,
    
    -- Impact configuration
    baseline_impact DECIMAL(15, 2) NOT NULL,
    impact_unit VARCHAR(20), -- currency, days, percentage, etc.
    
    -- Correlation configuration
    correlation_dependencies JSONB DEFAULT '[]',
    
    -- Mitigation strategies
    mitigation_strategies JSONB DEFAULT '[]',
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Monte Carlo Results table (for storing detailed results)
CREATE TABLE IF NOT EXISTS monte_carlo_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id UUID NOT NULL REFERENCES monte_carlo_simulations(id) ON DELETE CASCADE,
    
    -- Result type and format
    result_type VARCHAR(50) NOT NULL, -- cost_outcomes, schedule_outcomes, risk_contributions
    data_format VARCHAR(20) NOT NULL DEFAULT 'json', -- json, binary
    
    -- Result data (compressed for large datasets)
    result_data JSONB,
    result_data_compressed BYTEA, -- for very large datasets
    
    -- Metadata
    data_size INTEGER,
    compression_ratio DECIMAL(5, 2),
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Monte Carlo Visualizations table
CREATE TABLE IF NOT EXISTS monte_carlo_visualizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id UUID NOT NULL REFERENCES monte_carlo_simulations(id) ON DELETE CASCADE,
    
    -- Visualization configuration
    chart_type VARCHAR(50) NOT NULL, -- distribution, tornado, cdf, heat_map, scenario_overlay
    outcome_type VARCHAR(20) NOT NULL, -- cost, schedule
    format VARCHAR(10) NOT NULL, -- png, pdf, svg, html
    theme VARCHAR(30) NOT NULL DEFAULT 'professional',
    
    -- Chart metadata
    title VARCHAR(255),
    subtitle TEXT,
    chart_config JSONB,
    
    -- Chart data (base64 encoded or file path)
    chart_data TEXT,
    file_path VARCHAR(500),
    file_size INTEGER,
    
    -- Generation metadata
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    generated_by UUID REFERENCES auth.users(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_monte_carlo_simulations_user_id ON monte_carlo_simulations(user_id);
CREATE INDEX IF NOT EXISTS idx_monte_carlo_simulations_project_id ON monte_carlo_simulations(project_id);
CREATE INDEX IF NOT EXISTS idx_monte_carlo_simulations_status ON monte_carlo_simulations(status);
CREATE INDEX IF NOT EXISTS idx_monte_carlo_simulations_created_at ON monte_carlo_simulations(created_at);

CREATE INDEX IF NOT EXISTS idx_monte_carlo_scenarios_simulation_id ON monte_carlo_scenarios(simulation_id);
CREATE INDEX IF NOT EXISTS idx_monte_carlo_scenarios_created_by ON monte_carlo_scenarios(created_by);

CREATE INDEX IF NOT EXISTS idx_monte_carlo_risk_configs_simulation_id ON monte_carlo_risk_configs(simulation_id);
CREATE INDEX IF NOT EXISTS idx_monte_carlo_risk_configs_risk_id ON monte_carlo_risk_configs(risk_id);

CREATE INDEX IF NOT EXISTS idx_monte_carlo_results_simulation_id ON monte_carlo_results(simulation_id);
CREATE INDEX IF NOT EXISTS idx_monte_carlo_results_result_type ON monte_carlo_results(result_type);

CREATE INDEX IF NOT EXISTS idx_monte_carlo_visualizations_simulation_id ON monte_carlo_visualizations(simulation_id);
CREATE INDEX IF NOT EXISTS idx_monte_carlo_visualizations_chart_type ON monte_carlo_visualizations(chart_type);

-- Row Level Security (RLS) policies
ALTER TABLE monte_carlo_simulations ENABLE ROW LEVEL SECURITY;
ALTER TABLE monte_carlo_scenarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE monte_carlo_risk_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE monte_carlo_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE monte_carlo_visualizations ENABLE ROW LEVEL SECURITY;

-- Policies for monte_carlo_simulations
CREATE POLICY "Users can view their own simulations" ON monte_carlo_simulations
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can create their own simulations" ON monte_carlo_simulations
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own simulations" ON monte_carlo_simulations
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users can delete their own simulations" ON monte_carlo_simulations
    FOR DELETE USING (user_id = auth.uid());

-- Policies for monte_carlo_scenarios
CREATE POLICY "Users can view scenarios for their simulations" ON monte_carlo_scenarios
    FOR SELECT USING (
        simulation_id IN (
            SELECT id FROM monte_carlo_simulations WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create scenarios for their simulations" ON monte_carlo_scenarios
    FOR INSERT WITH CHECK (
        created_by = auth.uid() AND
        simulation_id IN (
            SELECT id FROM monte_carlo_simulations WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update scenarios they created" ON monte_carlo_scenarios
    FOR UPDATE USING (created_by = auth.uid());

CREATE POLICY "Users can delete scenarios they created" ON monte_carlo_scenarios
    FOR DELETE USING (created_by = auth.uid());

-- Policies for monte_carlo_risk_configs
CREATE POLICY "Users can view risk configs for their simulations" ON monte_carlo_risk_configs
    FOR SELECT USING (
        simulation_id IN (
            SELECT id FROM monte_carlo_simulations WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can manage risk configs for their simulations" ON monte_carlo_risk_configs
    FOR ALL USING (
        simulation_id IN (
            SELECT id FROM monte_carlo_simulations WHERE user_id = auth.uid()
        )
    );

-- Policies for monte_carlo_results
CREATE POLICY "Users can view results for their simulations" ON monte_carlo_results
    FOR SELECT USING (
        simulation_id IN (
            SELECT id FROM monte_carlo_simulations WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "System can manage results" ON monte_carlo_results
    FOR ALL USING (true); -- Results are managed by the system

-- Policies for monte_carlo_visualizations
CREATE POLICY "Users can view visualizations for their simulations" ON monte_carlo_visualizations
    FOR SELECT USING (
        simulation_id IN (
            SELECT id FROM monte_carlo_simulations WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can manage visualizations for their simulations" ON monte_carlo_visualizations
    FOR ALL USING (
        generated_by = auth.uid() OR
        simulation_id IN (
            SELECT id FROM monte_carlo_simulations WHERE user_id = auth.uid()
        )
    );

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_monte_carlo_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_monte_carlo_simulations_updated_at
    BEFORE UPDATE ON monte_carlo_simulations
    FOR EACH ROW EXECUTE FUNCTION update_monte_carlo_updated_at();

CREATE TRIGGER update_monte_carlo_scenarios_updated_at
    BEFORE UPDATE ON monte_carlo_scenarios
    FOR EACH ROW EXECUTE FUNCTION update_monte_carlo_updated_at();

CREATE TRIGGER update_monte_carlo_risk_configs_updated_at
    BEFORE UPDATE ON monte_carlo_risk_configs
    FOR EACH ROW EXECUTE FUNCTION update_monte_carlo_updated_at();

-- Comments for documentation
COMMENT ON TABLE monte_carlo_simulations IS 'Stores Monte Carlo simulation configurations and metadata';
COMMENT ON TABLE monte_carlo_scenarios IS 'Stores different scenarios for Monte Carlo analysis';
COMMENT ON TABLE monte_carlo_risk_configs IS 'Stores risk configurations for Monte Carlo simulations';
COMMENT ON TABLE monte_carlo_results IS 'Stores detailed simulation results data';
COMMENT ON TABLE monte_carlo_visualizations IS 'Stores generated visualization charts and metadata';

COMMENT ON COLUMN monte_carlo_simulations.results_summary IS 'JSON summary of key simulation results for quick access';
COMMENT ON COLUMN monte_carlo_risk_configs.distribution_parameters IS 'JSON object containing distribution-specific parameters';
COMMENT ON COLUMN monte_carlo_risk_configs.correlation_dependencies IS 'JSON array of risk IDs that this risk is correlated with';
COMMENT ON COLUMN monte_carlo_results.result_data_compressed IS 'Compressed binary data for large result sets';
COMMENT ON COLUMN monte_carlo_visualizations.chart_data IS 'Base64 encoded chart image or JSON chart specification';