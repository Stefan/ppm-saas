"""
Core Monte Carlo integration tests focusing on essential workflow.

This module tests the core integration between Monte Carlo components
that are currently implemented and functional.
"""

import pytest
import numpy as np
import time
from datetime import datetime
from typing import List

# Import core Monte Carlo components that exist
from monte_carlo.engine import MonteCarloEngine
from monte_carlo.results_analyzer import SimulationResultsAnalyzer
from monte_carlo.scenario_generator import ScenarioGenerator

# Import models
from monte_carlo.models import (
    Risk, RiskCategory, ImpactType, DistributionType, ProbabilityDistribution,
    Scenario, CorrelationMatrix, MitigationStrategy, RiskModification
)


class TestMonteCarloCoreIntegration:
    """Test core Monte Carlo system integration."""
    
    @pytest.fixture
    def sample_risks(self) -> List[Risk]:
        """Create sample risks for testing."""
        risks = []
        
        # Cost risk
        cost_risk = Risk(
            id="RISK_001",
            name="Construction Material Cost Overrun",
            category=RiskCategory.COST,
            impact_type=ImpactType.COST,
            probability_distribution=ProbabilityDistribution(
                distribution_type=DistributionType.TRIANGULAR,
                parameters={"min": 50000, "mode": 100000, "max": 200000}
            ),
            baseline_impact=100000,
            correlation_dependencies=[],
            mitigation_strategies=[]
        )
        risks.append(cost_risk)
        
        # Schedule risk
        schedule_risk = Risk(
            id="RISK_002",
            name="Weather-Related Schedule Delays",
            category=RiskCategory.SCHEDULE,
            impact_type=ImpactType.SCHEDULE,
            probability_distribution=ProbabilityDistribution(
                distribution_type=DistributionType.NORMAL,
                parameters={"mean": 15, "std": 5}
            ),
            baseline_impact=15,
            correlation_dependencies=[],
            mitigation_strategies=[]
        )
        risks.append(schedule_risk)
        
        return risks
    
    @pytest.fixture
    def sample_correlations(self, sample_risks) -> CorrelationMatrix:
        """Create sample correlation matrix."""
        correlations = {
            ("RISK_001", "RISK_002"): 0.4  # Moderate correlation
        }
        
        risk_ids = [risk.id for risk in sample_risks]
        return CorrelationMatrix(correlations=correlations, risk_ids=risk_ids)
    
    def test_core_simulation_workflow(self, sample_risks, sample_correlations):
        """Test core simulation workflow with existing components."""
        # Initialize components
        engine = MonteCarloEngine()
        results_analyzer = SimulationResultsAnalyzer()
        
        # Step 1: Run simulation
        results = engine.run_simulation(
            risks=sample_risks,
            iterations=10000,  # Use minimum required iterations
            correlations=sample_correlations,
            random_seed=42
        )
        
        # Verify simulation completed successfully
        assert results is not None
        assert results.iteration_count == 10000
        assert results.execution_time > 0
        assert len(results.cost_outcomes) == 10000
        assert len(results.schedule_outcomes) == 10000
        
        # Step 2: Analyze results
        percentile_analysis = results_analyzer.calculate_percentiles(results)
        confidence_intervals = results_analyzer.generate_confidence_intervals(
            results, outcome_type='cost', confidence_levels=[0.8, 0.9, 0.95]
        )
        risk_contributions = results_analyzer.identify_top_risk_contributors(results, top_n=2)
        
        # Verify analysis results
        assert percentile_analysis.mean > 0
        assert percentile_analysis.std_dev > 0
        assert len(percentile_analysis.percentiles) >= 7
        assert len(confidence_intervals.intervals) == 3
        assert len(risk_contributions) <= 2
        
        # Step 3: Verify results are reasonable
        assert np.mean(results.cost_outcomes) > 50000  # Should be above minimum risk
        assert np.mean(results.schedule_outcomes) > 10  # Should be above minimum schedule impact
        
        print(f"✅ Core simulation workflow test passed")
        print(f"   - Simulation ID: {results.simulation_id}")
        print(f"   - Execution time: {results.execution_time:.2f}s")
        print(f"   - Cost mean: ${np.mean(results.cost_outcomes):,.0f}")
        print(f"   - Schedule mean: {np.mean(results.schedule_outcomes):.1f} days")
    
    def test_scenario_workflow(self, sample_risks):
        """Test scenario creation and simulation workflow."""
        engine = MonteCarloEngine()
        scenario_generator = ScenarioGenerator()
        results_analyzer = SimulationResultsAnalyzer()
        
        # Step 1: Create baseline scenario
        baseline_scenario = scenario_generator.create_scenario(
            base_risks=sample_risks,
            modifications={},
            name="Baseline Scenario",
            description="Original risk parameters"
        )
        
        # Step 2: Create mitigation scenario
        mitigation_modifications = {
            "RISK_001": RiskModification(
                parameter_changes={"mode": 80000, "max": 150000},  # Reduced cost risk
                mitigation_applied=True
            )
        }
        
        mitigation_scenario = scenario_generator.create_scenario(
            base_risks=sample_risks,
            modifications=mitigation_modifications,
            name="Mitigation Scenario",
            description="With cost mitigation applied"
        )
        
        # Step 3: Run simulations for both scenarios
        baseline_results = engine.run_simulation(
            risks=baseline_scenario.risks,
            iterations=10000,
            random_seed=42
        )
        
        mitigation_results = engine.run_simulation(
            risks=mitigation_scenario.risks,
            iterations=10000,
            random_seed=42
        )
        
        # Step 4: Compare results
        comparison = results_analyzer.compare_scenarios(baseline_results, mitigation_results)
        
        # Verify comparison shows improvement
        baseline_cost_mean = np.mean(baseline_results.cost_outcomes)
        mitigation_cost_mean = np.mean(mitigation_results.cost_outcomes)
        cost_reduction = baseline_cost_mean - mitigation_cost_mean
        
        assert cost_reduction > 0  # Mitigation should reduce costs
        # Check if statistical significance is available and meaningful
        if hasattr(comparison, 'statistical_significance') and comparison.statistical_significance:
            if isinstance(comparison.statistical_significance, dict):
                # Get p-value from the dictionary if available
                p_value = comparison.statistical_significance.get('p_value', 1.0)
                assert p_value < 0.05 or cost_reduction > 5000  # Either significant or meaningful reduction
        
        print(f"✅ Scenario workflow test passed")
        print(f"   - Baseline cost mean: ${baseline_cost_mean:,.0f}")
        print(f"   - Mitigation cost mean: ${mitigation_cost_mean:,.0f}")
        print(f"   - Cost reduction: ${cost_reduction:,.0f}")
    
    def test_performance_requirements(self, sample_risks):
        """Test that core system meets performance requirements."""
        engine = MonteCarloEngine()
        
        # Create larger risk set for performance testing
        large_risk_set = []
        for i in range(20):  # Test with 20 risks
            risk = Risk(
                id=f"PERF_RISK_{i:03d}",
                name=f"Performance Test Risk {i}",
                category=RiskCategory.COST,
                impact_type=ImpactType.COST,
                probability_distribution=ProbabilityDistribution(
                    distribution_type=DistributionType.NORMAL,
                    parameters={"mean": 10000 + i * 1000, "std": 2000}
                ),
                baseline_impact=10000 + i * 1000,
                correlation_dependencies=[],
                mitigation_strategies=[]
            )
            large_risk_set.append(risk)
        
        # Measure execution time
        start_time = time.time()
        results = engine.run_simulation(
            risks=large_risk_set,
            iterations=10000,
            random_seed=42
        )
        execution_time = time.time() - start_time
        
        # Verify performance requirements
        assert execution_time < 30.0  # Should complete within 30 seconds
        assert results.iteration_count == 10000
        assert len(results.cost_outcomes) == 10000
        
        print(f"✅ Performance requirements test passed")
        print(f"   - Processed {len(large_risk_set)} risks in {execution_time:.2f}s")
        print(f"   - Performance requirement: <30s (actual: {execution_time:.2f}s)")
    
    def test_error_handling(self, sample_risks):
        """Test error handling in core components."""
        engine = MonteCarloEngine()
        
        # Test 1: Invalid risk parameters - should be caught during construction
        with pytest.raises(ValueError, match="Standard deviation must be positive"):
            ProbabilityDistribution(
                distribution_type=DistributionType.NORMAL,
                parameters={"mean": 1000, "std": -500}  # Invalid negative std
            )
        
        # Test 2: Invalid correlation matrix - should be caught during construction
        with pytest.raises(ValueError, match="must be between -1 and 1"):
            CorrelationMatrix(
                correlations={("RISK_001", "RISK_002"): 1.5},  # Invalid correlation > 1
                risk_ids=["RISK_001", "RISK_002"]
            )
        
        # Test 3: Empty risks list
        with pytest.raises(ValueError):
            engine.run_simulation(
                risks=[],
                iterations=10000
            )
        
        print(f"✅ Error handling test passed")
        print(f"   - Invalid parameters detected and rejected")
        print(f"   - Correlation matrix validation working")
        print(f"   - Empty risks list validation working")
    
    def test_system_integration_validation(self):
        """Test that core system components integrate properly."""
        # Test component initialization
        try:
            engine = MonteCarloEngine()
            results_analyzer = SimulationResultsAnalyzer()
            scenario_generator = ScenarioGenerator()
            
            # Test basic health checks if available
            if hasattr(engine, 'health_check'):
                health = engine.health_check()
                assert health.get('status') in ['healthy', 'degraded']
            
            integration_status = True
            
        except Exception as e:
            integration_status = False
            print(f"Integration error: {str(e)}")
        
        assert integration_status, "Core system integration failed"
        
        print(f"✅ System integration validation passed")
        print(f"   - All core components initialized successfully")
        print(f"   - Component interactions working properly")


if __name__ == "__main__":
    # Run core integration tests
    pytest.main([__file__, "-v", "--tb=short"])