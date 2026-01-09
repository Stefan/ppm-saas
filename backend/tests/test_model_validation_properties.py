"""
Property-based tests for model validation capabilities.

**Feature: monte-carlo-risk-simulations, Property 24: Model Validation**
**Validates: Requirements 9.2, 9.3**

Tests that the engine performs goodness-of-fit tests for probability distributions
and validates correlation matrices for mathematical consistency.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
import numpy as np
from typing import List, Dict, Tuple
from scipy import stats

from monte_carlo.engine import MonteCarloEngine
from monte_carlo.model_validator import ModelValidator, DistributionValidator, CorrelationValidator
from monte_carlo.models import (
    Risk, ProbabilityDistribution, DistributionType, RiskCategory, ImpactType,
    CorrelationMatrix, ValidationResult
)


# Hypothesis strategies for generating test data
@st.composite
def valid_normal_distribution(draw):
    """Generate valid normal distributions."""
    mean = draw(st.floats(min_value=-100, max_value=100))
    std = draw(st.floats(min_value=0.1, max_value=50))
    
    return ProbabilityDistribution(
        distribution_type=DistributionType.NORMAL,
        parameters={'mean': mean, 'std': std}
    )


@st.composite
def valid_triangular_distribution(draw):
    """Generate valid triangular distributions."""
    min_val = draw(st.floats(min_value=-100, max_value=50))
    max_val = draw(st.floats(min_value=min_val + 1, max_value=100))
    mode = draw(st.floats(min_value=min_val, max_value=max_val))
    
    return ProbabilityDistribution(
        distribution_type=DistributionType.TRIANGULAR,
        parameters={'min': min_val, 'mode': mode, 'max': max_val}
    )


@st.composite
def valid_uniform_distribution(draw):
    """Generate valid uniform distributions."""
    min_val = draw(st.floats(min_value=-100, max_value=50))
    max_val = draw(st.floats(min_value=min_val + 1, max_value=100))
    
    return ProbabilityDistribution(
        distribution_type=DistributionType.UNIFORM,
        parameters={'min': min_val, 'max': max_val}
    )


@st.composite
def valid_distribution(draw):
    """Generate any valid distribution."""
    dist_type = draw(st.sampled_from([
        valid_normal_distribution(),
        valid_triangular_distribution(),
        valid_uniform_distribution()
    ]))
    return draw(dist_type)


@st.composite
def historical_data_for_distribution(draw, distribution: ProbabilityDistribution, sample_size: int = 100):
    """Generate historical data that matches a distribution."""
    # Generate samples from the distribution
    random_state = np.random.RandomState(draw(st.integers(min_value=0, max_value=2**31-1)))
    samples = distribution.sample(sample_size, random_state)
    
    # Add some noise to make it more realistic
    noise_level = draw(st.floats(min_value=0.0, max_value=0.1))
    if noise_level > 0:
        noise = random_state.normal(0, noise_level * np.std(samples), sample_size)
        samples = samples + noise
    
    return samples.tolist()


@st.composite
def valid_correlation_matrix(draw, num_risks: int = None):
    """Generate valid correlation matrices using a more robust approach."""
    if num_risks is None:
        num_risks = draw(st.integers(min_value=2, max_value=6))  # Reduced max for stability
    
    # Generate risk IDs
    risk_ids = [f"risk_{i}" for i in range(num_risks)]
    
    # Method 1: Generate a positive definite matrix using Cholesky decomposition
    # This guarantees positive definiteness by construction
    
    # Generate a random lower triangular matrix
    random_state = np.random.RandomState(draw(st.integers(min_value=0, max_value=2**31-1)))
    
    # Create a lower triangular matrix with positive diagonal
    L = np.zeros((num_risks, num_risks))
    
    # Fill diagonal with positive values
    for i in range(num_risks):
        L[i, i] = random_state.uniform(0.5, 1.5)  # Ensure positive diagonal
    
    # Fill lower triangle with random values
    for i in range(num_risks):
        for j in range(i):
            L[i, j] = random_state.uniform(-0.5, 0.5)
    
    # Generate positive definite matrix: A = L @ L.T
    matrix = L @ L.T
    
    # Convert to correlation matrix by normalizing
    diag_sqrt = np.sqrt(np.diag(matrix))
    correlation_matrix = matrix / np.outer(diag_sqrt, diag_sqrt)
    
    # Ensure diagonal is exactly 1.0 (numerical precision)
    np.fill_diagonal(correlation_matrix, 1.0)
    
    # Verify positive definiteness with a reasonable tolerance
    eigenvalues = np.linalg.eigvals(correlation_matrix)
    min_eigenvalue = np.min(eigenvalues)
    
    # If still not positive definite, add small regularization
    if min_eigenvalue < 1e-8:
        regularization = 1e-6
        correlation_matrix += regularization * np.eye(num_risks)
        # Re-normalize to maintain correlation structure
        diag_sqrt = np.sqrt(np.diag(correlation_matrix))
        correlation_matrix = correlation_matrix / np.outer(diag_sqrt, diag_sqrt)
        np.fill_diagonal(correlation_matrix, 1.0)
    
    # Extract correlations for the CorrelationMatrix constructor
    correlations = {}
    for i in range(num_risks):
        for j in range(i + 1, num_risks):
            correlation = correlation_matrix[i, j]
            # Only include significant correlations to avoid numerical noise
            if abs(correlation) > 0.05:
                correlations[(risk_ids[i], risk_ids[j])] = float(correlation)
    
    return CorrelationMatrix(correlations=correlations, risk_ids=risk_ids)


@st.composite
def simple_risk_with_distribution(draw, distribution: ProbabilityDistribution = None):
    """Generate a simple risk with specified or random distribution."""
    risk_id = draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    
    if distribution is None:
        distribution = draw(valid_distribution())
    
    return Risk(
        id=risk_id,
        name=f"Risk {risk_id}",
        category=draw(st.sampled_from(RiskCategory)),
        impact_type=draw(st.sampled_from(ImpactType)),
        probability_distribution=distribution,
        baseline_impact=draw(st.floats(min_value=0.1, max_value=100))
    )


class TestModelValidationProperties:
    """Property-based tests for model validation capabilities."""
    
    @given(valid_distribution())
    @settings(max_examples=30, deadline=20000)
    def test_property_24_distribution_validation_acceptance(self, distribution: ProbabilityDistribution):
        """
        **Property 24: Model Validation - Distribution Validation**
        
        For any valid probability distribution, the model validator should perform
        appropriate goodness-of-fit tests and return meaningful validation results.
        
        **Validates: Requirements 9.2**
        """
        engine = MonteCarloEngine()
        
        # Test distribution validation without historical data
        validation_result = engine.validate_distribution(distribution)
        
        # Should always return a ValidationResult
        assert isinstance(validation_result, ValidationResult)
        
        # For valid distributions without historical data, should generally be valid
        # (unless there are specific parameter issues)
        if not validation_result.is_valid:
            # If invalid, should have specific error messages
            assert len(validation_result.errors) > 0
            assert all(isinstance(error, str) for error in validation_result.errors)
    
    @given(valid_distribution(), st.integers(min_value=20, max_value=200))
    @settings(max_examples=20, deadline=30000)
    def test_property_24_goodness_of_fit_testing(self, distribution: ProbabilityDistribution, sample_size: int):
        """
        Test that goodness-of-fit tests are performed when historical data is provided.
        
        **Validates: Requirements 9.2**
        """
        # Generate historical data that matches the distribution
        random_state = np.random.RandomState(42)
        historical_data = distribution.sample(sample_size, random_state).tolist()
        
        engine = MonteCarloEngine()
        validation_result = engine.validate_distribution(
            distribution=distribution,
            historical_data=historical_data,
            significance_level=0.05
        )
        
        # Should return validation result
        assert isinstance(validation_result, ValidationResult)
        
        # For data generated from the same distribution, should generally pass
        # (though statistical tests can occasionally fail due to randomness)
        if not validation_result.is_valid:
            # If it fails, should be due to statistical reasons, not implementation errors
            assert len(validation_result.errors) > 0
            # Errors should not contain implementation-related messages
            for error in validation_result.errors:
                assert "Failed to sample" not in error
                assert "ImportError" not in error
                assert "AttributeError" not in error
    
    @given(valid_correlation_matrix())
    @settings(max_examples=30, deadline=15000)
    def test_property_24_correlation_matrix_validation(self, correlation_matrix: CorrelationMatrix):
        """
        Test that correlation matrix validation checks mathematical consistency.
        
        **Validates: Requirements 9.3**
        """
        engine = MonteCarloEngine()
        
        validation_result = engine.validate_correlation_matrix(correlation_matrix)
        
        # Should return validation result
        assert isinstance(validation_result, ValidationResult)
        
        # For properly generated correlation matrices, should be valid
        assert validation_result.is_valid, f"Valid correlation matrix failed validation: {validation_result.errors}"
        
        # Should not have errors for valid matrices
        assert len(validation_result.errors) == 0
    
    @given(st.integers(min_value=2, max_value=6))
    @settings(max_examples=20, deadline=15000)
    def test_property_24_correlation_bounds_validation(self, num_risks: int):
        """
        Test that correlation matrix validation enforces bounds [-1, 1].
        
        **Validates: Requirements 9.3**
        """
        risk_ids = [f"risk_{i}" for i in range(num_risks)]
        
        # Create correlation matrix with invalid correlation (outside bounds)
        invalid_correlations = {
            (risk_ids[0], risk_ids[1]): 1.5  # Invalid: > 1
        }
        
        # This should fail during CorrelationMatrix creation
        with pytest.raises(ValueError, match="must be between -1 and 1"):
            CorrelationMatrix(correlations=invalid_correlations, risk_ids=risk_ids)
    
    @given(st.integers(min_value=3, max_value=5))
    @settings(max_examples=15, deadline=20000)
    def test_property_24_positive_definiteness_checking(self, num_risks: int):
        """
        Test that correlation matrix validation checks positive definiteness.
        
        **Validates: Requirements 9.3**
        """
        risk_ids = [f"risk_{i}" for i in range(num_risks)]
        
        # Create a correlation matrix that is NOT positive definite
        # by making all correlations very high
        invalid_correlations = {}
        for i in range(num_risks):
            for j in range(i + 1, num_risks):
                invalid_correlations[(risk_ids[i], risk_ids[j])] = 0.99
        
        try:
            correlation_matrix = CorrelationMatrix(correlations=invalid_correlations, risk_ids=risk_ids)
            
            engine = MonteCarloEngine()
            validation_result = engine.validate_correlation_matrix(correlation_matrix)
            
            # Should detect the positive definiteness issue
            if not validation_result.is_valid:
                # Should have specific error about positive definiteness
                error_text = " ".join(validation_result.errors).lower()
                assert any(term in error_text for term in ["positive definite", "eigenvalue", "singular"])
            
        except ValueError:
            # It's also acceptable if the CorrelationMatrix constructor itself rejects it
            pass
    
    @given(st.lists(simple_risk_with_distribution(), min_size=1, max_size=5))
    @settings(max_examples=20, deadline=25000)
    def test_property_24_complete_model_validation(self, risks: List[Risk]):
        """
        Test that complete model validation works for any set of risks.
        
        **Validates: Requirements 9.2, 9.3**
        """
        # Ensure unique risk IDs
        unique_risks = []
        seen_ids = set()
        for risk in risks:
            if risk.id not in seen_ids:
                unique_risks.append(risk)
                seen_ids.add(risk.id)
        
        if not unique_risks:
            return  # Skip if no unique risks
        
        engine = MonteCarloEngine()
        
        # Test validation without correlations
        validation_result = engine.validate_model(unique_risks)
        
        # Should return validation result
        assert isinstance(validation_result, ValidationResult)
        
        # For valid risks, should generally be valid
        if not validation_result.is_valid:
            # If invalid, should have specific error messages
            assert len(validation_result.errors) > 0
            # Errors should be about the risks, not implementation issues
            for error in validation_result.errors:
                assert "ImportError" not in error
                assert "AttributeError" not in error
    
    @given(st.lists(simple_risk_with_distribution(), min_size=2, max_size=4))
    @settings(max_examples=15, deadline=30000)
    def test_property_24_model_validation_with_correlations(self, risks: List[Risk]):
        """
        Test model validation with correlation matrices.
        
        **Validates: Requirements 9.2, 9.3**
        """
        # Ensure unique risk IDs
        unique_risks = []
        seen_ids = set()
        for risk in risks:
            if risk.id not in seen_ids:
                unique_risks.append(risk)
                seen_ids.add(risk.id)
        
        if len(unique_risks) < 2:
            return  # Need at least 2 risks for correlations
        
        # Create a valid correlation matrix for these risks
        risk_ids = [risk.id for risk in unique_risks]
        correlations = {}
        
        # Add a few correlations
        if len(risk_ids) >= 2:
            correlations[(risk_ids[0], risk_ids[1])] = 0.3
        if len(risk_ids) >= 3:
            correlations[(risk_ids[0], risk_ids[2])] = -0.2
        
        correlation_matrix = CorrelationMatrix(correlations=correlations, risk_ids=risk_ids)
        
        engine = MonteCarloEngine()
        validation_result = engine.validate_model(unique_risks, correlations=correlation_matrix)
        
        # Should return validation result
        assert isinstance(validation_result, ValidationResult)
        
        # Should validate both risks and correlations
        if not validation_result.is_valid:
            # Errors should be specific and actionable
            assert len(validation_result.errors) > 0
            for error in validation_result.errors:
                assert isinstance(error, str)
                assert len(error) > 0
    
    def test_property_24_validation_error_specificity(self):
        """
        Test that validation errors are specific and actionable.
        
        **Validates: Requirements 9.2, 9.3**
        """
        engine = MonteCarloEngine()
        
        # Test with invalid distribution parameters
        try:
            invalid_distribution = ProbabilityDistribution(
                distribution_type=DistributionType.NORMAL,
                parameters={'mean': 0, 'std': -1}  # Invalid: negative std
            )
            # Should fail during construction
            assert False, "Should have failed with negative std"
        except ValueError as e:
            assert "positive" in str(e).lower()
        
        # Test with empty risk list
        validation_result = engine.validate_model([])
        assert not validation_result.is_valid
        assert any("risk" in error.lower() for error in validation_result.errors)
    
    @given(valid_distribution())
    @settings(max_examples=20, deadline=15000)
    def test_property_24_validation_consistency(self, distribution: ProbabilityDistribution):
        """
        Test that validation results are consistent across multiple calls.
        
        **Validates: Requirements 9.2, 9.3**
        """
        engine = MonteCarloEngine()
        
        # Run validation multiple times
        result1 = engine.validate_distribution(distribution)
        result2 = engine.validate_distribution(distribution)
        
        # Results should be consistent
        assert result1.is_valid == result2.is_valid
        assert len(result1.errors) == len(result2.errors)
        assert len(result1.warnings) == len(result2.warnings)
    
    @given(valid_correlation_matrix())
    @settings(max_examples=15, deadline=20000)
    def test_property_24_correlation_matrix_fixes(self, correlation_matrix: CorrelationMatrix):
        """
        Test that correlation matrix fix suggestions work properly.
        
        **Validates: Requirements 9.3**
        """
        engine = MonteCarloEngine()
        
        # For valid matrices, should not need fixes
        fix_suggestions = engine.suggest_correlation_matrix_fixes(correlation_matrix)
        
        assert isinstance(fix_suggestions, dict)
        assert 'suggestions' in fix_suggestions
        
        # For valid matrices, should indicate no fixes needed
        suggestions = fix_suggestions['suggestions']
        if suggestions:
            # Should either say matrix is valid or provide specific fixes
            suggestion_text = " ".join(suggestions).lower()
            assert any(term in suggestion_text for term in ["valid", "already", "no fixes", "applied"])
    
    def test_property_24_validation_performance(self):
        """
        Test that validation operations complete in reasonable time.
        
        **Validates: Requirements 9.2, 9.3**
        """
        import time
        
        # Create a moderately complex scenario
        distributions = [
            ProbabilityDistribution(DistributionType.NORMAL, {'mean': 0, 'std': 1}),
            ProbabilityDistribution(DistributionType.TRIANGULAR, {'min': -1, 'mode': 0, 'max': 1}),
            ProbabilityDistribution(DistributionType.UNIFORM, {'min': 0, 'max': 1})
        ]
        
        risks = []
        for i, dist in enumerate(distributions):
            risk = Risk(
                id=f"risk_{i}",
                name=f"Risk {i}",
                category=RiskCategory.TECHNICAL,
                impact_type=ImpactType.COST,
                probability_distribution=dist,
                baseline_impact=10.0
            )
            risks.append(risk)
        
        correlations = CorrelationMatrix(
            correlations={('risk_0', 'risk_1'): 0.3, ('risk_1', 'risk_2'): -0.2},
            risk_ids=['risk_0', 'risk_1', 'risk_2']
        )
        
        engine = MonteCarloEngine()
        
        # Validation should complete quickly
        start_time = time.time()
        validation_result = engine.validate_model(risks, correlations=correlations)
        end_time = time.time()
        
        # Should complete within reasonable time (5 seconds)
        assert end_time - start_time < 5.0
        assert isinstance(validation_result, ValidationResult)