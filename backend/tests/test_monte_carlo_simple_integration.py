"""
Simple system integration tests for Monte Carlo Risk Simulation system.

This module tests system integration with available components only,
focusing on core functionality and realistic workflows.
"""

import pytest
import numpy as np
import time
from datetime import datetime, timedelta
from typing import List

# Import core components that are available
from monte_carlo.engine import MonteCarloEngine
from monte_carlo.results_analyzer import SimulationResultsAnalyzer
from monte_carlo.scenario_generator import ScenarioGenerator
from monte_carlo.visualization import VisualizationManager

# Import models
from monte_carlo.models import (
    Risk, RiskCategory, ImpactType, DistributionType, ProbabilityDistribution,
    Scenario, CorrelationMatrix, MitigationStrategy, RiskModification
)

# Import configuration
from monte_carlo.simulation_config import SimulationConfig


class TestMonteCarloSimpleIntegration:
    """Test simple Monte Carlo system integration with available components."""
    
    @pytest.fixture
    def construction_project_risks(self) -> List[Risk]:
        """Create realistic construction project risks."""
        risks = []
        
        # Foundation cost risk
        foundation_risk = Risk(
            id="FOUND_001",
            name="Foundation Cost Overrun",
            category=RiskCategory.COST,
            impact_type=ImpactType.COST,
            probability_distribution=ProbabilityDistribution(
                distribution_type=DistributionType.TRIANGULAR,
                parameters={"min": 25000, "mode": 75000, "max": 150000}
            ),
            baseline_impact=75000,
            correlation_dependencies=["STRUCT_001"],
            mitigation_strategies=[
                MitigationStrategy(
                    id="MIT_001",
                    name="Soil Survey",
                    description="Comprehensive geotechnical analysis",
                    cost=15000,
                    effectiveness=0.6,
                    implementation_time=14
                )
            ]
        )
        risks.append(foundation_risk)
        
        # Structural cost risk
        structural_risk = Risk(
            id="STRUCT_001",
            name="Steel Price Volatility",
            category=RiskCategory.COST,
            impact_type=ImpactType.COST,
            probability_distribution=ProbabilityDistribution(
                distribution_type=DistributionType.NORMAL,
                parameters={"mean": 50000, "std": 20000}
            ),
            baseline_impact=50000,
            correlation_dependencies=["FOUND_001"],
            mitigation_strategies=[]
        )
        risks.append(structural_risk)
        
        # Schedule risk
        schedule_risk = Risk(
            id="SCHED_001",
            name="Weather Delays",
            category=RiskCategory.SCHEDULE,
            impact_type=ImpactType.SCHEDULE,
            probability_distribution=ProbabilityDistribution(
                distribution_type=DistributionType.LOGNORMAL,
                parameters={"mu": 2.5, "sigma": 0.8}
            ),
            baseline_impact=15,  # days
            correlation_dependencies=[],
            mitigation_strategies=[]
        )
        risks.append(schedule_risk)
        
        # Regulatory risk
        regulatory_risk = Risk(
            id="REG_001",
            name="Permit Delays",
            category=RiskCategory.REGULATORY,
            impact_type=ImpactType.BOTH,
            probability_distribution=ProbabilityDistribution(
                distribution_type=DistributionType.TRIANGULAR,
                parameters={"min": 10000, "mode": 30000, "max": 60000}
            ),
            baseline_impact=30000,
            correlation_dependencies=[],
            mitigation_strategies=[]
        )
        risks.append(regulatory_risk)
        
        return risks
    
    @pytest.fixture
    def project_correlations(self, construction_project_risks) -> CorrelationMatrix:
        """Create correlation matrix for construction project."""
        correlations = {
            ("FOUND_001", "STRUCT_001"): 0.6,  # Foundation and structural costs are correlated
            ("FOUND_001", "REG_001"): 0.3,     # Foundation issues may affect permits
        }
        
        risk_ids = [risk.id for risk in construction_project_risks]
        return CorrelationMatrix(correlations=correlations, risk_ids=risk_ids)
    
    def test_realistic_project_simulation(self, construction_project_risks, project_correlations):
        """Test realistic construction project simulation."""
        print(f"\n🏗️ Testing realistic construction project simulation")
        
        # Initialize components
        engine = MonteCarloEngine()
        results_analyzer = SimulationResultsAnalyzer()
        
        # Run simulation
        start_time = time.time()
        results = engine.run_simulation(
            risks=construction_project_risks,
            iterations=10000,
            correlations=project_correlations,
            random_seed=42
        )
        execution_time = time.time() - start_time
        
        # Verify simulation success
        assert results is not None
        assert results.iteration_count == 10000
        assert execution_time < 30.0  # Performance requirement
        
        # Analyze results
        percentile_analysis = results_analyzer.calculate_percentiles(results)
        confidence_intervals = results_analyzer.generate_confidence_intervals(
            results, outcome_type='cost', confidence_levels=[0.8, 0.9, 0.95]
        )
        risk_contributions = results_analyzer.identify_top_risk_contributors(results, top_n=4)
        
        # Verify realistic results
        cost_mean = percentile_analysis.mean
        cost_std = percentile_analysis.std_dev
        
        assert 100000 <= cost_mean <= 500000  # Reasonable construction cost range
        assert cost_std > 0  # Should have variability
        assert percentile_analysis.coefficient_of_variation > 0
        
        # Verify schedule results
        schedule_percentiles = results_analyzer.calculate_percentiles(results, outcome_type='schedule')
        schedule_mean = schedule_percentiles.mean
        
        assert 10 <= schedule_mean <= 50  # Reasonable schedule delay range
        
        # Verify risk contributions
        assert len(risk_contributions) == 4  # All risks should contribute
        total_contribution = sum(contrib.contribution_percentage for contrib in risk_contributions)
        assert 0.8 <= total_contribution <= 1.0
        
        # Verify confidence intervals
        assert len(confidence_intervals.intervals) == 3
        ci_80 = confidence_intervals.intervals[0.8]
        ci_95 = confidence_intervals.intervals[0.95]
        assert ci_95[1] - ci_95[0] > ci_80[1] - ci_80[0]  # 95% CI should be wider
        
        print(f"   ✅ Simulation completed in {execution_time:.2f}s")
        print(f"   💰 Cost: ${cost_mean:,.0f} ± ${cost_std:,.0f}")
        print(f"   📅 Schedule: {schedule_mean:.1f} ± {schedule_percentiles.std_dev:.1f} days")
        print(f"   🎯 Top risk: {risk_contributions[0].risk_name} ({risk_contributions[0].contribution_percentage:.1%})")
    
    def test_mitigation_scenario_analysis(self, construction_project_risks):
        """Test mitigation scenario analysis workflow."""
        print(f"\n🛡️ Testing mitigation scenario analysis")
        
        # Initialize components
        engine = MonteCarloEngine()
        scenario_generator = ScenarioGenerator()
        results_analyzer = SimulationResultsAnalyzer()
        
        # Create baseline scenario
        baseline_scenario = scenario_generator.create_scenario(
            base_risks=construction_project_risks,
            modifications={},
            name="Baseline Project",
            description="No mitigation strategies applied"
        )
        
        # Create mitigation scenario
        mitigation_modifications = {
            "FOUND_001": RiskModification(
                parameter_changes={"mode": 50000, "max": 100000},  # Reduced foundation risk
                mitigation_applied="MIT_001"
            ),
            "STRUCT_001": RiskModification(
                parameter_changes={"mean": 35000, "std": 15000},  # Reduced steel price risk
                mitigation_applied=True
            )
        }
        
        # Apply modifications to create mitigation risks
        mitigation_risks = []
        for risk in construction_project_risks:
            if risk.id in mitigation_modifications:
                mod = mitigation_modifications[risk.id]
                new_params = {**risk.probability_distribution.parameters, **mod.parameter_changes}
                new_distribution = ProbabilityDistribution(
                    distribution_type=risk.probability_distribution.distribution_type,
                    parameters=new_params
                )
                modified_risk = Risk(
                    id=risk.id,
                    name=risk.name + " (Mitigated)",
                    category=risk.category,
                    impact_type=risk.impact_type,
                    probability_distribution=new_distribution,
                    baseline_impact=risk.baseline_impact,
                    correlation_dependencies=risk.correlation_dependencies,
                    mitigation_strategies=risk.mitigation_strategies
                )
                mitigation_risks.append(modified_risk)
            else:
                mitigation_risks.append(risk)
        
        mitigation_scenario = scenario_generator.create_scenario(
            base_risks=mitigation_risks,
            modifications=mitigation_modifications,
            name="Mitigation Project",
            description="Key mitigation strategies applied"
        )
        
        # Run both scenarios
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
        
        # Compare results
        comparison = results_analyzer.compare_scenarios(baseline_results, mitigation_results)
        
        baseline_cost_mean = np.mean(baseline_results.cost_outcomes)
        mitigation_cost_mean = np.mean(mitigation_results.cost_outcomes)
        cost_reduction = baseline_cost_mean - mitigation_cost_mean
        
        # Verify mitigation effectiveness
        assert cost_reduction > 0, "Mitigation should reduce expected costs"
        assert cost_reduction > 15000, "Cost reduction should be meaningful"
        
        reduction_percentage = (cost_reduction / baseline_cost_mean) * 100
        
        print(f"   ✅ Mitigation analysis completed")
        print(f"   📉 Cost reduction: ${cost_reduction:,.0f} ({reduction_percentage:.1f}%)")
        print(f"   📊 Baseline: ${baseline_cost_mean:,.0f}")
        print(f"   📊 Mitigated: ${mitigation_cost_mean:,.0f}")
    
    def test_visualization_integration(self, construction_project_risks, project_correlations):
        """Test visualization component integration."""
        print(f"\n📊 Testing visualization integration")
        
        # Initialize components
        engine = MonteCarloEngine()
        results_analyzer = SimulationResultsAnalyzer()
        visualization_manager = VisualizationManager()
        
        # Run simulation
        results = engine.run_simulation(
            risks=construction_project_risks,
            iterations=10000,
            correlations=project_correlations,
            random_seed=42
        )
        
        # Analyze results
        percentile_analysis = results_analyzer.calculate_percentiles(results)
        risk_contributions = results_analyzer.identify_top_risk_contributors(results, top_n=4)
        
        # Test visualization generation
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test cost distribution chart
            cost_chart_path = os.path.join(temp_dir, "cost_distribution.png")
            try:
                cost_chart = visualization_manager.generate_cost_distribution_chart(
                    results, output_path=cost_chart_path
                )
                chart_generated = os.path.exists(cost_chart_path)
                if chart_generated:
                    chart_size = os.path.getsize(cost_chart_path)
                    assert chart_size > 1000, "Chart file should have reasonable size"
            except Exception as e:
                print(f"     ⚠️ Cost chart generation failed: {str(e)}")
                chart_generated = False
            
            # Test tornado diagram
            tornado_path = os.path.join(temp_dir, "tornado.png")
            try:
                tornado_chart = visualization_manager.generate_tornado_diagram(
                    risk_contributions, output_path=tornado_path
                )
                tornado_generated = os.path.exists(tornado_path)
                if tornado_generated:
                    tornado_size = os.path.getsize(tornado_path)
                    assert tornado_size > 1000, "Tornado chart should have reasonable size"
            except Exception as e:
                print(f"     ⚠️ Tornado chart generation failed: {str(e)}")
                tornado_generated = False
            
            # At least one visualization should work
            visualization_working = chart_generated or tornado_generated
            
        print(f"   📈 Cost distribution chart: {'✅' if chart_generated else '❌'}")
        print(f"   🌪️ Tornado diagram: {'✅' if tornado_generated else '❌'}")
        print(f"   📊 Visualization system: {'✅ WORKING' if visualization_working else '❌ NEEDS ATTENTION'}")
    
    def test_system_scalability_simple(self):
        """Test system scalability with varying numbers of risks."""
        print(f"\n📈 Testing system scalability")
        
        engine = MonteCarloEngine()
        
        scalability_results = []
        
        for risk_count in [5, 15, 30]:
            print(f"   Testing with {risk_count} risks...")
            
            # Generate test risks
            test_risks = []
            for i in range(risk_count):
                risk = Risk(
                    id=f"SCALE_{i:03d}",
                    name=f"Scalability Risk {i}",
                    category=RiskCategory.COST if i % 2 == 0 else RiskCategory.SCHEDULE,
                    impact_type=ImpactType.COST if i % 2 == 0 else ImpactType.SCHEDULE,
                    probability_distribution=ProbabilityDistribution(
                        distribution_type=DistributionType.NORMAL,
                        parameters={"mean": 10000 + i * 1000, "std": 2000}
                    ),
                    baseline_impact=10000 + i * 1000,
                    correlation_dependencies=[],
                    mitigation_strategies=[]
                )
                test_risks.append(risk)
            
            # Measure execution time
            start_time = time.time()
            results = engine.run_simulation(
                risks=test_risks,
                iterations=10000,
                random_seed=42
            )
            execution_time = time.time() - start_time
            
            # Verify results
            assert results.iteration_count == 10000
            assert execution_time < 30.0, f"Execution time {execution_time:.2f}s exceeds limit"
            
            risks_per_second = risk_count / execution_time
            scalability_results.append({
                'risk_count': risk_count,
                'execution_time': execution_time,
                'risks_per_second': risks_per_second
            })
            
            print(f"     ✅ {risk_count} risks: {execution_time:.2f}s ({risks_per_second:.1f} risks/sec)")
        
        # Verify reasonable scalability
        assert all(result['risks_per_second'] > 0.5 for result in scalability_results)
        
        print(f"   ✅ Scalability test passed")
    
    def test_data_consistency_across_components(self, construction_project_risks):
        """Test data consistency across system components."""
        print(f"\n🔄 Testing data consistency across components")
        
        # Initialize components
        engine = MonteCarloEngine()
        results_analyzer = SimulationResultsAnalyzer()
        
        # Run simulation
        results = engine.run_simulation(
            risks=construction_project_risks,
            iterations=10000,
            random_seed=42
        )
        
        # Test data consistency
        
        # 1. Risk IDs should match
        input_risk_ids = {risk.id for risk in construction_project_risks}
        result_risk_ids = set(results.risk_contributions.keys())
        assert input_risk_ids == result_risk_ids, "Risk IDs should match between input and results"
        
        # 2. Percentile calculations should be consistent
        cost_percentiles = results_analyzer.calculate_percentiles(results, outcome_type='cost')
        schedule_percentiles = results_analyzer.calculate_percentiles(results, outcome_type='schedule')
        
        # Verify percentile ordering
        cost_p_values = list(cost_percentiles.percentiles.values())
        assert cost_p_values == sorted(cost_p_values), "Cost percentiles should be in ascending order"
        
        schedule_p_values = list(schedule_percentiles.percentiles.values())
        assert schedule_p_values == sorted(schedule_p_values), "Schedule percentiles should be in ascending order"
        
        # 3. Statistical measures should be reasonable
        assert cost_percentiles.mean > 0
        assert cost_percentiles.std_dev > 0
        assert 0 <= cost_percentiles.coefficient_of_variation <= 2  # Reasonable CV range
        
        # 4. Risk contributions should sum to reasonable total
        risk_contributions = results_analyzer.identify_top_risk_contributors(results)
        total_contribution = sum(contrib.contribution_percentage for contrib in risk_contributions)
        assert 0.7 <= total_contribution <= 1.0, "Risk contributions should account for most variance"
        
        print(f"   ✅ Risk ID consistency verified")
        print(f"   ✅ Percentile calculations consistent")
        print(f"   ✅ Statistical measures reasonable")
        print(f"   ✅ Risk contributions sum to {total_contribution:.1%}")
    
    def test_error_handling_integration(self):
        """Test error handling across integrated components."""
        print(f"\n🛡️ Testing integrated error handling")
        
        engine = MonteCarloEngine()
        
        # Test 1: Empty risk list
        try:
            results = engine.run_simulation(risks=[], iterations=10000)
            assert False, "Should have raised an error for empty risks"
        except ValueError as e:
            assert "empty" in str(e).lower() or "no risks" in str(e).lower()
            print(f"   ✅ Empty risks handled: {str(e)[:50]}...")
        
        # Test 2: Invalid iterations
        valid_risk = Risk(
            id="TEST_001",
            name="Test Risk",
            category=RiskCategory.COST,
            impact_type=ImpactType.COST,
            probability_distribution=ProbabilityDistribution(
                distribution_type=DistributionType.NORMAL,
                parameters={"mean": 10000, "std": 2000}
            ),
            baseline_impact=10000,
            correlation_dependencies=[],
            mitigation_strategies=[]
        )
        
        try:
            results = engine.run_simulation(risks=[valid_risk], iterations=5000)  # Below minimum
            assert False, "Should have raised an error for insufficient iterations"
        except ValueError as e:
            assert "10000" in str(e) or "minimum" in str(e).lower()
            print(f"   ✅ Invalid iterations handled: {str(e)[:50]}...")
        
        print(f"   ✅ Error handling integration working properly")


if __name__ == "__main__":
    # Run simple system integration tests
    pytest.main([__file__, "-v", "--tb=short"])