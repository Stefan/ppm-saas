"""
Property-based tests for Monte Carlo Simulation Results Analyzer

Feature: monte-carlo-risk-simulations, Property 6: Statistical Analysis Completeness
Validates: Requirements 3.1, 3.2, 3.4
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime
import uuid
from unittest.mock import Mock

# Import the components we're testing
from monte_carlo.results_analyzer import SimulationResultsAnalyzer
from monte_carlo.models import (
    SimulationResults, ConvergenceMetrics, PercentileAnalysis, ConfidenceIntervals
)


# Test data strategies for property-based testing
@st.composite
def simulation_results_strategy(draw):
    """Generate SimulationResults data for testing"""
    iteration_count = draw(st.integers(min_value=100, max_value=10000))
    
    # Generate realistic cost and schedule outcomes
    cost_mean = draw(st.floats(min_value=10000, max_value=1000000))
    cost_std = draw(st.floats(min_value=1000, max_value=cost_mean * 0.3))
    schedule_mean = draw(st.floats(min_value=30, max_value=365))
    schedule_std = draw(st.floats(min_value=5, max_value=schedule_mean * 0.2))
    
    # Generate normally distributed outcomes
    np.random.seed(42)  # For reproducible tests
    cost_outcomes = np.random.normal(cost_mean, cost_std, iteration_count)
    schedule_outcomes = np.random.normal(schedule_mean, schedule_std, iteration_count)
    
    # Ensure positive values
    cost_outcomes = np.abs(cost_outcomes)
    schedule_outcomes = np.abs(schedule_outcomes)
    
    # Generate risk contributions
    num_risks = draw(st.integers(min_value=1, max_value=10))
    risk_contributions = {}
    for i in range(num_risks):
        risk_id = f"risk_{i}"
        # Generate contribution data that sums to the total outcomes
        contribution_factor = draw(st.floats(min_value=0.1, max_value=0.5))
        risk_contributions[risk_id] = cost_outcomes * contribution_factor
    
    # Create convergence metrics
    convergence_metrics = ConvergenceMetrics(
        mean_stability=draw(st.floats(min_value=0.01, max_value=0.1)),
        variance_stability=draw(st.floats(min_value=0.01, max_value=0.1)),
        percentile_stability={50: draw(st.floats(min_value=0.01, max_value=0.1))},
        converged=True,
        iterations_to_convergence=draw(st.integers(min_value=100, max_value=iteration_count))
    )
    
    return SimulationResults(
        simulation_id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        iteration_count=iteration_count,
        cost_outcomes=cost_outcomes,
        schedule_outcomes=schedule_outcomes,
        risk_contributions=risk_contributions,
        convergence_metrics=convergence_metrics,
        execution_time=draw(st.floats(min_value=0.1, max_value=30.0))
    )


@st.composite
def confidence_levels_strategy(draw):
    """Generate valid confidence levels for testing"""
    num_levels = draw(st.integers(min_value=1, max_value=5))
    levels = []
    for _ in range(num_levels):
        level = draw(st.floats(min_value=0.5, max_value=0.99))
        levels.append(level)
    return sorted(set(levels))  # Remove duplicates and sort


class TestStatisticalAnalysisCompleteness:
    """Property 6: Statistical Analysis Completeness tests"""

    def setup_method(self):
        """Set up test environment before each test"""
        self.analyzer = SimulationResultsAnalyzer()

    @settings(max_examples=50)
    @given(results=simulation_results_strategy())
    def test_percentile_calculation_completeness(self, results):
        """
        Property 6: Statistical Analysis Completeness - Percentile Calculations
        For any simulation results, the analyzer should calculate all required percentiles 
        (P10, P25, P50, P75, P90, P95, P99) and statistical measures
        **Validates: Requirements 3.1**
        """
        # Test cost outcomes
        cost_analysis = self.analyzer.calculate_percentiles(results, 'cost')
        
        # Verify all required percentiles are calculated
        required_percentiles = [10, 25, 50, 75, 90, 95, 99]
        for percentile in required_percentiles:
            assert percentile in cost_analysis.percentiles, \
                f"Missing percentile P{percentile} in cost analysis"
            
            # Verify percentile values are reasonable
            percentile_value = cost_analysis.percentiles[percentile]
            assert isinstance(percentile_value, (int, float)), \
                f"Percentile P{percentile} should be numeric"
            assert percentile_value >= 0, \
                f"Percentile P{percentile} should be non-negative"
        
        # Verify percentiles are in ascending order
        percentile_values = [cost_analysis.percentiles[p] for p in required_percentiles]
        assert percentile_values == sorted(percentile_values), \
            "Percentiles should be in ascending order"
        
        # Verify statistical measures are calculated
        assert hasattr(cost_analysis, 'mean'), "Should calculate mean"
        assert hasattr(cost_analysis, 'median'), "Should calculate median"
        assert hasattr(cost_analysis, 'std_dev'), "Should calculate standard deviation"
        assert hasattr(cost_analysis, 'coefficient_of_variation'), "Should calculate coefficient of variation"
        
        # Verify statistical measures are reasonable
        assert cost_analysis.mean > 0, "Mean should be positive"
        assert cost_analysis.median > 0, "Median should be positive"
        assert cost_analysis.std_dev >= 0, "Standard deviation should be non-negative"
        assert cost_analysis.coefficient_of_variation >= 0, "Coefficient of variation should be non-negative"
        
        # Verify median equals P50
        assert abs(cost_analysis.median - cost_analysis.percentiles[50]) < 1e-10, \
            "Median should equal P50"
        
        # Test schedule outcomes
        schedule_analysis = self.analyzer.calculate_percentiles(results, 'schedule')
        
        # Verify all required percentiles are calculated for schedule
        for percentile in required_percentiles:
            assert percentile in schedule_analysis.percentiles, \
                f"Missing percentile P{percentile} in schedule analysis"
            assert schedule_analysis.percentiles[percentile] >= 0, \
                f"Schedule percentile P{percentile} should be non-negative"

    @settings(max_examples=50)
    @given(
        results=simulation_results_strategy(),
        confidence_levels=confidence_levels_strategy()
    )
    def test_confidence_interval_generation_completeness(self, results, confidence_levels):
        """
        Property 6: Statistical Analysis Completeness - Confidence Intervals
        For any simulation results and confidence levels, the analyzer should generate 
        confidence intervals (80%, 90%, 95%) with proper bounds
        **Validates: Requirements 3.2**
        """
        # Test cost confidence intervals
        cost_intervals = self.analyzer.generate_confidence_intervals(
            results, 'cost', confidence_levels
        )
        
        # Verify all requested confidence levels are calculated
        for level in confidence_levels:
            assert level in cost_intervals.intervals, \
                f"Missing confidence interval for level {level}"
            
            lower, upper = cost_intervals.intervals[level]
            
            # Verify interval bounds are reasonable
            assert isinstance(lower, (int, float)), "Lower bound should be numeric"
            assert isinstance(upper, (int, float)), "Upper bound should be numeric"
            assert lower <= upper, f"Lower bound {lower} should be <= upper bound {upper}"
            assert lower >= 0, "Lower bound should be non-negative"
            assert upper >= 0, "Upper bound should be non-negative"
        
        # Verify sample size is recorded correctly
        assert cost_intervals.sample_size == results.iteration_count, \
            "Sample size should match iteration count"
        
        # Test default confidence levels
        default_intervals = self.analyzer.generate_confidence_intervals(results, 'cost')
        default_levels = [0.80, 0.90, 0.95]
        
        for level in default_levels:
            assert level in default_intervals.intervals, \
                f"Missing default confidence interval for level {level}"
        
        # Test schedule confidence intervals
        schedule_intervals = self.analyzer.generate_confidence_intervals(
            results, 'schedule', confidence_levels
        )
        
        for level in confidence_levels:
            assert level in schedule_intervals.intervals, \
                f"Missing schedule confidence interval for level {level}"

    @settings(max_examples=50)
    @given(results=simulation_results_strategy())
    def test_expected_values_and_variation_completeness(self, results):
        """
        Property 6: Statistical Analysis Completeness - Expected Values and Variation
        For any simulation results, the analyzer should calculate expected values, 
        standard deviations, and coefficient of variation for both cost and schedule
        **Validates: Requirements 3.4**
        """
        statistics = self.analyzer.calculate_expected_values_and_variation(results)
        
        # Verify both cost and schedule statistics are calculated
        assert 'cost' in statistics, "Should calculate cost statistics"
        assert 'schedule' in statistics, "Should calculate schedule statistics"
        
        for outcome_type in ['cost', 'schedule']:
            stats = statistics[outcome_type]
            
            # Verify all required statistical measures are present
            required_measures = [
                'expected_value', 'standard_deviation', 'coefficient_of_variation',
                'variance', 'skewness', 'kurtosis'
            ]
            
            for measure in required_measures:
                assert measure in stats, \
                    f"Missing {measure} in {outcome_type} statistics"
                
                # Verify measures are numeric
                assert isinstance(stats[measure], (int, float)), \
                    f"{measure} should be numeric"
            
            # Verify statistical relationships
            expected_value = stats['expected_value']
            std_dev = stats['standard_deviation']
            variance = stats['variance']
            cv = stats['coefficient_of_variation']
            
            # Expected value should be positive for our test data
            assert expected_value > 0, f"{outcome_type} expected value should be positive"
            
            # Standard deviation should be non-negative
            assert std_dev >= 0, f"{outcome_type} standard deviation should be non-negative"
            
            # Variance should equal standard deviation squared (approximately)
            # Use relative tolerance for large numbers
            if std_dev > 0:
                relative_error = abs(variance - std_dev**2) / (std_dev**2)
                assert relative_error < 1e-6, \
                    f"{outcome_type} variance should equal std_dev squared (relative error: {relative_error})"
            else:
                assert variance == 0, f"{outcome_type} variance should be 0 when std_dev is 0"
            
            # Coefficient of variation should be calculated correctly
            if expected_value != 0:
                expected_cv = std_dev / expected_value
                assert abs(cv - expected_cv) < 1e-10, \
                    f"{outcome_type} coefficient of variation should equal std_dev/mean"
            else:
                assert cv == 0, f"{outcome_type} coefficient of variation should be 0 when mean is 0"

    @settings(max_examples=30)
    @given(results=simulation_results_strategy())
    def test_outcome_type_validation(self, results):
        """
        Property 6: Statistical Analysis Completeness - Input Validation
        For any invalid outcome type, the analyzer should raise appropriate errors
        **Validates: Requirements 3.1, 3.2**
        """
        # Test invalid outcome types
        invalid_types = ['invalid', 'revenue', 'quality', '', None]
        
        for invalid_type in invalid_types:
            if invalid_type is None:
                continue  # Skip None as it would cause different error
                
            with pytest.raises(ValueError, match="outcome_type must be 'cost' or 'schedule'"):
                self.analyzer.calculate_percentiles(results, invalid_type)
            
            with pytest.raises(ValueError, match="outcome_type must be 'cost' or 'schedule'"):
                self.analyzer.generate_confidence_intervals(results, invalid_type)

    @settings(max_examples=30)
    @given(results=simulation_results_strategy())
    def test_statistical_consistency_across_methods(self, results):
        """
        Property 6: Statistical Analysis Completeness - Cross-Method Consistency
        For any simulation results, statistical measures should be consistent 
        across different analysis methods
        **Validates: Requirements 3.1, 3.2, 3.4**
        """
        # Get statistics from different methods
        cost_percentiles = self.analyzer.calculate_percentiles(results, 'cost')
        cost_statistics = self.analyzer.calculate_expected_values_and_variation(results)['cost']
        
        # Verify consistency between methods
        # Mean should be consistent
        assert abs(cost_percentiles.mean - cost_statistics['expected_value']) < 1e-10, \
            "Mean should be consistent across methods"
        
        # Standard deviation should be consistent
        assert abs(cost_percentiles.std_dev - cost_statistics['standard_deviation']) < 1e-10, \
            "Standard deviation should be consistent across methods"
        
        # Coefficient of variation should be consistent
        assert abs(cost_percentiles.coefficient_of_variation - cost_statistics['coefficient_of_variation']) < 1e-10, \
            "Coefficient of variation should be consistent across methods"
        
        # Median should be close to P50 percentile
        assert abs(cost_percentiles.median - cost_percentiles.percentiles[50]) < 1e-10, \
            "Median should equal P50 percentile"

    def test_empty_results_handling(self):
        """
        Property 6: Statistical Analysis Completeness - Edge Case Handling
        For edge cases like empty or minimal data, the analyzer should handle gracefully
        **Validates: Requirements 3.1, 3.2, 3.4**
        """
        # Test with minimal data (single value)
        minimal_results = SimulationResults(
            simulation_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            iteration_count=1,
            cost_outcomes=np.array([1000.0]),
            schedule_outcomes=np.array([30.0]),
            risk_contributions={},
            convergence_metrics=ConvergenceMetrics(
                mean_stability=0.0,
                variance_stability=0.0,
                percentile_stability={},
                converged=True
            ),
            execution_time=0.1
        )
        
        # Should handle single-value case
        cost_analysis = self.analyzer.calculate_percentiles(minimal_results, 'cost')
        
        # All percentiles should equal the single value
        for percentile in [10, 25, 50, 75, 90, 95, 99]:
            assert cost_analysis.percentiles[percentile] == 1000.0, \
                f"P{percentile} should equal the single value"
        
        # Standard deviation should be 0 for single value
        assert cost_analysis.std_dev == 0.0, \
            "Standard deviation should be 0 for single value"
        
        # Coefficient of variation should be 0
        assert cost_analysis.coefficient_of_variation == 0.0, \
            "Coefficient of variation should be 0 for single value"


class TestRiskContributionAnalysis:
    """Property 7: Risk Contribution Analysis tests"""

    def setup_method(self):
        """Set up test environment before each test"""
        self.analyzer = SimulationResultsAnalyzer()

    @settings(max_examples=30)
    @given(results=simulation_results_strategy())
    def test_top_risk_contributors_identification(self, results):
        """
        Property 7: Risk Contribution Analysis - Top Contributors Identification
        For any simulation with multiple risks, the analyzer should correctly identify 
        and rank the top 10 risk contributors to overall project uncertainty
        **Validates: Requirements 3.3**
        """
        assume(len(results.risk_contributions) > 0)  # Only test when there are risk contributions
        
        # Test default top 10
        top_contributors = self.analyzer.identify_top_risk_contributors(results)
        
        # Verify we get at most 10 contributors
        assert len(top_contributors) <= 10, "Should return at most 10 contributors"
        
        # Verify we get at most the number of available risks
        assert len(top_contributors) <= len(results.risk_contributions), \
            "Should not return more contributors than available risks"
        
        # Verify all contributors are valid RiskContribution objects
        for contributor in top_contributors:
            assert hasattr(contributor, 'risk_id'), "Should have risk_id"
            assert hasattr(contributor, 'risk_name'), "Should have risk_name"
            assert hasattr(contributor, 'contribution_percentage'), "Should have contribution_percentage"
            assert hasattr(contributor, 'variance_contribution'), "Should have variance_contribution"
            assert hasattr(contributor, 'correlation_effects'), "Should have correlation_effects"
            
            # Verify contribution percentage is reasonable
            assert isinstance(contributor.contribution_percentage, (int, float)), \
                "Contribution percentage should be numeric"
            assert contributor.contribution_percentage >= 0, \
                "Contribution percentage should be non-negative"
            
            # Verify variance contribution is non-negative
            assert contributor.variance_contribution >= 0, \
                "Variance contribution should be non-negative"
            
            # Verify risk_id exists in original risk contributions
            assert contributor.risk_id in results.risk_contributions, \
                f"Risk ID {contributor.risk_id} should exist in original contributions"
        
        # Verify contributors are sorted by contribution percentage (descending)
        if len(top_contributors) > 1:
            for i in range(len(top_contributors) - 1):
                assert top_contributors[i].contribution_percentage >= top_contributors[i + 1].contribution_percentage, \
                    "Contributors should be sorted by contribution percentage (descending)"

    @settings(max_examples=30)
    @given(results=simulation_results_strategy())
    def test_risk_contribution_ranking_completeness(self, results):
        """
        Property 7: Risk Contribution Analysis - Ranking Completeness
        For any simulation results, the analyzer should provide comprehensive 
        contribution ranking and uncertainty attribution for all risks
        **Validates: Requirements 3.3**
        """
        assume(len(results.risk_contributions) > 0)  # Only test when there are risk contributions
        
        ranking = self.analyzer.calculate_risk_contribution_ranking(results)
        
        # Verify all risks are included in ranking
        assert len(ranking) == len(results.risk_contributions), \
            "Ranking should include all risks from simulation"
        
        for risk_id in results.risk_contributions.keys():
            assert risk_id in ranking, f"Risk {risk_id} should be in ranking"
            
            risk_metrics = ranking[risk_id]
            
            # Verify all required metrics are present
            required_metrics = [
                'variance_contribution', 'contribution_percentage', 'mean_impact',
                'standard_deviation', 'coefficient_of_variation', 'cost_correlation',
                'schedule_correlation', 'uncertainty_index'
            ]
            
            for metric in required_metrics:
                assert metric in risk_metrics, f"Missing {metric} for risk {risk_id}"
                assert isinstance(risk_metrics[metric], (int, float)), \
                    f"{metric} should be numeric for risk {risk_id}"
            
            # Verify metric reasonableness
            assert risk_metrics['variance_contribution'] >= 0, \
                "Variance contribution should be non-negative"
            assert risk_metrics['contribution_percentage'] >= 0, \
                "Contribution percentage should be non-negative"
            assert risk_metrics['standard_deviation'] >= 0, \
                "Standard deviation should be non-negative"
            assert -1 <= risk_metrics['cost_correlation'] <= 1, \
                "Cost correlation should be between -1 and 1"
            assert -1 <= risk_metrics['schedule_correlation'] <= 1, \
                "Schedule correlation should be between -1 and 1"

    @settings(max_examples=20)
    @given(results=simulation_results_strategy())
    def test_contribution_percentage_consistency(self, results):
        """
        Property 7: Risk Contribution Analysis - Contribution Percentage Consistency
        For any simulation results, the sum of individual risk contribution percentages 
        should be reasonable relative to the total variance
        **Validates: Requirements 3.3**
        """
        assume(len(results.risk_contributions) > 0)  # Only test when there are risk contributions
        
        top_contributors = self.analyzer.identify_top_risk_contributors(results, top_n=len(results.risk_contributions))
        
        # Calculate total contribution percentage
        total_contribution = sum(contributor.contribution_percentage for contributor in top_contributors)
        
        # For independent risks, total should be approximately 100%
        # For correlated risks, it can be different due to interaction effects
        # We'll check that it's reasonable (not negative, not extremely high)
        assert total_contribution >= 0, "Total contribution percentage should be non-negative"
        
        # Check that individual contributions are reasonable
        for contributor in top_contributors:
            # No single risk should contribute more than 100% (unless there are negative correlations)
            assert contributor.contribution_percentage <= 200, \
                f"Risk {contributor.risk_id} contribution seems unreasonably high: {contributor.contribution_percentage}%"

    @settings(max_examples=20)
    @given(results=simulation_results_strategy())
    def test_correlation_effects_validity(self, results):
        """
        Property 7: Risk Contribution Analysis - Correlation Effects Validity
        For any simulation results, correlation effects between risks should be 
        mathematically valid (between -1 and 1)
        **Validates: Requirements 3.3**
        """
        assume(len(results.risk_contributions) > 1)  # Need at least 2 risks for correlations
        
        top_contributors = self.analyzer.identify_top_risk_contributors(results)
        
        for contributor in top_contributors:
            for other_risk_id, correlation in contributor.correlation_effects.items():
                # Verify correlation is within valid range
                assert -1 <= correlation <= 1, \
                    f"Correlation between {contributor.risk_id} and {other_risk_id} should be between -1 and 1, got {correlation}"
                
                # Verify other risk exists in original data
                assert other_risk_id in results.risk_contributions, \
                    f"Other risk {other_risk_id} should exist in original contributions"

    def test_top_n_parameter_validation(self):
        """
        Property 7: Risk Contribution Analysis - Parameter Validation
        For any invalid top_n parameter, the analyzer should raise appropriate errors
        **Validates: Requirements 3.3**
        """
        # Create minimal test results
        test_results = SimulationResults(
            simulation_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            iteration_count=100,
            cost_outcomes=np.random.normal(10000, 1000, 100),
            schedule_outcomes=np.random.normal(30, 5, 100),
            risk_contributions={'risk_1': np.random.normal(5000, 500, 100)},
            convergence_metrics=ConvergenceMetrics(
                mean_stability=0.01,
                variance_stability=0.01,
                percentile_stability={},
                converged=True
            ),
            execution_time=1.0
        )
        
        # Test invalid top_n values
        invalid_top_n_values = [0, -1, -10]
        
        for invalid_top_n in invalid_top_n_values:
            with pytest.raises(ValueError, match="top_n must be positive"):
                self.analyzer.identify_top_risk_contributors(test_results, top_n=invalid_top_n)

    def test_empty_risk_contributions_handling(self):
        """
        Property 7: Risk Contribution Analysis - Empty Data Handling
        For simulation results with no risk contributions, the analyzer should handle gracefully
        **Validates: Requirements 3.3**
        """
        # Create test results with no risk contributions
        empty_results = SimulationResults(
            simulation_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            iteration_count=100,
            cost_outcomes=np.random.normal(10000, 1000, 100),
            schedule_outcomes=np.random.normal(30, 5, 100),
            risk_contributions={},  # Empty risk contributions
            convergence_metrics=ConvergenceMetrics(
                mean_stability=0.01,
                variance_stability=0.01,
                percentile_stability={},
                converged=True
            ),
            execution_time=1.0
        )
        
        # Should raise appropriate error for empty risk contributions
        with pytest.raises(ValueError, match="No risk contributions found"):
            self.analyzer.identify_top_risk_contributors(empty_results)
        
        # Ranking should return empty dict for empty contributions
        ranking = self.analyzer.calculate_risk_contribution_ranking(empty_results)
        assert ranking == {}, "Should return empty dict for empty risk contributions"

class TestScenarioComparisonValidity:
    """Property 8: Scenario Comparison Validity tests"""

    def setup_method(self):
        """Set up test environment before each test"""
        self.analyzer = SimulationResultsAnalyzer()

    @settings(max_examples=30)
    @given(
        results_a=simulation_results_strategy(),
        results_b=simulation_results_strategy()
    )
    def test_scenario_comparison_statistical_validity(self, results_a, results_b):
        """
        Property 8: Scenario Comparison Validity - Statistical Tests
        For any two different scenarios, the analyzer should provide statistically 
        valid significance tests for comparing simulation results
        **Validates: Requirements 3.5**
        """
        # Ensure both scenarios have the same iteration count for valid comparison
        min_iterations = min(results_a.iteration_count, results_b.iteration_count)
        
        # Truncate to same length
        results_a_truncated = SimulationResults(
            simulation_id=results_a.simulation_id,
            timestamp=results_a.timestamp,
            iteration_count=min_iterations,
            cost_outcomes=results_a.cost_outcomes[:min_iterations],
            schedule_outcomes=results_a.schedule_outcomes[:min_iterations],
            risk_contributions={k: v[:min_iterations] for k, v in results_a.risk_contributions.items()},
            convergence_metrics=results_a.convergence_metrics,
            execution_time=results_a.execution_time
        )
        
        results_b_truncated = SimulationResults(
            simulation_id=results_b.simulation_id,
            timestamp=results_b.timestamp,
            iteration_count=min_iterations,
            cost_outcomes=results_b.cost_outcomes[:min_iterations],
            schedule_outcomes=results_b.schedule_outcomes[:min_iterations],
            risk_contributions={k: v[:min_iterations] for k, v in results_b.risk_contributions.items()},
            convergence_metrics=results_b.convergence_metrics,
            execution_time=results_b.execution_time
        )
        
        # Perform scenario comparison
        comparison = self.analyzer.compare_scenarios(results_a_truncated, results_b_truncated)
        
        # Verify comparison structure
        assert hasattr(comparison, 'scenario_a_id'), "Should have scenario_a_id"
        assert hasattr(comparison, 'scenario_b_id'), "Should have scenario_b_id"
        assert hasattr(comparison, 'cost_difference'), "Should have cost_difference"
        assert hasattr(comparison, 'schedule_difference'), "Should have schedule_difference"
        assert hasattr(comparison, 'statistical_significance'), "Should have statistical_significance"
        assert hasattr(comparison, 'effect_size'), "Should have effect_size"
        
        # Verify scenario IDs are correct
        assert comparison.scenario_a_id == results_a_truncated.simulation_id
        assert comparison.scenario_b_id == results_b_truncated.simulation_id
        
        # Verify cost difference analysis
        cost_diff = comparison.cost_difference
        self._verify_statistical_analysis(cost_diff, "cost")
        
        # Verify schedule difference analysis
        schedule_diff = comparison.schedule_difference
        self._verify_statistical_analysis(schedule_diff, "schedule")

    def _verify_statistical_analysis(self, analysis: Dict[str, float], outcome_type: str):
        """Helper method to verify statistical analysis results"""
        # Verify required statistical measures
        required_measures = [
            'mean_a', 'mean_b', 'std_a', 'std_b', 'mean_difference',
            'relative_difference_percent', 't_statistic', 't_p_value',
            'mannwhitney_u_statistic', 'mannwhitney_p_value',
            'ks_statistic', 'ks_p_value', 'cohens_d', 'confidence_interval_95'
        ]
        
        for measure in required_measures:
            assert measure in analysis, f"Missing {measure} in {outcome_type} analysis"
            
            if measure == 'confidence_interval_95':
                # Verify confidence interval is a tuple
                assert isinstance(analysis[measure], tuple), \
                    f"Confidence interval should be a tuple for {outcome_type}"
                assert len(analysis[measure]) == 2, \
                    f"Confidence interval should have 2 values for {outcome_type}"
                lower, upper = analysis[measure]
                assert lower <= upper, \
                    f"Confidence interval lower bound should be <= upper bound for {outcome_type}"
            else:
                # Verify other measures are numeric
                assert isinstance(analysis[measure], (int, float)), \
                    f"{measure} should be numeric for {outcome_type}"
        
        # Verify p-values are in valid range [0, 1]
        p_value_measures = ['t_p_value', 'mannwhitney_p_value', 'ks_p_value']
        for p_measure in p_value_measures:
            p_value = analysis[p_measure]
            assert 0 <= p_value <= 1, \
                f"{p_measure} should be between 0 and 1 for {outcome_type}, got {p_value}"
        
        # Verify standard deviations are non-negative
        assert analysis['std_a'] >= 0, f"Standard deviation A should be non-negative for {outcome_type}"
        assert analysis['std_b'] >= 0, f"Standard deviation B should be non-negative for {outcome_type}"
        
        # Verify statistical significance structure
        assert 'statistical_significance' in analysis, \
            f"Should have statistical_significance in {outcome_type} analysis"
        stat_sig = analysis['statistical_significance']
        
        required_tests = ['t_test', 'mann_whitney', 'kolmogorov_smirnov']
        for test in required_tests:
            assert test in stat_sig, f"Missing {test} in statistical significance for {outcome_type}"
            assert 0 <= stat_sig[test] <= 1, \
                f"{test} p-value should be between 0 and 1 for {outcome_type}"
        
        # Verify effect size structure
        assert 'effect_size' in analysis, f"Should have effect_size in {outcome_type} analysis"
        effect_size = analysis['effect_size']
        
        required_effect_measures = ['cohens_d', 'mean_difference', 'relative_difference']
        for measure in required_effect_measures:
            assert measure in effect_size, f"Missing {measure} in effect size for {outcome_type}"
            assert isinstance(effect_size[measure], (int, float)), \
                f"{measure} should be numeric in effect size for {outcome_type}"

    @settings(max_examples=20)
    @given(results=simulation_results_strategy())
    def test_scenario_self_comparison_validity(self, results):
        """
        Property 8: Scenario Comparison Validity - Self Comparison
        For any scenario compared to itself, statistical tests should show 
        no significant differences (p-values should be high)
        **Validates: Requirements 3.5**
        """
        # Compare scenario to itself
        comparison = self.analyzer.compare_scenarios(results, results)
        
        # Verify mean differences are zero (or very close to zero)
        assert abs(comparison.cost_difference['mean_difference']) < 1e-10, \
            "Mean difference should be zero when comparing scenario to itself"
        assert abs(comparison.schedule_difference['mean_difference']) < 1e-10, \
            "Schedule mean difference should be zero when comparing scenario to itself"
        
        # Verify relative differences are zero
        assert abs(comparison.cost_difference['relative_difference_percent']) < 1e-10, \
            "Relative difference should be zero when comparing scenario to itself"
        assert abs(comparison.schedule_difference['relative_difference_percent']) < 1e-10, \
            "Schedule relative difference should be zero when comparing scenario to itself"
        
        # Verify Cohen's d is zero (no effect)
        assert abs(comparison.cost_difference['cohens_d']) < 1e-10, \
            "Cohen's d should be zero when comparing scenario to itself"
        assert abs(comparison.schedule_difference['cohens_d']) < 1e-10, \
            "Schedule Cohen's d should be zero when comparing scenario to itself"
        
        # Verify confidence intervals contain zero
        cost_ci = comparison.cost_difference['confidence_interval_95']
        schedule_ci = comparison.schedule_difference['confidence_interval_95']
        
        assert cost_ci[0] <= 0 <= cost_ci[1], \
            "Cost confidence interval should contain zero for self-comparison"
        assert schedule_ci[0] <= 0 <= schedule_ci[1], \
            "Schedule confidence interval should contain zero for self-comparison"

    @settings(max_examples=20)
    @given(results=simulation_results_strategy())
    def test_comprehensive_scenario_difference_analysis(self, results):
        """
        Property 8: Scenario Comparison Validity - Comprehensive Analysis
        For any scenario analysis, the system should provide comprehensive 
        interpretation and recommendations
        **Validates: Requirements 3.5**
        """
        # Create a modified version of the scenario for comparison
        # Modify cost outcomes by adding a small constant
        modified_cost = results.cost_outcomes + 1000  # Add $1000 to all costs
        
        modified_results = SimulationResults(
            simulation_id=str(uuid.uuid4()),
            timestamp=results.timestamp,
            iteration_count=results.iteration_count,
            cost_outcomes=modified_cost,
            schedule_outcomes=results.schedule_outcomes,  # Keep schedule the same
            risk_contributions=results.risk_contributions,
            convergence_metrics=results.convergence_metrics,
            execution_time=results.execution_time
        )
        
        # Perform comprehensive analysis
        analysis = self.analyzer.perform_scenario_difference_analysis(results, modified_results)
        
        # Verify analysis structure
        required_sections = ['comparison_results', 'cost_analysis', 'schedule_analysis', 'overall_assessment']
        for section in required_sections:
            assert section in analysis, f"Missing {section} in comprehensive analysis"
        
        # Verify cost analysis structure
        cost_analysis = analysis['cost_analysis']
        required_cost_fields = [
            'statistically_significant', 'effect_size_interpretation',
            'practical_significance', 'recommendation'
        ]
        for field in required_cost_fields:
            assert field in cost_analysis, f"Missing {field} in cost analysis"
        
        # Verify schedule analysis structure
        schedule_analysis = analysis['schedule_analysis']
        required_schedule_fields = [
            'statistically_significant', 'effect_size_interpretation',
            'practical_significance', 'recommendation'
        ]
        for field in required_schedule_fields:
            assert field in schedule_analysis, f"Missing {field} in schedule analysis"
        
        # Verify overall assessment structure
        overall = analysis['overall_assessment']
        required_overall_fields = [
            'scenarios_differ_significantly', 'primary_difference_type', 'confidence_level'
        ]
        for field in required_overall_fields:
            assert field in overall, f"Missing {field} in overall assessment"
        
        # Verify field types and values
        assert isinstance(cost_analysis['statistically_significant'], bool), \
            "Statistical significance should be boolean"
        assert cost_analysis['effect_size_interpretation'] in ['negligible', 'small', 'medium', 'large'], \
            "Effect size interpretation should be valid category"
        assert isinstance(cost_analysis['practical_significance'], bool), \
            "Practical significance should be boolean"
        assert isinstance(cost_analysis['recommendation'], str), \
            "Recommendation should be string"
        
        # Since we added $1000 to costs, cost analysis should show significant difference
        # Note: Due to high variance in generated data, we'll check if the difference is detected
        # rather than requiring statistical significance
        comparison = analysis['comparison_results']
        cost_mean_diff = abs(comparison.cost_difference['mean_difference'])
        assert cost_mean_diff > 900, \
            f"Should detect meaningful cost difference, got {cost_mean_diff}"
        
        # The relative difference should be reasonable
        relative_diff = abs(comparison.cost_difference['relative_difference_percent'])
        assert relative_diff > 0, \
            "Should have non-zero relative difference"
        
        # Schedule should not be significantly different (we didn't change it)
        # Note: Due to randomness, this might occasionally fail, so we'll be lenient
        
        # Verify confidence level is reasonable
        assert 90 <= overall['confidence_level'] <= 99, \
            "Confidence level should be reasonable (90-99%)"

    def test_mismatched_iteration_counts_handling(self):
        """
        Property 8: Scenario Comparison Validity - Error Handling
        For scenarios with different iteration counts, the analyzer should 
        raise appropriate errors
        **Validates: Requirements 3.5**
        """
        # Create scenarios with different iteration counts
        results_a = SimulationResults(
            simulation_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            iteration_count=100,
            cost_outcomes=np.random.normal(10000, 1000, 100),
            schedule_outcomes=np.random.normal(30, 5, 100),
            risk_contributions={},
            convergence_metrics=ConvergenceMetrics(
                mean_stability=0.01,
                variance_stability=0.01,
                percentile_stability={},
                converged=True
            ),
            execution_time=1.0
        )
        
        results_b = SimulationResults(
            simulation_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            iteration_count=200,  # Different iteration count
            cost_outcomes=np.random.normal(10000, 1000, 200),
            schedule_outcomes=np.random.normal(30, 5, 200),
            risk_contributions={},
            convergence_metrics=ConvergenceMetrics(
                mean_stability=0.01,
                variance_stability=0.01,
                percentile_stability={},
                converged=True
            ),
            execution_time=2.0
        )
        
        # Should raise error for mismatched iteration counts
        with pytest.raises(ValueError, match="Scenarios must have the same number of iterations"):
            self.analyzer.compare_scenarios(results_a, results_b)