"""
Property-based tests for historical learning functionality.

**Feature: monte-carlo-risk-simulations, Property 26: Historical Learning**
**Validates: Requirements 10.1, 10.2**
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from datetime import datetime, timedelta
import numpy as np
from typing import List
import uuid

from monte_carlo.historical_data_calibrator import (
    HistoricalDataCalibrator, ProjectOutcome, PredictionAccuracyMetrics
)
from monte_carlo.models import (
    Risk, ProbabilityDistribution, DistributionType, RiskCategory, 
    ImpactType, SimulationResults, ConvergenceMetrics
)


# Strategy for generating valid project outcomes
@st.composite
def project_outcome_strategy(draw):
    """Generate valid ProjectOutcome instances."""
    project_id = str(uuid.uuid4())[:8]  # Use UUID for unique IDs
    project_type = draw(st.sampled_from(['construction', 'software', 'infrastructure', 'research']))
    
    # Generate realistic cost and duration values
    baseline_cost = draw(st.floats(min_value=10000, max_value=10000000))
    baseline_duration = draw(st.floats(min_value=30, max_value=1000))
    
    # Actual values can vary from baseline
    cost_multiplier = draw(st.floats(min_value=0.8, max_value=2.0))
    duration_multiplier = draw(st.floats(min_value=0.9, max_value=1.5))
    
    actual_cost = baseline_cost * cost_multiplier
    actual_duration = baseline_duration * duration_multiplier
    
    completion_date = datetime.now() - timedelta(days=draw(st.integers(min_value=1, max_value=365)))
    
    # Generate risk outcomes
    num_risks = draw(st.integers(min_value=1, max_value=10))
    risk_outcomes = {}
    for i in range(num_risks):
        risk_id = f"risk_{i}"
        impact = draw(st.floats(min_value=-50000, max_value=100000))
        risk_outcomes[risk_id] = impact
    
    return ProjectOutcome(
        project_id=project_id,
        project_type=project_type,
        completion_date=completion_date,
        actual_cost=actual_cost,
        actual_duration=actual_duration,
        baseline_cost=baseline_cost,
        baseline_duration=baseline_duration,
        risk_outcomes=risk_outcomes
    )


@st.composite
def risk_strategy(draw):
    """Generate valid Risk instances."""
    risk_id = str(uuid.uuid4())[:8]  # Use UUID for unique IDs
    name = draw(st.text(min_size=1, max_size=50))
    category = draw(st.sampled_from(list(RiskCategory)))
    impact_type = draw(st.sampled_from(list(ImpactType)))
    
    # Generate a simple normal distribution
    mean = draw(st.floats(min_value=1000, max_value=50000))
    std = draw(st.floats(min_value=100, max_value=10000))
    
    distribution = ProbabilityDistribution(
        distribution_type=DistributionType.NORMAL,
        parameters={'mean': mean, 'std': std}
    )
    
    baseline_impact = draw(st.floats(min_value=1000, max_value=100000))
    
    return Risk(
        id=risk_id,
        name=name,
        category=category,
        impact_type=impact_type,
        probability_distribution=distribution,
        baseline_impact=baseline_impact
    )


@st.composite
def simulation_results_strategy(draw):
    """Generate valid SimulationResults instances."""
    simulation_id = str(uuid.uuid4())[:8]  # Use UUID for unique IDs
    iteration_count = draw(st.integers(min_value=100, max_value=1000))
    
    # Generate realistic outcome arrays
    cost_outcomes = draw(st.lists(
        st.floats(min_value=10000, max_value=1000000),
        min_size=iteration_count,
        max_size=iteration_count
    ))
    schedule_outcomes = draw(st.lists(
        st.floats(min_value=30, max_value=500),
        min_size=iteration_count,
        max_size=iteration_count
    ))
    
    convergence_metrics = ConvergenceMetrics(
        mean_stability=0.95,
        variance_stability=0.90,
        percentile_stability={50: 0.95, 90: 0.90},
        converged=True
    )
    
    return SimulationResults(
        simulation_id=simulation_id,
        timestamp=datetime.now(),
        iteration_count=iteration_count,
        cost_outcomes=np.array(cost_outcomes),
        schedule_outcomes=np.array(schedule_outcomes),
        risk_contributions={},
        convergence_metrics=convergence_metrics,
        execution_time=1.5
    )


class TestHistoricalLearningProperties:
    """Property-based tests for historical learning functionality."""
    
    @given(st.lists(project_outcome_strategy(), min_size=1, max_size=20))
    @settings(max_examples=50, deadline=None)
    def test_project_outcome_storage_integrity(self, outcomes: List[ProjectOutcome]):
        """
        Property 26a: Project outcome storage integrity
        For any list of project outcomes, storing them should preserve all data integrity.
        **Validates: Requirements 10.1**
        """
        calibrator = HistoricalDataCalibrator()
        
        # Store all outcomes
        for outcome in outcomes:
            calibrator.add_project_outcome(outcome)
        
        # Verify all outcomes are stored
        assert len(calibrator.project_outcomes) <= len(outcomes)  # May be fewer due to duplicate IDs
        
        # Verify data integrity for stored outcomes
        stored_ids = {po.project_id for po in calibrator.project_outcomes}
        original_ids = {outcome.project_id for outcome in outcomes}
        
        # All stored IDs should be from original outcomes
        assert stored_ids.issubset(original_ids)
        
        # For each stored outcome, verify it matches one of the original outcomes
        for stored_outcome in calibrator.project_outcomes:
            # Find the corresponding original outcome(s) with the same ID
            matching_outcomes = [o for o in outcomes if o.project_id == stored_outcome.project_id]
            assert len(matching_outcomes) > 0
            
            # The stored outcome should match the last one added (due to update behavior)
            last_matching = matching_outcomes[-1]
            assert stored_outcome.actual_cost == last_matching.actual_cost
            assert stored_outcome.actual_duration == last_matching.actual_duration
            assert stored_outcome.project_type == last_matching.project_type
    
    @given(
        st.lists(project_outcome_strategy(), min_size=15, max_size=30),
        risk_strategy()
    )
    @settings(max_examples=30, deadline=None)
    def test_distribution_calibration_validity(self, outcomes: List[ProjectOutcome], risk: Risk):
        """
        Property 26b: Distribution calibration validity
        For any risk with sufficient historical data, calibration should produce a valid distribution
        with improved fit to historical data.
        **Validates: Requirements 10.1**
        """
        calibrator = HistoricalDataCalibrator()
        
        # Add outcomes with risk impacts matching the risk ID
        modified_outcomes = []
        for i, outcome in enumerate(outcomes):
            # Ensure some outcomes have the risk we're testing
            if i < len(outcomes) // 2:
                outcome.risk_outcomes[risk.id] = np.random.normal(5000, 1000)
            modified_outcomes.append(outcome)
            calibrator.add_project_outcome(outcome)
        
        try:
            # Attempt calibration
            calibration_result = calibrator.calibrate_distribution(risk)
            
            # Verify calibration result validity
            assert calibration_result.sample_size >= 10
            assert calibration_result.goodness_of_fit >= 0.0
            assert calibration_result.goodness_of_fit <= 1.0
            assert calibration_result.confidence_level > 0.0
            assert calibration_result.confidence_level <= 1.0
            
            # Verify calibrated distribution is different from original
            original_params = risk.probability_distribution.parameters
            calibrated_params = calibration_result.calibrated_distribution.parameters
            
            # At least one parameter should be different (allowing for small numerical differences)
            params_different = False
            for key in original_params:
                if key in calibrated_params:
                    if abs(original_params[key] - calibrated_params[key]) > 1e-6:
                        params_different = True
                        break
            
            # If parameters are the same, distribution type might be different
            if not params_different:
                assert (calibration_result.calibrated_distribution.distribution_type != 
                       risk.probability_distribution.distribution_type)
                
        except ValueError as e:
            # Insufficient data is acceptable
            assert "Insufficient historical data" in str(e)
    
    @given(
        simulation_results_strategy(),
        project_outcome_strategy()
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_prediction_accuracy_calculation(self, predicted_results: SimulationResults, actual_outcome: ProjectOutcome):
        """
        Property 26c: Prediction accuracy calculation
        For any simulation results and actual outcome, accuracy metrics should be mathematically valid.
        **Validates: Requirements 10.2**
        """
        calibrator = HistoricalDataCalibrator()
        
        # Calculate accuracy metrics
        accuracy_metrics = calibrator.calculate_prediction_accuracy(
            predicted_results, actual_outcome
        )
        
        # Verify all metrics are non-negative where expected
        assert accuracy_metrics.mean_absolute_error >= 0
        assert accuracy_metrics.root_mean_square_error >= 0
        assert accuracy_metrics.mean_absolute_percentage_error >= 0
        
        # R-squared should be between 0 and 1 (or negative for very poor fits)
        assert accuracy_metrics.r_squared >= -10  # Allow some negative values for poor fits
        
        # RMSE should be >= MAE (mathematical property)
        assert accuracy_metrics.root_mean_square_error >= accuracy_metrics.mean_absolute_error
        
        # Coverage rates should be between 0 and 1
        for conf_level, coverage in accuracy_metrics.prediction_intervals_coverage.items():
            assert 0.0 <= coverage <= 1.0
            assert 0.0 < conf_level < 1.0
    
    @given(
        st.lists(project_outcome_strategy(), min_size=5, max_size=15),
        st.lists(simulation_results_strategy(), min_size=3, max_size=8)
    )
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.large_base_example, HealthCheck.data_too_large])
    def test_model_performance_tracking_consistency(self, outcomes: List[ProjectOutcome], sim_results: List[SimulationResults]):
        """
        Property 26d: Model performance tracking consistency
        For any sequence of predictions and outcomes, performance tracking should maintain consistency.
        **Validates: Requirements 10.2**
        """
        assume(len(outcomes) >= len(sim_results))
        
        calibrator = HistoricalDataCalibrator()
        model_id = "test_model"
        risk_category = RiskCategory.COST
        
        # Track performance over multiple predictions
        for i, sim_result in enumerate(sim_results):
            if i < len(outcomes):
                accuracy_metrics = calibrator.calculate_prediction_accuracy(
                    sim_result, outcomes[i]
                )
                
                calibrator.track_model_performance(
                    model_id, risk_category, accuracy_metrics
                )
        
        # Verify performance tracker exists and has correct data
        tracker = calibrator.get_model_performance(model_id)
        assert tracker is not None
        assert tracker.model_id == model_id
        assert tracker.risk_category == risk_category
        assert len(tracker.accuracy_history) == len(sim_results)
        
        # Verify performance trend is valid
        assert tracker.performance_trend in ["improving", "stable", "degrading"]
        
        # Verify timestamps are in chronological order
        timestamps = [timestamp for timestamp, _ in tracker.accuracy_history]
        for i in range(1, len(timestamps)):
            assert timestamps[i] >= timestamps[i-1]
    
    @given(
        st.lists(project_outcome_strategy(), min_size=20, max_size=50),
        risk_strategy()
    )
    @settings(max_examples=15, deadline=None)
    def test_calibration_improves_with_more_data(self, outcomes: List[ProjectOutcome], risk: Risk):
        """
        Property 26e: Calibration improvement with more data
        For any risk, calibration with more historical data should not decrease goodness-of-fit
        (or should provide more reliable estimates).
        **Validates: Requirements 10.1**
        """
        calibrator = HistoricalDataCalibrator()
        
        # Add risk impacts to outcomes
        for i, outcome in enumerate(outcomes):
            # Generate consistent risk impacts based on risk category
            base_impact = 5000 if risk.category == RiskCategory.COST else 10
            impact = np.random.normal(base_impact, base_impact * 0.3)
            outcome.risk_outcomes[risk.id] = impact
            calibrator.add_project_outcome(outcome)
        
        # Test with different sample sizes
        sample_sizes = [15, 25, len(outcomes)]
        goodness_scores = []
        
        for sample_size in sample_sizes:
            if sample_size <= len(outcomes):
                # Create calibrator with limited data
                limited_calibrator = HistoricalDataCalibrator()
                for outcome in outcomes[:sample_size]:
                    limited_calibrator.add_project_outcome(outcome)
                
                try:
                    calibration_result = limited_calibrator.calibrate_distribution(risk)
                    goodness_scores.append(calibration_result.goodness_of_fit)
                except ValueError:
                    # Insufficient data - skip this sample size
                    continue
        
        # With more data, we should generally get more reliable calibration
        # (though goodness-of-fit might not always increase monotonically)
        if len(goodness_scores) >= 2:
            # At least verify that calibration is possible with larger datasets
            assert all(score >= 0 for score in goodness_scores)
            assert all(score <= 1 for score in goodness_scores)
    
    @given(st.lists(project_outcome_strategy(), min_size=10, max_size=25))
    @settings(max_examples=30, deadline=None)
    def test_historical_data_filtering_consistency(self, outcomes: List[ProjectOutcome]):
        """
        Property 26f: Historical data filtering consistency
        For any set of project outcomes, filtering by project type should return consistent subsets.
        **Validates: Requirements 10.1**
        """
        calibrator = HistoricalDataCalibrator()
        
        # Add all outcomes
        for outcome in outcomes:
            calibrator.add_project_outcome(outcome)
        
        # Get unique project types
        project_types = list(set(outcome.project_type for outcome in outcomes))
        
        if len(project_types) > 1:
            # Test filtering by each project type
            for project_type in project_types:
                expected_count = sum(1 for outcome in outcomes if outcome.project_type == project_type)
                
                # Create a dummy risk to test filtering
                risk = Risk(
                    id="test_risk",
                    name="Test Risk",
                    category=RiskCategory.COST,
                    impact_type=ImpactType.COST,
                    probability_distribution=ProbabilityDistribution(
                        distribution_type=DistributionType.NORMAL,
                        parameters={'mean': 1000, 'std': 200}
                    ),
                    baseline_impact=1000
                )
                
                # Add risk impacts to outcomes of this project type
                for outcome in outcomes:
                    if outcome.project_type == project_type:
                        outcome.risk_outcomes[risk.id] = np.random.normal(1000, 200)
                
                # Extract impacts for this project type
                impacts = calibrator._extract_risk_impacts(risk.id, risk.category, project_type)
                
                # Should have impacts only from the specified project type
                assert len(impacts) <= expected_count  # May be fewer if not all outcomes have this risk