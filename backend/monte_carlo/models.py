"""
Core data models for Monte Carlo Risk Simulation System.

This module defines the fundamental data structures used throughout the system,
including Risk, ProbabilityDistribution, SimulationResults, and Scenario models.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import numpy as np


class RiskCategory(Enum):
    """Categories for risk classification."""
    TECHNICAL = "technical"
    SCHEDULE = "schedule"
    COST = "cost"
    RESOURCE = "resource"
    EXTERNAL = "external"
    QUALITY = "quality"
    REGULATORY = "regulatory"


class ImpactType(Enum):
    """Types of impact a risk can have."""
    COST = "cost"
    SCHEDULE = "schedule"
    BOTH = "both"


class DistributionType(Enum):
    """Supported probability distribution types."""
    NORMAL = "normal"
    TRIANGULAR = "triangular"
    UNIFORM = "uniform"
    BETA = "beta"
    LOGNORMAL = "lognormal"


@dataclass
class MitigationStrategy:
    """Represents a risk mitigation strategy."""
    id: str
    name: str
    description: str
    cost: float
    effectiveness: float  # 0.0 to 1.0
    implementation_time: int  # days
    
    def __post_init__(self):
        """Validate mitigation strategy parameters."""
        if not 0.0 <= self.effectiveness <= 1.0:
            raise ValueError("Effectiveness must be between 0.0 and 1.0")
        if self.cost < 0:
            raise ValueError("Cost must be non-negative")
        if self.implementation_time < 0:
            raise ValueError("Implementation time must be non-negative")


@dataclass
class ProbabilityDistribution:
    """Represents a probability distribution for risk modeling."""
    distribution_type: DistributionType
    parameters: Dict[str, float]
    bounds: Optional[Tuple[float, float]] = None
    
    def __post_init__(self):
        """Validate distribution parameters."""
        self._validate_parameters()
    
    def _validate_parameters(self):
        """Validate distribution parameters based on type."""
        if self.distribution_type == DistributionType.NORMAL:
            if 'mean' not in self.parameters or 'std' not in self.parameters:
                raise ValueError("Normal distribution requires 'mean' and 'std' parameters")
            if self.parameters['std'] <= 0:
                raise ValueError("Standard deviation must be positive")
                
        elif self.distribution_type == DistributionType.TRIANGULAR:
            required = {'min', 'mode', 'max'}
            if not required.issubset(self.parameters.keys()):
                raise ValueError("Triangular distribution requires 'min', 'mode', 'max' parameters")
            if not (self.parameters['min'] <= self.parameters['mode'] <= self.parameters['max']):
                raise ValueError("Triangular parameters must satisfy min <= mode <= max")
                
        elif self.distribution_type == DistributionType.UNIFORM:
            if 'min' not in self.parameters or 'max' not in self.parameters:
                raise ValueError("Uniform distribution requires 'min' and 'max' parameters")
            if self.parameters['min'] >= self.parameters['max']:
                raise ValueError("Uniform distribution min must be less than max")
                
        elif self.distribution_type == DistributionType.BETA:
            if 'alpha' not in self.parameters or 'beta' not in self.parameters:
                raise ValueError("Beta distribution requires 'alpha' and 'beta' parameters")
            if self.parameters['alpha'] <= 0 or self.parameters['beta'] <= 0:
                raise ValueError("Beta distribution parameters must be positive")
                
        elif self.distribution_type == DistributionType.LOGNORMAL:
            if 'mu' not in self.parameters or 'sigma' not in self.parameters:
                raise ValueError("Lognormal distribution requires 'mu' and 'sigma' parameters")
            if self.parameters['sigma'] <= 0:
                raise ValueError("Lognormal sigma must be positive")
    
    def sample(self, size: int, random_state: Optional[np.random.RandomState] = None) -> np.ndarray:
        """Generate random samples from the distribution."""
        if random_state is None:
            random_state = np.random.RandomState()
            
        if self.distribution_type == DistributionType.NORMAL:
            samples = random_state.normal(
                self.parameters['mean'], 
                self.parameters['std'], 
                size
            )
        elif self.distribution_type == DistributionType.TRIANGULAR:
            samples = random_state.triangular(
                self.parameters['min'],
                self.parameters['mode'],
                self.parameters['max'],
                size
            )
        elif self.distribution_type == DistributionType.UNIFORM:
            samples = random_state.uniform(
                self.parameters['min'],
                self.parameters['max'],
                size
            )
        elif self.distribution_type == DistributionType.BETA:
            samples = random_state.beta(
                self.parameters['alpha'],
                self.parameters['beta'],
                size
            )
        elif self.distribution_type == DistributionType.LOGNORMAL:
            samples = random_state.lognormal(
                self.parameters['mu'],
                self.parameters['sigma'],
                size
            )
        else:
            raise ValueError(f"Unsupported distribution type: {self.distribution_type}")
        
        # Apply bounds if specified
        if self.bounds is not None:
            samples = np.clip(samples, self.bounds[0], self.bounds[1])
            
        return samples


@dataclass
class Risk:
    """Core risk model representing a project risk."""
    id: str
    name: str
    category: RiskCategory
    impact_type: ImpactType
    probability_distribution: ProbabilityDistribution
    baseline_impact: float
    correlation_dependencies: List[str] = field(default_factory=list)
    mitigation_strategies: List[MitigationStrategy] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate risk parameters."""
        if not self.id:
            raise ValueError("Risk ID cannot be empty")
        if not self.name:
            raise ValueError("Risk name cannot be empty")


