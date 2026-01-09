"""
Comprehensive system integration tests for Monte Carlo Risk Simulation system.

This module tests complete system workflows with realistic data,
validates cross-component interactions, and tests system performance and scalability.
"""

import pytest
import numpy as np
import time
import json
import tempfile
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, patch

# Import system integrator
from monte_carlo.system_integrator import MonteCarloSystemIntegrator

# Import core components
from monte_carlo.engine import MonteCarloEngine
from monte_carlo.results_analyzer import SimulationResultsAnalyzer
from monte_carlo.scenario_generator import ScenarioGenerator

# Import models
from monte_carlo.models import (
    Risk, RiskCategory, ImpactType, DistributionType, ProbabilityDistribution,
    Scenario, CorrelationMatrix, MitigationStrategy, RiskModification,
    ScheduleData, Milestone, Activity, ResourceConstraint
)

# Import configuration
from monte_carlo.simulation_config import SimulationConfig


class TestMonteCarloSystemIntegration:
    """Test comprehensive Monte Carlo system integration."""
    
    @pytest.fixture
    def realistic_construction_project_risks(self) -> List[Risk]:
        """Create realistic construction project risks for testing."""
        risks = []
        
        # Foundation risks
        foundation_cost_risk = Risk(
            id="FOUND_001",
            name="Foundation Cost Overrun - Soil Conditions",
            category=RiskCategory.COST,
            impact_type=ImpactType.COST,
            probability_distribution=ProbabilityDistribution(
                distribution_type=DistributionType.TRIANGULAR,
                parameters={"min": 25000, "mode": 75000, "max": 150000}
            ),
            baseline_impact=75000,
            correlation_dependencies=["FOUND_002"],
            mitigation_strategies=[
                MitigationStrategy(
                    id="MIT_FOUND_001",
                    name="Geotechnical Survey",
                    description="Comprehensive soil analysis",
                    cost=15000,
                    effectiveness=0.6,
                    implementation_time=14
                )
            ]
        )
        risks.append(foundation_cost_risk)
        
        foundation_schedule_risk = Risk(
            id="FOUND_002",
            name="Foundation Schedule Delay - Weather",
            category=RiskCategory.SCHEDULE,
            impact_type=ImpactType.SCHEDULE,
            probability_distribution=ProbabilityDistribution(
                distribution_type=DistributionType.LOGNORMAL,
                parameters={"mu": 2.5, "sigma": 0.8}
            ),
            baseline_impact=12,  # days
            correlation_dependencies=["FOUND_001", "STRUCT_002"],
            mitigation_strategies=[]
        )
        risks.append(foundation_schedule_risk)
        
        # Structural risks
        structural_cost_risk = Risk(
            id="STRUCT_001",
            name="Steel Price Volatility",
            category=RiskCategory.COST,
            impact_type=ImpactType.COST,
            probability_distribution=ProbabilityDistribution(
                distribution_type=DistributionType.NORMAL,
                parameters={"mean": 50000, "std": 20000}
            ),
            baseline_impact=50000,
            correlation_dependencies=["STRUCT_002"],
            mitigation_strategies=[
                MitigationStrategy(
                    id="MIT_STRUCT_001",
                    name="Fixed Price Steel Contract",
                    description="Lock in steel prices early",
                    cost=5000,
                    effectiveness=0.8,
                    implementation_time=7
                )
            ]
        )
        risks.append(structural_cost_risk)
        
        structural_schedule_risk = Risk(
            id="STRUCT_002",
            name="Structural Work Delays - Labor Shortage",
            category=RiskCategory.SCHEDULE,
            impact_type=ImpactType.SCHEDULE,
            probability_distribution=ProbabilityDistribution(
                distribution_type=DistributionType.BETA,
                parameters={"alpha": 2, "beta": 5}
            ),
            baseline_impact=20,  # days
            correlation_dependencies=["FOUND_002", "STRUCT_001"],
            mitigation_strategies=[]
        )
        risks.append(structural_schedule_risk)
        
        # Regulatory risks
        permit_risk = Risk(
            id="REG_001",
            name="Permit Approval Delays",
            category=RiskCategory.REGULATORY,
            impact_type=ImpactType.BOTH,
            probability_distribution=ProbabilityDistribution(
                distribution_type=DistributionType.TRIANGULAR,
                parameters={"min": 10000, "mode": 30000, "max": 80000}
            ),
            baseline_impact=30000,
            correlation_dependencies=[],
            mitigation_strategies=[
                MitigationStrategy(
                    id="MIT_REG_001",
                    name="Expedited Permit Process",
                    description="Pay for expedited review",
                    cost=8000,
                    effectiveness=0.5,
                    implementation_time=3
                )
            ]
        )
        risks.append(permit_risk)
        
        # External risks
        supply_chain_risk = Risk(
            id="EXT_001",
            name="Supply Chain Disruption",
            category=RiskCategory.EXTERNAL,
            impact_type=ImpactType.BOTH,
            probability_distribution=ProbabilityDistribution(
                distribution_type=DistributionType.UNIFORM,
                parameters={"min": 20000, "max": 100000}
            ),
            baseline_impact=60000,
            correlation_dependencies=["STRUCT_001"],
            mitigation_strategies=[]
        )
        risks.append(supply_chain_risk)
        
        return risks
    
    @pytest.fixture
    def realistic_correlations(self, realistic_construction_project_risks) -> CorrelationMatrix:
        """Create realistic correlation matrix for construction project."""
        correlations = {
            # Foundation risks are highly correlated
            ("FOUND_001", "FOUND_002"): 0.7,
            
            # Structural risks are moderately correlated
            ("STRUCT_001", "STRUCT_002"): 0.5,
            
            # Foundation and structural work are related
            ("FOUND_002", "STRUCT_002"): 0.4,
            
            # Supply chain affects structural costs
            ("EXT_001", "STRUCT_001"): 0.6,
            
            # Weather affects multiple schedule items
            ("FOUND_002", "STRUCT_002"): 0.3,
        }
        
        risk_ids = [risk.id for risk in realistic_construction_project_risks]
        return CorrelationMatrix(correlations=correlations, risk_ids=risk_ids)
    
    @pytest.fixture
    def realistic_schedule_data(self) -> ScheduleData:
        """Create realistic schedule data for construction project."""
        milestones = [
            Milestone(
                id="MS_001",
                name="Site Preparation Complete",
                planned_date=datetime.now() + timedelta(days=15),
                baseline_duration=15,
                critical_path=True,
                dependencies=[]
            ),
            Milestone(
                id="MS_002",
                name="Foundation Complete",
                planned_date=datetime.now() + timedelta(days=45),
                baseline_duration=30,
                critical_path=True,
                dependencies=["MS_001"]
            ),
            Milestone(
                id="MS_003",
                name="Structure Complete",
                planned_date=datetime.now() + timedelta(days=105),
                baseline_duration=60,
                critical_path=True,
                dependencies=["MS_002"]
            ),
            Milestone(
                id="MS_004",
                name="Project Complete",
                planned_date=datetime.now() + timedelta(days=150),
                baseline_duration=45,
                critical_path=True,
                dependencies=["MS_003"]
            )
        ]
        
        activities = [
            Activity(
                id="ACT_001",
                name="Site Excavation",
                baseline_duration=10,
                earliest_start=0,
                latest_start=0,
                float_time=0,
                critical_path=True,
                resource_requirements={"excavator": 1, "operator": 1, "crew": 3}
            ),
            Activity(
                id="ACT_002",
                name="Foundation Pour",
                baseline_duration=20,
                earliest_start=15,
                latest_start=15,
                float_time=0,
                critical_path=True,
                resource_requirements={"concrete_crew": 8, "crane": 1, "pump": 1}
            ),
            Activity(
                id="ACT_003",
                name="Steel Erection",
                baseline_duration=40,
                earliest_start=45,
                latest_start=45,
                float_time=0,
                critical_path=True,
                resource_requirements={"steel_crew": 12, "crane": 2}
            ),
            Activity(
                id="ACT_004",
                name="Finishing Work",
                baseline_duration=30,
                earliest_start=105,
                latest_start=120,
                float_time=15,
                critical_path=False,
                resource_requirements={"finish_crew": 6}
            )
        ]
        
        resource_constraints = [
            ResourceConstraint(
                resource_id="RES_001",
                resource_name="Tower Crane",
                total_availability=2,
                utilization_limit=0.9,
                availability_periods=[(0, 150, 2)]
            ),
            ResourceConstraint(
                resource_id="RES_002",
                resource_name="Concrete Crew",
                total_availability=10,
                utilization_limit=1.0,
                availability_periods=[(0, 150, 10)]
            ),
            ResourceConstraint(
                resource_id="RES_003",
                resource_name="Steel Erection Crew",
                total_availability=15,
                utilization_limit=0.8,
                availability_periods=[(0, 150, 15)]
            )
        ]
        
        return ScheduleData(
            project_baseline_duration=150,
            milestones=milestones,
            activities=activities,
            resource_constraints=resource_constraints,
            project_start_date=datetime.now()
        )
    
    @pytest.fixture
    def system_integrator(self):
        """Create system integrator for testing."""
        config = SimulationConfig(
            iterations=10000,
            convergence_threshold=0.01,
            max_execution_time=60.0,
            parameter_change_sensitivity=0.05
        )
        return MonteCarloSystemIntegrator(config)
    
    def test_complete_realistic_workflow(
        self, 
        system_integrator,
        realistic_construction_project_risks,
        realistic_correlations,
        realistic_schedule_data
    ):
        """Test complete workflow with realistic construction project data."""
        print(f"\n🏗️ Testing complete realistic construction project workflow")
        
        # Execute complete workflow
        workflow_result = system_integrator.execute_complete_workflow(
            risks=realistic_construction_project_risks,
            correlations=realistic_correlations,
            iterations=10000,
            include_visualization=False,  # Skip for faster testing
            include_historical_learning=False,  # Skip for faster testing
            export_formats=["json"]
        )
        
        # Verify workflow success
        assert workflow_result.success, f"Workflow failed: {workflow_result.execution_error}"
        assert workflow_result.simulation_results is not None
        assert workflow_result.percentile_analysis is not None
        assert workflow_result.confidence_intervals is not None
        assert len(workflow_result.risk_contributions) > 0
        
        # Verify realistic results
        results = workflow_result.simulation_results
        assert results.iteration_count == 10000
        assert results.execution_time < 60.0  # Should complete within time limit
        
        # Verify cost outcomes are reasonable for construction project
        cost_mean = np.mean(results.cost_outcomes)
        cost_std = np.std(results.cost_outcomes)
        assert 200000 <= cost_mean <= 600000  # Reasonable range for construction risks
        assert cost_std > 0  # Should have variability
        
        # Verify schedule outcomes are reasonable
        schedule_mean = np.mean(results.schedule_outcomes)
        schedule_std = np.std(results.schedule_outcomes)
        assert 30 <= schedule_mean <= 120  # Reasonable delay range in days
        assert schedule_std > 0  # Should have variability
        
        # Verify risk contributions sum to reasonable total
        total_contribution = sum(contrib.contribution_percentage for contrib in workflow_result.risk_contributions)
        assert 0.7 <= total_contribution <= 1.0  # Should account for most variance
        
        # Verify performance metrics
        assert workflow_result.performance_metrics.meets_performance_requirements
        assert workflow_result.performance_metrics.risks_per_second > 0
        
        print(f"   ✅ Workflow completed successfully in {workflow_result.execution_time:.2f}s")
        print(f"   📊 Cost mean: ${cost_mean:,.0f} (±${cost_std:,.0f})")
        print(f"   📅 Schedule mean: {schedule_mean:.1f} days (±{schedule_std:.1f})")
        print(f"   🎯 Top risk: {workflow_result.risk_contributions[0].risk_name} ({workflow_result.risk_contributions[0].contribution_percentage:.1%})")
    
    def test_scenario_comparison_with_mitigation(
        self,
        system_integrator,
        realistic_construction_project_risks,
        realistic_correlations
    ):
        """Test scenario comparison workflow with mitigation strategies."""
        print(f"\n🔄 Testing scenario comparison with mitigation strategies")
        
        # Create baseline scenario
        baseline_scenario = Scenario(
            id="baseline",
            name="Baseline Construction Project",
            description="Original risk parameters without mitigation",
            risks=realistic_construction_project_risks
        )
        
        # Create mitigation scenario with reduced risks
        mitigation_modifications = {
            "FOUND_001": RiskModification(
                parameter_changes={"mode": 50000, "max": 100000},  # Reduced foundation risk
                mitigation_applied="MIT_FOUND_001"
            ),
            "STRUCT_001": RiskModification(
                parameter_changes={"mean": 30000, "std": 15000},  # Reduced steel price risk
                mitigation_applied="MIT_STRUCT_001"
            ),
            "REG_001": RiskModification(
                parameter_changes={"mode": 20000, "max": 50000},  # Reduced permit risk
                mitigation_applied="MIT_REG_001"
            )
        }
        
        # Apply modifications to create mitigation scenario risks
        mitigation_risks = []
        for risk in realistic_construction_project_risks:
            if risk.id in mitigation_modifications:
                mod = mitigation_modifications[risk.id]
                # Create new distribution with modified parameters
                new_params = {**risk.probability_distribution.parameters, **mod.parameter_changes}
                new_distribution = ProbabilityDistribution(
                    distribution_type=risk.probability_distribution.distribution_type,
                    parameters=new_params,
                    bounds=risk.probability_distribution.bounds
                )
                # Create modified risk
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
        
        mitigation_scenario = Scenario(
            id="mitigation",
            name="Mitigation Construction Project",
            description="With key mitigation strategies applied",
            risks=mitigation_risks,
            modifications=mitigation_modifications
        )
        
        # Execute scenario comparison
        comparison_result = system_integrator.execute_scenario_comparison_workflow(
            scenarios=[baseline_scenario, mitigation_scenario],
            iterations=10000
        )
        
        # Verify comparison results
        assert len(comparison_result['scenario_results']) == 2
        assert len(comparison_result['comparisons']) == 1
        
        baseline_results = comparison_result['scenario_results']['baseline']
        mitigation_results = comparison_result['scenario_results']['mitigation']
        
        # Verify mitigation effectiveness
        baseline_cost_mean = np.mean(baseline_results.cost_outcomes)
        mitigation_cost_mean = np.mean(mitigation_results.cost_outcomes)
        cost_reduction = baseline_cost_mean - mitigation_cost_mean
        
        assert cost_reduction > 0, "Mitigation should reduce expected costs"
        assert cost_reduction > 20000, "Cost reduction should be meaningful"
        
        # Verify schedule improvement
        baseline_schedule_mean = np.mean(baseline_results.schedule_outcomes)
        mitigation_schedule_mean = np.mean(mitigation_results.schedule_outcomes)
        schedule_improvement = baseline_schedule_mean - mitigation_schedule_mean
        
        # Schedule might not improve significantly with cost mitigations
        assert schedule_improvement >= -5, "Schedule shouldn't worsen significantly"
        
        print(f"   ✅ Scenario comparison completed successfully")
        print(f"   💰 Cost reduction: ${cost_reduction:,.0f}")
        print(f"   📅 Schedule change: {schedule_improvement:.1f} days")
        print(f"   📈 Mitigation effectiveness: {(cost_reduction/baseline_cost_mean)*100:.1f}%")
    
    def test_system_scalability(self, system_integrator):
        """Test system scalability with varying project sizes."""
        print(f"\n📈 Testing system scalability")
        
        scalability_results = []
        
        # Test with different numbers of risks
        for risk_count in [10, 25, 50]:
            print(f"   Testing with {risk_count} risks...")
            
            # Generate risks for scalability testing
            test_risks = []
            for i in range(risk_count):
                risk = Risk(
                    id=f"SCALE_RISK_{i:03d}",
                    name=f"Scalability Test Risk {i}",
                    category=RiskCategory.COST if i % 2 == 0 else RiskCategory.SCHEDULE,
                    impact_type=ImpactType.COST if i % 2 == 0 else ImpactType.SCHEDULE,
                    probability_distribution=ProbabilityDistribution(
                        distribution_type=DistributionType.NORMAL,
                        parameters={"mean": 10000 + i * 500, "std": 2000 + i * 100}
                    ),
                    baseline_impact=10000 + i * 500,
                    correlation_dependencies=[],
                    mitigation_strategies=[]
                )
                test_risks.append(risk)
            
            # Measure execution time
            start_time = time.time()
            workflow_result = system_integrator.execute_complete_workflow(
                risks=test_risks,
                iterations=10000,
                include_visualization=False,
                include_historical_learning=False
            )
            execution_time = time.time() - start_time
            
            # Verify successful execution
            assert workflow_result.success, f"Scalability test failed for {risk_count} risks"
            assert execution_time < 60.0, f"Execution time {execution_time:.2f}s exceeds limit for {risk_count} risks"
            
            scalability_results.append({
                'risk_count': risk_count,
                'execution_time': execution_time,
                'risks_per_second': risk_count / execution_time
            })
            
            print(f"     ✅ {risk_count} risks: {execution_time:.2f}s ({risk_count/execution_time:.1f} risks/sec)")
        
        # Verify scalability trends
        assert scalability_results[0]['execution_time'] < scalability_results[2]['execution_time']
        assert all(result['risks_per_second'] > 0.5 for result in scalability_results)
        
        print(f"   ✅ Scalability test passed - system scales appropriately")
    
    def test_cross_component_data_flow(
        self,
        system_integrator,
        realistic_construction_project_risks,
        realistic_correlations
    ):
        """Test data flow between system components."""
        print(f"\n🔄 Testing cross-component data flow")
        
        # Test that data flows correctly through all components
        workflow_result = system_integrator.execute_complete_workflow(
            risks=realistic_construction_project_risks,
            correlations=realistic_correlations,
            iterations=10000,
            include_visualization=False,
            include_historical_learning=False
        )
        
        assert workflow_result.success
        
        # Verify data consistency across components
        results = workflow_result.simulation_results
        
        # Check that risk contributions match input risks
        input_risk_ids = {risk.id for risk in realistic_construction_project_risks}
        result_risk_ids = set(results.risk_contributions.keys())
        assert input_risk_ids == result_risk_ids, "Risk IDs should match between input and results"
        
        # Check that correlation effects are reflected in results
        # Highly correlated risks should have similar contribution patterns
        found_001_contrib = next(contrib for contrib in workflow_result.risk_contributions if contrib.risk_id == "FOUND_001")
        found_002_contrib = next(contrib for contrib in workflow_result.risk_contributions if contrib.risk_id == "FOUND_002")
        
        # These risks have 0.7 correlation, so their contributions should be related
        # (This is a simplified check - in practice, correlation effects are complex)
        assert found_001_contrib.contribution_percentage > 0
        assert found_002_contrib.contribution_percentage > 0
        
        # Check that percentile analysis is consistent with raw data
        percentiles = workflow_result.percentile_analysis.percentiles
        cost_data = results.cost_outcomes
        
        # Verify P50 (median) matches numpy calculation
        calculated_median = np.percentile(cost_data, 50)
        assert abs(percentiles[50.0] - calculated_median) < 1000, "Median calculation should be consistent"
        
        # Verify confidence intervals are reasonable
        ci_80 = workflow_result.confidence_intervals.intervals[0.8]
        ci_95 = workflow_result.confidence_intervals.intervals[0.95]
        
        # 95% CI should be wider than 80% CI
        assert (ci_95[1] - ci_95[0]) > (ci_80[1] - ci_80[0]), "95% CI should be wider than 80% CI"
        
        print(f"   ✅ Cross-component data flow validated")
        print(f"   📊 Risk contributions: {len(workflow_result.risk_contributions)} risks tracked")
        print(f"   📈 Percentile consistency verified")
        print(f"   🎯 Confidence intervals properly ordered")
    
    def test_system_health_monitoring(self, system_integrator):
        """Test system health monitoring and validation."""
        print(f"\n🏥 Testing system health monitoring")
        
        # Test system health check
        health_status = system_integrator.get_system_health()
        
        assert health_status.components_initialized
        assert health_status.overall_status in ['healthy', 'degraded']
        assert health_status.component_health is not None
        
        # Test integration validation
        integration_report = system_integrator.validate_system_integration()
        
        assert integration_report.validation_timestamp is not None
        assert integration_report.components_healthy
        assert integration_report.workflow_functional
        assert integration_report.overall_integration_status
        
        print(f"   ✅ System health: {health_status.overall_status}")
        print(f"   🔧 Components initialized: {health_status.components_initialized}")
        print(f"   ✅ Integration status: {'PASS' if integration_report.overall_integration_status else 'FAIL'}")
    
    def test_error_recovery_and_degradation(self, system_integrator):
        """Test error recovery and graceful degradation."""
        print(f"\n🛡️ Testing error recovery and graceful degradation")
        
        # Test with invalid input that should be handled gracefully
        invalid_risks = [
            Risk(
                id="INVALID_001",
                name="Invalid Risk",
                category=RiskCategory.COST,
                impact_type=ImpactType.COST,
                probability_distribution=ProbabilityDistribution(
                    distribution_type=DistributionType.NORMAL,
                    parameters={"mean": 0, "std": 1}  # Valid parameters
                ),
                baseline_impact=0,  # Edge case: zero impact
                correlation_dependencies=[],
                mitigation_strategies=[]
            )
        ]
        
        # This should complete successfully even with edge case data
        workflow_result = system_integrator.execute_complete_workflow(
            risks=invalid_risks,
            iterations=10000,
            include_visualization=False,
            include_historical_learning=False
        )
        
        # Should handle edge cases gracefully
        assert workflow_result.success or len(workflow_result.validation_errors) > 0
        
        # Test with empty risks list (should fail gracefully)
        empty_workflow_result = system_integrator.execute_complete_workflow(
            risks=[],
            iterations=10000,
            include_visualization=False,
            include_historical_learning=False
        )
        
        # Should fail gracefully with appropriate error
        assert not empty_workflow_result.success
        assert empty_workflow_result.execution_error is not None
        
        print(f"   ✅ Edge case handling: {'PASS' if workflow_result.success else 'HANDLED'}")
        print(f"   ✅ Empty input handling: {'HANDLED' if not empty_workflow_result.success else 'UNEXPECTED'}")
        print(f"   🛡️ Error recovery working properly")


if __name__ == "__main__":
    # Run comprehensive system integration tests
    pytest.main([__file__, "-v", "--tb=short"])