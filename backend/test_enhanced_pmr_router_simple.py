"""
Simple test to verify Enhanced PMR router structure
Tests the router without full app integration
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_router_import():
    """Test that the router can be imported"""
    try:
        from routers.enhanced_pmr import router
        assert router is not None
        print("✅ Router imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import router: {e}")
        return False


def test_router_prefix():
    """Test that the router has the correct prefix"""
    try:
        from routers.enhanced_pmr import router
        assert router.prefix == "/api/reports/pmr"
        print("✅ Router prefix is correct: /api/reports/pmr")
        return True
    except Exception as e:
        print(f"❌ Failed to verify router prefix: {e}")
        return False


def test_router_tags():
    """Test that the router has the correct tags"""
    try:
        from routers.enhanced_pmr import router
        assert "Enhanced PMR" in router.tags
        print("✅ Router tags are correct")
        return True
    except Exception as e:
        print(f"❌ Failed to verify router tags: {e}")
        return False


def test_router_endpoints():
    """Test that the router has the expected endpoints"""
    try:
        from routers.enhanced_pmr import router
        
        # Get all routes
        routes = [route.path for route in router.routes]
        
        # Expected endpoints
        expected_endpoints = [
            "/api/reports/pmr/generate",
            "/api/reports/pmr/{report_id}",
            "/api/reports/pmr/projects/{project_id}/reports",
            "/api/reports/pmr/{report_id}/edit/chat",
            "/api/reports/pmr/{report_id}/edit/section",
            "/api/reports/pmr/{report_id}/edit/suggestions",
            "/api/reports/pmr/health"
        ]
        
        print(f"Found {len(routes)} routes:")
        for route in routes:
            print(f"  - {route}")
        
        # Check that all expected endpoints exist
        for endpoint in expected_endpoints:
            if endpoint not in routes:
                print(f"❌ Missing endpoint: {endpoint}")
                return False
        
        print("✅ All expected endpoints are present")
        return True
    except Exception as e:
        print(f"❌ Failed to verify router endpoints: {e}")
        return False


def test_endpoint_methods():
    """Test that endpoints have the correct HTTP methods"""
    try:
        from routers.enhanced_pmr import router
        
        # Check specific endpoints and their methods
        endpoint_methods = {}
        for route in router.routes:
            endpoint_methods[route.path] = route.methods
        
        # Verify POST /generate
        if "POST" not in endpoint_methods.get("/api/reports/pmr/generate", set()):
            print("❌ /generate should accept POST")
            return False
        
        # Verify GET /{report_id}
        if "GET" not in endpoint_methods.get("/api/reports/pmr/{report_id}", set()):
            print("❌ /{report_id} should accept GET")
            return False
        
        # Verify POST /edit/chat
        if "POST" not in endpoint_methods.get("/api/reports/pmr/{report_id}/edit/chat", set()):
            print("❌ /edit/chat should accept POST")
            return False
        
        print("✅ Endpoint HTTP methods are correct")
        return True
    except Exception as e:
        print(f"❌ Failed to verify endpoint methods: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("Testing Enhanced PMR Router")
    print("="*60 + "\n")
    
    tests = [
        test_router_import,
        test_router_prefix,
        test_router_tags,
        test_router_endpoints,
        test_endpoint_methods
    ]
    
    results = []
    for test in tests:
        print(f"\nRunning: {test.__name__}")
        print("-" * 60)
        result = test()
        results.append(result)
        print()
    
    print("="*60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("="*60)
    
    return all(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
