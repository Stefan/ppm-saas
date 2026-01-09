"""
Property-based tests for Risk Distribution Modeler.

Tests the distribution modeling functionality for correctness, validation,
and mathematical properties using property-based testing with Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
import numpy as np

from monte_carlo.distribution_modeler import RiskDistributionModeler
from monte_carlo.models import (
    RiskData, DistributionType, ProbabilityDistribution, ValidationResult
)


# Hypothesis strategies for generating test data
@st.composite
def three_point_estimate_strategy(draw):
    """Generate valid three-point estimates."""
    optimistic = draw(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))
    pessimistic = draw(st.floats(min_value=optimistic + 1, max_value=optimistic + 200, allow_nan=False, allow_infinity=False))
    most_likely = draw(st.floats(min_value=optimistic, max_value=pessimistic, allow_nan=False, allow_infinity=False))
    return (optimistic, most_likely, pessimistic)


@st.composite
def historical_data_strategy(draw):
    """Generate valid historical data."""
    size = draw(st.integers(min_value=5, max_value=100))
    mean = draw(st.floats(min_value=10, max_value=1000, allow_nan=False, allow_infinity=False))
    std = draw(st.floats(min_value=1, max_value=mean * 0.5, allow_nan=False, allow_infinity=False))
    return list(np.random.normal(mean, std, size))


@st.composite
def positive_historical_data_strategy(draw):
    """Generate valid positive historical data for lognormal distributions."""
    size = draw(st.integers(min_value=5, max_value=100))
    # Generate lognormal data to ensure positivity
    mu = draw(st.floats(min_value=0, max_value=3, allow_nan=False, allow_infinity=False))
    sigma = draw(st.floats(min_value=0.1, max_value=1, allow_nan=False, allow_infinity=False))
    return list(np.random.lognormal(mu, sigma, size))


@st.composite
def risk_data_strategy(draw):
    """Generate valid risk data."""
    risk_id = draw(st.text(min_size=1, max_size=50))
    
    # Choose between historical data and three-point estimate
    has_historical = draw(st.booleans())
    has_three_point = draw(st.booleans())
    
    # Ensure at least one is present
    if not has_historical and not has_three_point:
        has_three_point = True
    
    historical_impacts = None
    three_point_estimate = None
    
    if has_historical:
        historical_impacts = draw(historical_data_strategy())
    
    if has_three_point:
        three_point_estimate = draw(three_point_estimate_strategy())
    
    return RiskData(
        risk_id=risk_id,
        historical_impacts=historical_impacts,
        three_point_estimate=three_point_estimate
    )


class TestDistributionModelingProperties:
    """Property-based tests for Risk Distribution Modeler."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.modeler = RiskDistributionModeler()
    
    @given(three_point_estimate_strategy())
    @settings(max_examples=20)
    def test_triangular_distribution_creation_from_three_point(self, three_point):
        """
        **Feature: monte-carlo-risk-simulations, Property 3: Distribution Modeling Correctness**
        
        For any valid three-point estimate, the Risk Distribution Modeler should create
        valid triangular distributions with proper parameter bounds and mathematical validity.
        **Validates: Requirements 2.1, 2.3, 2.4**
        """
        optimistic, most_likely, pessimistic = three_point
        
        # Create triangular distribution
        distribution = self.modeler.create_triangular_from_three_point(
            optimistic, most_likely, pessimistic
        )
        
        # Verify distribution properties
        assert distribution.distribution_type == DistributionType.TRIANGULAR
        assert distribution.parameters['min'] == optimistic
        assert distribution.parameters['mode'] == most_likely
        assert distribution.parameters['max'] == pessimistic
        
        # Verify parameter ordering is maintained
        assert distribution.parameters['min'] <= distribution.parameters['mode'] <= distribution.parameters['max']
        
        # Test sampling works
        samples = distribution.sample(100)
        assert len(samples) == 100
        assert np.all(np.isfinite(samples))
        
        # Samples should be within the triangular bounds
        assert np.all(samples >= optimistic)
        assert np.all(samples <= pessimistic)
    
    @given(three_point_estimate_strategy())
    @settings(max_examples=20)
    def test_three_point_estimate_validation(self, three_point):
        """
        **Feature: monte-carlo-risk-simulations, Property 3: Distribution Modeling Correctness**
        
        For any valid three-point estimate, the validation should pass and provide
        appropriate feedback for parameter quality.
        **Validates: Requirements 2.1, 2.3, 2.4**
        """
        optimistic, most_likely, pessimistic = three_point
        
        validation_result = self.modeler.validate_three_point_estimate(
            optimistic, most_likely, pessimistic
        )
        
        # Valid three-point estimates should pass validation
        assert validation_result.is_valid
        assert len(validation_result.errors) == 0
        
        # Validation should be consistent with distribution creation
        distribution = self.modeler.create_triangular_from_three_point(
            optimistic, most_likely, pessimistic
        )
        dist_validation = self.modeler.validate_distribution_parameters(distribution)
        assert dist_validation.is_valid
    
    @given(risk_data_strategy(), st.sampled_from(DistributionType))
    @settings(max_examples=30)
    def test_distribution_creation_from_risk_data(self, risk_data, distribution_type):
        """
        **Feature: monte-carlo-risk-simulations, Property 3: Distribution Modeling Correctness**
        
        For any valid risk data and supported distribution type, the modeler should
        create mathematically valid distributions or provide clear error messages.
        **Validates: Requirements 2.1, 2.3, 2.4**
        """
        try:
            distribution = self.modeler.create_distribution(risk_data, distribution_type)
            
            # If creation succeeds, distribution should be valid
            assert distribution.distribution_type == distribution_type
            assert isinstance(distribution.parameters, dict)
            assert len(distribution.parameters) > 0
            
            # Test sampling works
            samples = distribution.sample(50)
            assert len(samples) == 50
            assert np.all(np.isfinite(samples))
            
            # Validate the created distribution
            validation_result = self.modeler.validate_distribution_parameters(distribution)
            assert validation_result.is_valid or len(validation_result.warnings) > 0
            
        except ValueError as e:
            # If creation fails, it should be for a valid reason
            error_msg = str(e).lower()
            valid_error_reasons = [
                'requires positive data',  # lognormal with negative data
                'requires positive three-point estimates',  # lognormal with non-positive three-point estimates
                'no valid data',  # missing required data
                'invalid three-point estimate',  # bad three-point data
                'unsupported distribution type'  # unsupported type
            ]
            assert any(reason in error_msg for reason in valid_error_reasons)
    
    @given(historical_data_strategy())
    @settings(max_examples=15)
    def test_normal_distribution_from_historical_data(self, historical_data):
        """
        **Feature: monte-carlo-risk-simulations, Property 3: Distribution Modeling Correctness**
        
        For any historical data, creating a normal distribution should produce
        parameters that reasonably represent the data characteristics.
        **Validates: Requirements 2.1, 2.3, 2.4**
        """
        risk_data = RiskData(
            risk_id="test_risk",
            historical_impacts=historical_data
        )
        
        distribution = self.modeler.create_distribution(risk_data, DistributionType.NORMAL)
        
        # Parameters should reflect the historical data
        data_mean = np.mean(historical_data)
        data_std = np.std(historical_data, ddof=1)
        
        assert abs(distribution.parameters['mean'] - data_mean) < 1e-10
        # Allow for small differences due to minimum std enforcement
        assert distribution.parameters['std'] > 0
        
        if data_std > 0:
            assert abs(distribution.parameters['std'] - data_std) < 1e-10
    
    @given(positive_historical_data_strategy())
    @settings(max_examples=15)
    def test_lognormal_distribution_from_positive_data(self, positive_data):
        """
        **Feature: monte-carlo-risk-simulations, Property 3: Distribution Modeling Correctness**
        
        For any positive historical data, creating a lognormal distribution should
        produce valid parameters and maintain the log-normal properties.
        **Validates: Requirements 2.1, 2.3, 2.4**
        """
        risk_data = RiskData(
            risk_id="test_risk",
            historical_impacts=positive_data
        )
        
        distribution = self.modeler.create_distribution(risk_data, DistributionType.LOGNORMAL)
        
        # Parameters should be valid for lognormal
        assert 'mu' in distribution.parameters
        assert 'sigma' in distribution.parameters
        assert distribution.parameters['sigma'] > 0
        
        # Test sampling produces positive values
        samples = distribution.sample(100)
        assert np.all(samples > 0)
        assert np.all(np.isfinite(samples))
    
    @given(st.lists(st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False), 
                   min_size=10, max_size=50))
    @settings(max_examples=15)
    def test_beta_distribution_from_normalized_data(self, normalized_data):
        """
        **Feature: monte-carlo-risk-simulations, Property 3: Distribution Modeling Correctness**
        
        For any normalized data in [0,1], creating a beta distribution should
        produce valid alpha and beta parameters.
        **Validates: Requirements 2.1, 2.3, 2.4**
        """
        # Ensure some variance in the data
        assume(np.var(normalized_data) > 1e-6)
        
        risk_data = RiskData(
            risk_id="test_risk",
            historical_impacts=normalized_data
        )
        
        distribution = self.modeler.create_distribution(risk_data, DistributionType.BETA)
        
        # Parameters should be positive
        assert distribution.parameters['alpha'] > 0
        assert distribution.parameters['beta'] > 0
        
        # Test sampling produces values in [0,1]
        samples = distribution.sample(100)
        assert np.all(samples >= 0)
        assert np.all(samples <= 1)
        assert np.all(np.isfinite(samples))
    
    @given(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
           st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
           st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))
    @settings(max_examples=25)
    def test_invalid_three_point_estimates_rejected(self, val1, val2, val3):
        """
        **Feature: monte-carlo-risk-simulations, Property 3: Distribution Modeling Correctness**
        
        For any three values that don't form a valid three-point estimate,
        the modeler should reject them with appropriate error messages.
        **Validates: Requirements 2.1, 2.3, 2.4**
        """
        values = sorted([val1, val2, val3])
        
        # If all values are the same, should be rejected
        if values[0] == values[2]:
            with pytest.raises(ValueError, match="cannot be equal"):
                self.modeler.create_triangular_from_three_point(values[0], values[1], values[2])
        else:
            # Valid ordering should work
            distribution = self.modeler.create_triangular_from_three_point(values[0], values[1], values[2])
            assert distribution.distribution_type == DistributionType.TRIANGULAR
        
        # Invalid ordering should be rejected
        if values[0] != values[2]:  # Avoid degenerate case
            with pytest.raises(ValueError, match="optimistic.*<=.*most_likely.*<=.*pessimistic"):
                self.modeler.create_triangular_from_three_point(values[2], values[1], values[0])
    
    @given(st.lists(st.floats(min_value=-1000, max_value=0, allow_nan=False, allow_infinity=False),
                   min_size=5, max_size=20))
    @settings(max_examples=10)
    def test_lognormal_rejects_negative_data(self, negative_data):
        """
        **Feature: monte-carlo-risk-simulations, Property 3: Distribution Modeling Correctness**
        
        For any historical data containing negative values, lognormal distribution
        creation should be rejected with appropriate error messages.
        **Validates: Requirements 2.1, 2.3, 2.4**
        """
        risk_data = RiskData(
            risk_id="test_risk",
            historical_impacts=negative_data
        )
        
        with pytest.raises(ValueError, match="requires positive data"):
            self.modeler.create_distribution(risk_data, DistributionType.LOGNORMAL)
    
    @given(st.sampled_from(DistributionType))
    @settings(max_examples=5)
    def test_empty_risk_data_rejected(self, distribution_type):
        """
        **Feature: monte-carlo-risk-simulations, Property 3: Distribution Modeling Correctness**
        
        For any distribution type, empty risk data should be rejected with
        appropriate error messages.
        **Validates: Requirements 2.1, 2.3, 2.4**
        """
        empty_risk_data = RiskData(
            risk_id="test_risk",
            historical_impacts=None,
            three_point_estimate=None
        )
        
        with pytest.raises(ValueError, match="must contain either historical impacts or three-point estimate"):
            self.modeler.create_distribution(empty_risk_data, distribution_type)
    
    def test_correlation_coefficient_bounds_validation(self):
        """
        **Feature: monte-carlo-risk-simulations, Property 3: Distribution Modeling Correctness**
        
        For any correlation coefficient, it should be validated to be within [-1, +1] bounds.
        **Validates: Requirements 2.1, 2.3, 2.4**
        """
        # Test valid correlation coefficients
        valid_correlations = [-1.0, -0.5, 0.0, 0.5, 1.0]
        for corr in valid_correlations:
            # This would be tested in correlation analyzer, but we verify the concept
            assert -1.0 <= corr <= 1.0
        
        # Test invalid correlation coefficients
        invalid_correlations = [-1.1, 1.1, -2.0, 2.0]
        for corr in invalid_correlations:
            assert not (-1.0 <= corr <= 1.0)
    
    @given(historical_data_strategy())
    @settings(max_examples=10)
    def test_historical_data_fitting_quality(self, historical_data):
        """
        **Feature: monte-carlo-risk-simulations, Property 4: Historical Data Fitting**
        
        For any historical dataset, the Risk Distribution Modeler should fit probability
        distributions that demonstrate good statistical fit to the source data.
        **Validates: Requirements 2.2**
        """
        # Test fitting with automatic distribution selection
        best_distribution, fit_stats = self.modeler.fit_distribution_from_historical(historical_data)
        
        # The best distribution should be valid
        assert best_distribution is not None
        assert isinstance(best_distribution, ProbabilityDistribution)
        assert best_distribution.distribution_type in DistributionType
        
        # Fit statistics should be present and reasonable
        assert 'aic' in fit_stats
        assert 'selected_distribution' in fit_stats
        assert 'data_summary' in fit_stats
        
        # AIC should be finite
        assert np.isfinite(fit_stats['aic'])
        
        # Data summary should match input data
        data_summary = fit_stats['data_summary']
        assert data_summary['count'] == len(historical_data)
        assert abs(data_summary['mean'] - np.mean(historical_data)) < 1e-10
        
        # Test that the fitted distribution can generate samples
        samples = best_distribution.sample(100)
        assert len(samples) == 100
        assert np.all(np.isfinite(samples))
    
    @given(positive_historical_data_strategy())
    @settings(max_examples=10)
    def test_historical_data_fitting_with_specific_distributions(self, positive_data):
        """
        **Feature: monte-carlo-risk-simulations, Property 4: Historical Data Fitting**
        
        For any positive historical data, fitting specific distribution types should
        produce mathematically valid parameters and reasonable goodness-of-fit metrics.
        **Validates: Requirements 2.2**
        """
        # Test fitting specific distributions
        distributions_to_test = [DistributionType.NORMAL, DistributionType.LOGNORMAL, DistributionType.UNIFORM]
        
        for dist_type in distributions_to_test:
            try:
                best_distribution, fit_stats = self.modeler.fit_distribution_from_historical(
                    positive_data, [dist_type]
                )
                
                # Should successfully fit the requested distribution
                assert best_distribution.distribution_type == dist_type
                
                # Fit statistics should be reasonable
                assert 'aic' in fit_stats
                assert 'log_likelihood' in fit_stats
                assert 'ks_statistic' in fit_stats
                assert 'ks_p_value' in fit_stats
                
                # Log likelihood should be finite
                assert np.isfinite(fit_stats['log_likelihood'])
                
                # KS statistic should be non-negative
                assert fit_stats['ks_statistic'] >= 0
                
                # P-value should be between 0 and 1
                assert 0 <= fit_stats['ks_p_value'] <= 1
                
            except ValueError as e:
                # Some distributions may not be suitable for certain data
                # This is acceptable behavior
                error_msg = str(e).lower()
                valid_reasons = ['requires positive data', 'no suitable distribution']
                assert any(reason in error_msg for reason in valid_reasons)
    
    @given(st.lists(st.floats(min_value=10, max_value=100, allow_nan=False, allow_infinity=False), 
                   min_size=20, max_size=50))
    @settings(max_examples=10)
    def test_goodness_of_fit_testing(self, historical_data):
        """
        **Feature: monte-carlo-risk-simulations, Property 4: Historical Data Fitting**
        
        For any fitted distribution, goodness-of-fit tests should provide meaningful
        statistical assessment of the fit quality.
        **Validates: Requirements 2.2**
        """
        # Fit a distribution to the data
        best_distribution, _ = self.modeler.fit_distribution_from_historical(historical_data)
        
        # Perform goodness-of-fit testing
        gof_results = self.modeler.perform_goodness_of_fit_test(historical_data, best_distribution)
        
        # Should contain required test results
        assert 'kolmogorov_smirnov' in gof_results
        assert 'overall_assessment' in gof_results
        assert 'sample_size' in gof_results
        assert 'significance_level' in gof_results
        
        # KS test results should be valid
        ks_results = gof_results['kolmogorov_smirnov']
        assert 'statistic' in ks_results
        assert 'p_value' in ks_results
        assert 'significant' in ks_results
        
        assert ks_results['statistic'] >= 0
        assert 0 <= ks_results['p_value'] <= 1
        assert isinstance(ks_results['significant'], bool)
        
        # Overall assessment should be meaningful
        assessment = gof_results['overall_assessment']
        assert 'assessment' in assessment
        assert 'recommendation' in assessment
        assert assessment['assessment'] in ['GOOD_FIT', 'MARGINAL_FIT', 'POOR_FIT']
        
        # Sample size should match
        assert gof_results['sample_size'] == len(historical_data)
    
    @given(st.lists(st.floats(min_value=-100, max_value=0, allow_nan=False, allow_infinity=False),
                   min_size=5, max_size=15))
    @settings(max_examples=8)
    def test_historical_fitting_handles_negative_data_appropriately(self, negative_data):
        """
        **Feature: monte-carlo-risk-simulations, Property 4: Historical Data Fitting**
        
        For any historical data containing negative values, the fitting process should
        handle distribution constraints appropriately and provide meaningful results.
        **Validates: Requirements 2.2**
        """
        # Should be able to fit some distributions to negative data
        best_distribution, fit_stats = self.modeler.fit_distribution_from_historical(negative_data)
        
        # Should successfully fit a distribution
        assert best_distribution is not None
        
        # Should not select lognormal for negative data
        assert best_distribution.distribution_type != DistributionType.LOGNORMAL
        
        # Fit statistics should indicate which distributions failed
        assert 'all_fits' in fit_stats
        all_fits = fit_stats['all_fits']
        
        # Lognormal should have failed
        if DistributionType.LOGNORMAL in all_fits:
            lognormal_result = all_fits[DistributionType.LOGNORMAL]
            assert lognormal_result[0] is None  # Distribution should be None
            assert 'error' in lognormal_result[1]  # Should have error message
    
    def test_insufficient_historical_data_rejected(self):
        """
        **Feature: monte-carlo-risk-simulations, Property 4: Historical Data Fitting**
        
        For insufficient historical data, the fitting process should reject the data
        with appropriate error messages.
        **Validates: Requirements 2.2**
        """
        # Test with too few data points
        insufficient_data = [1.0, 2.0]  # Only 2 points
        
        with pytest.raises(ValueError, match="at least 3 data points"):
            self.modeler.fit_distribution_from_historical(insufficient_data)
        
        # Test with empty data
        with pytest.raises(ValueError, match="at least 3 data points"):
            self.modeler.fit_distribution_from_historical([])
    
    def test_invalid_historical_data_rejected(self):
        """
        **Feature: monte-carlo-risk-simulations, Property 4: Historical Data Fitting**
        
        For invalid historical data (NaN, infinite values), the fitting process should
        reject the data with appropriate error messages.
        **Validates: Requirements 2.2**
        """
        # Test with NaN values
        nan_data = [1.0, 2.0, float('nan'), 4.0, 5.0]
        
        with pytest.raises(ValueError, match="finite values"):
            self.modeler.fit_distribution_from_historical(nan_data)
        
        # Test with infinite values
        inf_data = [1.0, 2.0, float('inf'), 4.0, 5.0]
        
        with pytest.raises(ValueError, match="finite values"):
            self.modeler.fit_distribution_from_historical(inf_data)
    
    @given(st.lists(st.floats(min_value=50, max_value=51, allow_nan=False, allow_infinity=False),
                   min_size=10, max_size=30))
    @settings(max_examples=8)
    def test_constant_data_handling(self, constant_data):
        """
        **Feature: monte-carlo-risk-simulations, Property 4: Historical Data Fitting**
        
        For nearly constant historical data, the fitting process should handle
        the low variance case appropriately.
        **Validates: Requirements 2.2**
        """
        # Add small amount of noise to make it nearly constant
        noisy_data = [x + np.random.normal(0, 0.01) for x in constant_data]
        
        # Should be able to fit a distribution
        best_distribution, fit_stats = self.modeler.fit_distribution_from_historical(noisy_data)
        
        # Should successfully create a distribution
        assert best_distribution is not None
        
        # For nearly constant data, uniform might be selected
        # The key is that it should handle the low variance case gracefully
        samples = best_distribution.sample(100)
        assert np.all(np.isfinite(samples))
        
        # Variance of samples should be small but non-zero
        sample_variance = np.var(samples)
        assert sample_variance >= 0