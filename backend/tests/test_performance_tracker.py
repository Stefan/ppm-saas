"""
Tests for Performance Tracker
"""

import pytest
from middleware.performance_tracker import PerformanceTracker
from datetime import datetime
import time


class TestPerformanceTracker:
    """Test suite for PerformanceTracker"""
    
    def test_tracker_initialization(self):
        """Test tracker initializes correctly"""
        tracker = PerformanceTracker(slow_query_threshold=1.0)
        
        assert tracker.total_requests == 0
        assert tracker.total_errors == 0
        assert len(tracker.slow_queries) == 0
        assert tracker.slow_query_threshold == 1.0
    
    def test_record_successful_request(self):
        """Test recording a successful request"""
        tracker = PerformanceTracker()
        
        tracker.record_request(
            endpoint="/projects",
            method="GET",
            duration=0.5,
            status_code=200
        )
        
        assert tracker.total_requests == 1
        assert tracker.total_errors == 0
        
        stats = tracker.get_stats()
        assert stats['total_requests'] == 1
        assert 'GET /projects' in stats['endpoint_stats']
    
    def test_record_error_request(self):
        """Test recording a request with error"""
        tracker = PerformanceTracker()
        
        tracker.record_request(
            endpoint="/projects",
            method="POST",
            duration=0.3,
            status_code=500,
            error="Database connection failed"
        )
        
        assert tracker.total_requests == 1
        assert tracker.total_errors == 1
        
        stats = tracker.get_stats()
        assert stats['total_errors'] == 1
    
    def test_slow_query_detection(self):
        """Test slow query detection"""
        tracker = PerformanceTracker(slow_query_threshold=0.5)
        
        # Fast query - should not be tracked
        tracker.record_request(
            endpoint="/health",
            method="GET",
            duration=0.1,
            status_code=200
        )
        
        # Slow query - should be tracked
        tracker.record_request(
            endpoint="/projects",
            method="GET",
            duration=1.5,
            status_code=200
        )
        
        assert len(tracker.slow_queries) == 1
        assert tracker.slow_queries[0]['endpoint'] == 'GET /projects'
        assert tracker.slow_queries[0]['duration'] == 1.5
    
    def test_endpoint_statistics(self):
        """Test endpoint statistics calculation"""
        tracker = PerformanceTracker()
        
        # Record multiple requests to same endpoint
        tracker.record_request("/projects", "GET", 0.1, 200)
        tracker.record_request("/projects", "GET", 0.2, 200)
        tracker.record_request("/projects", "GET", 0.3, 200)
        
        stats = tracker.get_stats()
        endpoint_stats = stats['endpoint_stats']['GET /projects']
        
        assert endpoint_stats['total_requests'] == 3
        assert endpoint_stats['avg_duration'] == pytest.approx(0.2, rel=0.01)
        assert endpoint_stats['min_duration'] == 0.1
        assert endpoint_stats['max_duration'] == 0.3
        assert endpoint_stats['error_rate'] == 0.0
    
    def test_error_rate_calculation(self):
        """Test error rate calculation"""
        tracker = PerformanceTracker()
        
        # 3 successful, 1 error = 25% error rate
        tracker.record_request("/api/test", "GET", 0.1, 200)
        tracker.record_request("/api/test", "GET", 0.1, 200)
        tracker.record_request("/api/test", "GET", 0.1, 200)
        tracker.record_request("/api/test", "GET", 0.1, 500)
        
        stats = tracker.get_stats()
        endpoint_stats = stats['endpoint_stats']['GET /api/test']
        
        assert endpoint_stats['error_rate'] == 25.0
    
    def test_health_status_healthy(self):
        """Test health status when system is healthy"""
        tracker = PerformanceTracker()
        
        # Record some successful requests
        for _ in range(10):
            tracker.record_request("/test", "GET", 0.1, 200)
        
        health = tracker.get_health_status()
        
        assert health['status'] == 'healthy'
        assert health['metrics']['total_requests'] == 10
        assert health['metrics']['error_rate'] == 0.0
    
    def test_health_status_degraded(self):
        """Test health status when system is degraded"""
        tracker = PerformanceTracker(slow_query_threshold=0.5)
        
        # Record some requests with moderate errors
        for _ in range(15):
            tracker.record_request("/test", "GET", 0.1, 200)
        for _ in range(1):
            tracker.record_request("/test", "GET", 0.1, 500)
        
        # Add some slow queries
        for _ in range(12):
            tracker.record_request("/slow", "GET", 1.0, 200)
        
        health = tracker.get_health_status()
        
        assert health['status'] == 'degraded'
    
    def test_health_status_unhealthy(self):
        """Test health status when system is unhealthy"""
        tracker = PerformanceTracker(slow_query_threshold=0.5)
        
        # Record many errors (>10% error rate)
        for _ in range(8):
            tracker.record_request("/test", "GET", 0.1, 200)
        for _ in range(2):
            tracker.record_request("/test", "GET", 0.1, 500)
        
        health = tracker.get_health_status()
        
        assert health['status'] == 'unhealthy'
        assert health['metrics']['error_rate'] == 20.0
    
    def test_reset_stats(self):
        """Test resetting statistics"""
        tracker = PerformanceTracker()
        
        # Record some data
        tracker.record_request("/test", "GET", 0.1, 200)
        tracker.record_request("/test", "GET", 1.5, 200)
        
        assert tracker.total_requests > 0
        assert len(tracker.slow_queries) > 0
        
        # Reset
        tracker.reset_stats()
        
        assert tracker.total_requests == 0
        assert tracker.total_errors == 0
        assert len(tracker.slow_queries) == 0
        assert len(tracker.endpoint_stats) == 0
