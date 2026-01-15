"""
Basic test for Enhanced PMR Service
Verifies service initialization and basic functionality
"""

import pytest
import os
from uuid import uuid4
from datetime import date
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch

# Import service
from services.enhanced_pmr_service import EnhancedPMRService
from models.pmr import (
    EnhancedPMRGenerationRequest, AIInsightCategory, PMRStatus
)


class TestEnhancedPMRServiceBasic:
    """Basic tests for Enhanced PMR Service"""
    
    def test_service_initialization(self):
        """Test that service can be initialized"""
        # Mock Supabase client
        mock_supabase = Mock()
        mock_openai_key = "test-key"
        
        # Initialize service
        service = EnhancedPMRService(mock_supabase, mock_openai_key)
        
        # Verify initialization
        assert service is not None
        assert service.supabase == mock_supabase
        assert service.openai_api_key == mock_openai_key
        assert service.ai_insights_engine is not None
        assert service.rag_agent is not None
    
    @pytest.mark.asyncio
    async def test_create_base_report(self):
        """Test base report creation"""
        # Mock Supabase client
        mock_supabase = Mock()
        mock_supabase.table = Mock(return_value=Mock(
            select=Mock(return_value=Mock(
                eq=Mock(return_value=Mock(
                    execute=Mock(return_value=Mock(
                        data=[{
                            "id": str(uuid4()),
                            "name": "Test Project",
                            "status": "active",
                            "priority": "high"
                        }]
                    ))
                ))
            ))
        ))
        
        # Initialize service
        service = EnhancedPMRService(mock_supabase, "test-key")
        
        # Create request
        request = EnhancedPMRGenerationRequest(
            project_id=uuid4(),
            report_month=date(2024, 1, 1),
            report_year=2024,
            template_id=uuid4(),
            title="Test PMR Report",
            include_ai_insights=True,
            include_monte_carlo=False
        )
        
        user_id = uuid4()
        
        # Create base report
        report = await service._create_base_report(request, user_id)
        
        # Verify report
        assert report is not None
        assert report.project_id == request.project_id
        assert report.title == request.title
        assert report.status == PMRStatus.draft
        assert report.generated_by == user_id
    
    @pytest.mark.asyncio
    async def test_collect_real_time_metrics(self):
        """Test real-time metrics collection"""
        # Mock Supabase client with various responses
        mock_supabase = Mock()
        
        def mock_table(table_name):
            mock_table_obj = Mock()
            mock_table_obj.select = Mock(return_value=mock_table_obj)
            mock_table_obj.eq = Mock(return_value=mock_table_obj)
            mock_table_obj.order = Mock(return_value=mock_table_obj)
            mock_table_obj.limit = Mock(return_value=mock_table_obj)
            
            # Return different data based on table
            if table_name == "financial_data":
                mock_table_obj.execute = Mock(return_value=Mock(
                    data=[{
                        "planned_cost": 1000000,
                        "actual_cost": 800000
                    }]
                ))
            elif table_name == "schedule_data":
                mock_table_obj.execute = Mock(return_value=Mock(
                    data=[{
                        "schedule_performance_index": 1.05
                    }]
                ))
            else:
                mock_table_obj.execute = Mock(return_value=Mock(data=[]))
            
            return mock_table_obj
        
        mock_supabase.table = mock_table
        
        # Initialize service
        service = EnhancedPMRService(mock_supabase, "test-key")
        
        # Collect metrics
        project_id = uuid4()
        metrics = await service._collect_real_time_metrics(project_id)
        
        # Verify metrics
        assert metrics is not None
        assert metrics.last_updated is not None
        assert metrics.budget_utilization == Decimal("0.8")
        assert metrics.schedule_performance_index == Decimal("1.05")
    
    def test_generate_monte_carlo_recommendations(self):
        """Test Monte Carlo recommendation generation"""
        # Mock Supabase client
        mock_supabase = Mock()
        
        # Initialize service
        service = EnhancedPMRService(mock_supabase, "test-key")
        
        # Test high budget risk
        budget_results = {
            "p50": Decimal("1.05"),
            "p80": Decimal("1.10"),
            "p95": Decimal("1.15")
        }
        schedule_results = {}
        
        recommendations = service._generate_monte_carlo_recommendations(
            budget_results, schedule_results
        )
        
        # Verify recommendations
        assert len(recommendations) > 0
        assert any("budget risk" in rec.lower() for rec in recommendations)
    
    def test_build_executive_summary_prompt(self):
        """Test executive summary prompt building"""
        # Mock Supabase client
        mock_supabase = Mock()
        
        # Initialize service
        service = EnhancedPMRService(mock_supabase, "test-key")
        
        # Create mock report
        from models.pmr import EnhancedPMRReport, RealTimeMetrics
        
        report = EnhancedPMRReport(
            project_id=uuid4(),
            report_month=date(2024, 1, 1),
            report_year=2024,
            template_id=uuid4(),
            title="Test Report",
            generated_by=uuid4()
        )
        
        report.real_time_metrics = RealTimeMetrics(
            budget_utilization=Decimal("0.85"),
            schedule_performance_index=Decimal("1.10"),
            risk_score=Decimal("0.25")
        )
        
        context = {
            "project": {
                "name": "Test Project",
                "status": "active",
                "priority": "high"
            },
            "current_metrics": {
                "budget_utilization": Decimal("0.85"),
                "schedule_performance": Decimal("1.10"),
                "risk_score": Decimal("0.25")
            }
        }
        
        # Build prompt
        prompt = service._build_executive_summary_prompt(report, context)
        
        # Verify prompt
        assert "Test Project" in prompt
        assert "Budget Utilization" in prompt
        assert "executive summary" in prompt.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
