"""
Property-based tests for Incomplete Data Handling
Feature: monte-carlo-risk-simulations, Property 20: Incomplete Data Handling
Validates: Requirements 7.2
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid

from monte_carlo.incomplete_data_handler import (
    IncompleteDataHandler, DefaultParameters, HistoricalRiskData
)
from monte_carlo.models import (
    Risk, RiskCategory, ImpactType, DistributionType, ProbabilityDistribution
)


# Test data strategies
@st.composite
def incomplete_risk_data_strategy(draw):
    """Generate incomplete risk data for testing."""
    # Base data that might be available
    base_data = {
        'id': str(uuid.uuid4()),
        'title': draw(st.text(min_size=5, max_size=100)),
        'category': draw(st.sampled_from(['technical', 'financial', 'operational', 'strategic', 'external']))
    }
    
    # Randomly include or exclude optional fields
    optional_fields = {
        'description': draw(st.one_of(st.none(), st.text(min_size=10, max_size=200))),
        'probability': draw(st.one_of(st.none(), st.floats(min_value=0.0, max_value=1.0))),
        'impact': draw(st.one_of(st.none(), st.floats(min_value=0.0, max_value=1.0))),
        'baseline_impact': draw(st.one_of(st.none(), st.floats(min_value=1.0, max_value=10000.0))),
        'distribution_type': draw(st.one_of(st.none(), st.sampled_from(['triangular', 'normal', 'uniform']))),
        'impact_type': draw(st.one_of(st.none(), st.sampled_from(['cost', 'schedule', 'both']))),
        'status': draw(st.one_of(st.none(), st.sampled_from(['identified', 'analyzing', 'mitigating'])))
    }
    
    # Randomly include some optional fields
    for field, value in optional_fields.items():
        if draw(st.booleans()):  # 50% chance to include each field
            base_data[field] = value
    
    return base_data


@st.composite
def project_context_strategy(draw):
    """Generate project context data."""
    context = {}
    
    # Randomly include context fields
    if draw(st.booleans()):
        context['project_size'] = draw(st.sampled_from(['small', 'medium', 'large', 'enterprise']))
    
    if draw(st.booleans()):
        context['complexity'] = draw(st.sampled_from(['low', 'medium', 'high']))
    
    if draw(st.booleans()):
        context['phase'] = draw(st.sampled_from(['planning', 'initiation', 'execution', 'monitoring', 'closing']))
    
    if draw(st.booleans()):
        context['budget'] = draw(st.floats(min_value=10000.0, max_value=10000000.0))
    
    return context if context else None


@st.composite
def historical_risk_strategy(draw):
    """Generate historical risk data for testing."""
    category = draw(st.sampled_from(list(RiskCategory)))
    
    return Risk(
        id=str(uuid.uuid4()),
        name=draw(st.text(min_size=5, max_size=50)),
        category=category,
        impact_type=draw(st.sampled_from(list(ImpactType))),
        probability_distribution=ProbabilityDistribution(
            distribution_type=DistributionType.TRIANGULAR,
            parameters={
                'min': draw(st.floats(min_value=0.1, max_value=1.0)),
                'mode': draw(st.floats(min_value=1.0, max_value=5.0)),
                'max': draw(st.floats(min_value=5.0, max_value=10.0))
            }
        ),
        baseline_impact=draw(st.floats(min_value=100.0, max_value=10000.0))
    )


class TestIncompleteDataHandling:
    """Property 20: Incomplete Data Handling tests"""

    @settings(max_examples=25, deadline=None)
    @given(
        incomplete_data=incomplete_risk_data_strategy(),
        project_context=project_context_strategy()
    )
    def test_default_parameter_generation(self, incomplete_data, project_context):
        """
        Property 20: Incomplete Data Handling - Default Parameter Generation
        For any incomplete risk data, the system should generate appropriate default parameters
        **Validates: Requirements 7.2**
        """
        # Create handler
        handler = IncompleteDataHandler()
        
        # Generate defaults for incomplete data
        defaults = handler.handle_incomplete_risk_data(
            risk_id=incomplete_data['id'],
            available_data=incomplete_data,
            project_context=project_context
        )
        
        # Verify defaults are generated
        assert isinstance(defaults, DefaultParameters), "Should return DefaultParameters object"
        
        # Verify required fields are populated
        assert defaults.probability_distribution is not None, "Should generate probability distribution"
        assert defaults.baseline_impact > 0, "Should generate positive baseline impact"
        assert isinstance(defaults.impact_type, ImpactType), "Should generate valid impact type"
        assert 0.0 <= defaults.confidence_level <= 1.0, "Should have valid confidence level"
        assert defaults.source in ['historical', 'category_default', 'system_default'], "Should have valid source"
        assert defaults.reasoning is not None, "Should provide reasoning for defaults"
        
        # Verify probability distribution is valid and sampleable
        try:
            test_samples = defaults.probability_distribution.sample(10)
            assert len(test_samples) == 10, "Distribution should be sampleable"
            assert all(x >= 0 for x in test_samples), "Distribution should produce non-negative samples"
            assert any(x > 0 for x in test_samples), "Distribution should produce some positive samples"
        except Exception as e:
            pytest.fail(f"Generated probability distribution should be valid: {str(e)}")
        
        # Verify baseline impact is reasonable
        assert defaults.baseline_impact <= 1e9, "Baseline impact should not be unreasonably large"
        
        # Verify confidence level reflects data completeness
        available_fields = len([v for v in incomplete_data.values() if v is not None])
        if available_fields <= 3:  # Very incomplete data
            assert defaults.confidence_level <= 0.7, "Should have lower confidence for very incomplete data"
        
        # Verify source is appropriate
        if 'category' in incomplete_data and incomplete_data['category'] is not None:
            assert defaults.source in ['historical', 'category_default'], "Should use category-based defaults when category is available"

    @settings(max_examples=20, deadline=None)
    @given(
        incomplete_data_list=st.lists(incomplete_risk_data_strategy(), min_size=1, max_size=5),
        historical_risks=st.lists(historical_risk_strategy(), min_size=3, max_size=10)
    )
    def test_historical_data_learning(self, incomplete_data_list, historical_risks):
        """
        Property 20: Incomplete Data Handling - Historical Data Learning
        For any historical risk data, the system should learn patterns and improve default generation
        **Validates: Requirements 7.2**
        """
        # Create handler
        handler = IncompleteDataHandler()
        
        # Update handler with historical data
        handler.update_historical_data(historical_risks)
        
        # Test default generation for each incomplete data entry
        for incomplete_data in incomplete_data_list:
            defaults = handler.handle_incomplete_risk_data(
                risk_id=incomplete_data['id'],
                available_data=incomplete_data
            )
            
            # Verify defaults are generated
            assert isinstance(defaults, DefaultParameters), "Should generate defaults even with historical data"
            
            # If category matches historical data, confidence should be higher
            if 'category' in incomplete_data and incomplete_data['category'] is not None:
                category_str = incomplete_data['category']
                
                # Check if we have historical data for this category
                has_historical_for_category = any(
                    risk.category.value == category_str or 
                    (category_str == 'financial' and risk.category == RiskCategory.COST) or
                    (category_str == 'operational' and risk.category == RiskCategory.RESOURCE)
                    for risk in historical_risks
                )
                
                if has_historical_for_category:
                    # Should have higher confidence when historical data is available
                    assert defaults.confidence_level >= 0.3, "Should have reasonable confidence with historical data"
                    
                    # Source should reflect historical data usage
                    assert defaults.source in ['historical', 'category_default'], "Should use historical or category defaults"
            
            # Verify generated parameters are still valid
            assert defaults.probability_distribution is not None, "Should maintain valid distribution"
            assert defaults.baseline_impact > 0, "Should maintain positive baseline impact"

    @settings(max_examples=15, deadline=None)
    @given(
        incomplete_data=incomplete_risk_data_strategy(),
        project_context=project_context_strategy()
    )
    def test_confidence_assessment_accuracy(self, incomplete_data, project_context):
        """
        Property 20: Incomplete Data Handling - Confidence Assessment
        For any incomplete data, confidence assessment should accurately reflect data completeness
        **Validates: Requirements 7.2**
        """
        # Create handler
        handler = IncompleteDataHandler()
        
        # Determine risk category for confidence assessment
        category_mapping = {
            'technical': RiskCategory.TECHNICAL,
            'financial': RiskCategory.COST,
            'operational': RiskCategory.RESOURCE,
            'strategic': RiskCategory.EXTERNAL,
            'external': RiskCategory.EXTERNAL
        }
        
        category = category_mapping.get(
            incomplete_data.get('category', 'external'), 
            RiskCategory.EXTERNAL
        )
        
        # Get confidence assessment
        confidence_scores = handler.get_confidence_assessment(category, incomplete_data)
        
        # Verify confidence scores structure
        assert isinstance(confidence_scores, dict), "Should return confidence scores dictionary"
        required_keys = ['overall', 'probability_distribution', 'baseline_impact', 'impact_type']
        for key in required_keys:
            assert key in confidence_scores, f"Should include {key} confidence score"
            assert 0.0 <= confidence_scores[key] <= 1.0, f"{key} confidence should be between 0 and 1"
        
        # Calculate actual data completeness
        total_expected_fields = 8  # Expected number of key fields
        available_fields = len([v for v in incomplete_data.values() if v is not None])
        data_completeness_ratio = available_fields / total_expected_fields
        
        # Confidence should correlate with data completeness
        if data_completeness_ratio >= 0.8:  # Very complete data
            assert confidence_scores['overall'] >= 0.6, "Should have high confidence for complete data"
        elif data_completeness_ratio <= 0.3:  # Very incomplete data
            assert confidence_scores['overall'] <= 0.7, "Should have lower confidence for incomplete data"
        
        # Overall confidence should be reasonable combination of individual scores
        individual_avg = (
            confidence_scores['probability_distribution'] + 
            confidence_scores['baseline_impact'] + 
            confidence_scores['impact_type']
        ) / 3
        
        # Overall should be close to weighted average (allowing some variance)
        assert abs(confidence_scores['overall'] - individual_avg) <= 0.3, "Overall confidence should reflect individual scores"

    @settings(max_examples=20, deadline=None)
    @given(
        incomplete_data=incomplete_risk_data_strategy(),
        project_context=project_context_strategy()
    )
    def test_default_validation_consistency(self, incomplete_data, project_context):
        """
        Property 20: Incomplete Data Handling - Default Validation
        For any generated defaults, validation should ensure consistency and reasonableness
        **Validates: Requirements 7.2**
        """
        # Create handler
        handler = IncompleteDataHandler()
        
        # Generate defaults
        defaults = handler.handle_incomplete_risk_data(
            risk_id=incomplete_data['id'],
            available_data=incomplete_data,
            project_context=project_context
        )
        
        # Validate the generated defaults
        validation_result = handler.validate_generated_defaults(defaults, incomplete_data)
        
        # Verify validation result structure
        assert hasattr(validation_result, 'is_valid'), "Should have is_valid field"
        assert hasattr(validation_result, 'errors'), "Should have errors list"
        assert hasattr(validation_result, 'warnings'), "Should have warnings list"
        assert hasattr(validation_result, 'recommendations'), "Should have recommendations list"
        
        # If validation fails, there should be specific errors
        if not validation_result.is_valid:
            assert len(validation_result.errors) > 0, "Invalid defaults should have specific errors"
            
            # Errors should be descriptive
            for error in validation_result.errors:
                assert isinstance(error, str), "Errors should be strings"
                assert len(error) > 10, "Errors should be descriptive"
        
        # If defaults have low confidence, there should be warnings or recommendations
        if defaults.confidence_level < 0.5:
            total_feedback = len(validation_result.warnings) + len(validation_result.recommendations)
            assert total_feedback > 0, "Low confidence defaults should have warnings or recommendations"
        
        # Verify consistency between original data and defaults
        if 'probability' in incomplete_data and incomplete_data['probability'] is not None:
            # Generated distribution should be somewhat consistent with original probability
            original_prob = incomplete_data['probability']
            
            # Test if distribution produces samples in reasonable range
            test_samples = defaults.probability_distribution.sample(100)
            sample_mean = sum(test_samples) / len(test_samples)
            
            # Allow for reasonable scaling based on baseline impact
            expected_range = defaults.baseline_impact * original_prob
            
            # Should be within reasonable bounds (allowing for distribution variance)
            if sample_mean > 0:  # Avoid division by zero
                ratio = abs(sample_mean - expected_range) / max(sample_mean, expected_range)
                if ratio > 2.0:  # More than 2x difference might indicate inconsistency
                    assert len(validation_result.warnings) > 0, "Large inconsistencies should generate warnings"

    @settings(max_examples=15, deadline=None)
    @given(
        risk_categories=st.lists(
            st.sampled_from(['technical', 'financial', 'operational', 'strategic', 'external']),
            min_size=1,
            max_size=5,
            unique=True
        ),
        incomplete_data_sets=st.lists(incomplete_risk_data_strategy(), min_size=2, max_size=8)
    )
    def test_category_based_defaults_consistency(self, risk_categories, incomplete_data_sets):
        """
        Property 20: Incomplete Data Handling - Category-Based Defaults
        For any risk category, default parameters should be consistent across similar incomplete data
        **Validates: Requirements 7.2**
        """
        # Create handler
        handler = IncompleteDataHandler()
        
        # Test defaults for each category
        for category in risk_categories:
            category_defaults = []
            
            # Generate defaults for multiple incomplete data sets with same category
            for incomplete_data in incomplete_data_sets[:3]:  # Limit to 3 for performance
                # Set the category for consistency
                test_data = incomplete_data.copy()
                test_data['category'] = category
                
                defaults = handler.handle_incomplete_risk_data(
                    risk_id=test_data['id'],
                    available_data=test_data
                )
                
                category_defaults.append(defaults)
            
            if len(category_defaults) < 2:
                continue  # Skip if not enough data
            
            # Verify consistency across defaults for same category
            first_defaults = category_defaults[0]
            
            for other_defaults in category_defaults[1:]:
                # Impact type should be consistent for same category
                assert first_defaults.impact_type == other_defaults.impact_type, \
                    f"Impact type should be consistent for {category} risks"
                
                # Distribution type should be consistent for same category (when using category defaults)
                if (first_defaults.source == 'category_default' and 
                    other_defaults.source == 'category_default'):
                    assert (first_defaults.probability_distribution.distribution_type == 
                           other_defaults.probability_distribution.distribution_type), \
                        f"Distribution type should be consistent for {category} category defaults"
                
                # Baseline impact should be in similar range for same category (within 10x)
                impact_ratio = max(first_defaults.baseline_impact, other_defaults.baseline_impact) / \
                              max(min(first_defaults.baseline_impact, other_defaults.baseline_impact), 1.0)
                assert impact_ratio <= 10.0, \
                    f"Baseline impacts should be in similar range for {category} risks"
                
                # Confidence levels should be similar for same category and source
                if first_defaults.source == other_defaults.source:
                    confidence_diff = abs(first_defaults.confidence_level - other_defaults.confidence_level)
                    assert confidence_diff <= 0.5, \
                        f"Confidence levels should be similar for {category} risks with same source"

    @settings(max_examples=10, deadline=None)
    @given(
        extremely_incomplete_data=st.builds(
            dict,
            id=st.text(min_size=10, max_size=50),
            # Only include minimal required fields
            title=st.one_of(st.none(), st.text(min_size=1, max_size=20))
        )
    )
    def test_extreme_incomplete_data_handling(self, extremely_incomplete_data):
        """
        Property 20: Incomplete Data Handling - Extreme Cases
        For any extremely incomplete data, the system should still generate valid defaults
        **Validates: Requirements 7.2**
        """
        # Create handler
        handler = IncompleteDataHandler()
        
        # Generate defaults for extremely incomplete data
        defaults = handler.handle_incomplete_risk_data(
            risk_id=extremely_incomplete_data['id'],
            available_data=extremely_incomplete_data
        )
        
        # Verify system handles extreme incompleteness gracefully
        assert isinstance(defaults, DefaultParameters), "Should handle extremely incomplete data"
        
        # Should fall back to system defaults
        assert defaults.source == 'system_default', "Should use system defaults for extremely incomplete data"
        
        # Should have low confidence
        assert defaults.confidence_level <= 0.5, "Should have low confidence for extremely incomplete data"
        
        # Should still generate valid parameters
        assert defaults.probability_distribution is not None, "Should generate distribution even for minimal data"
        assert defaults.baseline_impact > 0, "Should generate positive baseline impact even for minimal data"
        assert isinstance(defaults.impact_type, ImpactType), "Should generate valid impact type even for minimal data"
        
        # Distribution should still be sampleable
        try:
            test_samples = defaults.probability_distribution.sample(5)
            assert len(test_samples) == 5, "Distribution should work even with minimal data"
            assert all(x >= 0 for x in test_samples), "Should produce valid samples even with minimal data"
        except Exception as e:
            pytest.fail(f"Distribution should be valid even with extremely incomplete data: {str(e)}")
        
        # Should provide reasoning
        assert 'insufficient data' in defaults.reasoning.lower() or 'system default' in defaults.reasoning.lower(), \
            "Should explain use of system defaults for incomplete data"