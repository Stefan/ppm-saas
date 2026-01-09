"""
Risk Pattern Database for Monte Carlo Risk Simulations.

This module provides functionality to store, organize, and retrieve
risk patterns and outcomes by project type and phase.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
import json
import logging
from collections import defaultdict

from .models import (
    Risk, ProbabilityDistribution, DistributionType, RiskCategory,
    ImpactType, ValidationResult
)
from .historical_data_calibrator import ProjectOutcome

logger = logging.getLogger(__name__)


class ProjectPhase(Enum):
    """Project phases for risk pattern organization."""
    INITIATION = "initiation"
    PLANNING = "planning"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    CLOSURE = "closure"


@dataclass
class RiskPattern:
    """Represents a risk pattern observed in historical projects."""
    pattern_id: str
    risk_category: RiskCategory
    project_type: str
    project_phase: ProjectPhase
    typical_distribution: ProbabilityDistribution
    frequency_of_occurrence: float  # 0.0 to 1.0
    average_impact: float
    impact_variance: float
    correlation_patterns: Dict[str, float]  # other risk categories -> correlation
    mitigation_effectiveness: Dict[str, float]  # mitigation_type -> effectiveness
    
    # Metadata
    sample_size: int
    confidence_level: float
    last_updated: datetime
    contributing_projects: List[str]
    
    def __post_init__(self):
        """Validate risk pattern data."""
        if not 0.0 <= self.frequency_of_occurrence <= 1.0:
            raise ValueError("Frequency of occurrence must be between 0 and 1")
        if not 0.0 <= self.confidence_level <= 1.0:
            raise ValueError("Confidence level must be between 0 and 1")
        if self.sample_size <= 0:
            raise ValueError("Sample size must be positive")
        if self.impact_variance < 0:
            raise ValueError("Impact variance must be non-negative")


@dataclass
class ProjectTypeProfile:
    """Profile of risk patterns for a specific project type."""
    project_type: str
    total_projects_analyzed: int
    common_risk_categories: List[RiskCategory]
    typical_project_duration: float  # days
    typical_project_cost: float
    risk_patterns_by_phase: Dict[ProjectPhase, List[RiskPattern]]
    correlation_matrix: Dict[Tuple[RiskCategory, RiskCategory], float]
    success_factors: List[str]
    common_failure_modes: List[str]
    
    def __post_init__(self):
        """Validate project type profile."""
        if self.total_projects_analyzed <= 0:
            raise ValueError("Total projects analyzed must be positive")
        if self.typical_project_duration < 0:
            raise ValueError("Typical project duration must be non-negative")
        if self.typical_project_cost < 0:
            raise ValueError("Typical project cost must be non-negative")


@dataclass
class RiskOutcomeRecord:
    """Record of a specific risk outcome from a completed project."""
    project_id: str
    project_type: str
    project_phase: ProjectPhase
    risk_category: RiskCategory
    planned_impact: float
    actual_impact: float
    mitigation_applied: Optional[str]
    mitigation_cost: Optional[float]
    outcome_date: datetime
    lessons_learned: List[str]
    
    def __post_init__(self):
        """Validate risk outcome record."""
        if self.mitigation_cost is not None and self.mitigation_cost < 0:
            raise ValueError("Mitigation cost must be non-negative")


class RiskPatternDatabase:
    """
    Database for storing and retrieving risk patterns and outcomes
    organized by project type and phase.
    """
    
    def __init__(self):
        """Initialize the risk pattern database."""
        self.risk_patterns: Dict[str, RiskPattern] = {}
        self.project_type_profiles: Dict[str, ProjectTypeProfile] = {}
        self.risk_outcome_records: List[RiskOutcomeRecord] = []
        self.pattern_index: Dict[Tuple[str, RiskCategory, ProjectPhase], List[str]] = defaultdict(list)
        
    def add_project_outcome(self, outcome: ProjectOutcome) -> None:
        """
        Add a project outcome to the database and update risk patterns.
        
        Args:
            outcome: The project outcome to add
        """
        if not isinstance(outcome, ProjectOutcome):
            raise ValueError("Outcome must be a ProjectOutcome instance")
        
        # Extract risk outcome records from the project outcome
        for risk_id, actual_impact in outcome.risk_outcomes.items():
            # Infer risk category from risk ID (simplified approach)
            risk_category = self._infer_risk_category(risk_id)
            
            # Assume execution phase for simplicity (in practice, this would be tracked)
            project_phase = ProjectPhase.EXECUTION
            
            record = RiskOutcomeRecord(
                project_id=outcome.project_id,
                project_type=outcome.project_type,
                project_phase=project_phase,
                risk_category=risk_category,
                planned_impact=0.0,  # Would need to be tracked separately
                actual_impact=actual_impact,
                mitigation_applied=None,  # Would need to be tracked separately
                mitigation_cost=None,
                outcome_date=outcome.completion_date,
                lessons_learned=[]  # Would need to be tracked separately
            )
            
            self.risk_outcome_records.append(record)
        
        # Update patterns based on new data
        self._update_patterns_from_outcome(outcome)
        
        logger.info(f"Added project outcome {outcome.project_id} to risk pattern database")
    
    def get_risk_patterns(
        self,
        project_type: Optional[str] = None,
        risk_category: Optional[RiskCategory] = None,
        project_phase: Optional[ProjectPhase] = None,
        min_confidence: float = 0.0
    ) -> List[RiskPattern]:
        """
        Retrieve risk patterns matching the specified criteria.
        
        Args:
            project_type: Filter by project type (optional)
            risk_category: Filter by risk category (optional)
            project_phase: Filter by project phase (optional)
            min_confidence: Minimum confidence level required
            
        Returns:
            List of matching risk patterns
        """
        patterns = []
        
        for pattern in self.risk_patterns.values():
            # Apply filters
            if project_type and pattern.project_type != project_type:
                continue
            if risk_category and pattern.risk_category != risk_category:
                continue
            if project_phase and pattern.project_phase != project_phase:
                continue
            if pattern.confidence_level < min_confidence:
                continue
            
            patterns.append(pattern)
        
        # Sort by confidence level (highest first)
        patterns.sort(key=lambda p: p.confidence_level, reverse=True)
        
        return patterns
    
    def get_project_type_profile(self, project_type: str) -> Optional[ProjectTypeProfile]:
        """
        Get the risk profile for a specific project type.
        
        Args:
            project_type: The project type to get profile for
            
        Returns:
            ProjectTypeProfile if found, None otherwise
        """
        return self.project_type_profiles.get(project_type)
    
    def get_similar_project_patterns(
        self,
        target_project_type: str,
        target_characteristics: Dict[str, Any],
        similarity_threshold: float = 0.7
    ) -> List[RiskPattern]:
        """
        Get risk patterns from projects similar to the target project.
        
        Args:
            target_project_type: Type of the target project
            target_characteristics: Characteristics of the target project
            similarity_threshold: Minimum similarity score required
            
        Returns:
            List of risk patterns from similar projects
        """
        similar_patterns = []
        
        # Start with patterns from the same project type
        same_type_patterns = self.get_risk_patterns(project_type=target_project_type)
        similar_patterns.extend(same_type_patterns)
        
        # Add patterns from similar project types
        for project_type, profile in self.project_type_profiles.items():
            if project_type == target_project_type:
                continue
            
            similarity = self._calculate_project_type_similarity(
                target_project_type, target_characteristics, project_type, profile
            )
            
            if similarity >= similarity_threshold:
                type_patterns = self.get_risk_patterns(project_type=project_type)
                # Weight patterns by similarity
                for pattern in type_patterns:
                    pattern.confidence_level *= similarity
                similar_patterns.extend(type_patterns)
        
        # Sort by confidence and remove duplicates
        similar_patterns.sort(key=lambda p: p.confidence_level, reverse=True)
        
        return similar_patterns
    
    def analyze_risk_correlations(
        self,
        project_type: Optional[str] = None,
        min_sample_size: int = 5
    ) -> Dict[Tuple[RiskCategory, RiskCategory], float]:
        """
        Analyze correlations between different risk categories.
        
        Args:
            project_type: Filter by project type (optional)
            min_sample_size: Minimum number of projects required for correlation
            
        Returns:
            Dictionary mapping risk category pairs to correlation coefficients
        """
        correlations = {}
        
        # Group outcomes by project
        project_outcomes = defaultdict(dict)
        for record in self.risk_outcome_records:
            if project_type and record.project_type != project_type:
                continue
            
            project_outcomes[record.project_id][record.risk_category] = record.actual_impact
        
        # Calculate correlations between risk categories
        risk_categories = list(RiskCategory)
        
        for i, cat1 in enumerate(risk_categories):
            for j, cat2 in enumerate(risk_categories):
                if i >= j:  # Avoid duplicates and self-correlation
                    continue
                
                # Collect paired data
                cat1_impacts = []
                cat2_impacts = []
                
                for project_risks in project_outcomes.values():
                    if cat1 in project_risks and cat2 in project_risks:
                        cat1_impacts.append(project_risks[cat1])
                        cat2_impacts.append(project_risks[cat2])
                
                if len(cat1_impacts) >= min_sample_size:
                    # Calculate Pearson correlation coefficient
                    correlation = self._calculate_correlation(cat1_impacts, cat2_impacts)
                    correlations[(cat1, cat2)] = correlation
        
        return correlations
    
    def get_mitigation_effectiveness_data(
        self,
        risk_category: RiskCategory,
        project_type: Optional[str] = None
    ) -> Dict[str, Tuple[float, int]]:
        """
        Get mitigation effectiveness data for a specific risk category.
        
        Args:
            risk_category: The risk category to analyze
            project_type: Filter by project type (optional)
            
        Returns:
            Dictionary mapping mitigation types to (effectiveness, sample_size) tuples
        """
        mitigation_data = defaultdict(list)
        
        for record in self.risk_outcome_records:
            if record.risk_category != risk_category:
                continue
            if project_type and record.project_type != project_type:
                continue
            if not record.mitigation_applied:
                continue
            
            # Calculate effectiveness as reduction in impact
            if record.planned_impact > 0:
                effectiveness = max(0, (record.planned_impact - record.actual_impact) / record.planned_impact)
                mitigation_data[record.mitigation_applied].append(effectiveness)
        
        # Calculate average effectiveness and sample sizes
        effectiveness_summary = {}
        for mitigation_type, effectiveness_values in mitigation_data.items():
            avg_effectiveness = sum(effectiveness_values) / len(effectiveness_values)
            sample_size = len(effectiveness_values)
            effectiveness_summary[mitigation_type] = (avg_effectiveness, sample_size)
        
        return effectiveness_summary
    
    def export_patterns_to_json(self, file_path: str) -> None:
        """
        Export risk patterns to a JSON file.
        
        Args:
            file_path: Path to the output JSON file
        """
        export_data = {
            'risk_patterns': {},
            'project_type_profiles': {},
            'export_timestamp': datetime.now().isoformat()
        }
        
        # Export risk patterns
        for pattern_id, pattern in self.risk_patterns.items():
            export_data['risk_patterns'][pattern_id] = {
                'pattern_id': pattern.pattern_id,
                'risk_category': pattern.risk_category.value,
                'project_type': pattern.project_type,
                'project_phase': pattern.project_phase.value,
                'typical_distribution': {
                    'distribution_type': pattern.typical_distribution.distribution_type.value,
                    'parameters': pattern.typical_distribution.parameters,
                    'bounds': pattern.typical_distribution.bounds
                },
                'frequency_of_occurrence': pattern.frequency_of_occurrence,
                'average_impact': pattern.average_impact,
                'impact_variance': pattern.impact_variance,
                'correlation_patterns': pattern.correlation_patterns,
                'mitigation_effectiveness': pattern.mitigation_effectiveness,
                'sample_size': pattern.sample_size,
                'confidence_level': pattern.confidence_level,
                'last_updated': pattern.last_updated.isoformat(),
                'contributing_projects': pattern.contributing_projects
            }
        
        # Export project type profiles
        for project_type, profile in self.project_type_profiles.items():
            export_data['project_type_profiles'][project_type] = {
                'project_type': profile.project_type,
                'total_projects_analyzed': profile.total_projects_analyzed,
                'common_risk_categories': [cat.value for cat in profile.common_risk_categories],
                'typical_project_duration': profile.typical_project_duration,
                'typical_project_cost': profile.typical_project_cost,
                'success_factors': profile.success_factors,
                'common_failure_modes': profile.common_failure_modes
            }
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported risk patterns to {file_path}")
    
    def import_patterns_from_json(self, file_path: str) -> None:
        """
        Import risk patterns from a JSON file.
        
        Args:
            file_path: Path to the input JSON file
        """
        with open(file_path, 'r') as f:
            import_data = json.load(f)
        
        # Import risk patterns
        for pattern_id, pattern_data in import_data.get('risk_patterns', {}).items():
            distribution_data = pattern_data['typical_distribution']
            distribution = ProbabilityDistribution(
                distribution_type=DistributionType(distribution_data['distribution_type']),
                parameters=distribution_data['parameters'],
                bounds=distribution_data.get('bounds')
            )
            
            pattern = RiskPattern(
                pattern_id=pattern_data['pattern_id'],
                risk_category=RiskCategory(pattern_data['risk_category']),
                project_type=pattern_data['project_type'],
                project_phase=ProjectPhase(pattern_data['project_phase']),
                typical_distribution=distribution,
                frequency_of_occurrence=pattern_data['frequency_of_occurrence'],
                average_impact=pattern_data['average_impact'],
                impact_variance=pattern_data['impact_variance'],
                correlation_patterns=pattern_data['correlation_patterns'],
                mitigation_effectiveness=pattern_data['mitigation_effectiveness'],
                sample_size=pattern_data['sample_size'],
                confidence_level=pattern_data['confidence_level'],
                last_updated=datetime.fromisoformat(pattern_data['last_updated']),
                contributing_projects=pattern_data['contributing_projects']
            )
            
            self.risk_patterns[pattern_id] = pattern
            self._update_pattern_index(pattern)
        
        # Import project type profiles
        for project_type, profile_data in import_data.get('project_type_profiles', {}).items():
            profile = ProjectTypeProfile(
                project_type=profile_data['project_type'],
                total_projects_analyzed=profile_data['total_projects_analyzed'],
                common_risk_categories=[RiskCategory(cat) for cat in profile_data['common_risk_categories']],
                typical_project_duration=profile_data['typical_project_duration'],
                typical_project_cost=profile_data['typical_project_cost'],
                risk_patterns_by_phase={},  # Would need more complex import logic
                correlation_matrix={},  # Would need more complex import logic
                success_factors=profile_data['success_factors'],
                common_failure_modes=profile_data['common_failure_modes']
            )
            
            self.project_type_profiles[project_type] = profile
        
        logger.info(f"Imported risk patterns from {file_path}")
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the risk pattern database.
        
        Returns:
            Dictionary containing database statistics
        """
        stats = {
            'total_risk_patterns': len(self.risk_patterns),
            'total_project_types': len(self.project_type_profiles),
            'total_outcome_records': len(self.risk_outcome_records),
            'patterns_by_category': defaultdict(int),
            'patterns_by_project_type': defaultdict(int),
            'patterns_by_phase': defaultdict(int),
            'average_confidence_level': 0.0,
            'most_common_risk_category': None,
            'most_analyzed_project_type': None
        }
        
        if self.risk_patterns:
            # Count patterns by various dimensions
            confidence_levels = []
            for pattern in self.risk_patterns.values():
                stats['patterns_by_category'][pattern.risk_category.value] += 1
                stats['patterns_by_project_type'][pattern.project_type] += 1
                stats['patterns_by_phase'][pattern.project_phase.value] += 1
                confidence_levels.append(pattern.confidence_level)
            
            # Calculate average confidence
            stats['average_confidence_level'] = sum(confidence_levels) / len(confidence_levels)
            
            # Find most common category and project type
            stats['most_common_risk_category'] = max(
                stats['patterns_by_category'].items(), key=lambda x: x[1]
            )[0]
            stats['most_analyzed_project_type'] = max(
                stats['patterns_by_project_type'].items(), key=lambda x: x[1]
            )[0]
        
        # Convert defaultdicts to regular dicts for JSON serialization
        stats['patterns_by_category'] = dict(stats['patterns_by_category'])
        stats['patterns_by_project_type'] = dict(stats['patterns_by_project_type'])
        stats['patterns_by_phase'] = dict(stats['patterns_by_phase'])
        
        return stats
    
    def _infer_risk_category(self, risk_id: str) -> RiskCategory:
        """Infer risk category from risk ID (simplified approach)."""
        risk_id_lower = risk_id.lower()
        
        if 'cost' in risk_id_lower or 'budget' in risk_id_lower:
            return RiskCategory.COST
        elif 'schedule' in risk_id_lower or 'time' in risk_id_lower:
            return RiskCategory.SCHEDULE
        elif 'technical' in risk_id_lower or 'tech' in risk_id_lower:
            return RiskCategory.TECHNICAL
        elif 'resource' in risk_id_lower:
            return RiskCategory.RESOURCE
        elif 'quality' in risk_id_lower:
            return RiskCategory.QUALITY
        elif 'regulatory' in risk_id_lower or 'compliance' in risk_id_lower:
            return RiskCategory.REGULATORY
        else:
            return RiskCategory.EXTERNAL  # Default category
    
    def _update_patterns_from_outcome(self, outcome: ProjectOutcome) -> None:
        """Update risk patterns based on a new project outcome."""
        # This is a simplified implementation
        # In practice, you would analyze the outcome data and update existing patterns
        # or create new patterns based on statistical analysis
        
        project_type = outcome.project_type
        
        # Update or create project type profile
        if project_type not in self.project_type_profiles:
            self.project_type_profiles[project_type] = ProjectTypeProfile(
                project_type=project_type,
                total_projects_analyzed=1,
                common_risk_categories=[],
                typical_project_duration=outcome.actual_duration,
                typical_project_cost=outcome.actual_cost,
                risk_patterns_by_phase={},
                correlation_matrix={},
                success_factors=[],
                common_failure_modes=[]
            )
        else:
            profile = self.project_type_profiles[project_type]
            profile.total_projects_analyzed += 1
            
            # Update typical values (simple moving average)
            n = profile.total_projects_analyzed
            profile.typical_project_duration = (
                (profile.typical_project_duration * (n - 1) + outcome.actual_duration) / n
            )
            profile.typical_project_cost = (
                (profile.typical_project_cost * (n - 1) + outcome.actual_cost) / n
            )
    
    def _update_pattern_index(self, pattern: RiskPattern) -> None:
        """Update the pattern index for efficient retrieval."""
        index_key = (pattern.project_type, pattern.risk_category, pattern.project_phase)
        if pattern.pattern_id not in self.pattern_index[index_key]:
            self.pattern_index[index_key].append(pattern.pattern_id)
    
    def _calculate_project_type_similarity(
        self,
        target_type: str,
        target_characteristics: Dict[str, Any],
        candidate_type: str,
        candidate_profile: ProjectTypeProfile
    ) -> float:
        """Calculate similarity between project types."""
        # This is a simplified similarity calculation
        # In practice, you would use more sophisticated methods
        
        # Basic similarity based on project type names
        if target_type == candidate_type:
            return 1.0
        
        # Check for related project types
        construction_types = {'construction', 'infrastructure', 'building'}
        software_types = {'software', 'it', 'technology', 'development'}
        research_types = {'research', 'development', 'innovation'}
        
        target_in_construction = target_type.lower() in construction_types
        candidate_in_construction = candidate_type.lower() in construction_types
        
        target_in_software = target_type.lower() in software_types
        candidate_in_software = candidate_type.lower() in software_types
        
        target_in_research = target_type.lower() in research_types
        candidate_in_research = candidate_type.lower() in research_types
        
        if (target_in_construction and candidate_in_construction) or \
           (target_in_software and candidate_in_software) or \
           (target_in_research and candidate_in_research):
            return 0.7
        
        return 0.3  # Default low similarity
    
    def _calculate_correlation(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0
        
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        sum_y2 = sum(y * y for y in y_values)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator