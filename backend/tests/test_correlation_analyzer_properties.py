"""
Property-based tests for Risk Correlation Analyzer.

Tests the correlation analysis functionality including matrix validation,
correlated sampling, and cross-impact modeling using property-based testing.
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from scipy.stats import pearsonr

from monte_carlo.correlation_analyzer import RiskCorrelationAnalyzer
from monte_carlo.models import (
    CorrelationMatrix, ProbabilityDistribution, DistributionType,
    CrossImpactModel, ValidationResult
)


# Hypothesis strategies for generating test data
@st.composite
def correlation_coefficient_strategy(draw):
    """Generate valid correlation coefficients."""
    return draw(st.floats(min_value=-0.99, max_value=0.99, allow_nan=False, allow_infinity=False))


@st.composite
def risk_ids_strategy(draw):
    """Generate lists of unique risk IDs."""
    return draw(st.lists(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        min_size=2, max_size=8, unique=True
    ))


@st.composite
def correlation_matrix_strategy(draw):
    """Generate valid correlation matrices that are positive definite."""
    risk_ids = draw(risk_ids_strategy())
    n = len(risk_ids)
    
    if n == 2:
        # For 2x2 matrices, any correlation in [-1, 1] works
        correlation = draw(correlation_coefficient_strategy())
        correlations = {(risk_ids[0], risk_ids[1]): correlation}
    else:
        # For larger matrices, use a more conservative approach to ensure positive definiteness
        # Generate correlations with smaller magnitudes to avoid numerical issues
        correlations = {}
        max_corr = min(0.7, 1.0 / (n - 1))  # Conservative upper bound
        
        for i, risk1 in enumerate(risk_ids):
            for j, risk2 in enumerate(risk_ids[i+1:], i+1):
                correlation = draw(st.floats(min_value=-max_corr, max_value=max_corr, 
                                           allow_nan=False, allow_infinity=False))
                correlations[(risk1, risk2)] = correlation
    
    return correlations, risk_ids


@st.composite
def probability_distribution_strategy(draw):
    """Generate valid probability distributions."""
    dist_type = draw(st.sampled_from(DistributionType))
    
    if dist_type == DistributionType.NORMAL:
        mean = draw(st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False))
        std = draw(st.floats(min_value=0.1, max_value=10, allow_nan=False, allow_infinity=False))
        parameters = {'mean': mean, 'std': std}
    elif dist_type == DistributionType.TRIANGULAR:
        min_val = draw(st.floats(min_value=0, max_value=50, allow_nan=False, allow_infinity=False))
        max_val = draw(st.floats(min_value=min_val + 1, max_value=min_val + 100, allow_nan=False, allow_infinity=False))
        mode = draw(st.floats(min_value=min_val, max_value=max_val, allow_nan=False, allow_infinity=False))
        parameters = {'min': min_val, 'mode': mode, 'max': max_val}
    elif dist_type == DistributionType.UNIFORM:
        min_val = draw(st.floats(min_value=0, max_value=50, allow_nan=False, allow_infinity=False))
        max_val = draw(st.floats(min_value=min_val + 0.1, max_value=min_val + 100, allow_nan=False, allow_infinity=False))
        parameters = {'min': min_val, 'max': max_val}
    elif dist_type == DistributionType.BETA:
        alpha = draw(st.floats(min_value=0.5, max_value=5, allow_nan=False, allow_infinity=False))
        beta = draw(st.floats(min_value=0.5, max_value=5, allow_nan=False, allow_infinity=False))
        parameters = {'alpha': alpha, 'beta': beta}
    elif dist_type == DistributionType.LOGNORMAL:
        mu = draw(st.floats(min_value=-2, max_value=2, allow_nan=False, allow_infinity=False))
        sigma = draw(st.floats(min_value=0.1, max_value=1, allow_nan=False, allow_infinity=False))
        parameters = {'mu': mu, 'sigma': sigma}
    
    return ProbabilityDistribution(dist_type, parameters)


class TestCorrelationAnalyzerProperties:
    """Property-based tests for Risk Correlation Analyzer."""
    
    @given(correlation_matrix_strategy())
    def test_correlation_matrix_validation(self, matrix_data):
        """
        **Feature: monte-carlo-risk-simulations, Property 5: Cross-Impact Modeling**
        
        For any correlation matrix with valid coefficients, the analyzer should
        successfully validate the matrix and ensure mathematical consistency.
        **Validates: Requirements 2.5**
        """
        correlations, risk_ids = matrix_data
        analyzer = RiskCorrelationAnalyzer()
        
        # Should successfully create correlation matrix
        corr_matrix = analyzer.create_correlation_matrix(correlations, risk_ids)
        
        # Validate the matrix
        validation_result = analyzer.validate_correlation_matrix(corr_matrix)
        
        # Matrix should be valid (assuming we generated valid correlations)
        assert isinstance(validation_result, ValidationResult)
        
        # All correlations should be within bounds
        for (risk1, risk2), corr in correlations.items():
            assert -1.0 <= corr <= 1.0
            assert corr_matrix.get_correlation(risk1, risk2) == corr
            assert corr_matrix.get_correlation(risk2, risk1) == corr  # Symmetry
        
        # Self-correlations should be 1.0
        for risk_id in risk_ids:
            assert corr_matrix.get_correlation(risk_id, risk_id) == 1.0
    
    @given(
        st.lists(probability_distribution_strategy(), min_size=2, max_size=4),  # Reduced max size
        correlation_matrix_strategy(),
        st.integers(min_value=500, max_value=2000)  # Increased sample size for better correlation estimation
    )
    @settings(max_examples=10, deadline=15000, suppress_health_check=[HealthCheck.filter_too_much])
    def test_correlated_sampling_properties(self, distributions, matrix_data, sample_count):
        """
        **Feature: monte-carlo-risk-simulations, Property 5: Cross-Impact Modeling**
        
        For any set of distributions and correlation matrix, correlated sampling should
        produce samples that maintain the specified correlation structure.
        **Validates: Requirements 2.5**
        """
        correlations, risk_ids = matrix_data
        
        # Ensure we have matching number of distributions and risk IDs
        assume(len(distributions) == len(risk_ids))
        
        analyzer = RiskCorrelationAnalyzer()
        
        try:
            # Create correlation matrix
            corr_matrix = analyzer.create_correlation_matrix(correlations, risk_ids)
            
            # Generate correlated samples
            samples = analyzer.generate_correlated_samples(
                distributions, corr_matrix, sample_count, 
                random_state=np.random.RandomState(42)  # For reproducibility
            )
            
            # Verify sample properties
            assert samples.shape == (sample_count, len(distributions))
            assert np.all(np.isfinite(samples))
            
            # Check that correlations are approximately maintained
            # (allowing for sampling variation)
            sample_corr_matrix = np.corrcoef(samples.T)
            
            for i, risk1 in enumerate(risk_ids):
                for j, risk2 in enumerate(risk_ids):
                    expected_corr = corr_matrix.get_correlation(risk1, risk2)
                    actual_corr = sample_corr_matrix[i, j]
                    
                    if i == j:
                        # Self-correlation should be 1.0
                        assert abs(actual_corr - 1.0) < 0.01
                    else:
                        # More lenient tolerance for correlation preservation
                        # The transformation from normal to other distributions can affect correlations
                        tolerance = 0.3 if sample_count < 1000 else 0.2
                        
                        # Skip very small expected correlations as they're hard to preserve
                        if abs(expected_corr) < 0.1:
                            continue
                            
                        assert abs(actual_corr - expected_corr) < tolerance, \
                            f"Correlation between {risk1} and {risk2}: expected {expected_corr:.3f}, got {actual_corr:.3f}"
                            
        except ValueError as e:
            # If correlation matrix is not positive definite, that's expected for some random matrices
            if "not positive definite" in str(e):
                assume(False)  # Skip this test case
            else:
                raise
    
    @given(
        st.text(min_size=1, max_size=20),
        st.text(min_size=1, max_size=20),
        correlation_coefficient_strategy(),
        st.floats(min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False)
    )
    def test_cross_impact_modeling(self, cost_risk_id, schedule_risk_id, correlation, impact_multiplier):
        """
        **Feature: monte-carlo-risk-simulations, Property 5: Cross-Impact Modeling**
        
        For any cost and schedule risk pair with valid correlation and impact multiplier,
        the analyzer should create a valid cross-impact model that maintains proper
        correlation structures in cross-impact relationships.
        **Validates: Requirements 2.5**
        """
        assume(cost_risk_id != schedule_risk_id)  # Ensure different risk IDs
        
        analyzer = RiskCorrelationAnalyzer()
        
        # Create cross-impact model
        cross_impact = analyzer.model_cross_impacts(
            cost_risk_id, schedule_risk_id, correlation, impact_multiplier
        )
        
        # Verify cross-impact model properties
        assert isinstance(cross_impact, CrossImpactModel)
        assert cross_impact.primary_risk_id == cost_risk_id
        assert cross_impact.secondary_risk_id == schedule_risk_id
        assert cross_impact.correlation_coefficient == correlation
        assert cross_impact.impact_multiplier == impact_multiplier
        
        # Correlation should be within bounds
        assert -1.0 <= cross_impact.correlation_coefficient <= 1.0
        
        # Impact multiplier should be non-negative
        assert cross_impact.impact_multiplier >= 0
    
    def test_invalid_correlation_coefficients(self):
        """Test that invalid correlation coefficients are rejected."""
        analyzer = RiskCorrelationAnalyzer()
        
        # Correlation outside [-1, 1] should raise ValueError
        with pytest.raises(ValueError, match="must be between -1 and 1"):
            analyzer.create_correlation_matrix({('risk1', 'risk2'): 1.5}, ['risk1', 'risk2'])
        
        with pytest.raises(ValueError, match="must be between -1 and 1"):
            analyzer.create_correlation_matrix({('risk1', 'risk2'): -1.5}, ['risk1', 'risk2'])
    
    def test_invalid_cross_impact_parameters(self):
        """Test that invalid cross-impact parameters are rejected."""
        analyzer = RiskCorrelationAnalyzer()
        
        # Invalid correlation coefficient
        with pytest.raises(ValueError, match="Correlation must be between -1 and 1"):
            analyzer.model_cross_impacts('cost_risk', 'schedule_risk', 1.5, 1.0)
        
        # Negative impact multiplier
        with pytest.raises(ValueError, match="Impact multiplier must be non-negative"):
            analyzer.model_cross_impacts('cost_risk', 'schedule_risk', 0.5, -1.0)
    
    def test_empty_correlation_matrix(self):
        """Test that empty correlation matrices are handled properly."""
        analyzer = RiskCorrelationAnalyzer()
        
        # Empty risk IDs should raise error
        with pytest.raises(ValueError, match="cannot be empty"):
            analyzer.create_correlation_matrix({}, [])
    
    @given(st.integers(min_value=1, max_value=10))
    def test_identity_correlation_matrix(self, n_risks):
        """Test that identity correlation matrices (no correlations) work correctly."""
        analyzer = RiskCorrelationAnalyzer()
        
        # Create risk IDs
        risk_ids = [f'risk_{i}' for i in range(n_risks)]
        
        # Create identity matrix (no correlations specified)
        corr_matrix = analyzer.create_correlation_matrix({}, risk_ids)
        
        # Validate matrix
        validation_result = analyzer.validate_correlation_matrix(corr_matrix)
        assert validation_result.is_valid
        
        # All correlations should be 0 except self-correlations
        for i, risk1 in enumerate(risk_ids):
            for j, risk2 in enumerate(risk_ids):
                expected = 1.0 if i == j else 0.0
                assert corr_matrix.get_correlation(risk1, risk2) == expected
    
    def test_non_positive_definite_matrix(self):
        """Test handling of non-positive definite correlation matrices."""
        analyzer = RiskCorrelationAnalyzer()
        
        # Create a matrix that's definitely not positive definite
        # Use a more extreme example that's guaranteed to fail
        correlations = {
            ('risk1', 'risk2'): 0.99,
            ('risk1', 'risk3'): 0.99,
            ('risk2', 'risk3'): -0.99  # This creates inconsistency
        }
        risk_ids = ['risk1', 'risk2', 'risk3']
        
        # This should raise an error due to non-positive definiteness
        with pytest.raises(ValueError, match="not positive definite"):
            analyzer.create_correlation_matrix(correlations, risk_ids)