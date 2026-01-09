"""
Property-based tests for Monte Carlo Risk Simulation data models.

Tests the core data models for validation, consistency, and correctness
using property-based testing with Hypothesis.
"""

import pytest
from datetime import datetime
from hypothesis import given, strategies as st, assume, settings
import numpy as np

from monte_carlo.models import (
    Risk, ProbabilityDistribution, SimulationResults, Scenario,
    RiskCategory, ImpactType, DistributionType, MitigationStrategy,
    CorrelationMatrix, ConvergenceMetrics, RiskData, CrossImpactModel,
    MitigationAnalysis, RiskModification, ValidationResult, ProgressStatus
)


# Hypothesis strategies for generating test data
@st.composite
def probability_distribution_strategy(draw):
    """Generate valid probability distributions."""
    dist_type = draw(st.sampled_from(DistributionType))
    
    if dist_type == DistributionType.NORMAL:
        mean = draw(st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False))
        std = draw(st.floats(min_value=0.1, max_value=100, allow_nan=False, allow_infinity=False))
        parameters = {'mean': mean, 'std': std}
    elif dist_type == DistributionType.TRIANGULAR:
        min_val = draw(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))
        max_val = draw(st.floats(min_value=min_val + 1, max_value=min_val + 200, allow_nan=False, allow_infinity=False))
        mode = draw(st.floats(min_value=min_val, max_value=max_val, allow_nan=False, allow_infinity=False))
        parameters = {'min': min_val, 'mode': mode, 'max': max_val}
    elif dist_type == DistributionType.UNIFORM:
        min_val = draw(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))
        max_val = draw(st.floats(min_value=min_val + 0.1, max_value=min_val + 200, allow_nan=False, allow_infinity=False))
        parameters = {'min': min_val, 'max': max_val}
    elif dist_type == DistributionType.BETA:
        alpha = draw(st.floats(min_value=0.1, max_value=10, allow_nan=False, allow_infinity=False))
        beta = draw(st.floats(min_value=0.1, max_value=10, allow_nan=False, allow_infinity=False))
        parameters = {'alpha': alpha, 'beta': beta}
    elif dist_type == DistributionType.LOGNORMAL:
        mu = draw(st.floats(min_value=-5, max_value=5, allow_nan=False, allow_infinity=False))
        sigma = draw(st.floats(min_value=0.1, max_value=2, allow_nan=False, allow_infinity=False))
        parameters = {'mu': mu, 'sigma': sigma}
    
    bounds = draw(st.one_of(st.none(), st.tuples(
        st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
        st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False)
    ).filter(lambda x: x[0] < x[1])))
    
    return ProbabilityDistribution(dist_type, parameters, bounds)


@st.composite
def mitigation_strategy_strategy(draw):
    """Generate valid mitigation strategies."""
    return MitigationStrategy(
        id=draw(st.text(min_size=1, max_size=50)),
        name=draw(st.text(min_size=1, max_size=100)),
        description=draw(st.text(min_size=1, max_size=200)),
        cost=draw(st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False)),
        effectiveness=draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)),
        implementation_time=draw(st.integers(min_value=0, max_value=365))
    )


@st.composite
def risk_strategy(draw):
    """Generate valid risks."""
    return Risk(
        id=draw(st.text(min_size=1, max_size=50)),
        name=draw(st.text(min_size=1, max_size=100)),
        category=draw(st.sampled_from(RiskCategory)),
        impact_type=draw(st.sampled_from(ImpactType)),
        probability_distribution=draw(probability_distribution_strategy()),
        baseline_impact=draw(st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False)),
        correlation_dependencies=draw(st.lists(st.text(min_size=1, max_size=50), max_size=10)),
        mitigation_strategies=draw(st.lists(mitigation_strategy_strategy(), max_size=5))
    )


@st.composite
def convergence_metrics_strategy(draw):
    """Generate valid convergence metrics."""
    return ConvergenceMetrics(
        mean_stability=draw(st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False)),
        variance_stability=draw(st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False)),
        percentile_stability={
            0.1: draw(st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False)),
            0.5: draw(st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False)),
            0.9: draw(st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False))
        },
        converged=draw(st.booleans()),
        iterations_to_convergence=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=100000)))
    )


@st.composite
def simulation_results_strategy(draw):
    """Generate valid simulation results."""
    iteration_count = draw(st.integers(min_value=1000, max_value=50000))
    return SimulationResults(
        simulation_id=draw(st.text(min_size=1, max_size=50)),
        timestamp=datetime.now(),
        iteration_count=iteration_count,
        cost_outcomes=np.random.normal(100000, 10000, iteration_count),
        schedule_outcomes=np.random.normal(365, 30, iteration_count),
        risk_contributions={
            "risk1": np.random.normal(0, 1000, iteration_count),
            "risk2": np.random.normal(0, 2000, iteration_count)
        },
        convergence_metrics=draw(convergence_metrics_strategy()),
        execution_time=draw(st.floats(min_value=0.1, max_value=300, allow_nan=False, allow_infinity=False))
    )