@dataclass
class ConvergenceMetrics:
    """Metrics for assessing simulation convergence."""
    mean_stability: float
    variance_stability: float
    percentile_stability: Dict[float, float]
    converged: bool
    iterations_to_convergence: Optional[int] = None


@dataclass
class SimulationResults:
    """Results from a Monte Carlo simulation run."""
    simulation_id: str
    timestamp: datetime
    iteration_count: int
    cost_outcomes: np.ndarray
    schedule_outcomes: np.ndarray
    risk_contributions: Dict[str, np.ndarray]
    convergence_metrics: ConvergenceMetrics
    execution_time: float
    
    def __post_init__(self):
        """Validate simulation results."""
        if self.iteration_count <= 0:
            raise ValueError("Iteration count must be positive")
        if len(self.cost_outcomes) != self.iteration_count:
            raise ValueError("Cost outcomes length must match iteration count")
        if len(self.schedule_outcomes) != self.iteration_count:
            raise ValueError("Schedule outcomes length must match iteration count")
        if self.execution_time < 0:
            raise ValueError("Execution time must be non-negative")


@dataclass
class RiskModification:
    """Represents a modification to a risk for scenario analysis."""
    parameter_changes: Dict[str, float]
    distribution_type_change: Optional[DistributionType] = None
    mitigation_applied: Optional[str] = None  # mitigation strategy ID


@dataclass
class Scenario:
    """Represents a risk scenario for comparative analysis."""
    id: str
    name: str
    description: str
    risks: List[Risk]
    modifications: Dict[str, RiskModification] = field(default_factory=dict)
    simulation_results: Optional[SimulationResults] = None
    
    def __post_init__(self):
        """Validate scenario parameters."""
        if not self.id:
            raise ValueError("Scenario ID cannot be empty")
        if not self.name:
            raise ValueError("Scenario name cannot be empty")


@dataclass
class CorrelationMatrix:
    """Represents correlation relationships between risks."""
    correlations: Dict[Tuple[str, str], float]
    risk_ids: List[str]
    
    def __post_init__(self):
        """Validate correlation matrix."""
        for (risk1, risk2), correlation in self.correlations.items():
            if not -1.0 <= correlation <= 1.0:
                raise ValueError(f"Correlation between {risk1} and {risk2} must be between -1 and 1")
            if risk1 not in self.risk_ids or risk2 not in self.risk_ids:
                raise ValueError(f"Risk IDs {risk1}, {risk2} must be in risk_ids list")
    
    def get_correlation(self, risk1_id: str, risk2_id: str) -> float:
        """Get correlation coefficient between two risks."""
        if risk1_id == risk2_id:
            return 1.0
        
        key = (risk1_id, risk2_id)
        reverse_key = (risk2_id, risk1_id)
        
        if key in self.correlations:
            return self.correlations[key]
        elif reverse_key in self.correlations:
            return self.correlations[reverse_key]
        else:
            return 0.0  # No correlation specified


@dataclass
class PercentileAnalysis:
    """Statistical percentile analysis results."""
    percentiles: Dict[float, float]  # percentile -> value
    mean: float
    median: float
    std_dev: float
    coefficient_of_variation: float


@dataclass
class ConfidenceIntervals:
    """Confidence interval analysis results."""
    intervals: Dict[float, Tuple[float, float]]  # confidence_level -> (lower, upper)
    sample_size: int


