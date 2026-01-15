"""
Tests for Monte Carlo Analysis Service.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from uuid import uuid4
import numpy as np

from services.monte_carlo_service import MonteCarloAnalysisService


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client."""
    mock = Mock()
    mock.table = Mock(return_value=mock)
    mock.select = Mock(return_value=mock)
    mock.eq = Mock(return_value=mock)
    mock.execute = Mock(return_value=Mock(data=[]))
    return mock


@pytest.fixture
def service(mock_supabase):
    """Create MonteCarloAnalysisService instance."""
    return MonteCarloAnalysisService(mock_supabase)


@pytest.fixture
def sample_project_data():
    """Create sample project data for testing."""
    return {
        "project": {"id": str(uuid4()), "name": "Test Project"},
        "baseline_budget": 1000000.0,
        "current_spend": 400000.0,
        "baseline_duration": 365.0,
        "elapsed_time": 150.0,
        "financial_data": [],
        "risks": [
            {
                "id": "risk_1",
                "name": "Budget Overrun Risk",
                "category": "cost",
                "impact_type": "cost",
                "cost_impact": 50000.0,
                "distribution_type": "triangular",
                "min_impact": 20000.0,
                "most_likely_impact": 50000.0,
                "max_impact": 100000.0
            },
            {
                "id": "risk_2",
                "name": "Schedule Delay Risk",
                "category": "schedule",
                "impact_type": "schedule",
                "schedule_impact": 30.0,
                "distribution_type": "triangular",
                "min_impact": 10.0,
                "most_likely_impact": 30.0,
                "max_impact": 60.0
            }
        ],
        "milestones": [
            {
                "id": "milestone_1",
                "name": "Phase 1 Complete",
                "planned_date": "2024-06-01T00:00:00",
                "baseline_duration": 90.0,
                "critical_path": True,
                "dependencies": []
            }
        ],
        "resource_allocations": [
            {
                "id": "resource_1",
                "name": "Developer Team",
                "capacity": 100.0,
                "allocated": 85.0
            }
        ]
    }


