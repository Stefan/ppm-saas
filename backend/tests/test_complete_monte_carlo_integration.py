"""
Comprehensive integration tests for Monte Carlo Risk Simulation system.

This module tests complete workflows from risk import to visualization,
validating all component interactions and data flow.
"""

import pytest
import numpy as np
import json
import tempfile
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, patch

# Import available Monte Carlo components
from monte_carlo.engine import MonteCarloEngine
from monte_carlo.distribution_modeler import RiskDistributionModeler
from monte_carlo.correlation_analyzer import RiskCorrelationAnalyzer
from monte_carlo.results_analyzer import SimulationResultsAnalyzer
from monte_carlo.scenario_generator import ScenarioGenerator
from monte_carlo.visualization import VisualizationGenerator
from monte_carlo.risk_register_integration import RiskRegisterIntegrator
from monte_carlo.historical_data_calibrator import HistoricalDataCalibrator
from monte_carlo.continuous_improvement_engine import ContinuousImprovementEngine
from monte_carlo.risk_pattern_database import RiskPatternDatabase

# Import models
from monte_carlo.models import (
    Risk, RiskCategory, ImpactType, DistributionType, ProbabilityDistribution,
    Scenario, SimulationResults, CorrelationMatrix, MitigationStrategy,
    ScheduleData, Milestone, Activity, ResourceConstraint
)

# Import configuration
from monte_carlo.simulation_config import SimulationConfig, ConfigurationManager


