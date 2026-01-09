"""
Property-based tests for continuous improvement functionality.

**Feature: monte-carlo-risk-simulations, Property 27: Continuous Improvement**
**Validates: Requirements 10.3, 10.5**
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from datetime import datetime, timedelta
import numpy as np
from typing import List, Dict, Any

from monte_carlo.continuous_improvement_engine import (
    ContinuousImprovementEngine, ParameterSuggestion, StandardAssumptionUpdate,
    ImprovementMetrics, ProjectSimilarity
)
from monte_carlo.historical_data_calibrator import (
    HistoricalDataCalibrator, ProjectOutcome
)
from monte_carlo.models import (
    Risk, ProbabilityDistribution, DistributionType, RiskCategory, 
    ImpactType
)


# Strategy for generating project characteristics
@st.composite
def project_characteristics_strategy(draw):
    """Generate valid project characteristics."""
    project_type = draw(st.sampled_from(['construction', 'software', 'infrastructure', 'research']))
    budget = draw(st.floats(min_value=100000, max_value=50000000))
    duration = draw(st.floats(min_value=30, max_value=1000))
    complexity = draw(st.sampled_from(['low', 'medium', 'high']))
    team_size = draw(st.integers(min_value=5, max_value=200))
    
    return {
        'project_type': project_type,
        'budget': budget,
        'duration': duration,
        'complexity': complexity,
        'team_size': team_size
    }


@st.composite
def project_outcome_with_characteristics_strategy(draw):
    """Generate ProjectOutcome with characteristics."""
    project_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    characteristics = draw(project_characteristics_strategy())
    project_type = characteristics['project_type']
    
    # Generate realistic cost and duration values
    baseline_cost = characteristics['budget']
    baseline_duration = characteristics['duration']
    
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
        risk_id = f"risk_{i}"
        impact = draw(st.floats(min_value=-10000, max_value=50000))
        risk_outcomes[risk_id] = impact
    
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
def risk_strategy(draw):
    """Generate valid Risk instances."""
    risk_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    name = draw(st.text(min_size=1, max_size=50))
    category = draw(st.sampled_from(list(RiskCategory)))
    impact_type = draw(st.sampled_from(list(ImpactType)))
    
    # Generate a simple normal distribution
    mean = draw(st.floats(min_value=1000, max_value=20000))
    std = draw(st.floats(min_value=100, max_value=5000))
    
    distribution = ProbabilityDistribution(
        distribution_type=DistributionType.NORMAL,
        parameters={'mean': mean, 'std': std}
    )
    
    baseline_impact = draw(st.floats(min_value=1000, max_value=50000))
    
    return Risk(
        id=risk_id,
        name=name,
        category=category,
        impact_type=impact_type,
        probability_distribution=distribution,
        baseline_impact=baseline_impact
    )


class TestContinuousImprovementProperties:
    """Property-based tests for continuous improvement functionality."""
    
    @given(
        st.lists(project_outcome_with_characteristics_strategy(), min_size=5, max_size=15),
        project_characteristics_strategy(),
        st.lists(risk_strategy(), min_size=1, max_size=5)
    )
    @settings(max_examples=20, deadline=None)
    def test_parameter_suggestions_consistency(
        self, 
        historical_outcomes: List[ProjectOutcome], 
        target_characteristics: Dict[str, Any],
        target_risks: List[Risk]
    ):
        """
        Property 27a: Parameter suggestions consistency
        For any set of historical projects and target project, parameter suggestions should be
        consistent and based on similar projects.
        **Validates: Requirements 10.3**
        """
        # Setup
        calibrator = HistoricalDataCalibrator()
        for outcome in historical_outcomes:
            calibrator.add_project_outcome(outcome)
        
        improvement_engine = ContinuousImprovementEngine(calibrator)
        
        # Get parameter suggestions
        suggestions = improvement_engine.suggest_parameters_for_similar_projects(
            target_characteristics, target_risks, min_similarity_threshold=0.5
        )
        
        # Verify suggestions are valid
        for suggestion in suggestions:
            assert isinstance(suggestion, ParameterSuggestion)
            assert 0.0 <= suggestion.confidence <= 1.0
            assert suggestion.risk_id in [risk.id for risk in target_risks]
            assert suggestion.parameter_name in ['mean', 'std', 'min', 'max', 'mode']
            assert len(suggestion.supporting_projects) > 0
            assert suggestion.expected_improvement >= 0
        
        # Verify suggestions are ordered by confidence
        confidences = [s.confidence for s in suggestions]
        assert confidences == sorted(confidences, reverse=True)
        
        # Verify suggestions have reasonable reasoning
        for suggestion in suggestions:
            assert len(suggestion.reasoning) > 10  # Non-trivial reasoning
            assert "similar projects" in suggestion.reasoning.lower()
    
    @given(
        st.lists(project_outcome_with_characteristics_strategy(), min_size=10, max_size=25)
    )
    @settings(max_examples=15, deadline=None)
    def test_standard_assumption_updates_validity(self, historical_outcomes: List[ProjectOutcome]):
        """
        Property 27b: Standard assumption updates validity
        For any set of historical projects, standard assumption updates should be valid
        and based on sufficient evidence.
        **Validates: Requirements 10.5**
        """
        # Setup
        calibrator = HistoricalDataCalibrator()
        for outcome in historical_outcomes:
            calibrator.add_project_outcome(outcome)
        
        improvement_engine = ContinuousImprovementEngine(calibrator)
        
        # Get standard assumption updates
        updates = improvement_engine.recommend_standard_assumption_updates(
            min_evidence_threshold=0.6, min_project_count=3
        )
        
        # Verify updates are valid
        for update in updates:
            assert isinstance(update, StandardAssumptionUpdate)
            assert isinstance(update.risk_category, RiskCategory)
            assert update.assumption_type in ["distribution_type", "parameter_default", "correlation"]
            assert 0.0 <= update.evidence_strength <= 1.0
            assert update.implementation_priority in ["high", "medium", "low"]
            assert len(update.affected_project_types) > 0
        
        # Verify updates are ordered by priority and evidence
        priorities = [{"high": 3, "medium": 2, "low": 1}[u.implementation_priority] for u in updates]
        evidence_strengths = [u.evidence_strength for u in updates]
        
        # Should be ordered by priority first, then evidence strength
        for i in range(1, len(updates)):
            current_priority = priorities[i]
            prev_priority = priorities[i-1]
            
            if current_priority == prev_priority:
                # Same priority, should be ordered by evidence strength
                assert evidence_strengths[i] <= evidence_strengths[i-1]
            else:
                # Different priority, current should be <= previous
                assert current_priority <= prev_priority
    
    @given(
        st.text(min_size=1, max_size=20),
        st.floats(min_value=0.1, max_value=100.0),
        st.one_of(st.none(), st.floats(min_value=0.1, max_value=200.0))
    )
    @settings(max_examples=30, deadline=None)
    def test_improvement_metrics_tracking(
        self, 
        metric_name: str, 
        current_value: float, 
        baseline_value: float
    ):
        """
        Property 27c: Improvement metrics tracking
        For any metric name and values, improvement tracking should maintain mathematical consistency.
        **Validates: Requirements 10.3**
        """
        calibrator = HistoricalDataCalibrator()
        improvement_engine = ContinuousImprovementEngine(calibrator)
        
        # Track improvement metrics
        metrics = improvement_engine.track_improvement_metrics(
            metric_name, current_value, baseline_value
        )
        
        # Verify metrics are valid
        assert isinstance(metrics, ImprovementMetrics)
        assert metrics.metric_name == metric_name
        assert metrics.current_value == current_value
        assert metrics.trend_direction in ["improving", "stable", "degrading"]
        assert isinstance(metrics.measurement_period, timedelta)
        assert isinstance(metrics.last_updated, datetime)
        
        # Verify improvement percentage calculation
        if baseline_value and baseline_value != 0:
            expected_improvement = ((baseline_value - current_value) / abs(baseline_value)) * 100
            assert abs(metrics.improvement_percentage - expected_improvement) < 1e-6
        
        # Verify metrics are stored - find the most recent metric with this name
        stored_metrics = None
        for metric in reversed(improvement_engine.improvement_metrics):
            if metric.metric_name == metric_name:
                stored_metrics = metric
                break
        
        assert stored_metrics is not None
        assert stored_metrics.current_value == current_value
        assert stored_metrics.baseline_value == metrics.baseline_value
    
    @given(
        st.lists(project_outcome_with_characteristics_strategy(), min_size=8, max_size=20),
        project_characteristics_strategy()
    )
    @settings(max_examples=15, deadline=None)
    def test_project_similarity_calculation(
        self, 
        historical_outcomes: List[ProjectOutcome], 
        target_characteristics: Dict[str, Any]
    ):
        """
        Property 27d: Project similarity calculation
        For any target project and historical projects, similarity calculations should be
        mathematically consistent and symmetric.
        **Validates: Requirements 10.3**
        """
        calibrator = HistoricalDataCalibrator()
        for outcome in historical_outcomes:
            calibrator.add_project_outcome(outcome)
        
        improvement_engine = ContinuousImprovementEngine(calibrator)
        
        # Find similar projects
        similar_projects = improvement_engine._find_similar_projects(
            target_characteristics, min_similarity_threshold=0.3
        )
        
        # Verify similarity scores are valid
        for similar_project in similar_projects:
            assert isinstance(similar_project, ProjectSimilarity)
            assert 0.0 <= similar_project.similarity_score <= 1.0
            assert 0.0 <= similar_project.risk_pattern_overlap <= 1.0
            assert isinstance(similar_project.matching_characteristics, list)
        
        # Verify similarity scores are ordered
        scores = [sp.similarity_score for sp in similar_projects]
        assert scores == sorted(scores, reverse=True)
        
        # Test symmetry property (simplified test)
        if len(historical_outcomes) >= 2:
            outcome1 = historical_outcomes[0]
            outcome2 = historical_outcomes[1]
            
            sim1_to_2 = improvement_engine._calculate_project_similarity(
                outcome1.project_characteristics, outcome2.project_characteristics
            )
            sim2_to_1 = improvement_engine._calculate_project_similarity(
                outcome2.project_characteristics, outcome1.project_characteristics
            )
            
            # Similarity should be symmetric
            assert abs(sim1_to_2 - sim2_to_1) < 1e-6
    
    @given(
        st.lists(project_outcome_with_characteristics_strategy(), min_size=5, max_size=12),
        st.lists(st.text(min_size=1, max_size=15), min_size=3, max_size=8),
        st.lists(st.floats(min_value=0.1, max_value=100.0), min_size=3, max_size=8)
    )
    @settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_improvement_summary_completeness(
        self, 
        historical_outcomes: List[ProjectOutcome],
        metric_names: List[str],
        metric_values: List[float]
    ):
        """
        Property 27e: Improvement summary completeness
        For any improvement engine state, the summary should accurately reflect all tracked data.
        **Validates: Requirements 10.3, 10.5**
        """
        assume(len(metric_names) == len(metric_values))
        
        calibrator = HistoricalDataCalibrator()
        for outcome in historical_outcomes:
            calibrator.add_project_outcome(outcome)
        
        improvement_engine = ContinuousImprovementEngine(calibrator)
        
        # Track some metrics
        for name, value in zip(metric_names, metric_values):
            improvement_engine.track_improvement_metrics(name, value)
        
        # Generate some suggestions and updates
        if historical_outcomes:
            target_chars = historical_outcomes[0].project_characteristics
            dummy_risk = Risk(
                id="test_risk",
                name="Test Risk",
                category=RiskCategory.COST,
                impact_type=ImpactType.COST,
                probability_distribution=ProbabilityDistribution(
                    distribution_type=DistributionType.NORMAL,
                    parameters={'mean': 1000, 'std': 200}
                ),
                baseline_impact=1000
            )
            
            improvement_engine.suggest_parameters_for_similar_projects(
                target_chars, [dummy_risk], min_similarity_threshold=0.3
            )
            improvement_engine.recommend_standard_assumption_updates(
                min_evidence_threshold=0.5, min_project_count=2
            )
        
        # Get improvement summary
        summary = improvement_engine.get_improvement_summary()
        
        # Verify summary structure
        required_keys = [
            "total_parameter_suggestions", "total_standard_updates", "tracked_metrics",
            "metrics_by_trend", "high_priority_updates", "recent_suggestions", "top_improvements"
        ]
        for key in required_keys:
            assert key in summary
        
        # Verify summary accuracy - implementation now tracks all metrics including duplicates
        assert summary["tracked_metrics"] == len(metric_names)  # All metrics are tracked, including duplicates
        assert isinstance(summary["metrics_by_trend"], dict)
        assert all(trend in ["improving", "stable", "degrading"] for trend in summary["metrics_by_trend"].keys())
        
        # Verify counts are non-negative
        assert summary["total_parameter_suggestions"] >= 0
        assert summary["total_standard_updates"] >= 0
        assert summary["high_priority_updates"] >= 0
        
        # Verify trend counts sum to total metrics
        trend_sum = sum(summary["metrics_by_trend"].values())
        assert trend_sum == summary["tracked_metrics"]
    
    @given(
        st.lists(project_outcome_with_characteristics_strategy(), min_size=6, max_size=15),
        project_characteristics_strategy(),
        st.lists(risk_strategy(), min_size=2, max_size=4),
        st.floats(min_value=0.3, max_value=0.9)
    )
    @settings(max_examples=10, deadline=None)
    def test_suggestion_quality_improves_with_data(
        self, 
        historical_outcomes: List[ProjectOutcome], 
        target_characteristics: Dict[str, Any],
        target_risks: List[Risk],
        similarity_threshold: float
    ):
        """
        Property 27f: Suggestion quality improves with more data
        For any target project, suggestions should generally improve (higher confidence or more suggestions)
        with more historical data.
        **Validates: Requirements 10.3**
        """
        calibrator = HistoricalDataCalibrator()
        improvement_engine = ContinuousImprovementEngine(calibrator)
        
        # Test with different amounts of historical data
        data_sizes = [len(historical_outcomes) // 3, len(historical_outcomes) // 2, len(historical_outcomes)]
        suggestion_qualities = []
        
        for data_size in data_sizes:
            if data_size > 0:
                # Reset calibrator with limited data
                limited_calibrator = HistoricalDataCalibrator()
                for outcome in historical_outcomes[:data_size]:
                    limited_calibrator.add_project_outcome(outcome)
                
                limited_engine = ContinuousImprovementEngine(limited_calibrator)
                
                # Get suggestions
                suggestions = limited_engine.suggest_parameters_for_similar_projects(
                    target_characteristics, target_risks, similarity_threshold
                )
                
                # Calculate quality metric (average confidence * number of suggestions)
                if suggestions:
                    avg_confidence = sum(s.confidence for s in suggestions) / len(suggestions)
                    quality = avg_confidence * len(suggestions)
                else:
                    quality = 0.0
                
                suggestion_qualities.append(quality)
        
        # With more data, quality should generally not decrease significantly
        # (allowing for some variation due to randomness)
        if len(suggestion_qualities) >= 2:
            for i in range(1, len(suggestion_qualities)):
                # Allow for some decrease, but not more than 50%
                assert suggestion_qualities[i] >= suggestion_qualities[i-1] * 0.5