@dataclass
class RiskContribution:
    """Risk contribution to overall uncertainty."""
    risk_id: str
    risk_name: str
    contribution_percentage: float
    variance_contribution: float
    correlation_effects: Dict[str, float]


@dataclass
class ScenarioComparison:
    """Comparison results between scenarios."""
    scenario_a_id: str
    scenario_b_id: str
    cost_difference: Dict[str, float]  # statistical measures
    schedule_difference: Dict[str, float]
    statistical_significance: Dict[str, float]  # p-values
    effect_size: Dict[str, float]


@dataclass
class ValidationResult:
    """Result of model validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ProgressStatus:
    """Simulation progress tracking."""
    simulation_id: str
    current_iteration: int
    total_iterations: int
    elapsed_time: float
    estimated_remaining_time: float
    status: str  # "running", "completed", "failed", "cancelled"


@dataclass
class RiskData:
    """Raw risk data for distribution fitting."""
    risk_id: str
    historical_impacts: List[float]
    three_point_estimate: Optional[Tuple[float, float, float]] = None  # (optimistic, most_likely, pessimistic)
    expert_judgment: Optional[Dict[str, Any]] = None


@dataclass
class CrossImpactModel:
    """Model for cross-impact relationships between risks."""
    primary_risk_id: str
    secondary_risk_id: str
    correlation_coefficient: float
    impact_multiplier: float  # How much primary risk affects secondary
    
    def __post_init__(self):
        """Validate cross-impact model parameters."""
        if not -1.0 <= self.correlation_coefficient <= 1.0:
            raise ValueError("Correlation coefficient must be between -1 and 1")
        if self.impact_multiplier < 0:
            raise ValueError("Impact multiplier must be non-negative")


@dataclass
class MitigationAnalysis:
    """Analysis of mitigation strategy effectiveness."""
    strategy_id: str
    baseline_risk: float
    mitigated_risk: float
    risk_reduction: float
    cost_benefit_ratio: float
    net_present_value: float
    return_on_investment: float


@dataclass
class Milestone:
    """Represents a project milestone with timeline data."""
    id: str
    name: str
    planned_date: datetime
    baseline_duration: float  # days
    critical_path: bool = False
    dependencies: List[str] = field(default_factory=list)  # milestone IDs
    
    def __post_init__(self):
        """Validate milestone parameters."""
        if not self.id:
            raise ValueError("Milestone ID cannot be empty")
        if not self.name:
            raise ValueError("Milestone name cannot be empty")
        if self.baseline_duration < 0:
            raise ValueError("Baseline duration must be non-negative")


@dataclass
class Activity:
    """Represents a project activity with schedule risk implications."""
    id: str
    name: str
    baseline_duration: float  # days
    earliest_start: float  # days from project start
    latest_start: float  # days from project start
    float_time: float  # days of schedule float
    critical_path: bool = False
    resource_requirements: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate activity parameters."""
        if not self.id:
            raise ValueError("Activity ID cannot be empty")
        if not self.name:
            raise ValueError("Activity name cannot be empty")
        if self.baseline_duration < 0:
            raise ValueError("Baseline duration must be non-negative")
        if self.earliest_start < 0:
            raise ValueError("Earliest start must be non-negative")
        if self.latest_start < self.earliest_start:
            raise ValueError("Latest start must be >= earliest start")
        if self.float_time < 0:
            raise ValueError("Float time must be non-negative")


@dataclass
class ResourceConstraint:
    """Represents resource availability constraints affecting schedule."""
    resource_id: str
    resource_name: str
    total_availability: float  # units available per day
    utilization_limit: float = 1.0  # maximum utilization (0.0 to 1.0)
    availability_periods: List[Tuple[float, float, float]] = field(default_factory=list)  # (start_day, end_day, availability)
    
    def __post_init__(self):
        """Validate resource constraint parameters."""
        if not self.resource_id:
            raise ValueError("Resource ID cannot be empty")
        if not self.resource_name:
            raise ValueError("Resource name cannot be empty")
        if self.total_availability < 0:
            raise ValueError("Total availability must be non-negative")
        if not 0.0 <= self.utilization_limit <= 1.0:
            raise ValueError("Utilization limit must be between 0.0 and 1.0")


