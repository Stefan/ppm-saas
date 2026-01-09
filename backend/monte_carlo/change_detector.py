"""
Change Detection and Validation Guidance for Monte Carlo Risk Simulations.

This module provides model assumption change detection and validation area highlighting
with recommendations for maintaining model accuracy and reliability.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
import numpy as np
from enum import Enum, IntEnum

from .models import (
    Risk, ProbabilityDistribution, CorrelationMatrix, ValidationResult,
    SimulationResults, DistributionType
)


class ChangeType(Enum):
    """Types of changes that can be detected in model assumptions."""
    DISTRIBUTION_PARAMETERS = "distribution_parameters"
    DISTRIBUTION_TYPE = "distribution_type"
    CORRELATION_COEFFICIENTS = "correlation_coefficients"
    RISK_ADDED = "risk_added"
    RISK_REMOVED = "risk_removed"
    BASELINE_IMPACT = "baseline_impact"
    RISK_CATEGORY = "risk_category"
    IMPACT_TYPE = "impact_type"


class ChangeSeverity(IntEnum):
    """Severity levels for detected changes."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class DetectedChange:
    """Represents a detected change in model assumptions."""
    change_type: ChangeType
    severity: ChangeSeverity
    description: str
    affected_component: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    impact_assessment: str = ""
    recommendations: List[str] = field(default_factory=list)
    validation_areas: List[str] = field(default_factory=list)


@dataclass
class ValidationGuidance:
    """Guidance for validation areas that need attention."""
    area: str
    priority: str  # "high", "medium", "low"
    description: str
    recommended_actions: List[str]
    validation_methods: List[str]
    expected_effort: str  # "low", "medium", "high"


@dataclass
class ChangeDetectionReport:
    """Comprehensive report of detected changes and validation guidance."""
    timestamp: datetime
    total_changes: int
    changes_by_severity: Dict[ChangeSeverity, int]
    detected_changes: List[DetectedChange]
    validation_guidance: List[ValidationGuidance]
    overall_risk_assessment: str
    recommended_next_steps: List[str]


