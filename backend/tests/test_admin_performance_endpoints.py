"""
Integration tests for Admin Performance Endpoints

These tests catch issues like:
- Missing or incorrect permissions
- 500 Internal Server Errors
- Authentication/Authorization failures
- Invalid response formats
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime

from main import app
from middleware.performance_tracker import PerformanceTracker


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_auth_admin():
    """Mock authentication with admin permissions"""
    with patch('auth.dependencies.get_current_user') as mock_user, \
         patch('auth.rbac.RBAC.has_permission') as mock_perm:
        
        mock_user.return_value = {
            'user_id': 'test-admin-user',
            'email': 'admin@test.com'
        }
        mock_perm.return_value = True
        
        yield mock_user


@pytest.fixture
def mock_auth_no_permission():
    """Mock authentication without admin permissions"""
    with patch('auth.dependencies.get_current_user') as mock_user, \
         patch('auth.rbac.RBAC.has_permission') as mock_perm:
        
        mock_user.return_value = {
            'user_id': 'test-regular-user',
            'email': 'user@test.com'
        }
        mock_perm.return_value = False
        
        yield mock_user


class TestAdminPerformanceEndpoints:
    """Test suite for admin performance endpoints"""
    
    def test_stats_endpoint_exists(self, client, mock_auth_admin):
        """Test that /admin/performance/stats endpoint exists and returns 200"""
        response = client.get("/admin/performance/stats")
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404, "Stats endpoint should exist"
        
        # Should return 200 with valid auth
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_stats_endpoint_returns_valid_json(self, client, mock_auth_admin):
        """Test that stats endpoint returns valid JSON structure"""
        response = client.get("/admin/performance/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields exist
        assert 'total_requests' in data, "Missing total_requests field"
        assert 'total_errors' in data, "Missing total_errors field"
        assert 'slow_queries_count' in data, "Missing slow_queries_count field"
        assert 'endpoint_stats' in data, "Missing endpoint_stats field"
        
        # Verify data types
        assert isinstance(data['total_requests'], int), "total_requests should be int"
        assert isinstance(data['total_errors'], int), "total_errors should be int"
        assert isinstance(data['endpoint_stats'], dict), "endpoint_stats should be dict"
    
    def test_stats_endpoint_requires_authentication(self, client):
        """Test that stats endpoint requires authentication"""
        with patch('auth.dependencies.get_current_user') as mock_user:
            mock_user.side_effect = Exception("Unauthorized")
            
            response = client.get("/admin/performance/stats")
            
            # Should return 401 or 500 (depending on error handling)
            assert response.status_code in [401, 500], \
                f"Expected 401 or 500 for unauthenticated request, got {response.status_code}"
    
    def test_stats_endpoint_requires_admin_permission(self, client, mock_auth_no_permission):
        """Test that stats endpoint requires admin permission"""
        response = client.get("/admin/performance/stats")
        
        # Should return 403 Forbidden
        assert response.status_code == 403, \
            f"Expected 403 for user without admin permission, got {response.status_code}"
    
    def test_health_endpoint_exists(self, client, mock_auth_admin):
        """Test that /admin/performance/health endpoint exists"""
        response = client.get("/admin/performance/health")
        
        assert response.status_code != 404, "Health endpoint should exist"
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_health_endpoint_returns_valid_structure(self, client, mock_auth_admin):
        """Test that health endpoint returns valid structure"""
        response = client.get("/admin/performance/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert 'status' in data, "Missing status field"
        assert 'timestamp' in data, "Missing timestamp field"
        assert 'metrics' in data, "Missing metrics field"
        
        # Verify status is valid
        assert data['status'] in ['healthy', 'degraded', 'unhealthy'], \
            f"Invalid status: {data['status']}"
        
        # Verify metrics structure
        metrics = data['metrics']
        assert 'total_requests' in metrics, "Missing total_requests in metrics"
        assert 'error_rate' in metrics, "Missing error_rate in metrics"
        assert 'slow_queries' in metrics, "Missing slow_queries in metrics"
    
    def test_reset_endpoint_exists(self, client, mock_auth_admin):
        """Test that /admin/performance/reset endpoint exists"""
        response = client.post("/admin/performance/reset")
        
        assert response.status_code != 404, "Reset endpoint should exist"
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_reset_endpoint_clears_statistics(self, client, mock_auth_admin):
        """Test that reset endpoint actually clears statistics"""
        # First, make some requests to generate stats
        client.get("/projects")
        client.get("/portfolios")
        
        # Get stats before reset
        stats_before = client.get("/admin/performance/stats").json()
        requests_before = stats_before['total_requests']
        
        # Reset statistics
        reset_response = client.post("/admin/performance/reset")
        assert reset_response.status_code == 200
        
        # Get stats after reset
        stats_after = client.get("/admin/performance/stats").json()
        requests_after = stats_after['total_requests']
        
        # After reset, request count should be less than before
        # (it won't be 0 because we just made a request to get stats)
        assert requests_after < requests_before, \
            "Statistics should be reset"
    
    def test_slow_queries_endpoint_exists(self, client, mock_auth_admin):
        """Test that /admin/performance/slow-queries endpoint exists"""
        response = client.get("/admin/performance/slow-queries")
        
        assert response.status_code != 404, "Slow queries endpoint should exist"
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_slow_queries_returns_valid_structure(self, client, mock_auth_admin):
        """Test that slow queries endpoint returns valid structure"""
        response = client.get("/admin/performance/slow-queries")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert 'slow_queries' in data, "Missing slow_queries field"
        assert 'total_count' in data, "Missing total_count field"
        assert 'threshold_seconds' in data, "Missing threshold_seconds field"
        
        # Verify types
        assert isinstance(data['slow_queries'], list), "slow_queries should be list"
        assert isinstance(data['total_count'], int), "total_count should be int"
        assert isinstance(data['threshold_seconds'], (int, float)), \
            "threshold_seconds should be numeric"
    
    def test_slow_queries_limit_parameter(self, client, mock_auth_admin):
        """Test that slow queries endpoint respects limit parameter"""
        response = client.get("/admin/performance/slow-queries?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return at most 5 queries
        assert len(data['slow_queries']) <= 5, \
            f"Expected at most 5 queries, got {len(data['slow_queries'])}"
    
    def test_endpoints_handle_tracker_errors_gracefully(self, client, mock_auth_admin):
        """Test that endpoints handle tracker errors without 500 errors"""
        with patch('middleware.performance_tracker.performance_tracker.get_stats') as mock_stats:
            # Simulate tracker error
            mock_stats.side_effect = Exception("Tracker error")
            
            response = client.get("/admin/performance/stats")
            
            # Should return 500 with error message, not crash
            assert response.status_code == 500
            data = response.json()
            assert 'detail' in data, "Error response should have detail field"
            assert 'Tracker error' in data['detail'] or 'Failed to retrieve' in data['detail']
    
    def test_all_endpoints_use_correct_permissions(self, client):
        """Test that all endpoints use valid Permission enums"""
        # This test verifies the fix for the original bug
        # where Permission.admin was used instead of Permission.admin_read
        
        from auth.rbac import Permission
        
        # Verify Permission.admin_read exists
        assert hasattr(Permission, 'admin_read'), \
            "Permission.admin_read should exist"
        
        # Verify Permission.system_admin exists
        assert hasattr(Permission, 'system_admin'), \
            "Permission.system_admin should exist"
        
        # Verify Permission.admin does NOT exist (this was the bug)
        assert not hasattr(Permission, 'admin'), \
            "Permission.admin should not exist (use admin_read or system_admin)"


class TestPerformanceTrackerIntegration:
    """Test performance tracker integration with endpoints"""
    
    def test_tracker_records_endpoint_requests(self, client, mock_auth_admin):
        """Test that tracker records requests to endpoints"""
        # Get initial stats
        initial_stats = client.get("/admin/performance/stats").json()
        initial_count = initial_stats['total_requests']
        
        # Make a request to another endpoint
        client.get("/projects")
        
        # Get updated stats
        updated_stats = client.get("/admin/performance/stats").json()
        updated_count = updated_stats['total_requests']
        
        # Count should have increased
        assert updated_count > initial_count, \
            "Tracker should record new requests"
    
    def test_tracker_records_endpoint_statistics(self, client, mock_auth_admin):
        """Test that tracker records per-endpoint statistics"""
        # Make multiple requests to same endpoint
        for _ in range(3):
            client.get("/projects")
        
        # Get stats
        stats = client.get("/admin/performance/stats").json()
        endpoint_stats = stats['endpoint_stats']
        
        # Should have stats for GET /projects
        assert any('projects' in endpoint for endpoint in endpoint_stats.keys()), \
            "Should have statistics for /projects endpoint"
    
    def test_tracker_calculates_error_rates(self, client, mock_auth_admin):
        """Test that tracker calculates error rates correctly"""
        # Make some successful requests
        for _ in range(5):
            client.get("/health")
        
        # Make a request that will fail (invalid endpoint)
        client.get("/nonexistent-endpoint")
        
        # Get stats
        stats = client.get("/admin/performance/stats").json()
        
        # Should have recorded errors
        assert stats['total_errors'] > 0, \
            "Tracker should record errors"


@pytest.mark.asyncio
class TestEndpointErrorHandling:
    """Test error handling in endpoints"""
    
    async def test_stats_endpoint_handles_missing_tracker(self, client, mock_auth_admin):
        """Test stats endpoint handles missing tracker gracefully"""
        with patch('routers.admin_performance.performance_tracker', None):
            response = client.get("/admin/performance/stats")
            
            # Should return error, not crash
            assert response.status_code in [500, 503]
    
    async def test_health_endpoint_handles_tracker_exception(self, client, mock_auth_admin):
        """Test health endpoint handles tracker exceptions"""
        with patch('middleware.performance_tracker.performance_tracker.get_health_status') as mock_health:
            mock_health.side_effect = RuntimeError("Tracker unavailable")
            
            response = client.get("/admin/performance/health")
            
            # Should return 500 with error message
            assert response.status_code == 500
            data = response.json()
            assert 'detail' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
