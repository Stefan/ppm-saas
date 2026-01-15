"""
Test Enhanced PMR API Endpoints
Basic integration tests for the Enhanced PMR router
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, date
from decimal import Decimal

# Import the FastAPI app
from main import app

# Create test client
client = TestClient(app)


@pytest.fixture
def mock_auth():
    """Mock authentication"""
    with patch('auth.dependencies.get_current_user') as mock:
        mock.return_value = {
            "user_id": str(uuid4()),
            "email": "test@example.com",
            "role": "admin"
        }
        yield mock


@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    with patch('routers.enhanced_pmr.supabase') as mock:
        # Mock project response
        mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": str(uuid4()),
                "name": "Test Project",
                "status": "active"
            }
        ]
        yield mock


@pytest.fixture
def mock_enhanced_pmr_service():
    """Mock Enhanced PMR Service"""
    with patch('routers.enhanced_pmr.enhanced_pmr_service') as mock:
        # Create a mock report
        mock_report = MagicMock()
        mock_report.id = uuid4()
        mock_report.project_id = uuid4()
        mock_report.title = "Test PMR Report"
        mock_report.status = "draft"
        mock_report.report_month = date(2024, 1, 1)
        mock_report.report_year = 2024
        mock_report.ai_insights = []
        mock_report.ai_generated_summary = "Test summary"
        mock_report.ai_confidence_scores = {}
        mock_report.monte_carlo_analysis = None
        mock_report.collaboration_session = None
        mock_report.collaboration_enabled = False
        mock_report.real_time_metrics = None
        mock_report.generated_by = uuid4()
        mock_report.generated_at = datetime.utcnow()
        mock_report.last_modified = datetime.utcnow()
        mock_report.version = 1
        mock_report.total_edits = 0
        mock_report.total_collaborators = 0
        
        mock.generate_enhanced_pmr.return_value = mock_report
        yield mock


class TestEnhancedPMREndpoints:
    """Test Enhanced PMR API endpoints"""
    
    def test_health_check(self, mock_auth):
        """Test health check endpoint"""
        response = client.get("/api/reports/pmr/health")
        assert response.status_code == 200
        data = response.json()
        assert "service_available" in data
        assert "database_connected" in data
        assert "features" in data
    
    def test_generate_pmr_missing_service(self, mock_auth):
        """Test PMR generation when service is unavailable"""
        with patch('routers.enhanced_pmr.enhanced_pmr_service', None):
            response = client.post(
                "/api/reports/pmr/generate",
                json={
                    "project_id": str(uuid4()),
                    "report_month": "2024-01-01",
                    "report_year": 2024,
                    "template_id": str(uuid4()),
                    "title": "Test Report"
                }
            )
            assert response.status_code == 503
    
    def test_generate_pmr_project_not_found(self, mock_auth, mock_supabase):
        """Test PMR generation with non-existent project"""
        # Mock empty project response
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        with patch('routers.enhanced_pmr.enhanced_pmr_service', MagicMock()):
            response = client.post(
                "/api/reports/pmr/generate",
                json={
                    "project_id": str(uuid4()),
                    "report_month": "2024-01-01",
                    "report_year": 2024,
                    "template_id": str(uuid4()),
                    "title": "Test Report"
                }
            )
            assert response.status_code == 404
    
    def test_get_pmr_not_found(self, mock_auth, mock_supabase):
        """Test retrieving non-existent PMR"""
        # Mock empty report response
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        report_id = uuid4()
        response = client.get(f"/api/reports/pmr/{report_id}")
        assert response.status_code == 404
    
    def test_chat_edit_missing_service(self, mock_auth):
        """Test chat edit when service is unavailable"""
        with patch('routers.enhanced_pmr.enhanced_pmr_service', None):
            response = client.post(
                f"/api/reports/pmr/{uuid4()}/edit/chat",
                json={
                    "message": "Update the executive summary"
                }
            )
            assert response.status_code == 503
    
    def test_chat_edit_report_not_found(self, mock_auth, mock_supabase):
        """Test chat edit with non-existent report"""
        # Mock empty report response
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        with patch('routers.enhanced_pmr.enhanced_pmr_service', MagicMock()):
            response = client.post(
                f"/api/reports/pmr/{uuid4()}/edit/chat",
                json={
                    "message": "Update the executive summary"
                }
            )
            assert response.status_code == 404
    
    def test_update_section_missing_database(self, mock_auth):
        """Test section update when database is unavailable"""
        with patch('routers.enhanced_pmr.supabase', None):
            response = client.post(
                f"/api/reports/pmr/{uuid4()}/edit/section",
                json={
                    "section_id": "executive_summary",
                    "content": {"text": "Updated content"},
                    "merge_strategy": "replace"
                }
            )
            assert response.status_code == 503
    
    def test_get_ai_suggestions_missing_service(self, mock_auth):
        """Test AI suggestions when service is unavailable"""
        with patch('routers.enhanced_pmr.enhanced_pmr_service', None):
            response = client.get(f"/api/reports/pmr/{uuid4()}/edit/suggestions")
            assert response.status_code == 503
    
    def test_list_project_reports_missing_database(self, mock_auth):
        """Test listing reports when database is unavailable"""
        with patch('routers.enhanced_pmr.supabase', None):
            response = client.get(f"/api/reports/pmr/projects/{uuid4()}/reports")
            assert response.status_code == 503


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
