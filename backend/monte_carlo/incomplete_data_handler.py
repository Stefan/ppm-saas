"""
Incomplete Data Handler for Monte Carlo Risk Simulations.

This module provides functionality to handle incomplete risk register data by
generating default distribution parameters and using risk category-based defaults
from historical data.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

from .models import (
    Risk, RiskCategory, ImpactType, ProbabilityDistribution, 
    DistributionType, ValidationResult
)

logger = logging.getLogger(__name__)


@dataclass
class HistoricalRiskData:
    """Historical risk data for a specific category."""
    category: RiskCategory
    sample_count: int
    probability_stats: Dict[str, float]  # mean, std, min, max
    impact_stats: Dict[str, float]  # mean, std, min, max
    distribution_preferences: Dict[DistributionType, float]  # frequency of use
    baseline_impact_stats: Dict[str, float]  # mean, std, min, max
    correlation_patterns: Dict[str, float]  # common correlations with other categories
    last_updated: datetime


@dataclass
class DefaultParameters:
    """Default parameters for incomplete risk data."""
    probability_distribution: ProbabilityDistribution
    baseline_impact: float
    impact_type: ImpactType
    confidence_level: float  # 0.0 to 1.0, how confident we are in these defaults
    source: str  # "historical", "category_default", "system_default"
    reasoning: str  # explanation of how defaults were determined


class IncompleteDataHandler:
    """
    Handles incomplete risk register data by providing intelligent defaults.
    
    Uses historical data patterns, risk category-based defaults, and statistical
    methods to fill in missing information for Monte Carlo simulations.
    """
    
    def __init__(self):
        """Initialize the incomplete data handler."""
        self._historical_data: Dict[RiskCategory, HistoricalRiskData] = {}
        self._category_defaults: Dict[RiskCategory, DefaultParameters] = {}
        self._system_defaults: DefaultParameters = self._create_system_defaults()
        self._initialize_category_defaults()
    
    def handle_incomplete_risk_data(
        self,
        risk_id: str,
        available_data: Dict[str, Any],
        project_context: Optional[Dict[str, Any]] = None
    ) -> DefaultParameters:
        """
        Generate default parameters for incomplete risk data.
        
        Args:
            risk_id: ID of the risk needing defaults
            available_data: Available risk data (may be incomplete)
            project_context: Optional project context for better defaults
            
        Returns:
            DefaultParameters with generated defaults and confidence information
        """
        try:
            # Determine risk category
            category = self._determine_risk_category(available_data, project_context)
            
            # Check what data is missing
            missing_fields = self._identify_missing_fields(available_data)
            
            # Check if data is extremely incomplete (only id and maybe title, no category)
            meaningful_fields = len([
                v for k, v in available_data.items() 
                if v is not None and v != '' and k not in ['id', 'title']
            ])
            
            # Force system defaults only for extremely incomplete data without category
            if meaningful_fields == 0:  # Only id and title available
                return self._generate_system_defaults(
                    available_data, missing_fields, project_context
                )
            
            # Generate defaults based on available information
            if self._has_sufficient_historical_data(category):
                return self._generate_historical_defaults(
                    category, available_data, missing_fields, project_context
                )
            elif category in self._category_defaults:
                return self._generate_category_defaults(
                    category, available_data, missing_fields, project_context
                )
            else:
                return self._generate_system_defaults(
                    available_data, missing_fields, project_context
                )
                
        except Exception as e:
            logger.error(f"Failed to handle incomplete data for risk {risk_id}: {str(e)}")
            # Return system defaults as fallback
            return self._generate_system_defaults(available_data, [], project_context)
    
    def update_historical_data(
        self,
        completed_risks: List[Risk],
        actual_outcomes: Optional[Dict[str, float]] = None
    ):
        """
        Update historical data patterns from completed risks.
        
        Args:
            completed_risks: List of completed risks with actual outcomes
            actual_outcomes: Optional actual impact outcomes for calibration
        """
        try:
            # Group risks by category
            risks_by_category = {}
            for risk in completed_risks:
                if risk.category not in risks_by_category:
                    risks_by_category[risk.category] = []
                risks_by_category[risk.category].append(risk)
            
            # Update historical data for each category
            for category, risks in risks_by_category.items():
                self._update_category_historical_data(category, risks, actual_outcomes)
            
            logger.info(f"Updated historical data for {len(risks_by_category)} risk categories")
            
        except Exception as e:
            logger.error(f"Failed to update historical data: {str(e)}")
    
    def get_confidence_assessment(
        self,
        risk_category: RiskCategory,
        available_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Assess confidence levels for default parameter generation.
        
        Args:
            risk_category: Category of the risk
            available_data: Available risk data
            
        Returns:
            Dictionary with confidence scores for different aspects
        """
        confidence_scores = {
            'overall': 0.0,
            'probability_distribution': 0.0,
            'baseline_impact': 0.0,
            'impact_type': 0.0
        }
        
        try:
            # Base confidence on available data completeness
            total_fields = 8  # Expected number of key fields
            available_fields = len([v for v in available_data.values() if v is not None and v != ''])
            data_completeness = min(1.0, available_fields / total_fields)
            
            # Adjust confidence based on historical data availability
            historical_confidence = 0.0
            if risk_category in self._historical_data:
                historical_data = self._historical_data[risk_category]
                if historical_data.sample_count >= 10:
                    historical_confidence = min(1.0, historical_data.sample_count / 50.0)
            
            # Calculate specific confidence scores with minimum thresholds
            confidence_scores['probability_distribution'] = max(0.1, 
                0.6 * data_completeness + 0.4 * historical_confidence
            )
            
            confidence_scores['baseline_impact'] = max(0.1,
                0.7 * data_completeness + 0.3 * historical_confidence
            )
            
            confidence_scores['impact_type'] = max(0.1,
                0.8 * data_completeness + 0.2 * historical_confidence
            )
            
            # Overall confidence is weighted average with minimum threshold
            overall_confidence = (
                0.4 * confidence_scores['probability_distribution'] +
                0.4 * confidence_scores['baseline_impact'] +
                0.2 * confidence_scores['impact_type']
            )
            confidence_scores['overall'] = max(0.1, min(1.0, overall_confidence))
            
            # Special case: very complete data should have high confidence
            if data_completeness >= 0.8:
                confidence_scores['overall'] = max(0.7, confidence_scores['overall'])
            
        except Exception as e:
            logger.error(f"Failed to assess confidence: {str(e)}")
            # Return low confidence scores as fallback
            confidence_scores = {k: 0.2 for k in confidence_scores.keys()}
        
        return confidence_scores
    
    def validate_generated_defaults(
        self,
        defaults: DefaultParameters,
        original_data: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate generated default parameters for reasonableness.
        
        Args:
            defaults: Generated default parameters
            original_data: Original incomplete data
            
        Returns:
            ValidationResult indicating if defaults are reasonable
        """
        errors = []
        warnings = []
        recommendations = []
        
        try:
            # Validate probability distribution
            try:
                test_samples = defaults.probability_distribution.sample(100)
                if not all(np.isfinite(test_samples)):
                    errors.append("Generated probability distribution produces non-finite values")
                
                if np.any(test_samples < 0):
                    warnings.append("Generated probability distribution produces negative values")
                
                # Check for reasonable range
                sample_range = np.max(test_samples) - np.min(test_samples)
                if sample_range == 0:
                    warnings.append("Generated probability distribution has zero variance")
                elif sample_range > 1000 * defaults.baseline_impact:
                    warnings.append("Generated probability distribution has very wide range")
                    
            except Exception as e:
                errors.append(f"Generated probability distribution is invalid: {str(e)}")
            
            # Validate baseline impact
            if defaults.baseline_impact <= 0:
                errors.append("Generated baseline impact must be positive")
            elif defaults.baseline_impact > 1e9:  # Very large impact
                warnings.append("Generated baseline impact is very large")
            
            # Check confidence level
            if defaults.confidence_level < 0.3:
                warnings.append("Low confidence in generated defaults - consider manual review")
            elif defaults.confidence_level < 0.5:
                recommendations.append("Moderate confidence in defaults - validate with domain expert")
            
            # Cross-validate with original data if available
            if 'probability' in original_data and original_data['probability'] is not None:
                original_prob = float(original_data['probability'])
                # Check if generated distribution is consistent with original probability
                generated_samples = defaults.probability_distribution.sample(1000)
                generated_mean = np.mean(generated_samples)
                
                # Allow for reasonable deviation
                if abs(generated_mean - original_prob * defaults.baseline_impact) > defaults.baseline_impact * 0.5:
                    warnings.append("Generated distribution may not be consistent with original probability")
            
        except Exception as e:
            logger.error(f"Failed to validate generated defaults: {str(e)}")
            errors.append(f"Validation failed: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def _determine_risk_category(
        self,
        available_data: Dict[str, Any],
        project_context: Optional[Dict[str, Any]] = None
    ) -> RiskCategory:
        """
        Determine risk category from available data.
        
        Args:
            available_data: Available risk data
            project_context: Optional project context
            
        Returns:
            RiskCategory enum value
        """
        # Check if category is explicitly provided
        if 'category' in available_data and available_data['category']:
            category_str = available_data['category'].lower()
            category_mapping = {
                'technical': RiskCategory.TECHNICAL,
                'financial': RiskCategory.COST,
                'cost': RiskCategory.COST,
                'operational': RiskCategory.RESOURCE,
                'resource': RiskCategory.RESOURCE,
                'strategic': RiskCategory.EXTERNAL,
                'external': RiskCategory.EXTERNAL,
                'schedule': RiskCategory.SCHEDULE,
                'quality': RiskCategory.QUALITY,
                'regulatory': RiskCategory.REGULATORY
            }
            
            if category_str in category_mapping:
                return category_mapping[category_str]
        
        # Try to infer category from title or description
        if 'title' in available_data or 'description' in available_data:
            text = (available_data.get('title', '') + ' ' + 
                   available_data.get('description', '')).lower()
            
            # Technical keywords
            if any(keyword in text for keyword in ['technical', 'software', 'hardware', 'system', 'technology']):
                return RiskCategory.TECHNICAL
            
            # Cost/Financial keywords
            if any(keyword in text for keyword in ['cost', 'budget', 'financial', 'money', 'price']):
                return RiskCategory.COST
            
            # Schedule keywords
            if any(keyword in text for keyword in ['schedule', 'delay', 'timeline', 'deadline']):
                return RiskCategory.SCHEDULE
            
            # Resource keywords
            if any(keyword in text for keyword in ['resource', 'staff', 'personnel', 'equipment']):
                return RiskCategory.RESOURCE
            
            # Quality keywords
            if any(keyword in text for keyword in ['quality', 'defect', 'performance', 'reliability']):
                return RiskCategory.QUALITY
            
            # Regulatory keywords
            if any(keyword in text for keyword in ['regulatory', 'compliance', 'legal', 'permit']):
                return RiskCategory.REGULATORY
        
        # Default to external if cannot determine
        return RiskCategory.EXTERNAL
    
    def _identify_missing_fields(self, available_data: Dict[str, Any]) -> List[str]:
        """
        Identify which required fields are missing from the data.
        
        Args:
            available_data: Available risk data
            
        Returns:
            List of missing field names
        """
        required_fields = [
            'probability', 'impact', 'baseline_impact', 'distribution_type',
            'distribution_parameters', 'impact_type', 'category'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in available_data or available_data[field] is None:
                missing_fields.append(field)
        
        return missing_fields
    
    def _has_sufficient_historical_data(self, category: RiskCategory) -> bool:
        """
        Check if we have sufficient historical data for a category.
        
        Args:
            category: Risk category to check
            
        Returns:
            True if sufficient historical data is available
        """
        if category not in self._historical_data:
            return False
        
        historical_data = self._historical_data[category]
        return historical_data.sample_count >= 5  # Minimum 5 samples for historical defaults
    
    def _generate_historical_defaults(
        self,
        category: RiskCategory,
        available_data: Dict[str, Any],
        missing_fields: List[str],
        project_context: Optional[Dict[str, Any]] = None
    ) -> DefaultParameters:
        """
        Generate defaults based on historical data for the category.
        
        Args:
            category: Risk category
            available_data: Available risk data
            missing_fields: List of missing fields
            project_context: Optional project context
            
        Returns:
            DefaultParameters based on historical data
        """
        historical_data = self._historical_data[category]
        
        # Generate probability distribution
        if 'distribution_type' in missing_fields or 'distribution_parameters' in missing_fields:
            # Use most common distribution type for this category
            preferred_dist_type = max(
                historical_data.distribution_preferences.items(),
                key=lambda x: x[1]
            )[0]
            
            # Generate parameters based on historical statistics
            if preferred_dist_type == DistributionType.TRIANGULAR:
                # Use historical impact statistics to create triangular distribution
                mean_impact = historical_data.impact_stats['mean']
                std_impact = historical_data.impact_stats['std']
                
                # Create triangular parameters with proper validation
                mode = max(0.01, mean_impact)
                min_val = max(0.001, mean_impact - 2 * std_impact)
                max_val = mean_impact + 2 * std_impact
                
                # Ensure proper ordering
                if min_val >= mode:
                    min_val = mode * 0.5
                if max_val <= mode:
                    max_val = mode * 1.5
                
                probability_distribution = ProbabilityDistribution(
                    distribution_type=DistributionType.TRIANGULAR,
                    parameters={'min': min_val, 'mode': mode, 'max': max_val}
                )
            
            elif preferred_dist_type == DistributionType.NORMAL:
                mean_val = max(0.01, historical_data.impact_stats['mean'])
                std_val = max(0.01, historical_data.impact_stats['std'])
                
                probability_distribution = ProbabilityDistribution(
                    distribution_type=DistributionType.NORMAL,
                    parameters={'mean': mean_val, 'std': std_val}
                )
            
            else:
                # Default to triangular
                probability_distribution = self._create_default_triangular_distribution(
                    max(0.01, historical_data.impact_stats['mean'])
                )
        else:
            # Use existing distribution if available
            probability_distribution = self._create_distribution_from_data(available_data)
        
        # Generate baseline impact
        baseline_impact = available_data.get('baseline_impact')
        if baseline_impact is None:
            baseline_impact = max(1.0, historical_data.baseline_impact_stats['mean'])
            
            # Adjust based on project context if available
            if project_context and 'project_size' in project_context:
                size_multiplier = self._get_project_size_multiplier(project_context['project_size'])
                baseline_impact *= size_multiplier
        
        # Determine impact type
        impact_type = available_data.get('impact_type', ImpactType.BOTH)
        
        # Calculate confidence based on historical data quality
        confidence_level = min(0.9, 0.5 + (historical_data.sample_count / 100.0))
        
        return DefaultParameters(
            probability_distribution=probability_distribution,
            baseline_impact=baseline_impact,
            impact_type=impact_type,
            confidence_level=confidence_level,
            source="historical",
            reasoning=f"Based on {historical_data.sample_count} historical {category.value} risks"
        )
    
    def _generate_category_defaults(
        self,
        category: RiskCategory,
        available_data: Dict[str, Any],
        missing_fields: List[str],
        project_context: Optional[Dict[str, Any]] = None
    ) -> DefaultParameters:
        """
        Generate defaults based on category-specific patterns.
        
        Args:
            category: Risk category
            available_data: Available risk data
            missing_fields: List of missing fields
            project_context: Optional project context
            
        Returns:
            DefaultParameters based on category defaults
        """
        category_defaults = self._category_defaults[category]
        
        # Use category defaults as base and adjust with available data
        probability_distribution = category_defaults.probability_distribution
        baseline_impact = category_defaults.baseline_impact
        impact_type = category_defaults.impact_type
        
        # Adjust with available data
        if 'probability' in available_data and available_data['probability'] is not None:
            # Adjust distribution based on provided probability
            prob_value = float(available_data['probability'])
            probability_distribution = self._adjust_distribution_for_probability(
                probability_distribution, prob_value
            )
        
        if 'impact' in available_data and available_data['impact'] is not None:
            # Adjust baseline impact based on provided impact
            impact_value = float(available_data['impact'])
            # Only adjust if impact is reasonable (between 0.1 and 10), otherwise keep category default
            if 0.1 <= impact_value <= 10.0:
                baseline_impact = baseline_impact * impact_value
            elif impact_value > 10.0:
                baseline_impact = baseline_impact * min(impact_value, 5.0)  # Cap the multiplier
            # If impact is very small or 0, keep the category default baseline_impact
        
        # Adjust for project context
        if project_context:
            baseline_impact = self._adjust_for_project_context(baseline_impact, project_context)
        
        # Ensure baseline impact is always positive
        baseline_impact = max(1.0, baseline_impact)
        
        return DefaultParameters(
            probability_distribution=probability_distribution,
            baseline_impact=baseline_impact,
            impact_type=impact_type,
            confidence_level=0.6,  # Moderate confidence for category defaults
            source="category_default",
            reasoning=f"Based on typical {category.value} risk patterns"
        )
    
    def _generate_system_defaults(
        self,
        available_data: Dict[str, Any],
        missing_fields: List[str],
        project_context: Optional[Dict[str, Any]] = None
    ) -> DefaultParameters:
        """
        Generate system-wide defaults as fallback.
        
        Args:
            available_data: Available risk data
            missing_fields: List of missing fields
            project_context: Optional project context
            
        Returns:
            DefaultParameters based on system defaults
        """
        # Use conservative system defaults
        probability_distribution = self._create_default_triangular_distribution(0.5)
        baseline_impact = 1000.0  # Conservative default
        impact_type = ImpactType.BOTH
        
        # Adjust with any available data
        if 'probability' in available_data and available_data['probability'] is not None:
            prob_value = float(available_data['probability'])
            probability_distribution = self._adjust_distribution_for_probability(
                probability_distribution, prob_value
            )
        
        if 'impact' in available_data and available_data['impact'] is not None:
            impact_value = float(available_data['impact'])
            # Only adjust if impact is reasonable (between 0.1 and 10), otherwise keep system default
            if 0.1 <= impact_value <= 10.0:
                baseline_impact = baseline_impact * impact_value
            elif impact_value > 10.0:
                baseline_impact = baseline_impact * min(impact_value, 5.0)  # Cap the multiplier
        
        # Adjust for project context
        if project_context:
            baseline_impact = self._adjust_for_project_context(baseline_impact, project_context)
        
        # Ensure baseline impact is always positive
        baseline_impact = max(1.0, baseline_impact)
        
        return DefaultParameters(
            probability_distribution=probability_distribution,
            baseline_impact=baseline_impact,
            impact_type=impact_type,
            confidence_level=0.3,  # Low confidence for system defaults
            source="system_default",
            reasoning="Conservative system defaults due to insufficient data"
        )
    
    def _create_system_defaults(self) -> DefaultParameters:
        """Create conservative system-wide defaults."""
        return DefaultParameters(
            probability_distribution=self._create_default_triangular_distribution(0.5),
            baseline_impact=1000.0,
            impact_type=ImpactType.BOTH,
            confidence_level=0.3,
            source="system_default",
            reasoning="Conservative system defaults"
        )
    
    def _initialize_category_defaults(self):
        """Initialize default parameters for each risk category."""
        # Technical risks
        self._category_defaults[RiskCategory.TECHNICAL] = DefaultParameters(
            probability_distribution=self._create_default_triangular_distribution(0.6),
            baseline_impact=5000.0,
            impact_type=ImpactType.BOTH,
            confidence_level=0.7,
            source="category_default",
            reasoning="Technical risks typically affect both cost and schedule"
        )
        
        # Cost risks
        self._category_defaults[RiskCategory.COST] = DefaultParameters(
            probability_distribution=self._create_default_triangular_distribution(0.4),
            baseline_impact=8000.0,  # More consistent with technical risks
            impact_type=ImpactType.COST,
            confidence_level=0.8,
            source="category_default",
            reasoning="Cost risks primarily affect project budget"
        )
        
        # Schedule risks
        self._category_defaults[RiskCategory.SCHEDULE] = DefaultParameters(
            probability_distribution=self._create_default_triangular_distribution(0.5),
            baseline_impact=6000.0,  # Normalized to cost equivalent
            impact_type=ImpactType.SCHEDULE,
            confidence_level=0.8,
            source="category_default",
            reasoning="Schedule risks primarily affect project timeline"
        )
        
        # Resource risks
        self._category_defaults[RiskCategory.RESOURCE] = DefaultParameters(
            probability_distribution=self._create_default_triangular_distribution(0.3),
            baseline_impact=7000.0,  # More consistent range
            impact_type=ImpactType.BOTH,
            confidence_level=0.7,
            source="category_default",
            reasoning="Resource risks can affect both cost and schedule"
        )
        
        # External risks
        self._category_defaults[RiskCategory.EXTERNAL] = DefaultParameters(
            probability_distribution=self._create_default_triangular_distribution(0.2),
            baseline_impact=10000.0,  # Higher but more reasonable
            impact_type=ImpactType.BOTH,
            confidence_level=0.6,
            source="category_default",
            reasoning="External risks are less predictable but can have high impact"
        )
        
        # Quality risks
        self._category_defaults[RiskCategory.QUALITY] = DefaultParameters(
            probability_distribution=self._create_default_triangular_distribution(0.4),
            baseline_impact=6000.0,
            impact_type=ImpactType.BOTH,
            confidence_level=0.7,
            source="category_default",
            reasoning="Quality risks often require rework affecting cost and schedule"
        )
        
        # Regulatory risks
        self._category_defaults[RiskCategory.REGULATORY] = DefaultParameters(
            probability_distribution=self._create_default_triangular_distribution(0.1),
            baseline_impact=12000.0,  # High but more reasonable
            impact_type=ImpactType.BOTH,
            confidence_level=0.6,
            source="category_default",
            reasoning="Regulatory risks are infrequent but can have major impact"
        )
    
    def _create_default_triangular_distribution(self, mode_value: float) -> ProbabilityDistribution:
        """
        Create a default triangular distribution.
        
        Args:
            mode_value: Mode value for the distribution
            
        Returns:
            ProbabilityDistribution with triangular distribution
        """
        # Ensure valid triangular distribution parameters
        mode_value = max(0.01, abs(mode_value))  # Ensure positive mode
        
        min_val = mode_value * 0.1
        max_val = mode_value * 2.0
        
        # Ensure proper ordering: min < mode < max
        if min_val >= mode_value:
            min_val = mode_value * 0.5
        if max_val <= mode_value:
            max_val = mode_value * 1.5
        
        # Final safety check
        if min_val >= max_val:
            min_val = 0.1
            mode_value = 0.5
            max_val = 1.0
        
        return ProbabilityDistribution(
            distribution_type=DistributionType.TRIANGULAR,
            parameters={
                'min': min_val,
                'mode': mode_value,
                'max': max_val
            }
        )
    
    def _create_distribution_from_data(self, available_data: Dict[str, Any]) -> ProbabilityDistribution:
        """Create distribution from available data."""
        if 'distribution_type' in available_data and 'distribution_parameters' in available_data:
            try:
                dist_type = DistributionType(available_data['distribution_type'])
                return ProbabilityDistribution(
                    distribution_type=dist_type,
                    parameters=available_data['distribution_parameters']
                )
            except (ValueError, KeyError):
                pass
        
        # Default triangular distribution
        impact = available_data.get('impact', 0.5)
        return self._create_default_triangular_distribution(impact)
    
    def _adjust_distribution_for_probability(
        self,
        distribution: ProbabilityDistribution,
        probability: float
    ) -> ProbabilityDistribution:
        """
        Adjust distribution parameters based on probability value.
        
        Args:
            distribution: Original distribution
            probability: Probability value (0.0 to 1.0)
            
        Returns:
            Adjusted ProbabilityDistribution
        """
        if distribution.distribution_type == DistributionType.TRIANGULAR:
            # Scale triangular distribution based on probability
            params = distribution.parameters.copy()
            
            # Avoid scaling by 0 or very small values
            scale_factor = max(0.01, probability) if probability > 0 else 0.1
            
            params['min'] *= scale_factor
            params['mode'] *= scale_factor
            params['max'] *= scale_factor
            
            # Ensure proper ordering after scaling
            if params['min'] >= params['mode']:
                params['min'] = params['mode'] * 0.5
            if params['max'] <= params['mode']:
                params['max'] = params['mode'] * 1.5
            
            return ProbabilityDistribution(
                distribution_type=DistributionType.TRIANGULAR,
                parameters=params
            )
        
        # For other distributions, return as-is for now
        return distribution
    
    def _adjust_for_project_context(
        self,
        baseline_impact: float,
        project_context: Dict[str, Any]
    ) -> float:
        """
        Adjust baseline impact based on project context.
        
        Args:
            baseline_impact: Original baseline impact
            project_context: Project context information
            
        Returns:
            Adjusted baseline impact
        """
        adjusted_impact = baseline_impact
        
        # Adjust for project size
        if 'project_size' in project_context:
            size_multiplier = self._get_project_size_multiplier(project_context['project_size'])
            adjusted_impact *= size_multiplier
        
        # Adjust for project complexity
        if 'complexity' in project_context:
            complexity = project_context['complexity'].lower()
            if complexity == 'high':
                adjusted_impact *= 1.5
            elif complexity == 'low':
                adjusted_impact *= 0.7
        
        # Adjust for project phase
        if 'phase' in project_context:
            phase = project_context['phase'].lower()
            if phase in ['planning', 'initiation']:
                adjusted_impact *= 1.2  # Higher uncertainty in early phases
            elif phase in ['execution', 'monitoring']:
                adjusted_impact *= 0.9  # Lower uncertainty in later phases
        
        return adjusted_impact
    
    def _get_project_size_multiplier(self, project_size: str) -> float:
        """
        Get multiplier based on project size.
        
        Args:
            project_size: Project size description
            
        Returns:
            Multiplier for baseline impact
        """
        size_multipliers = {
            'small': 0.5,
            'medium': 1.0,
            'large': 2.0,
            'enterprise': 3.0
        }
        
        return size_multipliers.get(project_size.lower(), 1.0)
    
    def _update_category_historical_data(
        self,
        category: RiskCategory,
        risks: List[Risk],
        actual_outcomes: Optional[Dict[str, float]] = None
    ):
        """
        Update historical data for a specific category.
        
        Args:
            category: Risk category to update
            risks: List of risks in this category
            actual_outcomes: Optional actual outcomes for calibration
        """
        if not risks:
            return
        
        # Calculate statistics from the risks
        probabilities = []
        impacts = []
        baseline_impacts = []
        distribution_types = []
        
        for risk in risks:
            # Extract probability from distribution (simplified)
            if risk.probability_distribution.distribution_type == DistributionType.TRIANGULAR:
                mode = risk.probability_distribution.parameters.get('mode', 0.5)
                probabilities.append(mode)
            else:
                probabilities.append(0.5)  # Default
            
            impacts.append(risk.baseline_impact)
            baseline_impacts.append(risk.baseline_impact)
            distribution_types.append(risk.probability_distribution.distribution_type)
        
        # Calculate statistics
        prob_stats = {
            'mean': np.mean(probabilities),
            'std': np.std(probabilities),
            'min': np.min(probabilities),
            'max': np.max(probabilities)
        }
        
        impact_stats = {
            'mean': np.mean(impacts),
            'std': np.std(impacts),
            'min': np.min(impacts),
            'max': np.max(impacts)
        }
        
        baseline_impact_stats = {
            'mean': np.mean(baseline_impacts),
            'std': np.std(baseline_impacts),
            'min': np.min(baseline_impacts),
            'max': np.max(baseline_impacts)
        }
        
        # Calculate distribution preferences
        dist_counts = {}
        for dist_type in distribution_types:
            dist_counts[dist_type] = dist_counts.get(dist_type, 0) + 1
        
        total_count = len(distribution_types)
        distribution_preferences = {
            dist_type: count / total_count
            for dist_type, count in dist_counts.items()
        }
        
        # Update historical data
        self._historical_data[category] = HistoricalRiskData(
            category=category,
            sample_count=len(risks),
            probability_stats=prob_stats,
            impact_stats=impact_stats,
            distribution_preferences=distribution_preferences,
            baseline_impact_stats=baseline_impact_stats,
            correlation_patterns={},  # Would be calculated from correlation analysis
            last_updated=datetime.now()
        )