"""
Simplified integration tests for Monte Carlo Risk Simulation API endpoints.

These tests validate core functionality without full application dependencies.
"""

import pytest
import json
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock

# Import Monte Carlo components directly
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monte_carlo.models import (
    Risk, RiskCategory, ImpactType, DistributionType, ProbabilityDistribution,
    SimulationResults, ConvergenceMetrics
)
from monte_carlo.api_validation import (
    SimulationRequestValidator, ValidationError, BusinessLogicError,
    validate_and_sanitize_simulation_request, handle_api_exception
)

class TestMonteCarloAPIValidation:
    """Test API validation and error handling."""
    
    def test_simulation_request_validation_success(self):
        """Test successful validation of simulation request."""
        valid_request = {
            "risks": [{
                "id": "test-risk-001",
                "name": "Test Risk",
                "category": RiskCategory.COST.value,
                "impact_type": ImpactType.COST.value,
                "distribution_type": DistributionType.NORMAL.value,
                "distribution_parameters": {
                    "mean": 1000.0,
                    "std": 200.0
                },
                "baseline_impact": 1000.0,
                "correlation_dependencies": [],
                "mitigation_strategies": []
            }],
            "iterations": 10000,
            "random_seed": 42
        }
        
        # Validate using Pydantic validator
        validator = SimulationRequestValidator(**valid_request)
        assert validator.iterations == 10000
        assert len(validator.risks) == 1
        assert validator.random_seed == 42
        
        # Test full validation function
        result = validate_and_sanitize_simulation_request(valid_request)
        assert result["validation_status"] == "passed"
        assert "validated_data" in result
        assert "performance_info" in result
    
    def test_simulation_request_validation_errors(self):
        """Test validation errors for invalid requests."""
        # Test empty risks list
        with pytest.raises(Exception):
            SimulationRequestValidator(risks=[], iterations=10000)
        
        # Test invalid iterations
        with pytest.raises(Exception):
            SimulationRequestValidator(
                risks=[{
                    "id": "test-risk",
                    "name": "Test Risk",
                    "category": RiskCategory.COST.value,
                    "impact_type": ImpactType.COST.value,
                    "distribution_type": DistributionType.NORMAL.value,
                    "distribution_parameters": {"mean": 1000, "std": 200},
                    "baseline_impact": 1000
                }],
                iterations=5000  # Below minimum
            )
        
        # Test invalid distribution parameters
        invalid_request = {
            "risks": [{
                "id": "test-risk",
                "name": "Test Risk",
                "category": RiskCategory.COST.value,
                "impact_type": ImpactType.COST.value,
                "distribution_type": DistributionType.TRIANGULAR.value,
                "distribution_parameters": {
                    "min": 1000,
                    "mode": 500,  # Invalid: mode < min
                    "max": 2000
                },
                "baseline_impact": 1000
            }],
            "iterations": 10000
        }
        
        with pytest.raises(Exception):
            validate_and_sanitize_simulation_request(invalid_request)
    
    def test_risk_validation(self):
        """Test individual risk validation."""
        from monte_carlo.api_validation import RiskValidator
        
        # Valid risk
        valid_risk = {
            "id": "risk-001",
            "name": "Test Risk",
            "category": RiskCategory.COST.value,
            "impact_type": ImpactType.COST.value,
            "distribution_type": DistributionType.NORMAL.value,
            "distribution_parameters": {"mean": 1000, "std": 200},
            "baseline_impact": 1000,
            "correlation_dependencies": [],
            "mitigation_strategies": []
        }
        
        validator = RiskValidator(**valid_risk)
        assert validator.id == "risk-001"
        assert validator.name == "Test Risk"
        assert validator.baseline_impact == 1000
        
        # Invalid category
        invalid_risk = valid_risk.copy()
        invalid_risk["category"] = "invalid_category"
        
        with pytest.raises(Exception):
            RiskValidator(**invalid_risk)
        
        # Invalid distribution parameters
        invalid_risk = valid_risk.copy()
        invalid_risk["distribution_parameters"] = {"mean": 1000, "std": -200}  # Negative std
        
        with pytest.raises(Exception):
            RiskValidator(**invalid_risk)
    
    def test_correlation_validation(self):
        """Test correlation matrix validation."""
        valid_request = {
            "risks": [
                {
                    "id": "risk-001",
                    "name": "Risk 1",
                    "category": RiskCategory.COST.value,
                    "impact_type": ImpactType.COST.value,
                    "distribution_type": DistributionType.NORMAL.value,
                    "distribution_parameters": {"mean": 1000, "std": 200},
                    "baseline_impact": 1000
                },
                {
                    "id": "risk-002",
                    "name": "Risk 2",
                    "category": RiskCategory.COST.value,
                    "impact_type": ImpactType.COST.value,
                    "distribution_type": DistributionType.NORMAL.value,
                    "distribution_parameters": {"mean": 2000, "std": 300},
                    "baseline_impact": 2000
                }
            ],
            "iterations": 10000,
            "correlations": {
                "risk-001": {"risk-002": 0.5},
                "risk-002": {"risk-001": 0.5}
            }
        }
        
        # Should validate successfully
        validator = SimulationRequestValidator(**valid_request)
        assert validator.correlations is not None
        
        # Test invalid correlation value
        invalid_request = valid_request.copy()
        invalid_request["correlations"] = {
            "risk-001": {"risk-002": 1.5}  # Invalid: > 1.0
        }
        
        with pytest.raises(Exception):
            SimulationRequestValidator(**invalid_request)
        
        # Test correlation with non-existent risk
        invalid_request = valid_request.copy()
        invalid_request["correlations"] = {
            "risk-001": {"non-existent-risk": 0.5}
        }
        
        with pytest.raises(Exception):
            SimulationRequestValidator(**invalid_request)
    
    def test_error_handling_functions(self):
        """Test error handling utility functions."""
        # Test ValidationError handling
        validation_error = ValidationError("Test validation error", "test_field", "TEST_CODE")
        status_code, response = handle_api_exception(validation_error)
        
        assert status_code == 400
        assert response["error_type"] == "validation_error"
        assert response["message"] == "Test validation error"
        assert response["field"] == "test_field"
        assert response["code"] == "TEST_CODE"
        
        # Test BusinessLogicError handling
        business_error = BusinessLogicError("Test business logic error", "BUSINESS_CODE")
        status_code, response = handle_api_exception(business_error)
        
        assert status_code == 422
        assert response["error_type"] == "business_logic_error"
        assert response["message"] == "Test business logic error"
        assert response["code"] == "BUSINESS_CODE"
        
        # Test generic exception handling
        generic_error = Exception("Generic error")
        status_code, response = handle_api_exception(generic_error)
        
        assert status_code == 500
        assert response["error_type"] == "internal_error"
        assert response["message"] == "Generic error"
    
    def test_performance_validation(self):
        """Test performance validation for different simulation sizes."""
        from monte_carlo.api_validation import PerformanceValidator
        
        # Small simulation
        small_risks = [{"id": f"risk-{i}"} for i in range(5)]
        small_performance = PerformanceValidator.validate_simulation_complexity(small_risks, 10000)
        
        assert small_performance["performance_tier"] == "low"
        assert small_performance["complexity_score"] < 100
        assert len(small_performance["warnings"]) == 0
        
        # Large simulation - use more extreme values to trigger warnings
        large_risks = [{"id": f"risk-{i}"} for i in range(60)]  # More risks
        large_performance = PerformanceValidator.validate_simulation_complexity(large_risks, 150000)  # More iterations
        
        assert large_performance["performance_tier"] in ["medium", "high"]
        assert large_performance["complexity_score"] > 100
        
        # Should have warnings for large simulations
        warnings = large_performance["warnings"]
        assert len(warnings) > 0
        
        # Check for specific warnings
        warning_text = " ".join(warnings).lower()
        assert "performance" in warning_text or "risks" in warning_text or "iteration" in warning_text
    
    def test_input_sanitization(self):
        """Test input sanitization functions."""
        from monte_carlo.api_validation import InputSanitizer
        
        # Test string sanitization
        sanitized = InputSanitizer.sanitize_string("  test string  ")
        assert sanitized == "test string"
        
        # Test string length limit
        with pytest.raises(ValidationError):
            InputSanitizer.sanitize_string("x" * 2000, max_length=1000)
        
        # Test numeric sanitization
        sanitized_num = InputSanitizer.sanitize_numeric(123.45)
        assert sanitized_num == 123.45
        
        # Test numeric bounds
        with pytest.raises(ValidationError):
            InputSanitizer.sanitize_numeric(100, min_val=200)
        
        with pytest.raises(ValidationError):
            InputSanitizer.sanitize_numeric(300, max_val=200)
        
        # Test list sanitization
        sanitized_list = InputSanitizer.sanitize_list([1, 2, 3])
        assert sanitized_list == [1, 2, 3]
        
        # Test list length limit
        with pytest.raises(ValidationError):
            InputSanitizer.sanitize_list([1] * 200, max_items=100)

