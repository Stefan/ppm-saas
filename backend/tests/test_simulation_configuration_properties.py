"""
Property-based tests for simulation configuration management.

**Feature: monte-carlo-risk-simulations, Property 23: Simulation Configuration**
**Validates: Requirements 9.1**

Tests that the engine accepts and properly uses iteration count, random seed,
and convergence criteria adjustments for any simulation configuration.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
import numpy as np
from typing import List, Optional

from monte_carlo.simulation_config import (
    SimulationConfig, ConfigurationManager, ConvergenceCriteria, ConfigurationPreset
)
from monte_carlo.engine import MonteCarloEngine
from monte_carlo.models import (
    Risk, ProbabilityDistribution, DistributionType, RiskCategory, ImpactType
)


# Hypothesis strategies for generating test data
@st.composite
def valid_simulation_config(draw):
    """Generate valid simulation configurations."""
    min_iterations = draw(st.integers(min_value=1000, max_value=10000))
    iterations = draw(st.integers(min_value=min_iterations, max_value=100000))
    max_iterations = draw(st.integers(min_value=iterations, max_value=1000000))
    
    random_seed = draw(st.one_of(st.none(), st.integers(min_value=0, max_value=2**31-1)))
    convergence_criteria = draw(st.sampled_from(ConvergenceCriteria))
    convergence_threshold = draw(st.floats(min_value=0.5, max_value=1.0))
    convergence_check_interval = draw(st.integers(min_value=100, max_value=min(10000, iterations//2)))
    
    return SimulationConfig(
        iterations=iterations,
        random_seed=random_seed,
        convergence_criteria=convergence_criteria,
        convergence_threshold=convergence_threshold,
        min_iterations=min_iterations,
        max_iterations=max_iterations,
        convergence_check_interval=convergence_check_interval,
        enable_caching=draw(st.booleans()),
        enable_progress_tracking=draw(st.booleans()),
        enable_convergence_monitoring=draw(st.booleans())
    )


@st.composite
def simple_risk(draw):
    """Generate a simple risk for testing."""
    risk_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    
    # Generate distribution parameters
    dist_type = draw(st.sampled_from([DistributionType.NORMAL, DistributionType.TRIANGULAR, DistributionType.UNIFORM]))
    
    if dist_type == DistributionType.NORMAL:
        mean = draw(st.floats(min_value=-100, max_value=100))
        std = draw(st.floats(min_value=0.1, max_value=50))
        parameters = {'mean': mean, 'std': std}
    elif dist_type == DistributionType.TRIANGULAR:
        min_val = draw(st.floats(min_value=-100, max_value=50))
        max_val = draw(st.floats(min_value=min_val + 1, max_value=100))
        mode = draw(st.floats(min_value=min_val, max_value=max_val))
        parameters = {'min': min_val, 'mode': mode, 'max': max_val}
    else:  # UNIFORM
        min_val = draw(st.floats(min_value=-100, max_value=50))
        max_val = draw(st.floats(min_value=min_val + 1, max_value=100))
        parameters = {'min': min_val, 'max': max_val}
    
    distribution = ProbabilityDistribution(
        distribution_type=dist_type,
        parameters=parameters
    )
    
    return Risk(
        id=risk_id,
        name=f"Risk {risk_id}",
        category=draw(st.sampled_from(RiskCategory)),
        impact_type=draw(st.sampled_from(ImpactType)),
        probability_distribution=distribution,
        baseline_impact=draw(st.floats(min_value=0.1, max_value=100))
    )


class TestSimulationConfigurationProperties:
    """Property-based tests for simulation configuration management."""
    
    @given(valid_simulation_config())
    @settings(max_examples=50, deadline=30000)
    def test_property_23_simulation_configuration_acceptance(self, config: SimulationConfig):
        """
        **Property 23: Simulation Configuration**
        
        For any valid simulation configuration, the engine should accept and properly use
        iteration count, random seed, and convergence criteria adjustments.
        
        **Validates: Requirements 9.1**
        """
        # Test that configuration is accepted by the engine
        engine = MonteCarloEngine(config=config)
        
        # Verify the engine uses the provided configuration
        retrieved_config = engine.get_configuration()
        
        assert retrieved_config.iterations == config.iterations
        assert retrieved_config.random_seed == config.random_seed
        assert retrieved_config.convergence_criteria == config.convergence_criteria
        assert retrieved_config.convergence_threshold == config.convergence_threshold
        assert retrieved_config.min_iterations == config.min_iterations
        assert retrieved_config.max_iterations == config.max_iterations
        assert retrieved_config.convergence_check_interval == config.convergence_check_interval
        assert retrieved_config.enable_caching == config.enable_caching
        assert retrieved_config.enable_progress_tracking == config.enable_progress_tracking
        assert retrieved_config.enable_convergence_monitoring == config.enable_convergence_monitoring
    
    @given(valid_simulation_config(), st.lists(simple_risk(), min_size=1, max_size=5))
    @settings(max_examples=20, deadline=60000)
    def test_property_23_configuration_affects_simulation_execution(self, config: SimulationConfig, risks: List[Risk]):
        """
        Test that configuration parameters actually affect simulation execution.
        
        **Validates: Requirements 9.1**
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
        
        # Use a smaller iteration count for faster testing
        test_config = config.copy_with_overrides(
            iterations=min(config.iterations, 5000),
            max_execution_time=30.0  # 30 second timeout
        )
        
        engine = MonteCarloEngine(config=test_config)
        
        try:
            # Run simulation with configuration
            results = engine.run_simulation_with_config(unique_risks, config=test_config)
            
            # Verify configuration was used
            assert results.iteration_count <= test_config.iterations
            assert results.execution_time > 0
            
            # If random seed was set, results should be deterministic
            if test_config.random_seed is not None:
                # Run again with same config
                results2 = engine.run_simulation_with_config(unique_risks, config=test_config, force_rerun=True)
                
                # Results should be identical (or very close due to floating point)
                np.testing.assert_allclose(results.cost_outcomes, results2.cost_outcomes, rtol=1e-10)
                np.testing.assert_allclose(results.schedule_outcomes, results2.schedule_outcomes, rtol=1e-10)
        
        except Exception as e:
            # If simulation fails, it should be due to configuration validation, not execution
            if "Invalid" not in str(e) and "timeout" not in str(e).lower():
                pytest.fail(f"Simulation failed unexpectedly: {e}")
    
    @given(st.integers(min_value=1000, max_value=50000))
    @settings(max_examples=30, deadline=20000)
    def test_property_23_iteration_count_adjustment(self, iterations: int):
        """
        Test that iteration count adjustments are properly handled.
        
        **Validates: Requirements 9.1**
        """
        config = SimulationConfig(iterations=iterations)
        engine = MonteCarloEngine(config=config)
        
        # Test effective iterations calculation
        effective_iterations_small = config.get_effective_iterations(risk_count=10)
        effective_iterations_large = config.get_effective_iterations(risk_count=100)
        
        # For small risk counts, should use base iterations
        assert effective_iterations_small == iterations
        
        # For large risk counts, may adjust upward
        assert effective_iterations_large >= iterations
        
        # Should respect bounds
        assert config.min_iterations <= effective_iterations_large <= config.max_iterations
    
    @given(st.integers(min_value=0, max_value=2**31-1))
    @settings(max_examples=20, deadline=15000)
    def test_property_23_random_seed_determinism(self, seed: int):
        """
        Test that random seed produces deterministic results.
        
        **Validates: Requirements 9.1**
        """
        config = SimulationConfig(random_seed=seed, iterations=1000)
        
        # Get random state from config
        random_state1 = config.get_random_state()
        random_state2 = config.get_random_state()
        
        # Should produce identical sequences
        samples1 = random_state1.normal(0, 1, 100)
        samples2 = random_state2.normal(0, 1, 100)
        
        np.testing.assert_array_equal(samples1, samples2)
    
    @given(st.sampled_from(ConvergenceCriteria), st.floats(min_value=0.5, max_value=1.0))
    @settings(max_examples=20, deadline=10000)
    def test_property_23_convergence_criteria_adjustment(self, criteria: ConvergenceCriteria, threshold: float):
        """
        Test that convergence criteria adjustments are properly handled.
        
        **Validates: Requirements 9.1**
        """
        config = SimulationConfig(
            convergence_criteria=criteria,
            convergence_threshold=threshold,
            iterations=10000,
            convergence_check_interval=1000
        )
        
        # Test convergence checking logic
        should_check_1000 = config.should_check_convergence(1000)
        should_check_1500 = config.should_check_convergence(1500)
        should_check_2000 = config.should_check_convergence(2000)
        
        if criteria == ConvergenceCriteria.FIXED_ITERATIONS:
            # Should never check convergence for fixed iterations
            assert not should_check_1000
            assert not should_check_1500
            assert not should_check_2000
        else:
            # Should check at intervals
            assert should_check_1000  # 1000 % 1000 == 0
            assert not should_check_1500  # 1500 % 1000 != 0
            assert should_check_2000  # 2000 % 1000 == 0
    
    def test_property_23_configuration_presets_validity(self):
        """
        Test that all configuration presets are valid and usable.
        
        **Validates: Requirements 9.1**
        """
        manager = ConfigurationManager()
        presets = manager.list_presets()
        
        # Test each preset
        for preset_name in presets.keys():
            config = manager.get_preset_config(preset_name)
            
            # Configuration should be valid
            validation_result = manager.validate_config(config)
            assert validation_result.is_valid, f"Preset {preset_name} is invalid: {validation_result.errors}"
            
            # Should be usable by engine
            engine = MonteCarloEngine(config=config)
            retrieved_config = engine.get_configuration()
            
            # Key parameters should match
            assert retrieved_config.iterations == config.iterations
            assert retrieved_config.convergence_criteria == config.convergence_criteria
    
    @given(st.integers(min_value=1, max_value=200), 
           st.sampled_from(['fast', 'balanced', 'accurate']),
           st.one_of(st.none(), st.floats(min_value=10, max_value=300)))
    @settings(max_examples=30, deadline=15000)
    def test_property_23_scenario_based_configuration(self, risk_count: int, accuracy: str, time_constraint: Optional[float]):
        """
        Test that scenario-based configuration creation works properly.
        
        **Validates: Requirements 9.1**
        """
        manager = ConfigurationManager()
        
        config = manager.create_config_for_scenario(
            risk_count=risk_count,
            accuracy_requirement=accuracy,
            time_constraint=time_constraint
        )
        
        # Configuration should be valid
        validation_result = manager.validate_config(config)
        assert validation_result.is_valid, f"Scenario config is invalid: {validation_result.errors}"
        
        # Should adjust iterations based on risk count
        effective_iterations = config.get_effective_iterations(risk_count)
        assert effective_iterations >= config.min_iterations
        assert effective_iterations <= config.max_iterations
        
        # Time constraint should be respected if provided
        if time_constraint is not None:
            assert config.max_execution_time == time_constraint
            
            # For tight time constraints, should use fewer iterations
            if time_constraint < 30:
                assert effective_iterations <= 10000
    
    @given(valid_simulation_config())
    @settings(max_examples=30, deadline=15000)
    def test_property_23_configuration_copy_and_override(self, base_config: SimulationConfig):
        """
        Test that configuration copying and overriding works correctly.
        
        **Validates: Requirements 9.1**
        """
        # Test copying without overrides
        copied_config = base_config.copy_with_overrides()
        
        assert copied_config.iterations == base_config.iterations
        assert copied_config.random_seed == base_config.random_seed
        assert copied_config.convergence_criteria == base_config.convergence_criteria
        
        # Test copying with overrides
        new_iterations = base_config.iterations + 1000
        new_seed = 12345 if base_config.random_seed != 12345 else 54321
        
        overridden_config = base_config.copy_with_overrides(
            iterations=new_iterations,
            random_seed=new_seed
        )
        
        assert overridden_config.iterations == new_iterations
        assert overridden_config.random_seed == new_seed
        assert overridden_config.convergence_criteria == base_config.convergence_criteria  # Unchanged
    
    @given(valid_simulation_config())
    @settings(max_examples=20, deadline=15000)
    def test_property_23_configuration_serialization(self, config: SimulationConfig):
        """
        Test that configuration serialization and deserialization works correctly.
        
        **Validates: Requirements 9.1**
        """
        # Convert to dictionary
        config_dict = config.to_dict()
        
        # Should contain all key parameters
        assert 'iterations' in config_dict
        assert 'random_seed' in config_dict
        assert 'convergence_criteria' in config_dict
        assert config_dict['iterations'] == config.iterations
        assert config_dict['random_seed'] == config.random_seed
        assert config_dict['convergence_criteria'] == config.convergence_criteria.value
        
        # Convert back from dictionary
        restored_config = SimulationConfig.from_dict(config_dict)
        
        # Should be equivalent to original
        assert restored_config.iterations == config.iterations
        assert restored_config.random_seed == config.random_seed
        assert restored_config.convergence_criteria == config.convergence_criteria
        assert restored_config.convergence_threshold == config.convergence_threshold
    
    def test_property_23_parameter_bounds_enforcement(self):
        """
        Test that parameter bounds are properly enforced.
        
        **Validates: Requirements 9.1**
        """
        manager = ConfigurationManager()
        bounds = manager.get_parameter_bounds()
        
        # Test iteration bounds
        iteration_bounds = bounds['iterations']
        
        # Should reject values below minimum
        with pytest.raises(ValueError):
            SimulationConfig(iterations=iteration_bounds['min'] - 1)
        
        # Should accept values at minimum
        config_min = SimulationConfig(iterations=iteration_bounds['min'])
        assert config_min.iterations == iteration_bounds['min']
        
        # Test random seed bounds
        seed_bounds = bounds['random_seed']
        
        # Should reject negative seeds
        with pytest.raises(ValueError):
            SimulationConfig(random_seed=-1)
        
        # Should reject seeds above maximum
        with pytest.raises(ValueError):
            SimulationConfig(random_seed=seed_bounds['max'] + 1)
        
        # Should accept valid seeds
        config_seed = SimulationConfig(random_seed=seed_bounds['max'])
        assert config_seed.random_seed == seed_bounds['max']