@dataclass
class ScheduleData:
    """Container for schedule-related data used in simulations."""
    milestones: List[Milestone] = field(default_factory=list)
    activities: List[Activity] = field(default_factory=list)
    resource_constraints: List[ResourceConstraint] = field(default_factory=list)
    project_start_date: Optional[datetime] = None
    project_baseline_duration: float = 0.0  # days
    
    def __post_init__(self):
        """Validate schedule data consistency."""
        if self.project_baseline_duration < 0:
            raise ValueError("Project baseline duration must be non-negative")
        
        # Validate milestone dependencies
        milestone_ids = {m.id for m in self.milestones}
        for milestone in self.milestones:
            for dep_id in milestone.dependencies:
                if dep_id not in milestone_ids:
                    raise ValueError(f"Milestone {milestone.id} depends on unknown milestone {dep_id}")
        
        # Validate resource requirements reference existing constraints
        resource_ids = {rc.resource_id for rc in self.resource_constraints}
        for activity in self.activities:
            for resource_id in activity.resource_requirements:
                if resource_id not in resource_ids and resource_ids:  # Only validate if constraints are defined
                    raise ValueError(f"Activity {activity.id} requires unknown resource {resource_id}")


@dataclass
class SystemHealthStatus:
    """System health monitoring status."""
    overall_status: str = "unknown"  # "healthy", "degraded", "unhealthy"
    components_initialized: bool = False
    component_health: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    last_health_check: Optional[datetime] = None
    initialization_error: Optional[str] = None
    health_check_error: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """Performance metrics for system monitoring."""
    risk_count: int = 0
    iteration_count: int = 0
    total_execution_time: float = 0.0
    risks_per_second: float = 0.0
    iterations_per_second: float = 0.0
    memory_usage_mb: float = 0.0
    meets_performance_requirements: bool = False


@dataclass
class WorkflowResult:
    """Complete workflow execution results."""
    success: bool = False
    execution_time: float = 0.0
    simulation_results: Optional[SimulationResults] = None
    percentile_analysis: Optional[PercentileAnalysis] = None
    confidence_intervals: Optional[ConfidenceIntervals] = None
    risk_contributions: List[RiskContribution] = field(default_factory=list)
    visualizations: Dict[str, str] = field(default_factory=dict)  # chart_type -> file_path
    budget_compliance: Optional[Any] = None  # BudgetComplianceResult
    schedule_compliance: Optional[Any] = None  # ScheduleComplianceResult
    improvement_recommendations: Optional[Any] = None
    exports: Dict[str, str] = field(default_factory=dict)  # format -> file_path
    performance_metrics: Optional[PerformanceMetrics] = None
    
    # Error tracking
    execution_error: Optional[str] = None
    validation_errors: List[str] = field(default_factory=list)
    visualization_errors: List[str] = field(default_factory=list)
    distribution_output_errors: List[str] = field(default_factory=list)
    export_errors: List[str] = field(default_factory=list)
    
    # Calibration tracking
    calibration_applied: bool = False
    calibration_metrics: Optional[Any] = None


@dataclass
class IntegrationReport:
    """System integration validation report."""
    validation_timestamp: Optional[datetime] = None
    overall_integration_status: bool = False
    components_healthy: bool = False
    workflow_functional: bool = False
    api_integration_functional: bool = False
    component_health_details: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    integration_errors: List[str] = field(default_factory=list)
    performance_test_results: Optional[PerformanceMetrics] = None


@dataclass
class CalibrationResult:
    """Results from historical data calibration."""
    calibrated_risks: List[Risk]
    accuracy_metrics: Dict[str, float]
    calibration_confidence: float
    historical_data_quality: str  # "high", "medium", "low"
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ImprovementRecommendations:
    """Recommendations for system improvement."""
    parameter_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    process_improvements: List[str] = field(default_factory=list)
    model_updates: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    based_on_projects: int = 0


@dataclass
class BudgetComplianceResult:
    """Budget compliance probability analysis."""
    baseline_budget: float
    probability_within_budget: float
    probability_within_10_percent: float
    probability_within_20_percent: float
    expected_cost: float
    cost_at_risk_95: float  # 95th percentile cost
    contingency_recommendation: float


@dataclass
class ScheduleComplianceResult:
    """Schedule compliance probability analysis."""
    baseline_schedule: float  # days
    probability_on_time: float
    probability_within_1_week: float
    probability_within_1_month: float
    expected_duration: float
    duration_at_risk_95: float  # 95th percentile duration
    schedule_buffer_recommendation: float  # days