class TestMonteCarloEngineIntegration:
    """Test Monte Carlo engine integration without full API."""
    
    def test_engine_initialization(self):
        """Test Monte Carlo engine initialization."""
        from monte_carlo.engine import MonteCarloEngine
        
        engine = MonteCarloEngine()
        assert engine is not None
        
        # Test configuration
        assert hasattr(engine, '_config')
        assert hasattr(engine, '_active_simulations')
        assert hasattr(engine, '_simulation_cache')
    
    def test_risk_model_creation(self):
        """Test creating risk models."""
        # Create a probability distribution
        distribution = ProbabilityDistribution(
            distribution_type=DistributionType.NORMAL,
            parameters={"mean": 1000.0, "std": 200.0}
        )
        
        # Create a risk
        risk = Risk(
            id="test-risk-001",
            name="Test Risk",
            category=RiskCategory.COST,
            impact_type=ImpactType.COST,
            probability_distribution=distribution,
            baseline_impact=1000.0
        )
        
        assert risk.id == "test-risk-001"
        assert risk.name == "Test Risk"
        assert risk.category == RiskCategory.COST
        assert risk.impact_type == ImpactType.COST
        assert risk.baseline_impact == 1000.0
        
        # Test distribution sampling
        samples = risk.probability_distribution.sample(100)
        assert len(samples) == 100
        assert all(isinstance(sample, (int, float)) for sample in samples)
    
    def test_simulation_parameter_validation(self):
        """Test simulation parameter validation."""
        from monte_carlo.engine import MonteCarloEngine
        
        engine = MonteCarloEngine()
        
        # Create valid risks
        distribution = ProbabilityDistribution(
            distribution_type=DistributionType.NORMAL,
            parameters={"mean": 1000.0, "std": 200.0}
        )
        
        risks = [
            Risk(
                id=f"test-risk-{i:03d}",
                name=f"Test Risk {i}",
                category=RiskCategory.COST,
                impact_type=ImpactType.COST,
                probability_distribution=distribution,
                baseline_impact=1000.0 * (i + 1)
            )
            for i in range(3)
        ]
        
        # Test validation with valid parameters
        validation_result = engine.validate_simulation_parameters(risks, 10000)
        assert validation_result.is_valid is True
        assert len(validation_result.errors) == 0
        
        # Test validation with invalid parameters
        validation_result = engine.validate_simulation_parameters([], 10000)
        assert validation_result.is_valid is False
        assert len(validation_result.errors) > 0
        
        # Test validation with too few iterations
        validation_result = engine.validate_simulation_parameters(risks, 5000)
        assert validation_result.is_valid is False
        assert any("10,000 iterations" in error for error in validation_result.errors)
    
    def test_scenario_generator_integration(self):
        """Test scenario generator functionality."""
        from monte_carlo.scenario_generator import ScenarioGenerator
        from monte_carlo.models import RiskModification
        
        generator = ScenarioGenerator()
        
        # Create base risks
        distribution = ProbabilityDistribution(
            distribution_type=DistributionType.TRIANGULAR,
            parameters={"min": 500.0, "mode": 1000.0, "max": 2000.0}
        )
        
        base_risks = [
            Risk(
                id="scenario-risk-001",
                name="Scenario Test Risk",
                category=RiskCategory.SCHEDULE,
                impact_type=ImpactType.SCHEDULE,
                probability_distribution=distribution,
                baseline_impact=1000.0
            )
        ]
        
        # Create scenario with modifications
        modifications = {
            "scenario-risk-001": RiskModification(
                parameter_changes={"mode": 1500.0}
            )
        }
        
        scenario = generator.create_scenario(
            base_risks=base_risks,
            modifications=modifications,
            name="Test Scenario",
            description="A test scenario"
        )
        
        assert scenario.name == "Test Scenario"
        assert scenario.description == "A test scenario"
        assert len(scenario.risks) == 1
        assert len(scenario.modifications) == 1
        
        # Verify modification was applied
        modified_risk = scenario.risks[0]
        assert modified_risk.probability_distribution.parameters["mode"] == 1500.0
        
        # Test scenario isolation
        original_risk = base_risks[0]
        assert original_risk.probability_distribution.parameters["mode"] == 1000.0  # Unchanged
    
    def test_results_analyzer_integration(self):
        """Test results analyzer functionality."""
        from monte_carlo.results_analyzer import SimulationResultsAnalyzer
        import numpy as np
        from datetime import datetime
        
        analyzer = SimulationResultsAnalyzer()
        
        # Create mock simulation results
        iteration_count = 1000
        cost_outcomes = np.random.normal(10000, 2000, iteration_count)
        schedule_outcomes = np.random.normal(100, 20, iteration_count)
        
        convergence_metrics = ConvergenceMetrics(
            mean_stability=0.95,
            variance_stability=0.90,
            percentile_stability={50: 0.98, 90: 0.92},
            converged=True,
            iterations_to_convergence=800
        )
        
        results = SimulationResults(
            simulation_id="test-simulation-001",
            timestamp=datetime.now(),
            iteration_count=iteration_count,
            cost_outcomes=cost_outcomes,
            schedule_outcomes=schedule_outcomes,
            risk_contributions={"test-risk": cost_outcomes * 0.5},
            convergence_metrics=convergence_metrics,
            execution_time=5.0
        )
        
        # Test percentile analysis
        percentile_analysis = analyzer.calculate_percentiles(results)
        assert percentile_analysis.mean > 0
        assert percentile_analysis.median > 0
        assert percentile_analysis.std_dev > 0
        assert 10 in percentile_analysis.percentiles
        assert 90 in percentile_analysis.percentiles
        
        # Test confidence intervals
        confidence_intervals = analyzer.generate_confidence_intervals(results, 'cost', [0.8, 0.9, 0.95])
        assert 0.8 in confidence_intervals.intervals
        assert 0.9 in confidence_intervals.intervals
        assert 0.95 in confidence_intervals.intervals
        
        for level, (lower, upper) in confidence_intervals.intervals.items():
            assert lower < upper
            assert lower >= cost_outcomes.min()
            assert upper <= cost_outcomes.max()
        
        # Test risk contribution analysis
        risk_contributions = analyzer.identify_top_risk_contributors(results, top_n=5)
        assert len(risk_contributions) <= 5
        
        if risk_contributions:
            contrib = risk_contributions[0]
            assert contrib.risk_id == "test-risk"
            assert 0 <= contrib.contribution_percentage <= 100
            assert contrib.variance_contribution >= 0