class TestMonteCarloAnalysisService:
    """Test suite for MonteCarloAnalysisService."""
    
    def test_service_initialization(self, service):
        """Test service initializes correctly."""
        assert service is not None
        assert service.engine is not None
        assert service.supabase is not None
    
    @pytest.mark.asyncio
    async def test_create_budget_risks(self, service, sample_project_data):
        """Test budget risk creation from project data."""
        risks = await service._create_budget_risks(sample_project_data)
        
        assert len(risks) > 0
        assert all(hasattr(risk, 'id') for risk in risks)
        assert all(hasattr(risk, 'probability_distribution') for risk in risks)
    
    @pytest.mark.asyncio
    async def test_create_schedule_risks(self, service, sample_project_data):
        """Test schedule risk creation from project data."""
        risks = await service._create_schedule_risks(sample_project_data)
        
        assert len(risks) > 0
        assert all(hasattr(risk, 'id') for risk in risks)
        assert all(hasattr(risk, 'probability_distribution') for risk in risks)
    
    @pytest.mark.asyncio
    async def test_create_resource_risks(self, service, sample_project_data):
        """Test resource risk creation from project data."""
        risks = await service._create_resource_risks(sample_project_data)
        
        assert len(risks) > 0
        assert all(hasattr(risk, 'id') for risk in risks)
    
    def test_calculate_percentiles(self, service):
        """Test percentile calculation."""
        outcomes = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        percentiles = service._calculate_percentiles(outcomes, 0.95)
        
        assert "p50" in percentiles
        assert "mean" in percentiles
        assert "std" in percentiles
        assert percentiles["mean"] == 55.0  # Mean of 10-100 is 55
    
    def test_calculate_confidence_intervals(self, service):
        """Test confidence interval calculation."""
        outcomes = np.random.normal(100, 10, 1000)
        intervals = service._calculate_confidence_intervals(outcomes, 0.95)
        
        assert "confidence_level" in intervals
        assert "lower_bound" in intervals
        assert "upper_bound" in intervals
        assert intervals["lower_bound"] < intervals["upper_bound"]
    
    @pytest.mark.asyncio
    async def test_analyze_budget_variance(self, service, sample_project_data):
        """Test budget variance analysis."""
        with patch.object(service, '_fetch_project_data', return_value=sample_project_data):
            analysis = await service.analyze_budget_variance(
                uuid4(), sample_project_data, iterations=10000  # Use minimum required iterations
            )
            
            assert "baseline_budget" in analysis
            assert "expected_final_cost" in analysis
            assert "variance_from_baseline" in analysis
            assert "probability_within_budget" in analysis
            assert "percentiles" in analysis
    
    @pytest.mark.asyncio
    async def test_analyze_schedule_variance(self, service, sample_project_data):
        """Test schedule variance analysis."""
        with patch.object(service, '_fetch_project_data', return_value=sample_project_data):
            analysis = await service.analyze_schedule_variance(
                uuid4(), sample_project_data, iterations=10000  # Use minimum required iterations
            )
            
            assert "baseline_duration" in analysis
            assert "expected_final_duration" in analysis
            assert "variance_from_baseline" in analysis
            assert "probability_on_time" in analysis
    
    @pytest.mark.asyncio
    async def test_analyze_resource_risks(self, service, sample_project_data):
        """Test resource risk analysis."""
        with patch.object(service, '_fetch_project_data', return_value=sample_project_data):
            analysis = await service.analyze_resource_risks(
                uuid4(), sample_project_data, iterations=10000  # Use minimum required iterations
            )
            
            assert "total_resources" in analysis
            assert "resource_utilization" in analysis
            assert "conflict_probability" in analysis
            assert "recommendations" in analysis
    
    def test_generate_resource_recommendations(self, service):
        """Test resource recommendation generation."""
        resource_impact = {"utilization_rate": 0.95}
        conflict_analysis = {
            "conflict_probability": 0.4,
            "high_risk_resources": [{"resource_name": "Team A"}]
        }
        
        recommendations = service._generate_resource_recommendations(
            resource_impact, conflict_analysis
        )
        
        assert len(recommendations) > 0
        assert isinstance(recommendations, list)
    
    def test_generate_analysis_summary(self, service):
        """Test analysis summary generation."""
        budget_analysis = {
            "probability_within_budget": 0.6,
            "variance_percentage": 12.0
        }
        schedule_analysis = {
            "probability_on_time": 0.7,
            "variance_percentage": 8.0
        }
        resource_analysis = {
            "conflict_probability": {"conflict_probability": 0.3}
        }
        
        summary = service._generate_analysis_summary(
            budget_analysis, schedule_analysis, resource_analysis
        )
        
        assert "overall_risk_level" in summary
        assert "budget_risk_level" in summary
        assert "schedule_risk_level" in summary
        assert "resource_risk_level" in summary
        assert "key_insights" in summary
    
    def test_map_risk_category(self, service):
        """Test risk category mapping."""
        from monte_carlo.models import RiskCategory
        
        assert service._map_risk_category("cost") == RiskCategory.COST
        assert service._map_risk_category("schedule") == RiskCategory.SCHEDULE
        assert service._map_risk_category("resource") == RiskCategory.RESOURCE
    
    def test_map_impact_type(self, service):
        """Test impact type mapping."""
        from monte_carlo.models import ImpactType
        
        assert service._map_impact_type("cost") == ImpactType.COST
        assert service._map_impact_type("schedule") == ImpactType.SCHEDULE
        assert service._map_impact_type("both") == ImpactType.BOTH
    
    @pytest.mark.asyncio
    async def test_empty_budget_analysis(self, service):
        """Test empty budget analysis creation."""
        analysis = service._create_empty_budget_analysis(1000000.0, 400000.0)
        
        assert analysis["baseline_budget"] == 1000000.0
        assert analysis["current_spend"] == 400000.0
        assert analysis["probability_within_budget"] == 1.0
        assert "note" in analysis
    
    @pytest.mark.asyncio
    async def test_empty_schedule_analysis(self, service):
        """Test empty schedule analysis creation."""
        analysis = service._create_empty_schedule_analysis(365.0, 150.0)
        
        assert analysis["baseline_duration"] == 365.0
        assert analysis["elapsed_time"] == 150.0
        assert analysis["probability_on_time"] == 1.0
        assert "note" in analysis
    
    @pytest.mark.asyncio
    async def test_empty_resource_analysis(self, service):
        """Test empty resource analysis creation."""
        analysis = service._create_empty_resource_analysis()
        
        assert analysis["total_resources"] == 0
        assert "note" in analysis
        assert len(analysis["recommendations"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
