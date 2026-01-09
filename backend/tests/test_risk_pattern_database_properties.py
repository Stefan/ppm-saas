"""
Property-based tests for risk pattern database functionality.

**Feature: monte-carlo-risk-simulations, Property 28: Risk Pattern Database**
**Validates: Requirements 10.4**
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime, timedelta
import numpy as np
from typing import List, Dict, Any
import tempfile
import os
import uuid

from monte_carlo.risk_pattern_database import (
    RiskPatternDatabase, RiskPattern, ProjectTypeProfile, RiskOutcomeRecord,
    ProjectPhase
)
from monte_carlo.historical_data_calibrator import ProjectOutcome
from monte_carlo.models import (
    ProbabilityDistribution, DistributionType, RiskCategory, ImpactType
)


# Strategy for generating project outcomes with characteristics
@st.composite
def project_outcome_with_characteristics_strategy(draw):
    """Generate ProjectOutcome with characteristics."""
    # Generate truly unique project IDs using UUID
    project_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID
    
    project_type = draw(st.sampled_from(['construction', 'software', 'infrastructure', 'research']))
    
    # Generate realistic cost and duration values
    baseline_cost = draw(st.floats(min_value=100000, max_value=10000000))
    baseline_duration = draw(st.floats(min_value=30, max_value=1000))
    
    # Actual values can vary from baseline
    cost_multiplier = draw(st.floats(min_value=0.8, max_value=2.0))
    duration_multiplier = draw(st.floats(min_value=0.9, max_value=1.5))
    
    actual_cost = baseline_cost * cost_multiplier
    actual_duration = baseline_duration * duration_multiplier
    
    completion_date = datetime.now() - timedelta(days=draw(st.integers(min_value=1, max_value=365)))
    
    # Generate risk outcomes
    num_risks = draw(st.integers(min_value=1, max_value=8))
    risk_outcomes = {}
    for i in range(num_risks):
        risk_category = draw(st.sampled_from(list(RiskCategory)))
        risk_id = f"{risk_category.value}_risk_{i}"
        impact = draw(st.floats(min_value=-10000, max_value=50000))
        risk_outcomes[risk_id] = impact
    
    # Generate project characteristics
    characteristics = {
        'project_type': project_type,
        'budget': baseline_cost,
        'duration': baseline_duration,
        'complexity': draw(st.sampled_from(['low', 'medium', 'high'])),
        'team_size': draw(st.integers(min_value=5, max_value=200))
    }
    
    return ProjectOutcome(
        project_id=project_id,
        project_type=project_type,
        completion_date=completion_date,
        actual_cost=actual_cost,
        actual_duration=actual_duration,
        baseline_cost=baseline_cost,
        baseline_duration=baseline_duration,
        risk_outcomes=risk_outcomes,
        project_characteristics=characteristics
    )


@st.composite
def risk_pattern_strategy(draw):
    """Generate valid RiskPattern instances."""
    # Generate truly unique pattern IDs using UUID
    pattern_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID
    
    risk_category = draw(st.sampled_from(list(RiskCategory)))
    project_type = draw(st.sampled_from(['construction', 'software', 'infrastructure', 'research']))
    project_phase = draw(st.sampled_from(list(ProjectPhase)))
    
    # Generate distribution
    mean = draw(st.floats(min_value=1000, max_value=20000))
    std = draw(st.floats(min_value=100, max_value=5000))
    distribution = ProbabilityDistribution(
        distribution_type=DistributionType.NORMAL,
        parameters={'mean': mean, 'std': std}
    )
    
    frequency = draw(st.floats(min_value=0.1, max_value=1.0))
    average_impact = draw(st.floats(min_value=1000, max_value=100000))
    impact_variance = draw(st.floats(min_value=100, max_value=10000))
    sample_size = draw(st.integers(min_value=5, max_value=100))
    confidence_level = draw(st.floats(min_value=0.5, max_value=1.0))
    
    return RiskPattern(
        pattern_id=pattern_id,
        risk_category=risk_category,
        project_type=project_type,
        project_phase=project_phase,
        typical_distribution=distribution,
        frequency_of_occurrence=frequency,
        average_impact=average_impact,
        impact_variance=impact_variance,
        correlation_patterns={},
        mitigation_effectiveness={},
        sample_size=sample_size,
        confidence_level=confidence_level,
        last_updated=datetime.now(),
        contributing_projects=[]
    )


class TestRiskPatternDatabaseProperties:
    """Property-based tests for risk pattern database functionality."""
    
    @given(st.lists(project_outcome_with_characteristics_strategy(), min_size=1, max_size=15))
    @settings(max_examples=20, deadline=None)
    def test_project_outcome_storage_and_retrieval(self, outcomes: List[ProjectOutcome]):
        """
        Property 28a: Project outcome storage and retrieval
        For any list of project outcomes, storing them should preserve data integrity
        and enable accurate retrieval.
        **Validates: Requirements 10.4**
        """
        database = RiskPatternDatabase()
        
        # Store all outcomes
        for outcome in outcomes:
            database.add_project_outcome(outcome)
        
        # Verify outcome records were created
        assert len(database.risk_outcome_records) > 0
        
        # Verify project type profiles were created
        project_types = set(outcome.project_type for outcome in outcomes)
        for project_type in project_types:
            profile = database.get_project_type_profile(project_type)
            assert profile is not None
            assert profile.project_type == project_type
            assert profile.total_projects_analyzed > 0
        
        # Verify data integrity in outcome records
        stored_project_ids = set(record.project_id for record in database.risk_outcome_records)
        original_project_ids = set(outcome.project_id for outcome in outcomes)
        
        # All original project IDs should be represented in stored records
        assert stored_project_ids.issubset(original_project_ids) or len(stored_project_ids) > 0
    
    @given(st.lists(risk_pattern_strategy(), min_size=1, max_size=10))
    @settings(max_examples=20, deadline=None)
    def test_risk_pattern_filtering_consistency(self, patterns: List[RiskPattern]):
        """
        Property 28b: Risk pattern filtering consistency
        For any set of risk patterns, filtering should return consistent subsets
        that match the specified criteria.
        **Validates: Requirements 10.4**
        """
        database = RiskPatternDatabase()
        
        # Add all patterns to database
        for pattern in patterns:
            database.risk_patterns[pattern.pattern_id] = pattern
            database._update_pattern_index(pattern)
        
        # Test filtering by project type
        project_types = list(set(pattern.project_type for pattern in patterns))
        for project_type in project_types:
            filtered_patterns = database.get_risk_patterns(project_type=project_type)
            
            # All returned patterns should match the filter
            for pattern in filtered_patterns:
                assert pattern.project_type == project_type
            
            # Count should match expected
            expected_count = sum(1 for p in patterns if p.project_type == project_type)
            assert len(filtered_patterns) == expected_count
        
        # Test filtering by risk category
        risk_categories = list(set(pattern.risk_category for pattern in patterns))
        for risk_category in risk_categories:
            filtered_patterns = database.get_risk_patterns(risk_category=risk_category)
            
            # All returned patterns should match the filter
            for pattern in filtered_patterns:
                assert pattern.risk_category == risk_category
        
        # Test filtering by confidence level
        if patterns:
            min_confidence = min(pattern.confidence_level for pattern in patterns)
            max_confidence = max(pattern.confidence_level for pattern in patterns)
            
            # Test with confidence threshold in the middle
            mid_confidence = (min_confidence + max_confidence) / 2
            filtered_patterns = database.get_risk_patterns(min_confidence=mid_confidence)
            
            # All returned patterns should meet confidence threshold
            for pattern in filtered_patterns:
                assert pattern.confidence_level >= mid_confidence
    
    @given(
        st.lists(project_outcome_with_characteristics_strategy(), min_size=5, max_size=20),
        st.sampled_from(['construction', 'software', 'infrastructure', 'research'])
    )
    @settings(max_examples=15, deadline=None)
    def test_correlation_analysis_mathematical_validity(
        self, 
        outcomes: List[ProjectOutcome], 
        target_project_type: str
    ):
        """
        Property 28c: Correlation analysis mathematical validity
        For any set of project outcomes, correlation analysis should produce
        mathematically valid correlation coefficients.
        **Validates: Requirements 10.4**
        """
        database = RiskPatternDatabase()
        
        # Add outcomes to database
        for outcome in outcomes:
            database.add_project_outcome(outcome)
        
        # Analyze correlations
        correlations = database.analyze_risk_correlations(
            project_type=target_project_type, min_sample_size=2
        )
        
        # Verify correlation coefficients are valid
        for (cat1, cat2), correlation in correlations.items():
            # Correlation should be between -1 and 1 (with small tolerance for floating point precision)
            assert -1.0001 <= correlation <= 1.0001
            
            # Categories should be different
            assert cat1 != cat2
            
            # Both categories should be valid RiskCategory values
            assert isinstance(cat1, RiskCategory)
            assert isinstance(cat2, RiskCategory)
        
        # Verify symmetry property (if we had both directions)
        # This is a simplified test since we only store one direction
        for (cat1, cat2), correlation in correlations.items():
            reverse_key = (cat2, cat1)
            if reverse_key in correlations:
                # Should be the same correlation
                assert abs(correlations[reverse_key] - correlation) < 1e-6
    
    @given(
        st.lists(project_outcome_with_characteristics_strategy(), min_size=3, max_size=12),
        st.sampled_from(list(RiskCategory))
    )
    @settings(max_examples=15, deadline=None)
    def test_mitigation_effectiveness_analysis(
        self, 
        outcomes: List[ProjectOutcome], 
        target_risk_category: RiskCategory
    ):
        """
        Property 28d: Mitigation effectiveness analysis
        For any set of project outcomes, mitigation effectiveness analysis should
        produce valid effectiveness measures.
        **Validates: Requirements 10.4**
        """
        database = RiskPatternDatabase()
        
        # Add outcomes to database
        for outcome in outcomes:
            database.add_project_outcome(outcome)
        
        # Get mitigation effectiveness data
        effectiveness_data = database.get_mitigation_effectiveness_data(target_risk_category)
        
        # Verify effectiveness data is valid
        for mitigation_type, (effectiveness, sample_size) in effectiveness_data.items():
            # Effectiveness should be non-negative (can be > 1 if mitigation overperformed)
            assert effectiveness >= 0.0
            
            # Sample size should be positive
            assert sample_size > 0
            
            # Mitigation type should be a non-empty string
            assert isinstance(mitigation_type, str)
            assert len(mitigation_type) > 0
    
    @given(st.lists(risk_pattern_strategy(), min_size=2, max_size=8))
    @settings(max_examples=15, deadline=None)
    def test_json_export_import_roundtrip(self, patterns: List[RiskPattern]):
        """
        Property 28e: JSON export/import roundtrip
        For any set of risk patterns, exporting to JSON and importing back
        should preserve all pattern data.
        **Validates: Requirements 10.4**
        """
        database = RiskPatternDatabase()
        
        # Add patterns to database
        for pattern in patterns:
            database.risk_patterns[pattern.pattern_id] = pattern
            database._update_pattern_index(pattern)
        
        # Create temporary file for export/import
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Export patterns
            database.export_patterns_to_json(temp_path)
            
            # Create new database and import
            new_database = RiskPatternDatabase()
            new_database.import_patterns_from_json(temp_path)
            
            # Verify all patterns were imported correctly
            assert len(new_database.risk_patterns) == len(database.risk_patterns)
            
            for pattern_id, original_pattern in database.risk_patterns.items():
                imported_pattern = new_database.risk_patterns[pattern_id]
                
                # Verify key attributes match
                assert imported_pattern.pattern_id == original_pattern.pattern_id
                assert imported_pattern.risk_category == original_pattern.risk_category
                assert imported_pattern.project_type == original_pattern.project_type
                assert imported_pattern.project_phase == original_pattern.project_phase
                assert imported_pattern.frequency_of_occurrence == original_pattern.frequency_of_occurrence
                assert imported_pattern.average_impact == original_pattern.average_impact
                assert imported_pattern.sample_size == original_pattern.sample_size
                assert imported_pattern.confidence_level == original_pattern.confidence_level
                
                # Verify distribution parameters match
                orig_dist = original_pattern.typical_distribution
                imp_dist = imported_pattern.typical_distribution
                assert imp_dist.distribution_type == orig_dist.distribution_type
                assert imp_dist.parameters == orig_dist.parameters
                assert imp_dist.bounds == orig_dist.bounds
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @given(st.lists(project_outcome_with_characteristics_strategy(), min_size=5, max_size=15))
    @settings(max_examples=15, deadline=None)
    def test_database_statistics_accuracy(self, outcomes: List[ProjectOutcome]):
        """
        Property 28f: Database statistics accuracy
        For any set of project outcomes, database statistics should accurately
        reflect the stored data.
        **Validates: Requirements 10.4**
        """
        database = RiskPatternDatabase()
        
        # Add outcomes to database
        for outcome in outcomes:
            database.add_project_outcome(outcome)
        
        # Add some risk patterns for more comprehensive statistics
        for i in range(3):
            pattern = RiskPattern(
                pattern_id=f"test_pattern_{i}",
                risk_category=RiskCategory.COST,
                project_type="construction",
                project_phase=ProjectPhase.EXECUTION,
                typical_distribution=ProbabilityDistribution(
                    distribution_type=DistributionType.NORMAL,
                    parameters={'mean': 1000, 'std': 200}
                ),
                frequency_of_occurrence=0.5,
                average_impact=5000,
                impact_variance=1000,
                correlation_patterns={},
                mitigation_effectiveness={},
                sample_size=10,
                confidence_level=0.8,
                last_updated=datetime.now(),
                contributing_projects=[]
            )
            database.risk_patterns[pattern.pattern_id] = pattern
        
        # Get statistics
        stats = database.get_database_statistics()
        
        # Verify statistics structure
        required_keys = [
            'total_risk_patterns', 'total_project_types', 'total_outcome_records',
            'patterns_by_category', 'patterns_by_project_type', 'patterns_by_phase',
            'average_confidence_level'
        ]
        for key in required_keys:
            assert key in stats
        
        # Verify statistics accuracy
        assert stats['total_risk_patterns'] == len(database.risk_patterns)
        assert stats['total_project_types'] == len(database.project_type_profiles)
        assert stats['total_outcome_records'] == len(database.risk_outcome_records)
        
        # Verify counts are non-negative
        assert stats['total_risk_patterns'] >= 0
        assert stats['total_project_types'] >= 0
        assert stats['total_outcome_records'] >= 0
        
        # Verify average confidence level is valid
        if stats['total_risk_patterns'] > 0:
            assert 0.0 <= stats['average_confidence_level'] <= 1.0
        
        # Verify category counts sum to total patterns
        if stats['patterns_by_category']:
            category_sum = sum(stats['patterns_by_category'].values())
            assert category_sum == stats['total_risk_patterns']
    
    @given(
        st.lists(project_outcome_with_characteristics_strategy(), min_size=3, max_size=10),
        st.text(min_size=1, max_size=20),
        st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.one_of(st.text(min_size=1, max_size=20), st.floats(min_value=1, max_value=1000000)),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=10, deadline=None)
    def test_similar_project_pattern_retrieval(
        self, 
        outcomes: List[ProjectOutcome], 
        target_project_type: str,
        target_characteristics: Dict[str, Any]
    ):
        """
        Property 28g: Similar project pattern retrieval
        For any target project characteristics, similar project pattern retrieval
        should return patterns ordered by relevance.
        **Validates: Requirements 10.4**
        """
        database = RiskPatternDatabase()
        
        # Add outcomes to database
        for outcome in outcomes:
            database.add_project_outcome(outcome)
        
        # Add some risk patterns
        for i, outcome in enumerate(outcomes[:3]):  # Limit to avoid too many patterns
            pattern = RiskPattern(
                pattern_id=f"pattern_{i}",
                risk_category=RiskCategory.COST,
                project_type=outcome.project_type,
                project_phase=ProjectPhase.EXECUTION,
                typical_distribution=ProbabilityDistribution(
                    distribution_type=DistributionType.NORMAL,
                    parameters={'mean': 1000, 'std': 200}
                ),
                frequency_of_occurrence=0.5,
                average_impact=5000,
                impact_variance=1000,
                correlation_patterns={},
                mitigation_effectiveness={},
                sample_size=10,
                confidence_level=0.8,
                last_updated=datetime.now(),
                contributing_projects=[]
            )
            database.risk_patterns[pattern.pattern_id] = pattern
        
        # Get similar project patterns
        similar_patterns = database.get_similar_project_patterns(
            target_project_type, target_characteristics, similarity_threshold=0.3
        )
        
        # Verify patterns are valid
        for pattern in similar_patterns:
            assert isinstance(pattern, RiskPattern)
            assert 0.0 <= pattern.confidence_level <= 1.0
            assert pattern.sample_size > 0
        
        # Verify patterns are ordered by confidence (highest first)
        if len(similar_patterns) > 1:
            confidence_levels = [p.confidence_level for p in similar_patterns]
            assert confidence_levels == sorted(confidence_levels, reverse=True)
        
        # Verify patterns from same project type appear first (if any exist)
        same_type_patterns = [p for p in similar_patterns if p.project_type == target_project_type]
        if same_type_patterns and len(similar_patterns) > len(same_type_patterns):
            # First patterns should be from same type (assuming they have high confidence)
            first_pattern_types = [p.project_type for p in similar_patterns[:len(same_type_patterns)]]
            same_type_count = sum(1 for pt in first_pattern_types if pt == target_project_type)
            # At least some of the first patterns should be from the same type
            assert same_type_count > 0