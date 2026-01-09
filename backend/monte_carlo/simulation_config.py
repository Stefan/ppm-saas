"""
Simulation Configuration Management for Monte Carlo Risk Simulations.

This module provides configuration management capabilities including iteration count,
random seed, and convergence criteria adjustment with validation and parameter bounds checking.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import numpy as np

from .models import ValidationResult


class ConvergenceCriteria(Enum):
    """Types of convergence criteria for simulation termination."""
    FIXED_ITERATIONS = "fixed_iterations"
    MEAN_STABILITY = "mean_stability"
    VARIANCE_STABILITY = "variance_stability"
    PERCENTILE_STABILITY = "percentile_stability"
    COMBINED_STABILITY = "combined_stability"


@dataclass
class SimulationConfig:
    """
    Configuration parameters for Monte Carlo simulation execution.
    
    Provides comprehensive configuration management with validation and bounds checking
    for all simulation parameters including iteration count, random seed, and convergence criteria.
    """
    
    # Core simulation parameters
    iterations: int = 10000
    random_seed: Optional[int] = None
    
    # Convergence criteria
    convergence_criteria: ConvergenceCriteria = ConvergenceCriteria.FIXED_ITERATIONS
    convergence_threshold: float = 0.95
    min_iterations: int = 10000
    max_iterations: int = 1000000
    convergence_check_interval: int = 1000
    
    # Performance parameters
    max_execution_time: Optional[float] = None  # seconds
    parallel_execution: bool = False
    num_threads: Optional[int] = None
    
    # Statistical parameters
    confidence_levels: List[float] = field(default_factory=lambda: [0.80, 0.90, 0.95])
    percentiles: List[float] = field(default_factory=lambda: [10, 25, 50, 75, 90, 95, 99])
    
    # Caching and optimization
    enable_caching: bool = True
    cache_size_limit: int = 100  # Maximum number of cached simulations
    parameter_change_sensitivity: float = 1e-6  # Threshold for detecting parameter changes
    
    # Advanced options
    enable_progress_tracking: bool = True
    progress_callback_interval: int = 1000
    enable_convergence_monitoring: bool = True
    
    def __post_init__(self):
        """Validate configuration parameters after initialization."""
        validation_result = self.validate()
        if not validation_result.is_valid:
            raise ValueError(f"Invalid simulation configuration: {validation_result.errors}")
    
    def validate(self) -> ValidationResult:
        """
        Validate all configuration parameters and return detailed validation results.
        
        Returns:
            ValidationResult with validation status, errors, warnings, and recommendations
        """
        errors = []
        warnings = []
        recommendations = []
        
        # Validate iteration parameters
        if self.iterations < 1000:
            errors.append(f"Iterations must be at least 1000, got {self.iterations}")
        elif self.iterations < 10000:
            warnings.append(f"Iterations below 10000 may not provide reliable results: {self.iterations}")
        
        if self.min_iterations < 1000:
            errors.append(f"Minimum iterations must be at least 1000, got {self.min_iterations}")
        
        if self.max_iterations < self.min_iterations:
            errors.append(f"Maximum iterations ({self.max_iterations}) must be >= minimum iterations ({self.min_iterations})")
        
        if self.iterations < self.min_iterations:
            errors.append(f"Iterations ({self.iterations}) must be >= minimum iterations ({self.min_iterations})")
        
        if self.iterations > self.max_iterations:
            errors.append(f"Iterations ({self.iterations}) must be <= maximum iterations ({self.max_iterations})")
        
        # Validate random seed
        if self.random_seed is not None:
            if not isinstance(self.random_seed, int):
                errors.append("Random seed must be an integer")
            elif self.random_seed < 0 or self.random_seed > 2**32 - 1:
                errors.append(f"Random seed must be between 0 and {2**32 - 1}")
        
        # Validate convergence parameters
        if not 0.5 <= self.convergence_threshold <= 1.0:
            errors.append(f"Convergence threshold must be between 0.5 and 1.0, got {self.convergence_threshold}")
        
        if self.convergence_check_interval < 100:
            errors.append(f"Convergence check interval must be at least 100, got {self.convergence_check_interval}")
        elif self.convergence_check_interval > self.iterations // 10:
            warnings.append(f"Convergence check interval ({self.convergence_check_interval}) is large relative to iterations ({self.iterations})")
        
        # Validate performance parameters
        if self.max_execution_time is not None:
            if self.max_execution_time <= 0:
                errors.append(f"Maximum execution time must be positive, got {self.max_execution_time}")
            elif self.max_execution_time < 10:
                warnings.append(f"Maximum execution time ({self.max_execution_time}s) may be too short for reliable results")
        
        if self.num_threads is not None:
            if self.num_threads < 1:
                errors.append(f"Number of threads must be at least 1, got {self.num_threads}")
            elif self.num_threads > 32:
                warnings.append(f"Large number of threads ({self.num_threads}) may not improve performance")
        
        # Validate statistical parameters
        for level in self.confidence_levels:
            if not 0.5 <= level <= 0.99:
                errors.append(f"Confidence level must be between 0.5 and 0.99, got {level}")
        
        for percentile in self.percentiles:
            if not 1 <= percentile <= 99:
                errors.append(f"Percentile must be between 1 and 99, got {percentile}")
        
        # Validate caching parameters
        if self.cache_size_limit < 0:
            errors.append(f"Cache size limit must be non-negative, got {self.cache_size_limit}")
        elif self.cache_size_limit > 1000:
            warnings.append(f"Large cache size limit ({self.cache_size_limit}) may consume significant memory")
        
        if not 1e-10 <= self.parameter_change_sensitivity <= 1e-3:
            warnings.append(f"Parameter change sensitivity ({self.parameter_change_sensitivity}) may be too extreme")
        
        # Validate progress tracking parameters
        if self.progress_callback_interval < 100:
            warnings.append(f"Progress callback interval ({self.progress_callback_interval}) may cause performance overhead")
        elif self.progress_callback_interval > self.iterations // 5:
            warnings.append(f"Progress callback interval ({self.progress_callback_interval}) may provide infrequent updates")
        
        # Performance recommendations
        if self.iterations > 100000:
            recommendations.append("Consider enabling parallel execution for large iteration counts")
        
        if self.parallel_execution and self.num_threads is None:
            recommendations.append("Consider specifying number of threads for parallel execution")
        
        if not self.enable_caching and self.iterations > 50000:
            recommendations.append("Consider enabling caching for large simulations to improve re-execution performance")
        
        if self.convergence_criteria == ConvergenceCriteria.FIXED_ITERATIONS and self.iterations > 100000:
            recommendations.append("Consider using adaptive convergence criteria for large simulations")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def get_effective_iterations(self, risk_count: int) -> int:
        """
        Calculate effective iteration count based on risk count and configuration.
        
        Adjusts iteration count based on the number of risks to ensure statistical reliability.
        
        Args:
            risk_count: Number of risks in the simulation
            
        Returns:
            Effective iteration count for the simulation
        """
        base_iterations = self.iterations
        
        # Adjust for risk count - more risks may need more iterations for stability
        if risk_count > 50:
            risk_multiplier = 1.0 + (risk_count - 50) * 0.01  # 1% increase per risk above 50
            adjusted_iterations = int(base_iterations * risk_multiplier)
        else:
            adjusted_iterations = base_iterations
        
        # Ensure within bounds
        effective_iterations = max(self.min_iterations, min(adjusted_iterations, self.max_iterations))
        
        return effective_iterations
    
    def should_check_convergence(self, current_iteration: int) -> bool:
        """
        Determine if convergence should be checked at the current iteration.
        
        Args:
            current_iteration: Current iteration number (1-based)
            
        Returns:
            True if convergence should be checked, False otherwise
        """
        if self.convergence_criteria == ConvergenceCriteria.FIXED_ITERATIONS:
            return False
        
        if not self.enable_convergence_monitoring:
            return False
        
        if current_iteration < self.min_iterations:
            return False
        
        return current_iteration % self.convergence_check_interval == 0
    
    def get_random_state(self) -> np.random.RandomState:
        """
        Get a configured random state for reproducible simulations.
        
        Returns:
            NumPy RandomState object with configured seed
        """
        return np.random.RandomState(self.random_seed)
    
    def copy_with_overrides(self, **overrides) -> 'SimulationConfig':
        """
        Create a copy of the configuration with specified parameter overrides.
        
        Args:
            **overrides: Parameter overrides as keyword arguments
            
        Returns:
            New SimulationConfig instance with overrides applied
        """
        # Get current configuration as dict
        current_config = {
            'iterations': self.iterations,
            'random_seed': self.random_seed,
            'convergence_criteria': self.convergence_criteria,
            'convergence_threshold': self.convergence_threshold,
            'min_iterations': self.min_iterations,
            'max_iterations': self.max_iterations,
            'convergence_check_interval': self.convergence_check_interval,
            'max_execution_time': self.max_execution_time,
            'parallel_execution': self.parallel_execution,
            'num_threads': self.num_threads,
            'confidence_levels': self.confidence_levels.copy(),
            'percentiles': self.percentiles.copy(),
            'enable_caching': self.enable_caching,
            'cache_size_limit': self.cache_size_limit,
            'parameter_change_sensitivity': self.parameter_change_sensitivity,
            'enable_progress_tracking': self.enable_progress_tracking,
            'progress_callback_interval': self.progress_callback_interval,
            'enable_convergence_monitoring': self.enable_convergence_monitoring
        }
        
        # Apply overrides
        current_config.update(overrides)
        
        return SimulationConfig(**current_config)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary representation.
        
        Returns:
            Dictionary representation of the configuration
        """
        return {
            'iterations': self.iterations,
            'random_seed': self.random_seed,
            'convergence_criteria': self.convergence_criteria.value,
            'convergence_threshold': self.convergence_threshold,
            'min_iterations': self.min_iterations,
            'max_iterations': self.max_iterations,
            'convergence_check_interval': self.convergence_check_interval,
            'max_execution_time': self.max_execution_time,
            'parallel_execution': self.parallel_execution,
            'num_threads': self.num_threads,
            'confidence_levels': self.confidence_levels,
            'percentiles': self.percentiles,
            'enable_caching': self.enable_caching,
            'cache_size_limit': self.cache_size_limit,
            'parameter_change_sensitivity': self.parameter_change_sensitivity,
            'enable_progress_tracking': self.enable_progress_tracking,
            'progress_callback_interval': self.progress_callback_interval,
            'enable_convergence_monitoring': self.enable_convergence_monitoring
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'SimulationConfig':
        """
        Create configuration from dictionary representation.
        
        Args:
            config_dict: Dictionary containing configuration parameters
            
        Returns:
            SimulationConfig instance created from dictionary
        """
        # Handle enum conversion
        if 'convergence_criteria' in config_dict and isinstance(config_dict['convergence_criteria'], str):
            config_dict = config_dict.copy()
            config_dict['convergence_criteria'] = ConvergenceCriteria(config_dict['convergence_criteria'])
        
        return cls(**config_dict)


@dataclass
class ConfigurationPreset:
    """
    Predefined configuration presets for common simulation scenarios.
    """
    name: str
    description: str
    config: SimulationConfig
    
    @classmethod
    def get_fast_preset(cls) -> 'ConfigurationPreset':
        """Get configuration preset optimized for fast execution."""
        return cls(
            name="Fast",
            description="Optimized for quick results with minimal accuracy requirements",
            config=SimulationConfig(
                iterations=10000,
                convergence_criteria=ConvergenceCriteria.FIXED_ITERATIONS,
                enable_caching=True,
                enable_progress_tracking=False,
                enable_convergence_monitoring=False
            )
        )
    
    @classmethod
    def get_balanced_preset(cls) -> 'ConfigurationPreset':
        """Get configuration preset with balanced speed and accuracy."""
        return cls(
            name="Balanced",
            description="Balanced configuration for typical simulation needs",
            config=SimulationConfig(
                iterations=50000,
                convergence_criteria=ConvergenceCriteria.COMBINED_STABILITY,
                convergence_threshold=0.95,
                enable_caching=True,
                enable_progress_tracking=True,
                enable_convergence_monitoring=True
            )
        )
    
    @classmethod
    def get_accurate_preset(cls) -> 'ConfigurationPreset':
        """Get configuration preset optimized for maximum accuracy."""
        return cls(
            name="Accurate",
            description="High-accuracy configuration for critical simulations",
            config=SimulationConfig(
                iterations=100000,
                convergence_criteria=ConvergenceCriteria.COMBINED_STABILITY,
                convergence_threshold=0.98,
                min_iterations=50000,
                convergence_check_interval=5000,
                enable_caching=True,
                enable_progress_tracking=True,
                enable_convergence_monitoring=True,
                confidence_levels=[0.80, 0.90, 0.95, 0.99],
                percentiles=[5, 10, 25, 50, 75, 90, 95, 99]
            )
        )
    
    @classmethod
    def get_development_preset(cls) -> 'ConfigurationPreset':
        """Get configuration preset for development and testing."""
        return cls(
            name="Development",
            description="Fast configuration for development and testing purposes",
            config=SimulationConfig(
                iterations=5000,
                min_iterations=1000,  # Lower minimum for development
                convergence_criteria=ConvergenceCriteria.FIXED_ITERATIONS,
                enable_caching=False,
                enable_progress_tracking=True,
                enable_convergence_monitoring=False,
                progress_callback_interval=500
            )
        )


class ConfigurationManager:
    """
    Manager for simulation configuration with validation and preset management.
    
    Provides centralized configuration management with parameter bounds checking,
    validation, and preset configurations for common simulation scenarios.
    """
    
    def __init__(self):
        """Initialize configuration manager."""
        self._presets = {
            'fast': ConfigurationPreset.get_fast_preset(),
            'balanced': ConfigurationPreset.get_balanced_preset(),
            'accurate': ConfigurationPreset.get_accurate_preset(),
            'development': ConfigurationPreset.get_development_preset()
        }
        self._default_config = self._presets['balanced'].config
    
    def get_default_config(self) -> SimulationConfig:
        """
        Get the default simulation configuration.
        
        Returns:
            Default SimulationConfig instance
        """
        return self._default_config.copy_with_overrides()
    
    def get_preset_config(self, preset_name: str) -> SimulationConfig:
        """
        Get a preset configuration by name.
        
        Args:
            preset_name: Name of the preset ('fast', 'balanced', 'accurate', 'development')
            
        Returns:
            SimulationConfig instance for the specified preset
            
        Raises:
            ValueError: If preset name is not recognized
        """
        if preset_name not in self._presets:
            available_presets = list(self._presets.keys())
            raise ValueError(f"Unknown preset '{preset_name}'. Available presets: {available_presets}")
        
        return self._presets[preset_name].config.copy_with_overrides()
    
    def list_presets(self) -> Dict[str, str]:
        """
        List available configuration presets.
        
        Returns:
            Dictionary mapping preset names to descriptions
        """
        return {name: preset.description for name, preset in self._presets.items()}
    
    def validate_config(self, config: SimulationConfig) -> ValidationResult:
        """
        Validate a simulation configuration.
        
        Args:
            config: SimulationConfig to validate
            
        Returns:
            ValidationResult with validation status and details
        """
        return config.validate()
    
    def create_config_for_scenario(
        self,
        risk_count: int,
        accuracy_requirement: str = 'balanced',
        time_constraint: Optional[float] = None,
        **overrides
    ) -> SimulationConfig:
        """
        Create a configuration optimized for a specific scenario.
        
        Args:
            risk_count: Number of risks in the simulation
            accuracy_requirement: Accuracy level ('fast', 'balanced', 'accurate')
            time_constraint: Optional maximum execution time in seconds
            **overrides: Additional configuration overrides
            
        Returns:
            Optimized SimulationConfig for the scenario
        """
        # Start with base preset
        base_config = self.get_preset_config(accuracy_requirement)
        
        # Adjust for risk count
        effective_iterations = base_config.get_effective_iterations(risk_count)
        scenario_overrides = {'iterations': effective_iterations}
        
        # Adjust for time constraint
        if time_constraint is not None:
            scenario_overrides['max_execution_time'] = time_constraint
            
            # Reduce iterations if time constraint is tight
            if time_constraint < 30:  # Less than 30 seconds
                scenario_overrides['iterations'] = min(effective_iterations, 10000)
                scenario_overrides['convergence_criteria'] = ConvergenceCriteria.FIXED_ITERATIONS
            elif time_constraint < 120:  # Less than 2 minutes
                scenario_overrides['iterations'] = min(effective_iterations, 25000)
        
        # Enable parallel execution for large simulations
        if effective_iterations > 50000 and risk_count > 20:
            scenario_overrides['parallel_execution'] = True
            scenario_overrides['num_threads'] = min(8, max(2, risk_count // 10))
        
        # Apply all overrides
        scenario_overrides.update(overrides)
        
        return base_config.copy_with_overrides(**scenario_overrides)
    
    def get_parameter_bounds(self) -> Dict[str, Dict[str, Any]]:
        """
        Get parameter bounds and constraints for configuration validation.
        
        Returns:
            Dictionary containing parameter bounds and constraints
        """
        return {
            'iterations': {
                'min': 1000,
                'max': 1000000,
                'recommended_min': 10000,
                'recommended_max': 100000
            },
            'random_seed': {
                'min': 0,
                'max': 2**32 - 1,
                'type': 'integer'
            },
            'convergence_threshold': {
                'min': 0.5,
                'max': 1.0,
                'recommended_min': 0.90,
                'recommended_max': 0.99
            },
            'min_iterations': {
                'min': 1000,
                'max': 1000000,
                'recommended_min': 10000
            },
            'max_iterations': {
                'min': 1000,
                'max': 1000000,
                'recommended_max': 500000
            },
            'convergence_check_interval': {
                'min': 100,
                'max': 50000,
                'recommended_min': 1000,
                'recommended_max': 10000
            },
            'max_execution_time': {
                'min': 1.0,
                'max': 3600.0,  # 1 hour
                'recommended_min': 10.0,
                'recommended_max': 300.0  # 5 minutes
            },
            'num_threads': {
                'min': 1,
                'max': 32,
                'recommended_min': 2,
                'recommended_max': 8
            },
            'confidence_levels': {
                'element_min': 0.5,
                'element_max': 0.99,
                'recommended_values': [0.80, 0.90, 0.95]
            },
            'percentiles': {
                'element_min': 1,
                'element_max': 99,
                'recommended_values': [10, 25, 50, 75, 90, 95, 99]
            },
            'cache_size_limit': {
                'min': 0,
                'max': 1000,
                'recommended_max': 100
            },
            'parameter_change_sensitivity': {
                'min': 1e-10,
                'max': 1e-3,
                'recommended_value': 1e-6
            },
            'progress_callback_interval': {
                'min': 100,
                'max': 50000,
                'recommended_min': 1000,
                'recommended_max': 5000
            }
        }