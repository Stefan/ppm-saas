"""
Historical Data Calibration System for Monte Carlo Risk Simulations.

This module provides functionality to calibrate probability distributions using
completed project outcomes and track prediction accuracy metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy import stats
from scipy.optimize import minimize
import logging

from .models import (
    Risk, ProbabilityDistribution, DistributionType, RiskCategory,
    ValidationResult, SimulationResults
)

logger = logging.getLogger(__name__)


@dataclass
class ProjectOutcome:
    """Represents the actual outcome of a completed project."""
    project_id: str
    project_type: str
    completion_date: datetime
    actual_cost: float
    actual_duration: float  # days
    baseline_cost: float
    baseline_duration: float
    risk_outcomes: Dict[str, float]  # risk_id -> actual_impact
    project_characteristics: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate project outcome data."""
        if self.actual_cost < 0:
            raise ValueError("Actual cost must be non-negative")
        if self.actual_duration < 0:
            raise ValueError("Actual duration must be non-negative")
        if self.baseline_cost < 0:
            raise ValueError("Baseline cost must be non-negative")
        if self.baseline_duration < 0:
            raise ValueError("Baseline duration must be non-negative")


@dataclass
class CalibrationResult:
    """Result of distribution calibration using historical data."""
    original_distribution: ProbabilityDistribution
    calibrated_distribution: ProbabilityDistribution
    goodness_of_fit: float  # p-value from statistical test
    sample_size: int
    calibration_method: str
    confidence_level: float
    
    def __post_init__(self):
        """Validate calibration result."""
        if self.sample_size <= 0:
            raise ValueError("Sample size must be positive")
        if not 0.0 <= self.confidence_level <= 1.0:
            raise ValueError("Confidence level must be between 0 and 1")


@dataclass
class PredictionAccuracyMetrics:
    """Metrics for assessing prediction accuracy."""
    mean_absolute_error: float
    root_mean_square_error: float
    mean_absolute_percentage_error: float
    r_squared: float
    prediction_intervals_coverage: Dict[float, float]  # confidence_level -> coverage_rate
    bias: float
    
    def __post_init__(self):
        """Validate accuracy metrics."""
        if self.mean_absolute_error < 0:
            raise ValueError("Mean absolute error must be non-negative")
        if self.root_mean_square_error < 0:
            raise ValueError("Root mean square error must be non-negative")


@dataclass
class ModelPerformanceTracker:
    """Tracks model performance over time."""
    model_id: str
    risk_category: RiskCategory
    accuracy_history: List[Tuple[datetime, PredictionAccuracyMetrics]]
    calibration_history: List[Tuple[datetime, CalibrationResult]]
    performance_trend: str  # "improving", "stable", "degrading"
    last_updated: datetime
    
    def __post_init__(self):
        """Validate performance tracker."""
        if not self.model_id:
            raise ValueError("Model ID cannot be empty")