class TestDataModelValidation:
    """Test suite for data model validation using property-based testing."""
    
    @given(probability_distribution_strategy())
    @settings(max_examples=10)
    def test_probability_distribution_validation(self, distribution):
        """
        **Feature: monte-carlo-risk-simulations, Property 1: Simulation Execution Integrity**
        
        For any valid probability distribution, the system should successfully create
        the distribution and validate its parameters according to mathematical constraints.
        **Validates: Requirements 1.1, 1.3**
        """
        # The distribution should be created successfully (no exceptions)
        assert distribution.distribution_type in DistributionType
        assert isinstance(distribution.parameters, dict)
        assert len(distribution.parameters) > 0
        
        # Parameters should be valid for the distribution type
        if distribution.distribution_type == DistributionType.NORMAL:
            assert 'mean' in distribution.parameters
            assert 'std' in distribution.parameters
            assert distribution.parameters['std'] > 0
        elif distribution.distribution_type == DistributionType.TRIANGULAR:
            assert 'min' in distribution.parameters
            assert 'mode' in distribution.parameters
            assert 'max' in distribution.parameters
            assert distribution.parameters['min'] <= distribution.parameters['mode'] <= distribution.parameters['max']
        elif distribution.distribution_type == DistributionType.UNIFORM:
            assert 'min' in distribution.parameters
            assert 'max' in distribution.parameters
            assert distribution.parameters['min'] < distribution.parameters['max']
        elif distribution.distribution_type == DistributionType.BETA:
            assert 'alpha' in distribution.parameters
            assert 'beta' in distribution.parameters
            assert distribution.parameters['alpha'] > 0
            assert distribution.parameters['beta'] > 0
        elif distribution.distribution_type == DistributionType.LOGNORMAL:
            assert 'mu' in distribution.parameters
            assert 'sigma' in distribution.parameters
            assert distribution.parameters['sigma'] > 0
    
    @given(probability_distribution_strategy(), st.integers(min_value=1, max_value=100))
    @settings(max_examples=10)
    def test_distribution_sampling(self, distribution, sample_size):
        """
        **Feature: monte-carlo-risk-simulations, Property 1: Simulation Execution Integrity**
        
        For any valid probability distribution and sample size, the distribution should
        generate the correct number of samples without errors.
        **Validates: Requirements 1.1, 1.3**
        """
        samples = distribution.sample(sample_size)
        
        # Should generate correct number of samples
        assert len(samples) == sample_size
        assert isinstance(samples, np.ndarray)
        
        # Samples should be finite numbers
        assert np.all(np.isfinite(samples))
        
        # If bounds are specified, samples should respect them
        if distribution.bounds is not None:
            lower, upper = distribution.bounds
            assert np.all(samples >= lower)
            assert np.all(samples <= upper)
    
    @given(risk_strategy())
    @settings(max_examples=10)
    def test_risk_model_validation(self, risk):
        """
        **Feature: monte-carlo-risk-simulations, Property 1: Simulation Execution Integrity**
        
        For any valid risk, the risk model should maintain data integrity and
        validate all required fields.
        **Validates: Requirements 1.1, 1.3**
        """
        # Risk should have all required fields
        assert risk.id
        assert risk.name
        assert isinstance(risk.category, RiskCategory)
        assert isinstance(risk.impact_type, ImpactType)
        assert isinstance(risk.probability_distribution, ProbabilityDistribution)
        assert risk.baseline_impact >= 0
        assert isinstance(risk.correlation_dependencies, list)
        assert isinstance(risk.mitigation_strategies, list)
        
        # All mitigation strategies should be valid
        for strategy in risk.mitigation_strategies:
            assert isinstance(strategy, MitigationStrategy)
            assert 0.0 <= strategy.effectiveness <= 1.0
            assert strategy.cost >= 0
            assert strategy.implementation_time >= 0
    
    @given(simulation_results_strategy())
    @settings(max_examples=10)
    def test_simulation_results_validation(self, results):
        """
        **Feature: monte-carlo-risk-simulations, Property 1: Simulation Execution Integrity**
        
        For any simulation results, the data should maintain consistency between
        iteration count and outcome arrays.
        **Validates: Requirements 1.1, 1.3**
        """
        # Basic validation
        assert results.simulation_id
        assert results.iteration_count > 0
        assert results.execution_time >= 0
        
        # Array lengths should match iteration count
        assert len(results.cost_outcomes) == results.iteration_count
        assert len(results.schedule_outcomes) == results.iteration_count
        
        # Risk contributions should have consistent lengths
        for risk_id, contributions in results.risk_contributions.items():
            assert len(contributions) == results.iteration_count
        
        # Outcomes should be finite numbers
        assert np.all(np.isfinite(results.cost_outcomes))
        assert np.all(np.isfinite(results.schedule_outcomes))
        
        # Convergence metrics should be valid
        assert isinstance(results.convergence_metrics, ConvergenceMetrics)
        assert 0 <= results.convergence_metrics.mean_stability <= 1
        assert 0 <= results.convergence_metrics.variance_stability <= 1
    
    @given(st.lists(st.text(min_size=1, max_size=20), min_size=2, max_size=5, unique=True))
    @settings(max_examples=10)
    def test_correlation_matrix_validation(self, risk_ids):
        """
        **Feature: monte-carlo-risk-simulations, Property 1: Simulation Execution Integrity**
        
        For any correlation matrix, correlation coefficients should be within [-1, 1]
        and the matrix should maintain mathematical consistency.
        **Validates: Requirements 1.1, 1.3**
        """
        # Create valid correlations
        correlations = {}
        for i, risk1 in enumerate(risk_ids):
            for j, risk2 in enumerate(risk_ids[i+1:], i+1):
                # Generate correlation between -1 and 1
                correlation = np.random.uniform(-0.9, 0.9)  # Avoid exactly ±1 for numerical stability
                correlations[(risk1, risk2)] = correlation
        
        matrix = CorrelationMatrix(correlations, risk_ids)
        
        # All correlations should be within bounds
        for (risk1, risk2), corr in matrix.correlations.items():
            assert -1.0 <= corr <= 1.0
            assert risk1 in risk_ids
            assert risk2 in risk_ids
        
        # Self-correlation should be 1.0
        for risk_id in risk_ids:
            assert matrix.get_correlation(risk_id, risk_id) == 1.0
        
        # Correlation should be symmetric
        for (risk1, risk2), corr in matrix.correlations.items():
            assert matrix.get_correlation(risk1, risk2) == matrix.get_correlation(risk2, risk1)
    
    def test_invalid_distribution_parameters(self):
        """Test that invalid distribution parameters raise appropriate errors."""
        # Normal distribution with negative std
        with pytest.raises(ValueError, match="Standard deviation must be positive"):
            ProbabilityDistribution(DistributionType.NORMAL, {'mean': 0, 'std': -1})
        
        # Triangular distribution with invalid ordering
        with pytest.raises(ValueError, match="min <= mode <= max"):
            ProbabilityDistribution(DistributionType.TRIANGULAR, {'min': 10, 'mode': 5, 'max': 15})
        
        # Uniform distribution with min >= max
        with pytest.raises(ValueError, match="min must be less than max"):
            ProbabilityDistribution(DistributionType.UNIFORM, {'min': 10, 'max': 5})
        
        # Beta distribution with non-positive parameters
        with pytest.raises(ValueError, match="parameters must be positive"):
            ProbabilityDistribution(DistributionType.BETA, {'alpha': -1, 'beta': 2})
        
        # Lognormal distribution with non-positive sigma
        with pytest.raises(ValueError, match="sigma must be positive"):
            ProbabilityDistribution(DistributionType.LOGNORMAL, {'mu': 0, 'sigma': -1})
    
    def test_invalid_risk_parameters(self):
        """Test that invalid risk parameters raise appropriate errors."""
        valid_distribution = ProbabilityDistribution(
            DistributionType.NORMAL, 
            {'mean': 0, 'std': 1}
        )
        
        # Empty risk ID
        with pytest.raises(ValueError, match="Risk ID cannot be empty"):
            Risk("", "Test Risk", RiskCategory.TECHNICAL, ImpactType.COST, valid_distribution, 1000)
        
        # Empty risk name
        with pytest.raises(ValueError, match="Risk name cannot be empty"):
            Risk("risk1", "", RiskCategory.TECHNICAL, ImpactType.COST, valid_distribution, 1000)
    
    def test_invalid_mitigation_strategy_parameters(self):
        """Test that invalid mitigation strategy parameters raise appropriate errors."""
        # Effectiveness outside [0, 1]
        with pytest.raises(ValueError, match="Effectiveness must be between 0.0 and 1.0"):
            MitigationStrategy("m1", "Test", "Description", 1000, 1.5, 30)
        
        # Negative cost
        with pytest.raises(ValueError, match="Cost must be non-negative"):
            MitigationStrategy("m1", "Test", "Description", -1000, 0.5, 30)
        
        # Negative implementation time
        with pytest.raises(ValueError, match="Implementation time must be non-negative"):
            MitigationStrategy("m1", "Test", "Description", 1000, 0.5, -30)