"""
Performance Tracking Middleware

Tracks all API requests with timing, status codes, and error information.
Stores metrics in memory for real-time dashboard display.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    In-memory performance metrics tracker.
    
    Tracks:
    - Request counts per endpoint
    - Response times (min, max, avg)
    - Error rates
    - Recent slow queries
    - Requests per minute
    """
    
    def __init__(self, slow_query_threshold: float = 1.0):
        """
        Initialize performance tracker.
        
        Args:
            slow_query_threshold: Threshold in seconds for slow query detection
        """
        self.slow_query_threshold = slow_query_threshold
        self.start_time = datetime.now()
        
        # Endpoint statistics
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_requests': 0,
            'total_duration': 0.0,
            'min_duration': float('inf'),
            'max_duration': 0.0,
            'error_count': 0,
            'status_codes': defaultdict(int),
            'recent_requests': []  # Last 100 requests for RPM calculation
        })
        
        # Global statistics
        self.total_requests = 0
        self.total_errors = 0
        
        # Slow queries tracking
        self.slow_queries: List[Dict[str, Any]] = []
        self.max_slow_queries = 50  # Keep last 50 slow queries
        
    def record_request(
        self,
        endpoint: str,
        method: str,
        duration: float,
        status_code: int,
        error: Optional[str] = None
    ):
        """Record a request with its metrics."""
        now = datetime.now()
        
        # Update global stats
        self.total_requests += 1
        if status_code >= 400:
            self.total_errors += 1
        
        # Update endpoint stats
        stats = self.endpoint_stats[f"{method} {endpoint}"]
        stats['total_requests'] += 1
        stats['total_duration'] += duration
        stats['min_duration'] = min(stats['min_duration'], duration)
        stats['max_duration'] = max(stats['max_duration'], duration)
        stats['status_codes'][status_code] += 1
        
        if status_code >= 400:
            stats['error_count'] += 1
        
        # Track recent requests for RPM calculation
        stats['recent_requests'].append(now)
        # Keep only last 100 requests
        if len(stats['recent_requests']) > 100:
            stats['recent_requests'] = stats['recent_requests'][-100:]
        
        # Track slow queries
        if duration >= self.slow_query_threshold:
            self.slow_queries.append({
                'endpoint': f"{method} {endpoint}",
                'duration': duration,
                'timestamp': now.isoformat(),
                'status_code': status_code,
                'error': error
            })
            # Keep only recent slow queries
            if len(self.slow_queries) > self.max_slow_queries:
                self.slow_queries = self.slow_queries[-self.max_slow_queries:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        endpoint_stats = {}
        
        for endpoint, stats in self.endpoint_stats.items():
            total_requests = stats['total_requests']
            if total_requests == 0:
                continue
            
            # Calculate average duration
            avg_duration = stats['total_duration'] / total_requests
            
            # Calculate error rate
            error_rate = (stats['error_count'] / total_requests) * 100
            
            # Calculate requests per minute
            rpm = self._calculate_rpm(stats['recent_requests'])
            
            endpoint_stats[endpoint] = {
                'total_requests': total_requests,
                'avg_duration': avg_duration,
                'min_duration': stats['min_duration'] if stats['min_duration'] != float('inf') else 0,
                'max_duration': stats['max_duration'],
                'error_rate': round(error_rate, 2),
                'requests_per_minute': rpm
            }
        
        return {
            'total_requests': self.total_requests,
            'total_errors': self.total_errors,
            'slow_queries_count': len(self.slow_queries),
            'endpoint_stats': endpoint_stats,
            'recent_slow_queries': self.slow_queries[-10:],  # Last 10 slow queries
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
        }
    
    def _calculate_rpm(self, recent_requests: List[datetime]) -> float:
        """Calculate requests per minute from recent requests."""
        if not recent_requests:
            return 0.0
        
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        # Count requests in the last minute
        recent_count = sum(1 for req_time in recent_requests if req_time >= one_minute_ago)
        
        return round(recent_count, 2)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status based on current metrics."""
        stats = self.get_stats()
        
        # Calculate error rate
        error_rate = 0.0
        if stats['total_requests'] > 0:
            error_rate = (stats['total_errors'] / stats['total_requests']) * 100
        
        # Determine health status
        if error_rate > 10 or stats['slow_queries_count'] > 20:
            status = 'unhealthy'
        elif error_rate > 5 or stats['slow_queries_count'] > 10:
            status = 'degraded'
        else:
            status = 'healthy'
        
        # Calculate uptime
        uptime_seconds = stats['uptime_seconds']
        uptime_hours = uptime_seconds / 3600
        uptime_str = f"{int(uptime_hours)}h {int((uptime_seconds % 3600) / 60)}m"
        
        return {
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                'total_requests': stats['total_requests'],
                'error_rate': round(error_rate, 2),
                'slow_queries': stats['slow_queries_count'],
                'uptime': uptime_str
            },
            'cache_status': 'in-memory'
        }
    
    def reset_stats(self):
        """Reset all statistics."""
        self.endpoint_stats.clear()
        self.total_requests = 0
        self.total_errors = 0
        self.slow_queries.clear()
        self.start_time = datetime.now()
        logger.info("Performance statistics reset")


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track request performance.
    """
    
    def __init__(self, app, tracker: PerformanceTracker):
        super().__init__(app)
        self.tracker = tracker
    
    async def dispatch(self, request: Request, call_next):
        """Process request and track performance."""
        # Skip tracking for health check endpoints to avoid noise
        if request.url.path in ['/health', '/']:
            return await call_next(request)
        
        start_time = time.time()
        error_message = None
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            error_message = str(e)
            status_code = 500
            # Re-raise to let FastAPI handle it
            raise
        finally:
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            self.tracker.record_request(
                endpoint=request.url.path,
                method=request.method,
                duration=duration,
                status_code=status_code,
                error=error_message
            )
        
        return response


# Global tracker instance
performance_tracker = PerformanceTracker(slow_query_threshold=1.0)