class HistoricalDataCalibrator:
    """
    Calibrates probability distributions using completed project outcomes
    and tracks prediction accuracy metrics.
    """
    
    def __init__(self):
        """Initialize the historical data calibrator."""
        self.project_outcomes: List[ProjectOutcome] = []
        self.performance_trackers: Dict[str, ModelPerformanceTracker] = {}
        self.calibration_cache: Dict[str, CalibrationResult] = {}
        
    def add_project_outcome(self, outcome: ProjectOutcome) -> None:
        """
        Add a completed project outcome to the historical database.
        
        Args:
            outcome: The project outcome to add
        """
        if not isinstance(outcome, ProjectOutcome):
            raise ValueError("Outcome must be a ProjectOutcome instance")
            
        # Check for duplicate project IDs
        existing_ids = {po.project_id for po in self.project_outcomes}
        if outcome.project_id in existing_ids:
            logger.warning(f"Project {outcome.project_id} already exists, updating")
            self.project_outcomes = [po for po in self.project_outcomes 
                                   if po.project_id != outcome.project_id]
        
        self.project_outcomes.append(outcome)
        logger.info(f"Added project outcome for {outcome.project_id}")
    
    def calibrate_distribution(
        self, 
        risk: Risk, 
        project_type: Optional[str] = None,
        min_sample_size: int = 10
    ) -> CalibrationResult:
        """
        Calibrate a risk's probability distribution using historical data.
        
        Args:
            risk: The risk to calibrate
            project_type: Filter by project type (optional)
            min_sample_size: Minimum number of historical samples required
            
        Returns:
            CalibrationResult with the calibrated distribution
        """
        # Extract historical data for this risk
        historical_impacts = self._extract_risk_impacts(
            risk.id, risk.category, project_type
        )
        
        if len(historical_impacts) < min_sample_size:
            raise ValueError(
                f"Insufficient historical data: {len(historical_impacts)} samples "
                f"(minimum {min_sample_size} required)"
            )
        
        # Try different distribution types and select the best fit
        best_distribution = None
        best_fit_score = -np.inf
        best_method = None
        
        distribution_types = [
            DistributionType.NORMAL,
            DistributionType.LOGNORMAL,
            DistributionType.TRIANGULAR,
            DistributionType.BETA
        ]
        
        for dist_type in distribution_types:
            try:
                fitted_dist, fit_score, method = self._fit_distribution(
                    historical_impacts, dist_type
                )
                
                if fit_score > best_fit_score:
                    best_distribution = fitted_dist
                    best_fit_score = fit_score
                    best_method = method
                    
            except Exception as e:
                logger.debug(f"Failed to fit {dist_type}: {e}")
                continue
        
        if best_distribution is None:
            raise ValueError("Could not fit any distribution to historical data")
        
        # Perform goodness-of-fit test
        goodness_of_fit = self._goodness_of_fit_test(
            historical_impacts, best_distribution
        )
        
        calibration_result = CalibrationResult(
            original_distribution=risk.probability_distribution,
            calibrated_distribution=best_distribution,
            goodness_of_fit=goodness_of_fit,
            sample_size=len(historical_impacts),
            calibration_method=best_method,
            confidence_level=0.95
        )
        
        # Cache the result
        cache_key = f"{risk.id}_{project_type or 'all'}"
        self.calibration_cache[cache_key] = calibration_result
        
        logger.info(
            f"Calibrated distribution for risk {risk.id} using {len(historical_impacts)} samples"
        )
        
        return calibration_result
    
    def calculate_prediction_accuracy(
        self, 
        predicted_results: SimulationResults,
        actual_outcome: ProjectOutcome
    ) -> PredictionAccuracyMetrics:
        """
        Calculate prediction accuracy metrics by comparing simulation results
        with actual project outcomes.
        
        Args:
            predicted_results: Results from Monte Carlo simulation
            actual_outcome: Actual project outcome
            
        Returns:
            PredictionAccuracyMetrics with accuracy measures
        """
        # Extract predicted values (using median as point estimate)
        predicted_cost = np.median(predicted_results.cost_outcomes)
        predicted_duration = np.median(predicted_results.schedule_outcomes)
        
        # Calculate error metrics
        cost_error = abs(predicted_cost - actual_outcome.actual_cost)
        duration_error = abs(predicted_duration - actual_outcome.actual_duration)
        
        # Mean Absolute Error (average of cost and duration errors)
        mae = (cost_error + duration_error) / 2
        
        # Root Mean Square Error
        rmse = np.sqrt((cost_error**2 + duration_error**2) / 2)
        
        # Mean Absolute Percentage Error
        cost_mape = abs(predicted_cost - actual_outcome.actual_cost) / actual_outcome.actual_cost * 100
        duration_mape = abs(predicted_duration - actual_outcome.actual_duration) / actual_outcome.actual_duration * 100
        mape = (cost_mape + duration_mape) / 2
        
        # R-squared (simplified for single prediction)
        cost_variance = np.var(predicted_results.cost_outcomes)
        duration_variance = np.var(predicted_results.schedule_outcomes)
        total_variance = (cost_variance + duration_variance) / 2
        
        prediction_variance = (cost_error**2 + duration_error**2) / 2
        r_squared = max(0, 1 - (prediction_variance / total_variance)) if total_variance > 0 else 0
        
        # Prediction interval coverage
        coverage = self._calculate_prediction_interval_coverage(
            predicted_results, actual_outcome
        )
        
        # Bias (positive means over-prediction, negative means under-prediction)
        cost_bias = predicted_cost - actual_outcome.actual_cost
        duration_bias = predicted_duration - actual_outcome.actual_duration
        bias = (cost_bias + duration_bias) / 2
        
        return PredictionAccuracyMetrics(
            mean_absolute_error=mae,
            root_mean_square_error=rmse,
            mean_absolute_percentage_error=mape,
            r_squared=r_squared,
            prediction_intervals_coverage=coverage,
            bias=bias
        )
    
    def track_model_performance(
        self, 
        model_id: str,
        risk_category: RiskCategory,
        accuracy_metrics: PredictionAccuracyMetrics,
        calibration_result: Optional[CalibrationResult] = None
    ) -> None:
        """
        Track model performance over time.
        
        Args:
            model_id: Identifier for the model being tracked
            risk_category: Category of risks this model handles
            accuracy_metrics: Latest accuracy metrics
            calibration_result: Latest calibration result (optional)
        """
        current_time = datetime.now()
        
        if model_id not in self.performance_trackers:
            self.performance_trackers[model_id] = ModelPerformanceTracker(
                model_id=model_id,
                risk_category=risk_category,
                accuracy_history=[],
                calibration_history=[],
                performance_trend="stable",
                last_updated=current_time
            )
        
        tracker = self.performance_trackers[model_id]
        
        # Add accuracy metrics to history
        tracker.accuracy_history.append((current_time, accuracy_metrics))
        
        # Add calibration result if provided
        if calibration_result:
            tracker.calibration_history.append((current_time, calibration_result))
        
        # Update performance trend
        tracker.performance_trend = self._assess_performance_trend(tracker)
        tracker.last_updated = current_time
        
        logger.info(f"Updated performance tracking for model {model_id}")
    
    def get_model_performance(self, model_id: str) -> Optional[ModelPerformanceTracker]:
        """
        Get performance tracking information for a model.
        
        Args:
            model_id: Identifier for the model
            
        Returns:
            ModelPerformanceTracker if found, None otherwise
        """
        return self.performance_trackers.get(model_id)
    
    def _extract_risk_impacts(
        self, 
        risk_id: str, 
        risk_category: RiskCategory,
        project_type: Optional[str] = None
    ) -> List[float]:
        """Extract historical impact data for a specific risk."""
        impacts = []
        
        for outcome in self.project_outcomes:
            # Filter by project type if specified
            if project_type and outcome.project_type != project_type:
                continue
            
            # Look for exact risk ID match first
            if risk_id in outcome.risk_outcomes:
                impacts.append(outcome.risk_outcomes[risk_id])
            else:
                # If no exact match, look for similar risks in the same category
                # This is a simplified approach - in practice, you might use more
                # sophisticated matching based on risk characteristics
                for outcome_risk_id, impact in outcome.risk_outcomes.items():
                    if outcome_risk_id.startswith(risk_category.value):
                        impacts.append(impact)
        
        return impacts
    
    def _fit_distribution(
        self, 
        data: List[float], 
        distribution_type: DistributionType
    ) -> Tuple[ProbabilityDistribution, float, str]:
        """Fit a specific distribution type to historical data."""
        data_array = np.array(data)
        
        if distribution_type == DistributionType.NORMAL:
            mean, std = stats.norm.fit(data_array)
            fitted_dist = ProbabilityDistribution(
                distribution_type=DistributionType.NORMAL,
                parameters={'mean': mean, 'std': std}
            )
            # Use negative log-likelihood as fit score (higher is better)
            fit_score = -stats.norm.nnlf((mean, std), data_array)
            method = "maximum_likelihood"
            
        elif distribution_type == DistributionType.LOGNORMAL:
            # Ensure all data is positive for lognormal
            if np.any(data_array <= 0):
                raise ValueError("Lognormal distribution requires positive data")
            
            shape, loc, scale = stats.lognorm.fit(data_array)
            fitted_dist = ProbabilityDistribution(
                distribution_type=DistributionType.LOGNORMAL,
                parameters={'mu': np.log(scale), 'sigma': shape}
            )
            fit_score = -stats.lognorm.nnlf((shape, loc, scale), data_array)
            method = "maximum_likelihood"
            
        elif distribution_type == DistributionType.TRIANGULAR:
            # Use method of moments for triangular distribution
            min_val = np.min(data_array)
            max_val = np.max(data_array)
            mean_val = np.mean(data_array)
            
            # Estimate mode using method of moments
            # For triangular: mean = (min + mode + max) / 3
            mode = 3 * mean_val - min_val - max_val
            mode = np.clip(mode, min_val, max_val)  # Ensure mode is within bounds
            
            fitted_dist = ProbabilityDistribution(
                distribution_type=DistributionType.TRIANGULAR,
                parameters={'min': min_val, 'mode': mode, 'max': max_val}
            )
            
            # Calculate fit score using KS test
            ks_stat, _ = stats.kstest(data_array, 
                                   lambda x: stats.triang.cdf(x, (mode-min_val)/(max_val-min_val), 
                                                             loc=min_val, scale=max_val-min_val))
            fit_score = -ks_stat  # Negative because lower KS stat is better
            method = "method_of_moments"
            
        elif distribution_type == DistributionType.BETA:
            # Fit beta distribution (scaled to data range)
            min_val = np.min(data_array)
            max_val = np.max(data_array)
            
            # Normalize data to [0, 1] for beta fitting
            normalized_data = (data_array - min_val) / (max_val - min_val)
            
            alpha, beta, loc, scale = stats.beta.fit(normalized_data)
            
            fitted_dist = ProbabilityDistribution(
                distribution_type=DistributionType.BETA,
                parameters={'alpha': alpha, 'beta': beta},
                bounds=(min_val, max_val)
            )
            fit_score = -stats.beta.nnlf((alpha, beta, loc, scale), normalized_data)
            method = "maximum_likelihood"
            
        else:
            raise ValueError(f"Unsupported distribution type: {distribution_type}")
        
        return fitted_dist, fit_score, method
    
    def _goodness_of_fit_test(
        self, 
        data: List[float], 
        distribution: ProbabilityDistribution
    ) -> float:
        """Perform goodness-of-fit test for a distribution."""
        data_array = np.array(data)
        
        if distribution.distribution_type == DistributionType.NORMAL:
            mean = distribution.parameters['mean']
            std = distribution.parameters['std']
            _, p_value = stats.kstest(data_array, 
                                    lambda x: stats.norm.cdf(x, mean, std))
            
        elif distribution.distribution_type == DistributionType.LOGNORMAL:
            mu = distribution.parameters['mu']
            sigma = distribution.parameters['sigma']
            _, p_value = stats.kstest(data_array,
                                    lambda x: stats.lognorm.cdf(x, sigma, scale=np.exp(mu)))
            
        elif distribution.distribution_type == DistributionType.TRIANGULAR:
            min_val = distribution.parameters['min']
            mode = distribution.parameters['mode']
            max_val = distribution.parameters['max']
            c = (mode - min_val) / (max_val - min_val)
            _, p_value = stats.kstest(data_array,
                                    lambda x: stats.triang.cdf(x, c, loc=min_val, scale=max_val-min_val))
            
        elif distribution.distribution_type == DistributionType.BETA:
            alpha = distribution.parameters['alpha']
            beta = distribution.parameters['beta']
            min_val, max_val = distribution.bounds or (0, 1)
            
            # Normalize data for beta test
            normalized_data = (data_array - min_val) / (max_val - min_val)
            _, p_value = stats.kstest(normalized_data,
                                    lambda x: stats.beta.cdf(x, alpha, beta))
            
        else:
            # Default to Anderson-Darling test
            _, _, p_value = stats.anderson(data_array)
            p_value = p_value[2] if len(p_value) > 2 else 0.05  # Use 5% significance level
        
        return p_value
    
    def _calculate_prediction_interval_coverage(
        self, 
        predicted_results: SimulationResults,
        actual_outcome: ProjectOutcome
    ) -> Dict[float, float]:
        """Calculate prediction interval coverage rates."""
        coverage = {}
        
        confidence_levels = [0.80, 0.90, 0.95]
        
        for conf_level in confidence_levels:
            alpha = 1 - conf_level
            lower_percentile = (alpha / 2) * 100
            upper_percentile = (1 - alpha / 2) * 100
            
            # Cost coverage
            cost_lower = np.percentile(predicted_results.cost_outcomes, lower_percentile)
            cost_upper = np.percentile(predicted_results.cost_outcomes, upper_percentile)
            cost_covered = cost_lower <= actual_outcome.actual_cost <= cost_upper
            
            # Schedule coverage
            schedule_lower = np.percentile(predicted_results.schedule_outcomes, lower_percentile)
            schedule_upper = np.percentile(predicted_results.schedule_outcomes, upper_percentile)
            schedule_covered = schedule_lower <= actual_outcome.actual_duration <= schedule_upper
            
            # Overall coverage (both cost and schedule must be covered)
            overall_coverage = 1.0 if (cost_covered and schedule_covered) else 0.0
            coverage[conf_level] = overall_coverage
        
        return coverage
    
    def _assess_performance_trend(self, tracker: ModelPerformanceTracker) -> str:
        """Assess whether model performance is improving, stable, or degrading."""
        if len(tracker.accuracy_history) < 3:
            return "stable"  # Not enough data to assess trend
        
        # Look at the last 3 accuracy measurements
        recent_metrics = tracker.accuracy_history[-3:]
        mae_values = [metrics.mean_absolute_error for _, metrics in recent_metrics]
        
        # Simple trend analysis based on MAE
        if mae_values[-1] < mae_values[0] * 0.9:  # 10% improvement
            return "improving"
        elif mae_values[-1] > mae_values[0] * 1.1:  # 10% degradation
            return "degrading"
        else:
            return "stable"