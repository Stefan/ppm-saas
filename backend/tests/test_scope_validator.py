"""
Unit Tests for ScopeValidator

This module contains unit tests for the ScopeValidator class, focusing on:
- Boundary enforcement with off-topic queries
- Competitor and external tool filtering
- PPM domain scope validation
- Response content filtering

Requirements Validated: 2.2, 10.1, 10.2, 10.3, 10.4, 10.5
"""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import uuid

# Import test setup
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.scope_validator import (
    ScopeValidator, ScopeValidationResult, ScopeViolationType
)

# Configure pytest for async tests
pytestmark = pytest.mark.asyncio


class TestScopeValidator:
    """Test ScopeValidator functionality"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client"""
        mock_client = Mock()
        mock_client.table.return_value.select.return_value.execute.return_value.data = []
        mock_client.table.return_value.insert.return_value.execute.return_value = Mock()
        mock_client.table.return_value.upsert.return_value.execute.return_value = Mock()
        mock_client.rpc.return_value.execute.return_value.data = []
        return mock_client
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        
        # Mock different responses based on the content being filtered
        def mock_create(**kwargs):
            messages = kwargs.get('messages', [])
            if len(messages) > 1:
                content = messages[1]['content']
                if 'filter' in content.lower():
                    # This is a filter_content call - extract the content to filter
                    if 'microsoft project' in content.lower():
                        mock_response.choices[0].message.content = "This feature works like our PPM platform but with better integration."
                    elif 'cora methodology' in content.lower():
                        mock_response.choices[0].message.content = "This aligns with PPM best practices for project governance."
                    elif 'use the project dashboard' in content.lower():
                        # For clean PPM content, return it unchanged
                        mock_response.choices[0].message.content = "Use the project dashboard to monitor budget variance and resource utilization across your portfolio."
                    else:
                        # Default fallback for clean content
                        mock_response.choices[0].message.content = content.split('Content to filter:')[-1].split('Provide the filtered version:')[0].strip()
                else:
                    # This is a validation call
                    mock_response.choices[0].message.content = json.dumps({
                        "is_ppm_related": True,
                        "confidence": 0.8,
                        "reasoning": "Query is related to project management",
                        "suggested_redirect": None
                    })
            else:
                mock_response.choices[0].message.content = json.dumps({
                    "is_ppm_related": True,
                    "confidence": 0.8,
                    "reasoning": "Query is related to project management",
                    "suggested_redirect": None
                })
            return mock_response
        
        mock_client.chat.completions.create = mock_create
        return mock_client
    
    @pytest.fixture
    def scope_validator(self, mock_supabase, mock_openai_client):
        """Create ScopeValidator instance with mocked dependencies"""
        with patch('services.scope_validator.OpenAI', return_value=mock_openai_client):
            validator = ScopeValidator(mock_supabase, "test-api-key")
            validator.openai_client = mock_openai_client
            return validator
    
    # Test boundary enforcement with off-topic queries
    
    async def test_validate_query_rejects_weather_queries(self, scope_validator):
        """Test that weather-related queries are rejected as off-topic"""
        # Requirements: 10.1, 10.2
        query = "What's the weather like today?"
        
        result = await scope_validator.validate_query(query)
        
        assert not result.is_valid
        assert len(result.violations) > 0
        assert any(v["type"] == ScopeViolationType.OFF_TOPIC.value for v in result.violations)
        assert any("weather" in v["matched_text"].lower() for v in result.violations)
    
    async def test_validate_query_rejects_sports_queries(self, scope_validator):
        """Test that sports-related queries are rejected as off-topic"""
        # Requirements: 10.1, 10.2
        query = "Who won the football game last night?"
        
        result = await scope_validator.validate_query(query)
        
        assert not result.is_valid
        assert len(result.violations) > 0
        assert any(v["type"] == ScopeViolationType.OFF_TOPIC.value for v in result.violations)
        assert any("football" in v["matched_text"].lower() for v in result.violations)
    
    async def test_validate_query_rejects_entertainment_queries(self, scope_validator):
        """Test that entertainment-related queries are rejected as off-topic"""
        # Requirements: 10.1, 10.2
        query = "What movies are playing this weekend?"
        
        result = await scope_validator.validate_query(query)
        
        assert not result.is_valid
        assert len(result.violations) > 0
        assert any(v["type"] == ScopeViolationType.OFF_TOPIC.value for v in result.violations)
        assert any("movies" in v["matched_text"].lower() for v in result.violations)
    
    async def test_validate_query_rejects_personal_life_queries(self, scope_validator):
        """Test that personal life queries are rejected as off-topic"""
        # Requirements: 10.1, 10.2
        query = "How do I improve my relationship with my family?"
        
        result = await scope_validator.validate_query(query)
        
        assert not result.is_valid
        assert len(result.violations) > 0
        assert any(v["type"] == ScopeViolationType.OFF_TOPIC.value for v in result.violations)
        assert any("family" in v["matched_text"].lower() for v in result.violations)
    
    async def test_validate_query_rejects_medical_queries(self, scope_validator):
        """Test that medical queries are rejected as off-topic"""
        # Requirements: 10.1, 10.2
        query = "I have a headache, what medicine should I take?"
        
        result = await scope_validator.validate_query(query)
        
        assert not result.is_valid
        assert len(result.violations) > 0
        assert any(v["type"] == ScopeViolationType.OFF_TOPIC.value for v in result.violations)
        assert any("medicine" in v["matched_text"].lower() for v in result.violations)
    
    # Test competitor and external tool filtering
    
    async def test_validate_query_rejects_microsoft_project_mentions(self, scope_validator):
        """Test that Microsoft Project mentions are rejected"""
        # Requirements: 10.1, 10.3
        query = "How does this compare to Microsoft Project?"
        
        result = await scope_validator.validate_query(query)
        
        assert not result.is_valid
        assert len(result.violations) > 0
        assert any(v["type"] == ScopeViolationType.COMPETITOR_MENTION.value for v in result.violations)
        assert any("microsoft project" in v["matched_text"].lower() for v in result.violations)
    
    async def test_validate_query_rejects_primavera_mentions(self, scope_validator):
        """Test that Primavera mentions are rejected"""
        # Requirements: 10.1, 10.3
        query = "Can I import data from Primavera P6?"
        
        result = await scope_validator.validate_query(query)
        
        assert not result.is_valid
        assert len(result.violations) > 0
        assert any(v["type"] == ScopeViolationType.COMPETITOR_MENTION.value for v in result.violations)
        assert any("primavera" in v["matched_text"].lower() for v in result.violations)
    
    async def test_validate_query_rejects_smartsheet_mentions(self, scope_validator):
        """Test that Smartsheet mentions are rejected"""
        # Requirements: 10.1, 10.3
        query = "Is this better than Smartsheet for project management?"
        
        result = await scope_validator.validate_query(query)
        
        assert not result.is_valid
        assert len(result.violations) > 0
        assert any(v["type"] == ScopeViolationType.COMPETITOR_MENTION.value for v in result.violations)
        assert any("smartsheet" in v["matched_text"].lower() for v in result.violations)
    
    async def test_validate_query_rejects_asana_mentions(self, scope_validator):
        """Test that Asana mentions are rejected"""
        # Requirements: 10.1, 10.3
        query = "How do I migrate from Asana to this platform?"
        
        result = await scope_validator.validate_query(query)
        
        assert not result.is_valid
        assert len(result.violations) > 0
        assert any(v["type"] == ScopeViolationType.COMPETITOR_MENTION.value for v in result.violations)
        assert any("asana" in v["matched_text"].lower() for v in result.violations)
    
    async def test_validate_query_rejects_monday_com_mentions(self, scope_validator):
        """Test that Monday.com mentions are rejected"""
        # Requirements: 10.1, 10.3
        query = "Does this have the same features as Monday.com?"
        
        result = await scope_validator.validate_query(query)
        
        assert not result.is_valid
        assert len(result.violations) > 0
        assert any(v["type"] == ScopeViolationType.COMPETITOR_MENTION.value for v in result.violations)
        assert any("monday" in v["matched_text"].lower() for v in result.violations)
    
    async def test_validate_query_rejects_jira_mentions(self, scope_validator):
        """Test that JIRA mentions are rejected"""
        # Requirements: 10.1, 10.3
        query = "Can I integrate with JIRA for issue tracking?"
        
        result = await scope_validator.validate_query(query)
        
        assert not result.is_valid
        assert len(result.violations) > 0
        assert any(v["type"] == ScopeViolationType.COMPETITOR_MENTION.value for v in result.violations)
        assert any("jira" in v["matched_text"].lower() for v in result.violations)
    
    # Test Cora methodology filtering
    
    async def test_validate_query_rejects_cora_methodology_mentions(self, scope_validator):
        """Test that Cora methodology mentions are rejected"""
        # Requirements: 10.2, 10.4
        query = "How does this align with Cora methodology best practices?"
        
        result = await scope_validator.validate_query(query)
        
        assert not result.is_valid
        assert len(result.violations) > 0
        assert any(v["type"] == ScopeViolationType.CORA_METHODOLOGY.value for v in result.violations)
        assert any("cora methodology" in v["matched_text"].lower() for v in result.violations)
        assert any(v["severity"] == "critical" for v in result.violations)
    
    async def test_validate_query_rejects_cora_framework_mentions(self, scope_validator):
        """Test that Cora framework mentions are rejected"""
        # Requirements: 10.2, 10.4
        query = "Does this support the Cora framework approach?"
        
        result = await scope_validator.validate_query(query)
        
        assert not result.is_valid
        assert len(result.violations) > 0
        assert any(v["type"] == ScopeViolationType.CORA_METHODOLOGY.value for v in result.violations)
        assert any("cora framework" in v["matched_text"].lower() for v in result.violations)
    
    # Test PPM domain acceptance
    
    async def test_validate_query_accepts_project_management_queries(self, scope_validator):
        """Test that valid project management queries are accepted"""
        # Requirements: 2.2, 10.5
        query = "How do I create a new project and assign resources?"
        
        result = await scope_validator.validate_query(query)
        
        assert result.is_valid
        assert len(result.violations) == 0
        assert result.confidence > 0.5
    
    async def test_validate_query_accepts_budget_tracking_queries(self, scope_validator):
        """Test that budget tracking queries are accepted"""
        # Requirements: 2.2, 10.5
        query = "How can I track budget variance in my portfolio?"
        
        result = await scope_validator.validate_query(query)
        
        assert result.is_valid
        assert len(result.violations) == 0
        assert result.confidence > 0.5
    
    async def test_validate_query_accepts_resource_allocation_queries(self, scope_validator):
        """Test that resource allocation queries are accepted"""
        # Requirements: 2.2, 10.5
        query = "What's the best way to optimize resource allocation across projects?"
        
        result = await scope_validator.validate_query(query)
        
        assert result.is_valid
        assert len(result.violations) == 0
        assert result.confidence > 0.5
    
    async def test_validate_query_accepts_risk_management_queries(self, scope_validator):
        """Test that risk management queries are accepted"""
        # Requirements: 2.2, 10.5
        query = "How do I set up risk monitoring and escalation workflows?"
        
        result = await scope_validator.validate_query(query)
        
        assert result.is_valid
        assert len(result.violations) == 0
        assert result.confidence > 0.5
    
    # Test response validation and filtering
    
    async def test_validate_response_filters_competitor_mentions(self, scope_validator):
        """Test that responses with competitor mentions are filtered"""
        # Requirements: 10.1, 10.3
        response = "You can achieve this similar to how Microsoft Project handles resource allocation."
        original_query = "How do I allocate resources?"
        
        result = await scope_validator.validate_response(response, original_query)
        
        assert not result.is_valid
        assert len(result.violations) > 0
        assert any(v["type"] == ScopeViolationType.COMPETITOR_MENTION.value for v in result.violations)
        assert result.filtered_content != response
        assert "microsoft project" not in result.filtered_content.lower()
    
    async def test_validate_response_filters_external_references(self, scope_validator):
        """Test that responses with external references are filtered"""
        # Requirements: 10.1, 10.3
        response = "You should visit smartsheet.com to see how they handle this feature."
        original_query = "How do I manage project timelines?"
        
        result = await scope_validator.validate_response(response, original_query)
        
        assert not result.is_valid
        assert len(result.violations) > 0
        assert any(v["type"] == ScopeViolationType.EXTERNAL_TOOL.value for v in result.violations)
        assert result.filtered_content != response
    
    async def test_validate_response_accepts_clean_ppm_responses(self, scope_validator):
        """Test that clean PPM responses are accepted"""
        # Requirements: 2.2, 10.5
        response = "To allocate resources, navigate to the Resource Management section and use the allocation matrix to assign team members to project tasks."
        original_query = "How do I allocate resources?"
        
        result = await scope_validator.validate_response(response, original_query)
        
        assert result.is_valid
        assert len(result.violations) == 0
        assert result.filtered_content == response
        assert result.confidence > 0.5
    
    # Test content filtering functionality
    
    async def test_filter_content_removes_competitor_mentions(self, scope_validator):
        """Test that content filtering removes competitor mentions"""
        # Requirements: 10.1, 10.3
        content = "This feature works like Microsoft Project but with better integration."
        
        filtered_content = await scope_validator.filter_content(content)
        
        assert "microsoft project" not in filtered_content.lower()
        assert "ppm platform" in filtered_content.lower() or "[ppm platform]" in filtered_content.lower()
    
    async def test_filter_content_removes_cora_references(self, scope_validator):
        """Test that content filtering removes Cora methodology references"""
        # Requirements: 10.2, 10.4
        content = "This aligns with Cora methodology principles for project governance."
        
        filtered_content = await scope_validator.filter_content(content)
        
        assert "cora methodology" not in filtered_content.lower()
        assert "ppm best practices" in filtered_content.lower()
    
    async def test_filter_content_preserves_ppm_content(self, scope_validator):
        """Test that content filtering preserves valid PPM content"""
        # Requirements: 2.2, 10.5
        content = "Use the project dashboard to monitor budget variance and resource utilization across your portfolio."
        
        filtered_content = await scope_validator.filter_content(content)
        
        # The content should either remain unchanged or be a reasonable PPM-focused alternative
        # Since we're mocking the AI, we expect it to preserve the PPM content
        assert len(filtered_content) > 0  # Should not be empty
        assert "project" in filtered_content.lower() or "ppm" in filtered_content.lower()  # Should contain PPM-related terms
        # Should not contain competitor mentions
        assert "microsoft project" not in filtered_content.lower()
        assert "cora methodology" not in filtered_content.lower()
    
    # Test general business advice filtering
    
    async def test_validate_query_rejects_general_business_advice_without_ppm_context(self, scope_validator):
        """Test that general business advice without PPM context is rejected"""
        # Requirements: 10.1, 10.4
        query = "What's the best market analysis approach for my startup?"
        
        result = await scope_validator.validate_query(query)
        
        assert not result.is_valid
        assert len(result.violations) > 0
        assert any(v["type"] == ScopeViolationType.GENERAL_BUSINESS_ADVICE.value for v in result.violations)
    
    async def test_validate_query_accepts_business_advice_with_ppm_context(self, scope_validator):
        """Test that business advice with PPM context is accepted"""
        # Requirements: 2.2, 10.5
        query = "How can I use project portfolio analysis to improve my business strategy?"
        
        result = await scope_validator.validate_query(query)
        
        assert result.is_valid
        assert len(result.violations) == 0
        assert result.confidence > 0.5
    
    # Test edge cases and error handling
    
    async def test_validate_query_handles_empty_query(self, scope_validator):
        """Test that empty queries are handled gracefully"""
        # Requirements: 10.5
        query = ""
        
        result = await scope_validator.validate_query(query)
        
        assert isinstance(result, ScopeValidationResult)
        assert result.confidence >= 0.0
    
    async def test_validate_query_handles_whitespace_only_query(self, scope_validator):
        """Test that whitespace-only queries are handled gracefully"""
        # Requirements: 10.5
        query = "   \n\t   "
        
        result = await scope_validator.validate_query(query)
        
        assert isinstance(result, ScopeValidationResult)
        assert result.confidence >= 0.0
    
    async def test_validate_response_handles_openai_api_error(self, scope_validator, mock_openai_client):
        """Test that OpenAI API errors are handled gracefully"""
        # Requirements: 10.5
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        response = "This is a test response about project management."
        original_query = "How do I manage projects?"
        
        result = await scope_validator.validate_response(response, original_query)
        
        assert isinstance(result, ScopeValidationResult)
        assert result.confidence >= 0.0
        assert result.filtered_content == response  # Should fallback to original
    
    # Test multiple violations in single query
    
    async def test_validate_query_detects_multiple_violations(self, scope_validator):
        """Test that multiple violations in a single query are detected"""
        # Requirements: 10.1, 10.2, 10.3
        query = "How does this compare to Microsoft Project and Cora methodology for weather forecasting projects?"
        
        result = await scope_validator.validate_query(query)
        
        assert not result.is_valid
        assert len(result.violations) >= 3  # Should detect competitor, cora, and off-topic
        
        violation_types = [v["type"] for v in result.violations]
        assert ScopeViolationType.COMPETITOR_MENTION.value in violation_types
        assert ScopeViolationType.CORA_METHODOLOGY.value in violation_types
        assert ScopeViolationType.OFF_TOPIC.value in violation_types
    
    # Test confidence scoring
    
    async def test_validation_confidence_decreases_with_violations(self, scope_validator):
        """Test that validation confidence decreases as violations increase"""
        # Requirements: 10.5
        clean_query = "How do I create a project schedule?"
        dirty_query = "How does Microsoft Project handle Cora methodology for weather tracking?"
        
        clean_result = await scope_validator.validate_query(clean_query)
        dirty_result = await scope_validator.validate_query(dirty_query)
        
        assert clean_result.confidence > dirty_result.confidence
        assert clean_result.is_valid
        assert not dirty_result.is_valid