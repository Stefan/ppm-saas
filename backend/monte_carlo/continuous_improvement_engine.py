"""
Continuous Improvement Engine for Monte Carlo Risk Simulations.

This module provides functionality for automatic parameter suggestions,
recommendation systems, and continuous learning from historical data.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
import numpy as np
from scipy import stats
import logging
from collections import defaultdict

from .models import (
    Risk, ProbabilityDistribution, DistributionType, RiskCategory,
    ImpactType, ValidationResult
)
from .historical_data_calibrator import (
    HistoricalDataCalibrator, ProjectOutcome, CalibrationResult,
    PredictionAccuracyMetrics
)

logger = logging.getLogger(__name__)


@dataclass
class ProjectSimilarity:
    """Represents similarity between projects for parameter suggestion."""
    project_id: str
    similarity_score: float  # 0.0 to 1.0
    matching_characteristics: List[str]
    risk_pattern_overlap: float
    
    def __post_init__(self):
        """Validate project similarity."""
        if not 0.0 <= self.similarity_score <= 1.0:
            raise ValueError("Similarity score must be between 0 and 1")
        if not 0.0 <= self.risk_pattern_overlap <= 1.0:
            raise ValueError("Risk pattern overlap must be between 0 and 1")


@dataclass
class ParameterSuggestion:
    """Represents a suggested parameter improvement."""
    risk_id: str
    parameter_name: str
    current_value: float
    suggested_value: float
    confidence: float  # 0.0 to 1.0
    reasoning: str
    supporting_projects: List[str]
    expected_improvement: float  # expected reduction in prediction error
    
    def __post_init__(self):
        """Validate parameter suggestion."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0 and 1")


@dataclass
class StandardAssumptionUpdate:
    """Represents a recommended update to standard risk assumptions."""
    risk_category: RiskCategory
    assumption_type: str  # "distribution_type", "parameter_default", "correlation"
    current_assumption: Any
    recommended_assumption: Any
    evidence_strength: float  # 0.0 to 1.0
    affected_project_types: List[str]
    implementation_priority: str  # "high", "medium", "low"
    
    def __post_init__(self):
        """Validate standard assumption update."""
        if not 0.0 <= self.evidence_strength <= 1.0:
            raise ValueError("Evidence strength must be between 0 and 1")
        if self.implementation_priority not in ["high", "medium", "low"]:
            raise ValueError("Implementation priority must be high, medium, or low")


@dataclass
class ImprovementMetrics:
    """Metrics tracking improvement over time."""
    metric_name: str
    baseline_value: float
    current_value: float
    improvement_percentage: float
    trend_direction: str  # "improving", "stable", "degrading"
    measurement_period: timedelta
    last_updated: datetime
    
    def __post_init__(self):
        """Validate improvement metrics."""
        if self.trend_direction not in ["improving", "stable", "degrading"]:
            raise ValueError("Trend direction must be improving, stable, or degrading")


