"""
Unit tests for AI Insights Engine
"""

import pytest
import os
from uuid import uuid4
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Import the AI Insights Engine
from services.ai_insights_engine import AIInsightsEngine
from models.pmr import (
    AIInsightCategory, AIInsightType, AIInsightPriority,
    EnhancedAIInsight
)


class TestAIInsightsEngine:
    """Test suite for AI Insights Engine"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client"""
        mock_client = Mock()
        mock_table = Mock()
        mock_client.table.return_value = mock_table
        return mock_client
    
    @pytest.fixture
    def mock_openai_key(self):
        """Mock OpenAI API key"""
        return "test-api-key"
    
    @pytest.fixture
    def engine(self, mock_supabase, mock_openai_key):
        """Create AI Insights Engine instance"""
        with patch('services.ai_insights_engine.OpenAI'):
            engine = AIInsightsEngine(mock_supabase, mock_openai_key)
            return engine
    
    def test_engine_initialization(self, engine):
        """Test that engine initializes correctly"""
        assert engine is not None
        assert engine.model == "gpt-4"
        assert engine.temperature == 0.7
        assert engine.confidence_threshold == 0.7
    
    def test_calculate_confidence_score(self, engine):
        """Test confidence score calculation"""
        # Test with high quality data
        score = engine.calculate_confidence_score(
            data_quality=0.9,
            data_completeness=0.9,
            historical_accuracy=0.9
        )
        assert score >= Decimal("0.8")
        assert score <= Decimal("1.0")
        
        # Test with low quality data
        score = engine.calculate_confidence_score(
            data_quality=0.3,
            data_completeness=0.3,
            historical_accuracy=0.3
        )
        assert score >= Decimal("0.0")
        assert score <= Decimal("0.5")
    
    def test_extract_supporting_data_prediction(self, engine):
        """Test extracting supporting data for predictions"""
        category_data = {
            "historical_values": [100, 110, 120],
            "trend": "increasing",
            "variance": 10.5
        }
        
        supporting_data = engine.extract_supporting_data(
            category_data=category_data,
            insight_type=AIInsightType.prediction
        )
        
        assert "historical_data" in supporting_data
        assert "trend_direction" in supporting_data
        assert supporting_data["trend_direction"] == "increasing"
    
    def test_extract_supporting_data_recommendation(self, engine):
        """Test extracting supporting data for recommendations"""
        category_data = {
            "current_value": 85.0,
            "target_value": 100.0,
            "benchmark": 90.0
        }
        
        supporting_data = engine.extract_supporting_data(
            category_data=category_data,
            insight_type=AIInsightType.recommendation
        )
        
        assert "current_value" in supporting_data
        assert "target_value" in supporting_data
        assert supporting_data["current_value"] == 85.0
    
    def test_extract_supporting_data_alert(self, engine):
        """Test extracting supporting data for alerts"""
        category_data = {
            "threshold": 100.0,
            "current_value": 120.0,
            "severity": "high"
        }
        
        supporting_data = engine.extract_supporting_data(
            category_data=category_data,
            insight_type=AIInsightType.alert
        )
        
        assert "threshold" in supporting_data
        assert "severity" in supporting_data
        assert supporting_data["severity"] == "high"
    
    def test_build_system_prompt_budget(self, engine):
        """Test system prompt building for budget category"""
        prompt = engine._build_system_prompt(AIInsightCategory.budget)
        
        assert "budget" in prompt.lower()
        assert "financial" in prompt.lower()
        assert "cost" in prompt.lower()
    
    def test_build_system_prompt_schedule(self, engine):
        """Test system prompt building for schedule category"""
        prompt = engine._build_system_prompt(AIInsightCategory.schedule)
        
        assert "schedule" in prompt.lower()
        assert "timeline" in prompt.lower()
        assert "milestone" in prompt.lower()
    
    def test_build_user_prompt(self, engine):
        """Test user prompt building"""
        category_data = {
            "current_utilization": 0.85,
            "data_quality": 0.9,
            "data_completeness": 1.0
        }
        
        context = {
            "project": {
                "name": "Test Project",
                "status": "active",
                "priority": "high"
            }
        }
        
        prompt = engine._build_user_prompt(
            category=AIInsightCategory.resource,
            category_data=category_data,
            context=context
        )
        
        assert "Test Project" in prompt
        assert "current_utilization" in prompt
        assert "JSON format" in prompt
    
    def test_parse_insights_from_response_valid_json(self, engine):
        """Test parsing valid JSON response"""
        report_id = uuid4()
        ai_response = """
        [
            {
                "type": "prediction",
                "title": "Budget Overrun Risk",
                "content": "Project is trending 10% over budget",
                "priority": "high",
                "recommended_actions": ["Review spending", "Adjust forecast"],
                "predicted_impact": "Potential 10% budget overrun"
            }
        ]
        """
        
        category_data = {
            "data_quality": 0.9,
            "data_completeness": 0.9
        }
        
        insights = engine._parse_insights_from_response(
            report_id=report_id,
            category=AIInsightCategory.budget,
            ai_response=ai_response,
            category_data=category_data
        )
        
        assert len(insights) == 1
        assert insights[0].title == "Budget Overrun Risk"
        assert insights[0].insight_type == AIInsightType.prediction
        assert insights[0].priority == AIInsightPriority.high
        assert len(insights[0].recommended_actions) == 2
    
    def test_parse_insights_from_response_invalid_json(self, engine):
        """Test parsing invalid JSON response (fallback)"""
        report_id = uuid4()
        ai_response = "This is not valid JSON but contains useful information"
        
        category_data = {
            "data_quality": 0.7,
            "data_completeness": 0.8
        }
        
        insights = engine._parse_insights_from_response(
            report_id=report_id,
            category=AIInsightCategory.schedule,
            ai_response=ai_response,
            category_data=category_data
        )
        
        # Should create a fallback insight
        assert len(insights) == 1
        assert insights[0].insight_type == AIInsightType.summary
        assert insights[0].category == AIInsightCategory.schedule


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