class TestCompleteMonteCarloIntegration:
    """Test complete Monte Carlo system integration workflows."""
    
    @pytest.fixture
    def sample_risks(self) -> List[Risk]:
        """Create sample risks for testing."""
        risks = []
        
        # Cost risk - Construction delays
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
            correlation_dependencies=["RISK_002"],
            mitigation_strategies=[
                MitigationStrategy(
                    id="MIT_001",
                    name="Fixed Price Contract",
                    description="Lock in material prices",
                    cost=10000,
                    effectiveness=0.7,
                    implementation_time=30
                )
            ]
        )
        risks.append(cost_risk)
        
        # Schedule risk - Weather delays
        schedule_risk = Risk(
            id="RISK_002",
            name="Weather-Related Schedule Delays",
            category=RiskCategory.SCHEDULE,
            impact_type=ImpactType.SCHEDULE,
            probability_distribution=ProbabilityDistribution(
                distribution_type=DistributionType.LOGNORMAL,
                parameters={"mu": 2.0, "sigma": 0.5}
            ),
            baseline_impact=15,  # days
            correlation_dependencies=["RISK_001"],
            mitigation_strategies=[]
        )
        risks.append(schedule_risk)
        
        # Combined risk - Regulatory approval
        combined_risk = Risk(
            id="RISK_003",
            name="Regulatory Approval Delays",
            category=RiskCategory.REGULATORY,
            impact_type=ImpactType.BOTH,
            probability_distribution=ProbabilityDistribution(
                distribution_type=DistributionType.BETA,
                parameters={"alpha": 2, "beta": 5, "scale": 50000}
            ),
            baseline_impact=75000,
            correlation_dependencies=[],
            mitigation_strategies=[]
        )
        risks.append(combined_risk)
        
        return risks
    
    @pytest.fixture
    def sample_correlations(self, sample_risks) -> CorrelationMatrix:
        """Create sample correlation matrix."""
        correlations = {
            ("RISK_001", "RISK_002"): 0.6,  # Material costs and weather delays are correlated
            ("RISK_001", "RISK_003"): 0.3,  # Material costs and regulatory delays are weakly correlated
            ("RISK_002", "RISK_003"): 0.2   # Weather and regulatory delays are weakly correlated
        }
        
        risk_ids = [risk.id for risk in sample_risks]
        return CorrelationMatrix(correlations=correlations, risk_ids=risk_ids)
    
    @pytest.fixture
    def sample_schedule_data(self) -> ScheduleData:
        """Create sample schedule data."""
        milestones = [
            Milestone(
                id="M001",
                name="Foundation Complete",
                baseline_duration=30,
                critical_path=True,
                dependencies=[]
            ),
            Milestone(
                id="M002", 
                name="Structure Complete",
                baseline_duration=60,
                critical_path=True,
                dependencies=["M001"]
            )
        ]
        
        activities = [
            Activity(
                id="A001",
                name="Site Preparation",
                baseline_duration=10,
                earliest_start=0,
                latest_start=0,
                float_time=0,
                critical_path=True,
                resource_requirements={"excavator": 1, "crew": 5}
            ),
            Activity(
                id="A002",
                name="Foundation Work",
                baseline_duration=20,
                earliest_start=10,
                latest_start=10,
                float_time=0,
                critical_path=True,
                resource_requirements={"concrete_crew": 8, "crane": 1}
            )
        ]
        
        resource_constraints = [
            ResourceConstraint(
                resource_id="R001",
                resource_name="Crane",
                total_availability=1,
                utilization_limit=0.8,
                availability_periods=[(0, 100)]
            ),
            ResourceConstraint(
                resource_id="R002",
                resource_name="Concrete Crew",
                total_availability=10,
                utilization_limit=1.0,
                availability_periods=[(0, 100)]
            )
        ]
        
        return ScheduleData(
            project_baseline_duration=90,
            milestones=milestones,
            activities=activities,
            resource_constraints=resource_constraints
        )
    
    @pytest.fixture
    def integrated_system(self):
        """Create fully integrated Monte Carlo system."""
        # Initialize all components
        engine = MonteCarloEngine()
        distribution_modeler = RiskDistributionModeler()
        correlation_analyzer = RiskCorrelationAnalyzer()
        results_analyzer = SimulationResultsAnalyzer()
        scenario_generator = ScenarioGenerator()
        confidence_calculator = ConfidenceIntervalCalculator()
        visualization_generator = VisualizationGenerator()
        risk_register_integrator = RiskRegisterIntegrator()
        historical_calibrator = HistoricalDataCalibrator()
        improvement_engine = ContinuousImprovementEngine()
        pattern_database = RiskPatternDatabase()
        
        return {
            'engine': engine,
            'distribution_modeler': distribution_modeler,
            'correlation_analyzer': correlation_analyzer,
            'results_analyzer': results_analyzer,
            'scenario_generator': scenario_generator,
            'confidence_calculator': confidence_calculator,
            'visualization_generator': visualization_generator,
            'risk_register_integrator': risk_register_integrator,
            'historical_calibrator': historical_calibrator,
            'improvement_engine': improvement_engine,
            'pattern_database': pattern_database
        }
    
    def test_complete_simulation_workflow(
        self, 
        integrated_system, 
        sample_risks, 
        sample_correlations,
        sample_schedule_data
    ):
        """Test complete simulation workflow from start to finish."""
        engine = integrated_system['engine']
        results_analyzer = integrated_system['results_analyzer']
        
        # Step 1: Run simulation
        results = engine.run_simulation(
            risks=sample_risks,
            iterations=10000,
            correlations=sample_correlations,
            random_seed=42,
            baseline_costs={"project_baseline": 1000000},
            schedule_data=sample_schedule_data
        )
        
        # Verify simulation completed successfully
        assert results is not None
        assert results.iteration_count == 10000
        assert results.execution_time > 0
        assert len(results.cost_outcomes) == 10000
        assert len(results.schedule_outcomes) == 10000
        assert results.convergence_metrics.converged
        
        # Step 2: Analyze results
        percentile_analysis = results_analyzer.calculate_percentiles(results)
        confidence_intervals = results_analyzer.generate_confidence_intervals(results, [0.8, 0.9, 0.95])
        risk_contributions = results_analyzer.identify_top_risk_contributors(results, top_n=3)
        
        # Verify analysis results
        assert percentile_analysis.mean > 0
        assert percentile_analysis.std_dev > 0
        assert len(percentile_analysis.percentiles) >= 7  # P10, P25, P50, P75, P90, P95, P99
        assert len(confidence_intervals.intervals) == 3
        assert len(risk_contributions) <= 3
        
        # Step 3: Verify risk contributions sum to reasonable total
        total_contribution = sum(contrib.contribution_percentage for contrib in risk_contributions)
        assert 0.8 <= total_contribution <= 1.0  # Should account for most of the variance
        
        # Step 4: Verify cost and schedule outcomes are reasonable
        assert np.mean(results.cost_outcomes) > 1000000  # Should be above baseline due to risks
        assert np.mean(results.schedule_outcomes) > 90    # Should be above baseline due to schedule risks
        
        print(f"✅ Complete simulation workflow test passed")
        print(f"   - Simulation ID: {results.simulation_id}")
        print(f"   - Execution time: {results.execution_time:.2f}s")
        print(f"   - Cost mean: ${np.mean(results.cost_outcomes):,.0f}")
        print(f"   - Schedule mean: {np.mean(results.schedule_outcomes):.1f} days")
        print(f"   - Top risk contributor: {risk_contributions[0].risk_name} ({risk_contributions[0].contribution_percentage:.1%})")
    
    def test_scenario_comparison_workflow(
        self, 
        integrated_system, 
        sample_risks, 
        sample_correlations
    ):
        """Test scenario creation and comparison workflow."""
        engine = integrated_system['engine']
        scenario_generator = integrated_system['scenario_generator']
        results_analyzer = integrated_system['results_analyzer']
        
        # Step 1: Create baseline scenario
        baseline_scenario = scenario_generator.create_scenario(
            base_risks=sample_risks,
            modifications={},
            name="Baseline Scenario",
            description="Original risk parameters"
        )
        
        # Step 2: Create mitigation scenario with reduced risk impacts
        from monte_carlo.models import RiskModification
        mitigation_modifications = {
            "RISK_001": RiskModification(
                parameter_changes={"mode": 80000, "max": 150000},  # Reduced material cost risk
                mitigation_applied=True
            ),
            "RISK_002": RiskModification(
                parameter_changes={"sigma": 0.3},  # Reduced weather delay variability
                mitigation_applied=True
            )
        }
        
        mitigation_scenario = scenario_generator.create_scenario(
            base_risks=sample_risks,
            modifications=mitigation_modifications,
            name="Mitigation Scenario",
            description="With risk mitigation strategies applied"
        )
        
        # Step 3: Run simulations for both scenarios
        baseline_results = engine.run_simulation(
            risks=baseline_scenario.risks,
            iterations=10000,
            correlations=sample_correlations,
            random_seed=42
        )
        
        mitigation_results = engine.run_simulation(
            risks=mitigation_scenario.risks,
            iterations=10000,
            correlations=sample_correlations,
            random_seed=42
        )
        
        # Step 4: Compare scenarios
        comparison = results_analyzer.compare_scenarios(baseline_results, mitigation_results)
        
        # Verify comparison results
        assert comparison.cost_difference < 0  # Mitigation should reduce costs
        assert comparison.statistical_significance < 0.05  # Should be statistically significant
        assert comparison.effect_size > 0.2  # Should have meaningful effect size
        
        # Step 5: Verify mitigation effectiveness
        baseline_cost_mean = np.mean(baseline_results.cost_outcomes)
        mitigation_cost_mean = np.mean(mitigation_results.cost_outcomes)
        cost_reduction = baseline_cost_mean - mitigation_cost_mean
        
        assert cost_reduction > 0  # Mitigation should reduce expected costs
        assert cost_reduction > 10000  # Should have meaningful impact
        
        print(f"✅ Scenario comparison workflow test passed")
        print(f"   - Baseline cost mean: ${baseline_cost_mean:,.0f}")
        print(f"   - Mitigation cost mean: ${mitigation_cost_mean:,.0f}")
        print(f"   - Cost reduction: ${cost_reduction:,.0f}")
        print(f"   - Statistical significance: p={comparison.statistical_significance:.4f}")
    
    def test_visualization_generation_workflow(
        self, 
        integrated_system, 
        sample_risks, 
        sample_correlations
    ):
        """Test visualization generation workflow."""
        engine = integrated_system['engine']
        visualization_generator = integrated_system['visualization_generator']
        results_analyzer = integrated_system['results_analyzer']
        
        # Step 1: Run simulation
        results = engine.run_simulation(
            risks=sample_risks,
            iterations=10000,
            correlations=sample_correlations,
            random_seed=42
        )
        
        # Step 2: Generate all visualization types
        with tempfile.TemporaryDirectory() as temp_dir:
            # Cost distribution chart
            cost_chart_path = os.path.join(temp_dir, "cost_distribution.png")
            cost_chart = visualization_generator.generate_cost_distribution_chart(
                results, 
                output_path=cost_chart_path
            )
            assert os.path.exists(cost_chart_path)
            assert os.path.getsize(cost_chart_path) > 1000  # Should be a real image file
            
            # Schedule distribution chart
            schedule_chart_path = os.path.join(temp_dir, "schedule_distribution.png")
            schedule_chart = visualization_generator.generate_schedule_distribution_chart(
                results,
                output_path=schedule_chart_path
            )
            assert os.path.exists(schedule_chart_path)
            assert os.path.getsize(schedule_chart_path) > 1000
            
            # Risk contribution tornado diagram
            risk_contributions = results_analyzer.identify_top_risk_contributors(results, top_n=3)
            tornado_chart_path = os.path.join(temp_dir, "tornado_diagram.png")
            tornado_chart = visualization_generator.generate_tornado_diagram(
                risk_contributions,
                output_path=tornado_chart_path
            )
            assert os.path.exists(tornado_chart_path)
            assert os.path.getsize(tornado_chart_path) > 1000
            
            # CDF chart with percentiles
            cdf_chart_path = os.path.join(temp_dir, "cdf_chart.png")
            percentile_analysis = results_analyzer.calculate_percentiles(results)
            cdf_chart = visualization_generator.generate_cdf_chart(
                results,
                percentile_analysis,
                output_path=cdf_chart_path
            )
            assert os.path.exists(cdf_chart_path)
            assert os.path.getsize(cdf_chart_path) > 1000
            
            # Risk heat map
            heatmap_path = os.path.join(temp_dir, "risk_heatmap.png")
            heatmap = visualization_generator.generate_risk_heatmap(
                sample_risks,
                results,
                output_path=heatmap_path
            )
            assert os.path.exists(heatmap_path)
            assert os.path.getsize(heatmap_path) > 1000
        
        print(f"✅ Visualization generation workflow test passed")
        print(f"   - Generated 5 chart types successfully")
        print(f"   - All files created with reasonable sizes")
    
    def test_risk_register_integration_workflow(
        self, 
        integrated_system, 
        sample_risks
    ):
        """Test risk register integration workflow."""
        risk_register_integrator = integrated_system['risk_register_integrator']
        engine = integrated_system['engine']
        
        # Step 1: Mock risk register data
        mock_risk_register_data = [
            {
                "id": "REG_001",
                "name": "Supply Chain Disruption",
                "category": "EXTERNAL",
                "probability": 0.3,
                "impact_cost": 150000,
                "impact_schedule": 20,
                "description": "Potential supply chain issues",
                "mitigation_status": "planned"
            },
            {
                "id": "REG_002", 
                "name": "Labor Shortage",
                "category": "RESOURCE",
                "probability": 0.4,
                "impact_cost": 80000,
                "impact_schedule": 15,
                "description": "Skilled labor availability issues",
                "mitigation_status": "active"
            }
        ]
        
        # Step 2: Import risks from register
        imported_risks = risk_register_integrator.import_risks_from_register(
            mock_risk_register_data
        )
        
        # Verify import results
        assert len(imported_risks) == 2
        assert all(isinstance(risk, Risk) for risk in imported_risks)
        assert imported_risks[0].id == "REG_001"
        assert imported_risks[1].id == "REG_002"
        
        # Step 3: Handle incomplete data
        incomplete_risk_data = [
            {
                "id": "REG_003",
                "name": "Incomplete Risk",
                "category": "TECHNICAL",
                # Missing probability and impact data
            }
        ]
        
        risks_with_defaults = risk_register_integrator.handle_incomplete_data(
            incomplete_risk_data
        )
        
        # Verify default handling
        assert len(risks_with_defaults) == 1
        incomplete_risk = risks_with_defaults[0]
        assert incomplete_risk.probability_distribution is not None
        assert incomplete_risk.baseline_impact > 0
        
        # Step 4: Test traceability
        all_risks = imported_risks + risks_with_defaults
        results = engine.run_simulation(
            risks=all_risks,
            iterations=1000,  # Smaller for faster test
            random_seed=42
        )
        
        # Verify traceability is maintained
        assert len(results.risk_contributions) == len(all_risks)
        for risk_id in results.risk_contributions.keys():
            assert any(risk.id == risk_id for risk in all_risks)
        
        print(f"✅ Risk register integration workflow test passed")
        print(f"   - Imported {len(imported_risks)} complete risks")
        print(f"   - Handled {len(risks_with_defaults)} incomplete risks")
        print(f"   - Maintained traceability for all {len(all_risks)} risks")
    
    def test_historical_learning_workflow(
        self, 
        integrated_system, 
        sample_risks
    ):
        """Test historical data learning and calibration workflow."""
        historical_calibrator = integrated_system['historical_calibrator']
        improvement_engine = integrated_system['improvement_engine']
        pattern_database = integrated_system['pattern_database']
        
        # Step 1: Create mock historical project data
        historical_projects = [
            {
                "project_id": "PROJ_001",
                "project_type": "construction",
                "planned_cost": 1000000,
                "actual_cost": 1150000,
                "planned_duration": 90,
                "actual_duration": 105,
                "risks_realized": ["material_cost_overrun", "weather_delays"],
                "completion_date": datetime.now() - timedelta(days=365)
            },
            {
                "project_id": "PROJ_002", 
                "project_type": "construction",
                "planned_cost": 800000,
                "actual_cost": 920000,
                "planned_duration": 75,
                "actual_duration": 82,
                "risks_realized": ["regulatory_delays"],
                "completion_date": datetime.now() - timedelta(days=180)
            },
            {
                "project_id": "PROJ_003",
                "project_type": "construction", 
                "planned_cost": 1200000,
                "actual_cost": 1080000,
                "planned_duration": 100,
                "actual_duration": 95,
                "risks_realized": [],  # Project went better than expected
                "completion_date": datetime.now() - timedelta(days=90)
            }
        ]
        
        # Step 2: Calibrate distributions using historical data
        calibration_results = historical_calibrator.calibrate_distributions(
            sample_risks,
            historical_projects
        )
        
        # Verify calibration results
        assert calibration_results is not None
        assert len(calibration_results.calibrated_risks) > 0
        assert calibration_results.accuracy_metrics is not None
        assert 0 <= calibration_results.accuracy_metrics.mean_absolute_error <= 1
        
        # Step 3: Store risk patterns
        for project in historical_projects:
            pattern_database.store_risk_pattern(
                project_type=project["project_type"],
                risk_pattern={
                    "cost_variance": (project["actual_cost"] - project["planned_cost"]) / project["planned_cost"],
                    "schedule_variance": (project["actual_duration"] - project["planned_duration"]) / project["planned_duration"],
                    "risks_realized": project["risks_realized"]
                },
                project_outcome={
                    "success": project["actual_cost"] <= project["planned_cost"] * 1.1,
                    "cost_performance": project["actual_cost"] / project["planned_cost"],
                    "schedule_performance": project["actual_duration"] / project["planned_duration"]
                }
            )
        
        # Step 4: Generate improvement recommendations
        recommendations = improvement_engine.generate_recommendations(
            current_risks=sample_risks,
            historical_data=historical_projects,
            project_type="construction"
        )
        
        # Verify recommendations
        assert recommendations is not None
        assert len(recommendations.parameter_suggestions) > 0
        assert len(recommendations.process_improvements) >= 0
        
        # Step 5: Retrieve similar patterns
        similar_patterns = pattern_database.get_similar_patterns(
            project_type="construction",
            risk_categories=["COST", "SCHEDULE"]
        )
        
        # Verify pattern retrieval
        assert len(similar_patterns) > 0
        assert all("cost_variance" in pattern for pattern in similar_patterns)
        
        print(f"✅ Historical learning workflow test passed")
        print(f"   - Calibrated {len(calibration_results.calibrated_risks)} risk distributions")
        print(f"   - Stored {len(historical_projects)} risk patterns")
        print(f"   - Generated {len(recommendations.parameter_suggestions)} recommendations")
        print(f"   - Retrieved {len(similar_patterns)} similar patterns")
    
    def test_performance_requirements(
        self, 
        integrated_system, 
        sample_risks, 
        sample_correlations
    ):
        """Test that system meets performance requirements."""
        engine = integrated_system['engine']
        
        # Test with maximum supported configuration
        large_risk_set = []
        for i in range(50):  # Test with 50 risks (within 100 risk limit)
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
        assert results.convergence_metrics.converged
        
        print(f"✅ Performance requirements test passed")
        print(f"   - Processed {len(large_risk_set)} risks in {execution_time:.2f}s")
        print(f"   - Performance requirement: <30s (actual: {execution_time:.2f}s)")
        print(f"   - Simulation converged successfully")
    
    def test_error_handling_and_recovery(
        self, 
        integrated_system, 
        sample_risks
    ):
        """Test error handling and graceful degradation."""
        engine = integrated_system['engine']
        
        # Test 1: Invalid risk parameters
        invalid_risks = [
            Risk(
                id="INVALID_001",
                name="Invalid Risk",
                category=RiskCategory.COST,
                impact_type=ImpactType.COST,
                probability_distribution=ProbabilityDistribution(
                    distribution_type=DistributionType.NORMAL,
                    parameters={"mean": -1000, "std": -500}  # Invalid negative std
                ),
                baseline_impact=1000,
                correlation_dependencies=[],
                mitigation_strategies=[]
            )
        ]
        
        # Should handle invalid parameters gracefully
        validation_result = engine.validate_simulation_parameters(invalid_risks)
        assert not validation_result.is_valid
        assert len(validation_result.errors) > 0
        
        # Test 2: Correlation matrix issues
        invalid_correlations = CorrelationMatrix(
            correlations={("RISK_001", "RISK_002"): 1.5},  # Invalid correlation > 1
            risk_ids=["RISK_001", "RISK_002"]
        )
        
        with pytest.raises(ValueError):
            engine.run_simulation(
                risks=sample_risks[:2],
                iterations=1000,
                correlations=invalid_correlations
            )
        
        # Test 3: Memory constraints with very large iteration count
        # This should either complete or fail gracefully
        try:
            results = engine.run_simulation(
                risks=sample_risks[:1],  # Single risk to minimize memory usage
                iterations=1000000,  # Very large iteration count
                random_seed=42
            )
            # If it completes, verify it's reasonable
            assert results.iteration_count <= 1000000
        except MemoryError:
            # Graceful failure is acceptable for extreme cases
            pass
        
        print(f"✅ Error handling and recovery test passed")
        print(f"   - Invalid parameters detected and rejected")
        print(f"   - Correlation matrix validation working")
        print(f"   - Memory constraints handled appropriately")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])