class ContinuousImprovementEngine:
    """
    Engine for continuous improvement of risk simulation models through
    automatic parameter suggestions and recommendation systems.
    """
    
    def __init__(self, historical_calibrator: HistoricalDataCalibrator):
        """
        Initialize the continuous improvement engine.
        
        Args:
            historical_calibrator: The historical data calibrator instance
        """
        self.historical_calibrator = historical_calibrator
        self.parameter_suggestions: Dict[str, List[ParameterSuggestion]] = defaultdict(list)
        self.standard_assumption_updates: List[StandardAssumptionUpdate] = []
        self.improvement_metrics: List[ImprovementMetrics] = []  # Changed to list to handle duplicates
        self.similarity_cache: Dict[frozenset, float] = {}  # Updated type hint
        
    def suggest_parameters_for_similar_projects(
        self,
        target_project_characteristics: Dict[str, Any],
        target_risks: List[Risk],
        min_similarity_threshold: float = 0.7,
        max_suggestions: int = 10
    ) -> List[ParameterSuggestion]:
        """
        Suggest improved distribution parameters based on similar historical projects.
        
        Args:
            target_project_characteristics: Characteristics of the target project
            target_risks: List of risks for the target project
            min_similarity_threshold: Minimum similarity score to consider
            max_suggestions: Maximum number of suggestions to return
            
        Returns:
            List of parameter suggestions ordered by confidence
        """
        suggestions = []
        
        # Find similar projects
        similar_projects = self._find_similar_projects(
            target_project_characteristics, min_similarity_threshold
        )
        
        if not similar_projects:
            logger.info("No similar projects found for parameter suggestions")
            return suggestions
        
        # Analyze each risk for potential improvements
        for risk in target_risks:
            risk_suggestions = self._analyze_risk_for_improvements(
                risk, similar_projects, target_project_characteristics
            )
            suggestions.extend(risk_suggestions)
        
        # Sort by confidence and limit results
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        suggestions = suggestions[:max_suggestions]
        
        # Cache suggestions for this project
        project_key = self._generate_project_key(target_project_characteristics)
        self.parameter_suggestions[project_key] = suggestions
        
        logger.info(f"Generated {len(suggestions)} parameter suggestions")
        return suggestions
    
    def recommend_standard_assumption_updates(
        self,
        min_evidence_threshold: float = 0.8,
        min_project_count: int = 5
    ) -> List[StandardAssumptionUpdate]:
        """
        Recommend updates to standard risk assumptions based on accumulated evidence.
        
        Args:
            min_evidence_threshold: Minimum evidence strength to recommend update
            min_project_count: Minimum number of projects required for recommendation
            
        Returns:
            List of recommended standard assumption updates
        """
        recommendations = []
        
        # Analyze distribution type preferences by category
        distribution_recommendations = self._analyze_distribution_preferences(
            min_evidence_threshold, min_project_count
        )
        recommendations.extend(distribution_recommendations)
        
        # Analyze parameter defaults by category
        parameter_recommendations = self._analyze_parameter_defaults(
            min_evidence_threshold, min_project_count
        )
        recommendations.extend(parameter_recommendations)
        
        # Analyze correlation patterns
        correlation_recommendations = self._analyze_correlation_patterns(
            min_evidence_threshold, min_project_count
        )
        recommendations.extend(correlation_recommendations)
        
        # Sort by implementation priority and evidence strength
        recommendations.sort(
            key=lambda x: (
                {"high": 3, "medium": 2, "low": 1}[x.implementation_priority],
                x.evidence_strength
            ),
            reverse=True
        )
        
        self.standard_assumption_updates = recommendations
        logger.info(f"Generated {len(recommendations)} standard assumption updates")
        
        return recommendations
    
    def track_improvement_metrics(
        self,
        metric_name: str,
        current_value: float,
        baseline_value: Optional[float] = None,
        measurement_period: Optional[timedelta] = None
    ) -> ImprovementMetrics:
        """
        Track improvement metrics over time.
        
        Args:
            metric_name: Name of the metric being tracked
            current_value: Current value of the metric
            baseline_value: Baseline value for comparison (optional)
            measurement_period: Period over which improvement is measured
            
        Returns:
            ImprovementMetrics instance
        """
        current_time = datetime.now()
        
        # Find existing metric with the same name (most recent one)
        existing_metric = None
        for metric in reversed(self.improvement_metrics):
            if metric.metric_name == metric_name:
                existing_metric = metric
                break
        
        if existing_metric:
            baseline = baseline_value or existing_metric.baseline_value
        else:
            baseline = baseline_value or current_value
        
        # Calculate improvement percentage
        if baseline != 0:
            improvement_percentage = ((baseline - current_value) / abs(baseline)) * 100
        else:
            improvement_percentage = 0.0
        
        # Determine trend direction
        if existing_metric:
            previous_value = existing_metric.current_value
            if current_value < previous_value * 0.95:  # 5% improvement threshold
                trend_direction = "improving"
            elif current_value > previous_value * 1.05:  # 5% degradation threshold
                trend_direction = "degrading"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "stable"
        
        # Create new metrics entry (always append, don't overwrite)
        metrics = ImprovementMetrics(
            metric_name=metric_name,
            baseline_value=baseline,
            current_value=current_value,
            improvement_percentage=improvement_percentage,
            trend_direction=trend_direction,
            measurement_period=measurement_period or timedelta(days=30),
            last_updated=current_time
        )
        
        self.improvement_metrics.append(metrics)
        logger.info(f"Added improvement metrics for {metric_name}")
        
        return metrics
    
    def get_improvement_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all improvement activities and metrics.
        
        Returns:
            Dictionary containing improvement summary
        """
        summary = {
            "total_parameter_suggestions": sum(
                len(suggestions) for suggestions in self.parameter_suggestions.values()
            ),
            "total_standard_updates": len(self.standard_assumption_updates),
            "tracked_metrics": len(self.improvement_metrics),  # Total count of all metrics
            "metrics_by_trend": {
                "improving": 0,
                "stable": 0,
                "degrading": 0
            },
            "high_priority_updates": 0,
            "recent_suggestions": [],
            "top_improvements": []
        }
        
        # Count metrics by trend (all metrics, including duplicates)
        for metrics in self.improvement_metrics:
            summary["metrics_by_trend"][metrics.trend_direction] += 1
        
        # Count high priority updates
        summary["high_priority_updates"] = sum(
            1 for update in self.standard_assumption_updates
            if update.implementation_priority == "high"
        )
        
        # Get recent suggestions (last 7 days)
        recent_cutoff = datetime.now() - timedelta(days=7)
        for project_key, suggestions in self.parameter_suggestions.items():
            for suggestion in suggestions:
                if suggestion.confidence > 0.8:  # High confidence suggestions
                    summary["recent_suggestions"].append({
                        "project": project_key,
                        "risk_id": suggestion.risk_id,
                        "parameter": suggestion.parameter_name,
                        "confidence": suggestion.confidence
                    })
        
        # Get top improvements
        for metrics in self.improvement_metrics:
            if metrics.improvement_percentage > 5:  # At least 5% improvement
                summary["top_improvements"].append({
                    "metric": metrics.metric_name,
                    "improvement": metrics.improvement_percentage,
                    "trend": metrics.trend_direction
                })
        
        # Sort top improvements by percentage
        summary["top_improvements"].sort(
            key=lambda x: x["improvement"], reverse=True
        )
        summary["top_improvements"] = summary["top_improvements"][:5]
        
        return summary
    
    def _find_similar_projects(
        self,
        target_characteristics: Dict[str, Any],
        min_similarity_threshold: float
    ) -> List[ProjectSimilarity]:
        """Find projects similar to the target project."""
        similar_projects = []
        
        for outcome in self.historical_calibrator.project_outcomes:
            similarity_score = self._calculate_project_similarity(
                target_characteristics, outcome.project_characteristics
            )
            
            if similarity_score >= min_similarity_threshold:
                # Calculate risk pattern overlap
                risk_overlap = self._calculate_risk_pattern_overlap(
                    target_characteristics, outcome
                )
                
                # Find matching characteristics
                matching_chars = self._find_matching_characteristics(
                    target_characteristics, outcome.project_characteristics
                )
                
                similar_project = ProjectSimilarity(
                    project_id=outcome.project_id,
                    similarity_score=similarity_score,
                    matching_characteristics=matching_chars,
                    risk_pattern_overlap=risk_overlap
                )
                similar_projects.append(similar_project)
        
        # Sort by similarity score
        similar_projects.sort(key=lambda x: x.similarity_score, reverse=True)
        return similar_projects
    
    def _calculate_project_similarity(
        self,
        target_chars: Dict[str, Any],
        project_chars: Dict[str, Any]
    ) -> float:
        """Calculate similarity score between two projects."""
        if not target_chars or not project_chars:
            return 0.0
        
        # Create a truly symmetric cache key by using frozensets
        target_items = frozenset(target_chars.items())
        project_items = frozenset(project_chars.items())
        cache_key = frozenset([target_items, project_items])
        
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
        
        # Calculate similarity based on common characteristics
        common_keys = set(target_chars.keys()) & set(project_chars.keys())
        if not common_keys:
            similarity = 0.0
        else:
            matches = 0
            total = len(common_keys)
            
            for key in common_keys:
                target_val = target_chars[key]
                project_val = project_chars[key]
                
                if isinstance(target_val, (int, float)) and isinstance(project_val, (int, float)):
                    # Numerical similarity (within 20% is considered similar)
                    if target_val != 0:
                        diff_ratio = abs(target_val - project_val) / abs(target_val)
                        if diff_ratio <= 0.2:
                            matches += 1
                    elif project_val == 0:
                        matches += 1
                elif target_val == project_val:
                    # Exact match for non-numerical values
                    matches += 1
            
            similarity = matches / total
        
        # Cache the result with the symmetric key
        self.similarity_cache[cache_key] = similarity
        return similarity
    
    def _calculate_risk_pattern_overlap(
        self,
        target_characteristics: Dict[str, Any],
        historical_outcome: ProjectOutcome
    ) -> float:
        """Calculate overlap in risk patterns between target and historical project."""
        # This is a simplified implementation
        # In practice, you might analyze risk categories, impact types, etc.
        
        target_project_type = target_characteristics.get('project_type', 'unknown')
        historical_project_type = historical_outcome.project_type
        
        if target_project_type == historical_project_type:
            return 1.0
        elif target_project_type in ['construction', 'infrastructure'] and \
             historical_project_type in ['construction', 'infrastructure']:
            return 0.8
        elif target_project_type in ['software', 'research'] and \
             historical_project_type in ['software', 'research']:
            return 0.7
        else:
            return 0.3
    
    def _find_matching_characteristics(
        self,
        target_chars: Dict[str, Any],
        project_chars: Dict[str, Any]
    ) -> List[str]:
        """Find characteristics that match between projects."""
        matching = []
        
        for key in set(target_chars.keys()) & set(project_chars.keys()):
            if target_chars[key] == project_chars[key]:
                matching.append(key)
        
        return matching
    
    def _analyze_risk_for_improvements(
        self,
        risk: Risk,
        similar_projects: List[ProjectSimilarity],
        target_characteristics: Dict[str, Any]
    ) -> List[ParameterSuggestion]:
        """Analyze a specific risk for potential parameter improvements."""
        suggestions = []
        
        # Collect historical data for this risk from similar projects
        historical_impacts = []
        supporting_projects = []
        
        for similar_project in similar_projects:
            outcome = next(
                (po for po in self.historical_calibrator.project_outcomes
                 if po.project_id == similar_project.project_id),
                None
            )
            
            if outcome and risk.id in outcome.risk_outcomes:
                historical_impacts.append(outcome.risk_outcomes[risk.id])
                supporting_projects.append(similar_project.project_id)
        
        if len(historical_impacts) < 3:  # Need minimum data for suggestions
            return suggestions
        
        # Analyze current vs. historical distribution parameters
        historical_array = np.array(historical_impacts)
        
        # Suggest mean adjustment for normal distributions
        if risk.probability_distribution.distribution_type == DistributionType.NORMAL:
            current_mean = risk.probability_distribution.parameters['mean']
            historical_mean = np.mean(historical_array)
            
            if abs(current_mean - historical_mean) > abs(current_mean) * 0.1:  # 10% difference
                confidence = min(0.9, len(historical_impacts) / 10.0)  # Higher confidence with more data
                expected_improvement = abs(current_mean - historical_mean) / abs(current_mean) * 10
                
                suggestion = ParameterSuggestion(
                    risk_id=risk.id,
                    parameter_name='mean',
                    current_value=current_mean,
                    suggested_value=historical_mean,
                    confidence=confidence,
                    reasoning=f"Historical data from {len(historical_impacts)} similar projects suggests different mean",
                    supporting_projects=supporting_projects,
                    expected_improvement=expected_improvement
                )
                suggestions.append(suggestion)
            
            # Suggest standard deviation adjustment
            current_std = risk.probability_distribution.parameters['std']
            historical_std = np.std(historical_array)
            
            if abs(current_std - historical_std) > current_std * 0.15:  # 15% difference
                confidence = min(0.8, len(historical_impacts) / 12.0)
                expected_improvement = abs(current_std - historical_std) / current_std * 8
                
                suggestion = ParameterSuggestion(
                    risk_id=risk.id,
                    parameter_name='std',
                    current_value=current_std,
                    suggested_value=historical_std,
                    confidence=confidence,
                    reasoning=f"Historical variability from {len(historical_impacts)} similar projects suggests different standard deviation",
                    supporting_projects=supporting_projects,
                    expected_improvement=expected_improvement
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    def _analyze_distribution_preferences(
        self,
        min_evidence_threshold: float,
        min_project_count: int
    ) -> List[StandardAssumptionUpdate]:
        """Analyze which distribution types work best for each risk category."""
        recommendations = []
        
        # Group calibration results by risk category
        category_distributions = defaultdict(list)
        
        for calibration_result in self.historical_calibrator.calibration_cache.values():
            # Extract risk category from calibration context (simplified)
            # In practice, you'd need to track this more systematically
            dist_type = calibration_result.calibrated_distribution.distribution_type
            goodness_of_fit = calibration_result.goodness_of_fit
            
            # Assume we can infer category from distribution characteristics
            # This is simplified - in practice you'd track this explicitly
            category = RiskCategory.COST  # Placeholder
            
            category_distributions[category].append((dist_type, goodness_of_fit))
        
        # Analyze each category
        for category, distributions in category_distributions.items():
            if len(distributions) < min_project_count:
                continue
            
            # Find the most successful distribution type
            dist_performance = defaultdict(list)
            for dist_type, goodness in distributions:
                dist_performance[dist_type].append(goodness)
            
            # Calculate average performance for each distribution type
            avg_performance = {}
            for dist_type, goodness_values in dist_performance.items():
                avg_performance[dist_type] = np.mean(goodness_values)
            
            # Find the best performing distribution
            best_dist = max(avg_performance.items(), key=lambda x: x[1])
            best_dist_type, best_performance = best_dist
            
            if best_performance >= min_evidence_threshold:
                recommendation = StandardAssumptionUpdate(
                    risk_category=category,
                    assumption_type="distribution_type",
                    current_assumption=DistributionType.NORMAL,  # Assume normal is current default
                    recommended_assumption=best_dist_type,
                    evidence_strength=best_performance,
                    affected_project_types=["all"],
                    implementation_priority="medium"
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def _analyze_parameter_defaults(
        self,
        min_evidence_threshold: float,
        min_project_count: int
    ) -> List[StandardAssumptionUpdate]:
        """Analyze default parameter values for each risk category."""
        recommendations = []
        
        # This is a simplified implementation
        # In practice, you'd analyze parameter distributions across categories
        
        return recommendations
    
    def _analyze_correlation_patterns(
        self,
        min_evidence_threshold: float,
        min_project_count: int
    ) -> List[StandardAssumptionUpdate]:
        """Analyze common correlation patterns between risk types."""
        recommendations = []
        
        # This is a simplified implementation
        # In practice, you'd analyze correlation matrices from historical projects
        
        return recommendations
    
    def _generate_project_key(self, characteristics: Dict[str, Any]) -> str:
        """Generate a unique key for a project based on its characteristics."""
        # Create a stable key from project characteristics
        sorted_items = sorted(characteristics.items())
        return str(hash(tuple(sorted_items)))