class TestMonteCarloAPIErrorScenarios:
    """Test error scenarios and edge cases."""
    
    def test_graceful_degradation_manager(self):
        """Test graceful degradation for system failures."""
        from monte_carlo.api_validation import GracefulDegradationManager
        
        manager = GracefulDegradationManager()
        
        # Test database failure
        db_fallback = manager.handle_system_failure("database", "store_results")
        assert db_fallback["status"] == "degraded"
        assert "fallback_used" in db_fallback
        
        # Test cache failure
        cache_fallback = manager.handle_system_failure("cache", "retrieve_data")
        assert cache_fallback["status"] == "degraded"
        assert cache_fallback["fallback_used"] == "direct_computation"
        
        # Test unknown system failure
        unknown_fallback = manager.handle_system_failure("unknown_system", "unknown_operation")
        assert unknown_fallback["status"] == "failed"
        assert unknown_fallback["fallback_used"] == "none"
    
    def test_user_friendly_error_messages(self):
        """Test user-friendly error message generation."""
        from monte_carlo.api_validation import create_user_friendly_error_message
        
        # Test validation error
        validation_error = {
            "error_type": "validation_error",
            "message": "Invalid parameter",
            "field": "iterations"
        }
        
        friendly_message = create_user_friendly_error_message(validation_error)
        assert "Invalid iterations" in friendly_message
        assert "invalid parameter" in friendly_message.lower()
        
        # Test business logic error
        business_error = {
            "error_type": "business_logic_error",
            "message": "Simulation failed to converge"
        }
        
        friendly_message = create_user_friendly_error_message(business_error)
        assert "Operation failed" in friendly_message
        assert "simulation failed to converge" in friendly_message.lower()
        
        # Test external system error
        external_error = {
            "error_type": "external_system_error",
            "system": "database",
            "recoverable": True
        }
        
        friendly_message = create_user_friendly_error_message(external_error)
        assert "database" in friendly_message.lower()
        assert "try again" in friendly_message.lower()
    
    def test_edge_case_handling(self):
        """Test handling of edge cases in validation."""
        # Test very large numbers
        large_request = {
            "risks": [{
                "id": "large-risk",
                "name": "Large Risk",
                "category": RiskCategory.COST.value,
                "impact_type": ImpactType.COST.value,
                "distribution_type": DistributionType.NORMAL.value,
                "distribution_parameters": {
                    "mean": 1e9,  # Very large number
                    "std": 1e8
                },
                "baseline_impact": 1e9
            }],
            "iterations": 10000
        }
        
        # Should handle large numbers gracefully
        try:
            result = validate_and_sanitize_simulation_request(large_request)
            assert result["validation_status"] == "passed"
        except Exception as e:
            # If validation fails, it should be with a clear error message
            assert "bounds" in str(e).lower() or "range" in str(e).lower()
        
        # Test very small numbers
        small_request = {
            "risks": [{
                "id": "small-risk",
                "name": "Small Risk",
                "category": RiskCategory.COST.value,
                "impact_type": ImpactType.COST.value,
                "distribution_type": DistributionType.NORMAL.value,
                "distribution_parameters": {
                    "mean": 0.001,
                    "std": 0.0001
                },
                "baseline_impact": 0.001
            }],
            "iterations": 10000
        }
        
        # Should handle small numbers gracefully
        result = validate_and_sanitize_simulation_request(small_request)
        assert result["validation_status"] == "passed"

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])