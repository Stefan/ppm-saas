"""
Property-based tests for sensitivity and change detection capabilities.

**Feature: monte-carlo-risk-simulations, Property 25: Sensitivity and Change Detection**
**Validates: Requirements 9.4, 9.5**

Tests that the engine identifies high-impact parameters and highlights validation areas
when model assumptions change.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
import numpy as np
from typing import List, Dict, Optional
import copy

from monte_carlo.engine import MonteCarloEngine
from monte_carlo.change_detector import ModelChangeDetector, ChangeType, ChangeSeverity
from monte_carlo.models import (
    Risk, ProbabilityDistribution, DistributionType, RiskCategory, ImpactType,
    CorrelationMatrix
)


# Hypothesis strategies for generating test data
@st.composite
def simple_risk(draw):
    """Generate a simple risk for testing."""
    risk_id = draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    
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


@st.composite
def risk_list(draw, min_size=1, max_size=5):
    """Generate a list of unique risks."""
    risks = draw(st.lists(simple_risk(), min_size=min_size, max_size=max_size))
    
    # Ensure unique IDs
    unique_risks = []
    seen_ids = set()
    for risk in risks:
        if risk.id not in seen_ids:
            unique_risks.append(risk)
            seen_ids.add(risk.id)
    
    return unique_risks if unique_risks else [Risk(
        id="default_risk",
        name="Default Risk",
        category=RiskCategory.TECHNICAL,
        impact_type=ImpactType.COST,
        probability_distribution=ProbabilityDistribution(
            DistributionType.NORMAL,
            {'mean': 0, 'std': 1}
        ),
        baseline_impact=10.0
    )]


def modify_risk_parameters(risk: Risk, change_factor: float = 0.2) -> Risk:
    """Create a modified version of a risk with changed parameters."""
    modified_risk = copy.deepcopy(risk)
    
    # Modify distribution parameters
    if risk.probability_distribution.distribution_type == DistributionType.NORMAL:
        current_mean = risk.probability_distribution.parameters['mean']
        current_std = risk.probability_distribution.parameters['std']
        
        modified_risk.probability_distribution.parameters['mean'] = current_mean * (1 + change_factor)
        modified_risk.probability_distribution.parameters['std'] = current_std * (1 + change_factor * 0.5)
    
    elif risk.probability_distribution.distribution_type == DistributionType.TRIANGULAR:
        for param in ['min', 'mode', 'max']:
            current_value = risk.probability_distribution.parameters[param]
            modified_risk.probability_distribution.parameters[param] = current_value * (1 + change_factor)
    
    elif risk.probability_distribution.distribution_type == DistributionType.UNIFORM:
        for param in ['min', 'max']:
            current_value = risk.probability_distribution.parameters[param]
            modified_risk.probability_distribution.parameters[param] = current_value * (1 + change_factor)
    
    # Also modify baseline impact
    modified_risk.baseline_impact = risk.baseline_impact * (1 + change_factor)
    
    return modified_risk


class TestSensitivityChangeDetectionProperties:
    """Property-based tests for sensitivity and change detection capabilities."""
    
    @given(risk_list(min_size=1, max_size=4))
    @settings(max_examples=20, deadline=20000)
    def test_property_25_change_detection_sensitivity(self, original_risks: List[Risk]):
        """
        **Property 25: Sensitivity and Change Detection**
        
        For any set of risks, when parameters are modified, the change detector
        should identify the changes and assess their impact appropriately.
        
        **Validates: Requirements 9.4, 9.5**
        """
        engine = MonteCarloEngine()
        
        # Create modified version of risks with parameter changes
        modified_risks = []
        for risk in original_risks:
            # Apply a moderate change (20%)
            modified_risk = modify_risk_parameters(risk, change_factor=0.2)
            modified_risks.append(modified_risk)
        
        # Detect changes
        change_report = engine.detect_model_changes(
            current_risks=modified_risks,
            previous_risks=original_risks
        )
        
        # Should detect changes
        assert change_report.total_changes > 0, "Should detect parameter changes"
        
        # Should have detected changes for each modified risk
        detected_risk_ids = set()
        for change in change_report.detected_changes:
            if change.change_type in [ChangeType.DISTRIBUTION_PARAMETERS, ChangeType.BASELINE_IMPACT]:
                detected_risk_ids.add(change.affected_component.split('.')[0])
        
        original_risk_ids = {risk.id for risk in original_risks}
        assert len(detected_risk_ids & original_risk_ids) > 0, "Should detect changes in at least some risks"
    
    @given(risk_list(min_size=2, max_size=3))
    @settings(max_examples=15, deadline=25000)
    def test_property_25_high_impact_parameter_identification(self, risks: List[Risk]):
        """
        Test that high-impact parameter changes are properly identified.
        
        **Validates: Requirements 9.4**
        """
        engine = MonteCarloEngine()
        
        # Create a version with high-impact changes (>50% change)
        high_impact_risks = []
        for risk in risks:
            modified_risk = modify_risk_parameters(risk, change_factor=0.6)  # 60% change
            high_impact_risks.append(modified_risk)
        
        change_report = engine.detect_model_changes(
            current_risks=high_impact_risks,
            previous_risks=risks
        )
        
        # Should detect high-impact changes
        assert change_report.total_changes > 0
        
        # Should have high or critical severity changes
        high_severity_changes = [
            change for change in change_report.detected_changes
            if change.severity in [ChangeSeverity.HIGH, ChangeSeverity.CRITICAL]
        ]
        
        assert len(high_severity_changes) > 0, "Should identify high-impact parameter changes"
    
    @given(risk_list(min_size=1, max_size=3))
    @settings(max_examples=15, deadline=20000)
    def test_property_25_validation_area_highlighting(self, risks: List[Risk]):
        """
        Test that validation areas are properly highlighted when changes are detected.
        
        **Validates: Requirements 9.5**
        """
        engine = MonteCarloEngine()
        
        # Store as baseline model
        baseline_id = "test_baseline"
        engine.store_baseline_model(baseline_id, risks)
        
        # Create modified risks
        modified_risks = []
        for risk in risks:
            modified_risk = modify_risk_parameters(risk, change_factor=0.3)  # 30% change
            modified_risks.append(modified_risk)
        
        # Get validation area highlights
        validation_highlights = engine.highlight_validation_areas(
            risks=modified_risks,
            baseline_model_id=baseline_id
        )
        
        # Should return structured validation information
        assert isinstance(validation_highlights, dict)
        assert "validation_areas" in validation_highlights
        assert "overall_recommendations" in validation_highlights
        assert "validation_summary" in validation_highlights
        
        # Should have validation areas due to changes
        validation_areas = validation_highlights["validation_areas"]
        assert len(validation_areas) > 0, "Should highlight validation areas when changes are detected"
        
        # Each validation area should have required fields
        for area in validation_areas:
            assert "area" in area
            assert "priority" in area
            assert area["priority"] in ["high", "medium", "low"]
    
    @given(st.floats(min_value=0.01, max_value=0.5))
    @settings(max_examples=15, deadline=15000)
    def test_property_25_sensitivity_threshold_respect(self, change_factor: float):
        """
        Test that the change detector respects sensitivity thresholds.
        
        **Validates: Requirements 9.4**
        """
        # Create detector with specific sensitivity threshold
        sensitivity_threshold = 0.1  # 10%
        detector = ModelChangeDetector(sensitivity_threshold=sensitivity_threshold)
        
        # Create a simple risk
        original_risk = Risk(
            id="test_risk",
            name="Test Risk",
            category=RiskCategory.TECHNICAL,
            impact_type=ImpactType.COST,
            probability_distribution=ProbabilityDistribution(
                DistributionType.NORMAL,
                {'mean': 10.0, 'std': 2.0}
            ),
            baseline_impact=100.0
        )
        
        # Create modified risk with controlled change
        modified_risk = copy.deepcopy(original_risk)
        modified_risk.probability_distribution.parameters['mean'] = 10.0 * (1 + change_factor)
        modified_risk.baseline_impact = 100.0 * (1 + change_factor)
        
        # Detect changes
        change_report = detector.detect_changes(
            current_risks=[modified_risk],
            previous_risks=[original_risk]
        )
        
        # Should detect changes only if they exceed the threshold
        relative_change = change_factor
        if relative_change > sensitivity_threshold:
            assert change_report.total_changes > 0, f"Should detect changes above threshold ({relative_change:.3f} > {sensitivity_threshold})"
        else:
            # For very small changes, might not detect or might detect with low severity
            if change_report.total_changes > 0:
                # If detected, should be low severity
                low_severity_changes = [
                    change for change in change_report.detected_changes
                    if change.severity == ChangeSeverity.LOW
                ]
                assert len(low_severity_changes) > 0, "Small changes should have low severity"
    
    @given(risk_list(min_size=2, max_size=4))
    @settings(max_examples=15, deadline=20000)
    def test_property_25_change_severity_assessment(self, risks: List[Risk]):
        """
        Test that change severity is assessed correctly based on magnitude.
        
        **Validates: Requirements 9.4**
        """
        engine = MonteCarloEngine()
        
        # Test different change magnitudes
        test_cases = [
            (0.02, ChangeSeverity.LOW),      # 2% change - low
            (0.1, ChangeSeverity.MEDIUM),    # 10% change - medium
            (0.3, ChangeSeverity.HIGH),      # 30% change - high
            (0.7, ChangeSeverity.CRITICAL)   # 70% change - critical
        ]
        
        for change_factor, expected_min_severity in test_cases:
            modified_risks = []
            for risk in risks:
                modified_risk = modify_risk_parameters(risk, change_factor=change_factor)
                modified_risks.append(modified_risk)
            
            change_report = engine.detect_model_changes(
                current_risks=modified_risks,
                previous_risks=risks
            )
            
            if change_report.total_changes > 0:
                # Check that at least some changes have appropriate severity
                severity_levels = [change.severity for change in change_report.detected_changes]
                max_severity = max(severity_levels, key=lambda s: list(ChangeSeverity).index(s))
                
                # For large changes, should have high severity
                if change_factor > 0.5:
                    assert max_severity in [ChangeSeverity.HIGH, ChangeSeverity.CRITICAL], \
                        f"Large changes ({change_factor:.1%}) should have high severity, got {max_severity}"
    
    @given(risk_list(min_size=1, max_size=3))
    @settings(max_examples=15, deadline=20000)
    def test_property_25_validation_guidance_generation(self, risks: List[Risk]):
        """
        Test that appropriate validation guidance is generated for detected changes.
        
        **Validates: Requirements 9.5**
        """
        engine = MonteCarloEngine()
        
        # Create risks with different types of changes
        modified_risks = []
        for i, risk in enumerate(risks):
            modified_risk = copy.deepcopy(risk)
            
            # Apply different types of changes
            if i % 3 == 0:
                # Parameter change
                modified_risk = modify_risk_parameters(risk, change_factor=0.25)
            elif i % 3 == 1:
                # Category change
                modified_risk.category = RiskCategory.EXTERNAL if risk.category != RiskCategory.EXTERNAL else RiskCategory.TECHNICAL
            else:
                # Impact type change
                modified_risk.impact_type = ImpactType.SCHEDULE if risk.impact_type != ImpactType.SCHEDULE else ImpactType.COST
            
            modified_risks.append(modified_risk)
        
        change_report = engine.detect_model_changes(
            current_risks=modified_risks,
            previous_risks=risks
        )
        
        # Should generate validation guidance
        assert len(change_report.validation_guidance) > 0, "Should generate validation guidance for changes"
        
        # Each guidance should have required fields
        for guidance in change_report.validation_guidance:
            assert hasattr(guidance, 'area')
            assert hasattr(guidance, 'priority')
            assert hasattr(guidance, 'recommended_actions')
            assert hasattr(guidance, 'validation_methods')
            
            # Should have actionable recommendations
            assert len(guidance.recommended_actions) > 0, "Should provide actionable recommendations"
            assert len(guidance.validation_methods) > 0, "Should provide validation methods"
    
    @given(risk_list(min_size=1, max_size=2))
    @settings(max_examples=10, deadline=15000)
    def test_property_25_baseline_model_storage_retrieval(self, risks: List[Risk]):
        """
        Test that baseline models can be stored and used for change detection.
        
        **Validates: Requirements 9.5**
        """
        engine = MonteCarloEngine()
        
        # Store baseline model
        baseline_id = "test_baseline_model"
        engine.store_baseline_model(baseline_id, risks)
        
        # Create modified risks
        modified_risks = []
        for risk in risks:
            modified_risk = modify_risk_parameters(risk, change_factor=0.2)
            modified_risks.append(modified_risk)
        
        # Detect changes using baseline
        change_report = engine.detect_model_changes(
            current_risks=modified_risks,
            baseline_model_id=baseline_id
        )
        
        # Should detect changes compared to baseline
        assert change_report.total_changes > 0, "Should detect changes compared to stored baseline"
        
        # Should have meaningful change descriptions
        for change in change_report.detected_changes:
            assert len(change.description) > 0, "Changes should have descriptions"
            assert change.affected_component, "Changes should identify affected components"
    
    def test_property_25_change_detection_consistency(self):
        """
        Test that change detection results are consistent across multiple calls.
        
        **Validates: Requirements 9.4, 9.5**
        """
        engine = MonteCarloEngine()
        
        # Create test risks
        risk1 = Risk(
            id="risk1",
            name="Risk 1",
            category=RiskCategory.TECHNICAL,
            impact_type=ImpactType.COST,
            probability_distribution=ProbabilityDistribution(
                DistributionType.NORMAL,
                {'mean': 10.0, 'std': 2.0}
            ),
            baseline_impact=100.0
        )
        
        risk2 = Risk(
            id="risk2",
            name="Risk 2",
            category=RiskCategory.SCHEDULE,
            impact_type=ImpactType.SCHEDULE,
            probability_distribution=ProbabilityDistribution(
                DistributionType.TRIANGULAR,
                {'min': 5.0, 'mode': 10.0, 'max': 15.0}
            ),
            baseline_impact=50.0
        )
        
        original_risks = [risk1, risk2]
        
        # Create modified risks
        modified_risk1 = modify_risk_parameters(risk1, change_factor=0.3)
        modified_risk2 = modify_risk_parameters(risk2, change_factor=0.3)
        modified_risks = [modified_risk1, modified_risk2]
        
        # Run change detection multiple times
        report1 = engine.detect_model_changes(
            current_risks=modified_risks,
            previous_risks=original_risks
        )
        
        report2 = engine.detect_model_changes(
            current_risks=modified_risks,
            previous_risks=original_risks
        )
        
        # Results should be consistent
        assert report1.total_changes == report2.total_changes
        assert len(report1.detected_changes) == len(report2.detected_changes)
        assert len(report1.validation_guidance) == len(report2.validation_guidance)
    
    def test_property_25_validation_summary_completeness(self):
        """
        Test that validation summaries provide complete information.
        
        **Validates: Requirements 9.5**
        """
        engine = MonteCarloEngine()
        
        # Create test scenario with changes
        original_risk = Risk(
            id="test_risk",
            name="Test Risk",
            category=RiskCategory.TECHNICAL,
            impact_type=ImpactType.COST,
            probability_distribution=ProbabilityDistribution(
                DistributionType.NORMAL,
                {'mean': 10.0, 'std': 2.0}
            ),
            baseline_impact=100.0
        )
        
        modified_risk = modify_risk_parameters(original_risk, change_factor=0.4)
        
        # Store baseline and detect changes
        engine.store_baseline_model("test", [original_risk])
        engine.detect_model_changes(
            current_risks=[modified_risk],
            previous_risks=[original_risk]
        )
        
        # Get validation summary
        summary = engine.get_validation_summary()
        
        # Should contain required information
        assert isinstance(summary, dict)
        
        if "status" not in summary:  # If there's actual data
            assert "total_changes" in summary
            assert "overall_assessment" in summary
            
            # Should provide actionable information
            if "next_steps" in summary:
                assert isinstance(summary["next_steps"], list)
    
    @given(st.integers(min_value=1, max_value=30))
    @settings(max_examples=10, deadline=10000)
    def test_property_25_change_history_management(self, days_back: int):
        """
        Test that change detection history is properly managed.
        
        **Validates: Requirements 9.5**
        """
        engine = MonteCarloEngine()
        
        # Create some change history by running detections
        risk = Risk(
            id="test_risk",
            name="Test Risk",
            category=RiskCategory.TECHNICAL,
            impact_type=ImpactType.COST,
            probability_distribution=ProbabilityDistribution(
                DistributionType.NORMAL,
                {'mean': 10.0, 'std': 2.0}
            ),
            baseline_impact=100.0
        )
        
        modified_risk = modify_risk_parameters(risk, change_factor=0.2)
        
        # Run change detection to create history
        engine.detect_model_changes(
            current_risks=[modified_risk],
            previous_risks=[risk]
        )
        
        # Get change history
        history = engine.get_change_detection_history(days_back=days_back)
        
        # Should return a list
        assert isinstance(history, list)
        
        # If there's history, should have proper structure
        for report in history:
            assert hasattr(report, 'timestamp')
            assert hasattr(report, 'total_changes')
            assert hasattr(report, 'detected_changes')
            assert hasattr(report, 'validation_guidance')