class ModelChangeDetector:
    """
    Detector for model assumption changes with validation guidance.
    
    Provides comprehensive change detection capabilities including parameter changes,
    structural changes, and correlation modifications with severity assessment
    and validation recommendations.
    """
    
    def __init__(self, sensitivity_threshold: float = 1e-6):
        """
        Initialize the change detector.
        
        Args:
            sensitivity_threshold: Threshold for detecting parameter changes
        """
        self.sensitivity_threshold = sensitivity_threshold
        self._change_history: List[ChangeDetectionReport] = []
        self._baseline_models: Dict[str, Dict[str, Any]] = {}
    
    def detect_changes(
        self,
        current_risks: List[Risk],
        previous_risks: Optional[List[Risk]] = None,
        current_correlations: Optional[CorrelationMatrix] = None,
        previous_correlations: Optional[CorrelationMatrix] = None,
        baseline_model_id: Optional[str] = None
    ) -> ChangeDetectionReport:
        """
        Detect changes between current and previous model configurations.
        
        Args:
            current_risks: Current list of risks
            previous_risks: Previous list of risks for comparison
            current_correlations: Current correlation matrix
            previous_correlations: Previous correlation matrix
            baseline_model_id: Optional ID for baseline model comparison
            
        Returns:
            ChangeDetectionReport with detected changes and guidance
        """
        detected_changes = []
        
        # Use baseline model if no previous model provided
        if previous_risks is None and baseline_model_id:
            baseline_data = self._baseline_models.get(baseline_model_id)
            if baseline_data:
                previous_risks = baseline_data.get('risks')
                previous_correlations = baseline_data.get('correlations')
        
        if previous_risks is not None:
            # Detect risk-level changes
            risk_changes = self._detect_risk_changes(current_risks, previous_risks)
            detected_changes.extend(risk_changes)
        
        if current_correlations and previous_correlations:
            # Detect correlation changes
            correlation_changes = self._detect_correlation_changes(
                current_correlations, previous_correlations
            )
            detected_changes.extend(correlation_changes)
        
        # Generate validation guidance based on detected changes
        validation_guidance = self._generate_validation_guidance(detected_changes)
        
        # Assess overall risk and provide recommendations
        overall_assessment, next_steps = self._assess_overall_impact(detected_changes)
        
        # Count changes by severity
        changes_by_severity = {severity: 0 for severity in ChangeSeverity}
        for change in detected_changes:
            changes_by_severity[change.severity] += 1
        
        report = ChangeDetectionReport(
            timestamp=datetime.now(),
            total_changes=len(detected_changes),
            changes_by_severity=changes_by_severity,
            detected_changes=detected_changes,
            validation_guidance=validation_guidance,
            overall_risk_assessment=overall_assessment,
            recommended_next_steps=next_steps
        )
        
        # Store in history
        self._change_history.append(report)
        
        return report
    
    def _detect_risk_changes(
        self,
        current_risks: List[Risk],
        previous_risks: List[Risk]
    ) -> List[DetectedChange]:
        """Detect changes in individual risks."""
        changes = []
        
        # Create lookup dictionaries
        current_risk_dict = {risk.id: risk for risk in current_risks}
        previous_risk_dict = {risk.id: risk for risk in previous_risks}
        
        current_ids = set(current_risk_dict.keys())
        previous_ids = set(previous_risk_dict.keys())
        
        # Detect added risks
        added_risks = current_ids - previous_ids
        for risk_id in added_risks:
            changes.append(DetectedChange(
                change_type=ChangeType.RISK_ADDED,
                severity=ChangeSeverity.MEDIUM,
                description=f"New risk '{risk_id}' added to model",
                affected_component=risk_id,
                new_value=current_risk_dict[risk_id].name,
                impact_assessment="Addition of new risk may affect overall uncertainty and correlations",
                recommendations=[
                    "Validate new risk parameters against historical data",
                    "Review correlations with existing risks",
                    "Update simulation iterations if needed"
                ],
                validation_areas=["Risk parameters", "Correlation structure", "Simulation convergence"]
            ))
        
        # Detect removed risks
        removed_risks = previous_ids - current_ids
        for risk_id in removed_risks:
            changes.append(DetectedChange(
                change_type=ChangeType.RISK_REMOVED,
                severity=ChangeSeverity.HIGH,
                description=f"Risk '{risk_id}' removed from model",
                affected_component=risk_id,
                old_value=previous_risk_dict[risk_id].name,
                impact_assessment="Removal of risk may significantly change overall uncertainty profile",
                recommendations=[
                    "Verify removal is intentional",
                    "Update correlation matrix to remove references",
                    "Re-validate overall model assumptions"
                ],
                validation_areas=["Model completeness", "Correlation matrix", "Overall uncertainty"]
            ))
        
        # Detect changes in common risks
        common_risks = current_ids & previous_ids
        for risk_id in common_risks:
            current_risk = current_risk_dict[risk_id]
            previous_risk = previous_risk_dict[risk_id]
            
            # Check distribution changes
            dist_changes = self._detect_distribution_changes(
                current_risk.probability_distribution,
                previous_risk.probability_distribution,
                risk_id
            )
            changes.extend(dist_changes)
            
            # Check baseline impact changes
            if abs(current_risk.baseline_impact - previous_risk.baseline_impact) > self.sensitivity_threshold:
                severity = self._assess_parameter_change_severity(
                    current_risk.baseline_impact,
                    previous_risk.baseline_impact
                )
                changes.append(DetectedChange(
                    change_type=ChangeType.BASELINE_IMPACT,
                    severity=severity,
                    description=f"Baseline impact changed for risk '{risk_id}'",
                    affected_component=risk_id,
                    old_value=previous_risk.baseline_impact,
                    new_value=current_risk.baseline_impact,
                    impact_assessment=f"Impact change of {abs(current_risk.baseline_impact - previous_risk.baseline_impact):.2f}",
                    recommendations=[
                        "Validate new baseline impact against recent data",
                        "Check if change affects risk ranking",
                        "Update risk mitigation strategies if needed"
                    ],
                    validation_areas=["Baseline impact validation", "Risk ranking", "Mitigation effectiveness"]
                ))
            
            # Check category changes
            if current_risk.category != previous_risk.category:
                changes.append(DetectedChange(
                    change_type=ChangeType.RISK_CATEGORY,
                    severity=ChangeSeverity.MEDIUM,
                    description=f"Risk category changed for '{risk_id}'",
                    affected_component=risk_id,
                    old_value=previous_risk.category.value,
                    new_value=current_risk.category.value,
                    impact_assessment="Category change may affect risk grouping and correlation assumptions",
                    recommendations=[
                        "Review correlation assumptions for new category",
                        "Validate category-specific default parameters",
                        "Update risk reporting and grouping"
                    ],
                    validation_areas=["Risk categorization", "Correlation assumptions", "Reporting structure"]
                ))
            
            # Check impact type changes
            if current_risk.impact_type != previous_risk.impact_type:
                changes.append(DetectedChange(
                    change_type=ChangeType.IMPACT_TYPE,
                    severity=ChangeSeverity.HIGH,
                    description=f"Impact type changed for '{risk_id}'",
                    affected_component=risk_id,
                    old_value=previous_risk.impact_type.value,
                    new_value=current_risk.impact_type.value,
                    impact_assessment="Impact type change significantly affects simulation calculations",
                    recommendations=[
                        "Verify impact type change is correct",
                        "Update cross-impact modeling if applicable",
                        "Re-validate simulation results"
                    ],
                    validation_areas=["Impact type validation", "Cross-impact modeling", "Simulation accuracy"]
                ))
        
        return changes
    
    def _detect_distribution_changes(
        self,
        current_dist: ProbabilityDistribution,
        previous_dist: ProbabilityDistribution,
        risk_id: str
    ) -> List[DetectedChange]:
        """Detect changes in probability distributions."""
        changes = []
        
        # Check distribution type change
        if current_dist.distribution_type != previous_dist.distribution_type:
            changes.append(DetectedChange(
                change_type=ChangeType.DISTRIBUTION_TYPE,
                severity=ChangeSeverity.HIGH,
                description=f"Distribution type changed for risk '{risk_id}'",
                affected_component=risk_id,
                old_value=previous_dist.distribution_type.value,
                new_value=current_dist.distribution_type.value,
                impact_assessment="Distribution type change significantly affects risk modeling",
                recommendations=[
                    "Validate new distribution type against historical data",
                    "Perform goodness-of-fit tests",
                    "Compare simulation results before and after change"
                ],
                validation_areas=["Distribution fitting", "Goodness-of-fit", "Simulation comparison"]
            ))
        
        # Check parameter changes (only if same distribution type)
        elif current_dist.distribution_type == previous_dist.distribution_type:
            param_changes = self._detect_parameter_changes(
                current_dist.parameters,
                previous_dist.parameters,
                risk_id,
                current_dist.distribution_type
            )
            changes.extend(param_changes)
        
        return changes
    
    def _detect_parameter_changes(
        self,
        current_params: Dict[str, float],
        previous_params: Dict[str, float],
        risk_id: str,
        dist_type: DistributionType
    ) -> List[DetectedChange]:
        """Detect changes in distribution parameters."""
        changes = []
        
        all_param_names = set(current_params.keys()) | set(previous_params.keys())
        
        for param_name in all_param_names:
            current_value = current_params.get(param_name, 0.0)
            previous_value = previous_params.get(param_name, 0.0)
            
            if abs(current_value - previous_value) > self.sensitivity_threshold:
                severity = self._assess_parameter_change_severity(current_value, previous_value)
                
                # Assess impact based on parameter type and distribution
                impact_assessment = self._assess_parameter_impact(
                    param_name, current_value, previous_value, dist_type
                )
                
                changes.append(DetectedChange(
                    change_type=ChangeType.DISTRIBUTION_PARAMETERS,
                    severity=severity,
                    description=f"Parameter '{param_name}' changed for risk '{risk_id}'",
                    affected_component=f"{risk_id}.{param_name}",
                    old_value=previous_value,
                    new_value=current_value,
                    impact_assessment=impact_assessment,
                    recommendations=[
                        f"Validate new {param_name} value against recent data",
                        "Perform sensitivity analysis on parameter change",
                        "Update documentation with change rationale"
                    ],
                    validation_areas=[
                        "Parameter validation",
                        "Sensitivity analysis",
                        "Documentation update"
                    ]
                ))
        
        return changes
    
    def _detect_correlation_changes(
        self,
        current_correlations: CorrelationMatrix,
        previous_correlations: CorrelationMatrix
    ) -> List[DetectedChange]:
        """Detect changes in correlation matrices."""
        changes = []
        
        # Get all correlation pairs
        current_corrs = current_correlations.correlations
        previous_corrs = previous_correlations.correlations
        
        all_pairs = set(current_corrs.keys()) | set(previous_corrs.keys())
        
        for pair in all_pairs:
            current_corr = current_corrs.get(pair, 0.0)
            previous_corr = previous_corrs.get(pair, 0.0)
            
            if abs(current_corr - previous_corr) > self.sensitivity_threshold:
                severity = self._assess_correlation_change_severity(current_corr, previous_corr)
                
                changes.append(DetectedChange(
                    change_type=ChangeType.CORRELATION_COEFFICIENTS,
                    severity=severity,
                    description=f"Correlation changed between {pair[0]} and {pair[1]}",
                    affected_component=f"{pair[0]} <-> {pair[1]}",
                    old_value=previous_corr,
                    new_value=current_corr,
                    impact_assessment=f"Correlation change of {abs(current_corr - previous_corr):.3f}",
                    recommendations=[
                        "Validate new correlation against historical data",
                        "Check for triangular consistency with other correlations",
                        "Verify correlation matrix remains positive definite"
                    ],
                    validation_areas=[
                        "Correlation validation",
                        "Matrix consistency",
                        "Positive definiteness"
                    ]
                ))
        
        return changes
    
    def _assess_parameter_change_severity(
        self,
        current_value: float,
        previous_value: float
    ) -> ChangeSeverity:
        """Assess the severity of a parameter change."""
        if previous_value == 0:
            return ChangeSeverity.HIGH if current_value != 0 else ChangeSeverity.LOW
        
        relative_change = abs((current_value - previous_value) / previous_value)
        
        if relative_change > 0.5:  # >50% change
            return ChangeSeverity.CRITICAL
        elif relative_change > 0.2:  # >20% change
            return ChangeSeverity.HIGH
        elif relative_change > 0.05:  # >5% change
            return ChangeSeverity.MEDIUM
        else:
            return ChangeSeverity.LOW
    
    def _assess_correlation_change_severity(
        self,
        current_corr: float,
        previous_corr: float
    ) -> ChangeSeverity:
        """Assess the severity of a correlation change."""
        change_magnitude = abs(current_corr - previous_corr)
        
        if change_magnitude > 0.5:
            return ChangeSeverity.CRITICAL
        elif change_magnitude > 0.3:
            return ChangeSeverity.HIGH
        elif change_magnitude > 0.1:
            return ChangeSeverity.MEDIUM
        else:
            return ChangeSeverity.LOW
    
    def _assess_parameter_impact(
        self,
        param_name: str,
        current_value: float,
        previous_value: float,
        dist_type: DistributionType
    ) -> str:
        """Assess the impact of a parameter change on the distribution."""
        relative_change = abs((current_value - previous_value) / max(abs(previous_value), 1e-6))
        
        impact_descriptions = {
            DistributionType.NORMAL: {
                'mean': f"Mean shift of {current_value - previous_value:.3f} ({relative_change:.1%} change)",
                'std': f"Standard deviation change of {current_value - previous_value:.3f} ({relative_change:.1%} change)"
            },
            DistributionType.TRIANGULAR: {
                'min': f"Minimum value change of {current_value - previous_value:.3f}",
                'mode': f"Mode shift of {current_value - previous_value:.3f}",
                'max': f"Maximum value change of {current_value - previous_value:.3f}"
            },
            DistributionType.UNIFORM: {
                'min': f"Lower bound change of {current_value - previous_value:.3f}",
                'max': f"Upper bound change of {current_value - previous_value:.3f}"
            }
        }
        
        return impact_descriptions.get(dist_type, {}).get(
            param_name,
            f"Parameter change of {current_value - previous_value:.3f} ({relative_change:.1%})"
        )
    
    def _generate_validation_guidance(
        self,
        detected_changes: List[DetectedChange]
    ) -> List[ValidationGuidance]:
        """Generate validation guidance based on detected changes."""
        guidance = []
        
        # Group changes by validation area
        validation_areas = {}
        for change in detected_changes:
            for area in change.validation_areas:
                if area not in validation_areas:
                    validation_areas[area] = []
                validation_areas[area].append(change)
        
        # Generate guidance for each area
        for area, changes in validation_areas.items():
            max_severity = max(change.severity for change in changes)
            priority = self._severity_to_priority(max_severity)
            
            # Collect unique recommendations and methods
            all_recommendations = set()
            for change in changes:
                all_recommendations.update(change.recommendations)
            
            validation_methods = self._get_validation_methods_for_area(area)
            expected_effort = self._estimate_validation_effort(area, len(changes), max_severity)
            
            guidance.append(ValidationGuidance(
                area=area,
                priority=priority,
                description=f"Validation needed due to {len(changes)} change(s) in {area.lower()}",
                recommended_actions=list(all_recommendations),
                validation_methods=validation_methods,
                expected_effort=expected_effort
            ))
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        guidance.sort(key=lambda g: priority_order.get(g.priority, 3))
        
        return guidance
    
    def _severity_to_priority(self, severity: ChangeSeverity) -> str:
        """Convert change severity to validation priority."""
        severity_to_priority_map = {
            ChangeSeverity.CRITICAL: "high",
            ChangeSeverity.HIGH: "high",
            ChangeSeverity.MEDIUM: "medium",
            ChangeSeverity.LOW: "low"
        }
        return severity_to_priority_map.get(severity, "medium")
    
    def _get_validation_methods_for_area(self, area: str) -> List[str]:
        """Get appropriate validation methods for a validation area."""
        validation_methods = {
            "Risk parameters": [
                "Historical data comparison",
                "Expert judgment validation",
                "Sensitivity analysis"
            ],
            "Distribution fitting": [
                "Goodness-of-fit tests",
                "Q-Q plots",
                "Kolmogorov-Smirnov test"
            ],
            "Correlation validation": [
                "Historical correlation analysis",
                "Correlation stability tests",
                "Cross-validation"
            ],
            "Matrix consistency": [
                "Positive definiteness check",
                "Eigenvalue analysis",
                "Triangular inequality validation"
            ],
            "Simulation accuracy": [
                "Convergence testing",
                "Result comparison",
                "Sensitivity analysis"
            ],
            "Model completeness": [
                "Risk register review",
                "Stakeholder validation",
                "Coverage analysis"
            ]
        }
        
        return validation_methods.get(area, ["Manual review", "Expert validation"])
    
    def _estimate_validation_effort(
        self,
        area: str,
        num_changes: int,
        max_severity: ChangeSeverity
    ) -> str:
        """Estimate the effort required for validation."""
        base_effort = {
            "Risk parameters": "medium",
            "Distribution fitting": "high",
            "Correlation validation": "high",
            "Matrix consistency": "medium",
            "Simulation accuracy": "high",
            "Model completeness": "medium"
        }.get(area, "medium")
        
        # Adjust based on number of changes and severity
        if max_severity in [ChangeSeverity.CRITICAL, ChangeSeverity.HIGH] or num_changes > 3:
            if base_effort == "low":
                return "medium"
            elif base_effort == "medium":
                return "high"
        
        return base_effort
    
    def _assess_overall_impact(
        self,
        detected_changes: List[DetectedChange]
    ) -> Tuple[str, List[str]]:
        """Assess overall impact and provide next steps."""
        if not detected_changes:
            return "No significant changes detected", ["Continue with current model"]
        
        # Count changes by severity
        severity_counts = {severity: 0 for severity in ChangeSeverity}
        for change in detected_changes:
            severity_counts[change.severity] += 1
        
        # Assess overall risk
        if severity_counts[ChangeSeverity.CRITICAL] > 0:
            overall_risk = "Critical changes detected - immediate validation required"
        elif severity_counts[ChangeSeverity.HIGH] > 2:
            overall_risk = "Multiple high-impact changes - comprehensive validation recommended"
        elif severity_counts[ChangeSeverity.HIGH] > 0:
            overall_risk = "High-impact changes detected - targeted validation needed"
        elif severity_counts[ChangeSeverity.MEDIUM] > 5:
            overall_risk = "Many moderate changes - review and validation recommended"
        else:
            overall_risk = "Minor changes detected - routine validation sufficient"
        
        # Generate next steps
        next_steps = []
        
        if severity_counts[ChangeSeverity.CRITICAL] > 0:
            next_steps.extend([
                "Immediately halt simulation runs until critical changes are validated",
                "Perform emergency validation of critical parameters",
                "Document rationale for all critical changes"
            ])
        
        if severity_counts[ChangeSeverity.HIGH] > 0:
            next_steps.extend([
                "Prioritize validation of high-impact changes",
                "Run comparative simulations to assess impact",
                "Update model documentation"
            ])
        
        if severity_counts[ChangeSeverity.MEDIUM] > 0:
            next_steps.extend([
                "Schedule validation activities for moderate changes",
                "Review change patterns for systematic issues"
            ])
        
        if not next_steps:
            next_steps = [
                "Continue monitoring for additional changes",
                "Perform routine model validation"
            ]
        
        return overall_risk, next_steps
    
    def store_baseline_model(
        self,
        model_id: str,
        risks: List[Risk],
        correlations: Optional[CorrelationMatrix] = None
    ):
        """Store a baseline model for future change detection."""
        self._baseline_models[model_id] = {
            'risks': risks,
            'correlations': correlations,
            'timestamp': datetime.now()
        }
    
    def get_change_history(self, days_back: int = 30) -> List[ChangeDetectionReport]:
        """Get change detection history for the specified number of days."""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        return [
            report for report in self._change_history
            if report.timestamp >= cutoff_date
        ]
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get a summary of validation areas needing attention."""
        if not self._change_history:
            return {"status": "No change history available"}
        
        latest_report = self._change_history[-1]
        
        high_priority_areas = [
            guidance for guidance in latest_report.validation_guidance
            if guidance.priority == "high"
        ]
        
        return {
            "total_changes": latest_report.total_changes,
            "critical_changes": latest_report.changes_by_severity.get(ChangeSeverity.CRITICAL, 0),
            "high_priority_validation_areas": len(high_priority_areas),
            "overall_assessment": latest_report.overall_risk_assessment,
            "next_steps": latest_report.recommended_next_steps[:3]  # Top 3 next steps
        }