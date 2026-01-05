#!/usr/bin/env python3
"""
Test AI Implementation
This script tests the AI features implementation locally and in production
"""

import requests
import json
import time
from datetime import datetime

# Configuration
LOCAL_URL = "http://localhost:8000"
PRODUCTION_URL = "https://orka-ppm.onrender.com"

def test_endpoint(base_url, endpoint, method="GET", data=None, headers=None):
    """Test a single endpoint"""
    url = f"{base_url}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=30)
        
        return {
            "success": True,
            "status_code": response.status_code,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "response_time": response.elapsed.total_seconds()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response_time": 0
        }

def test_ai_features(base_url, auth_token=None):
    """Test all AI features"""
    print(f"\n🧪 Testing AI features at {base_url}")
    
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    tests = [
        {
            "name": "Health Check",
            "endpoint": "/",
            "method": "GET"
        },
        {
            "name": "RAG Query",
            "endpoint": "/ai/rag-query",
            "method": "POST",
            "data": {
                "query": "Show me all projects that are at risk",
                "conversation_id": f"test_{int(time.time())}"
            }
        },
        {
            "name": "Resource Optimizer",
            "endpoint": "/ai/resource-optimizer",
            "method": "POST",
            "data": {}
        },
        {
            "name": "Risk Forecast",
            "endpoint": "/ai/risk-forecast",
            "method": "POST",
            "data": {}
        },
        {
            "name": "AI Metrics",
            "endpoint": "/ai/metrics",
            "method": "GET"
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"  🔄 Testing {test['name']}...")
        
        result = test_endpoint(
            base_url, 
            test["endpoint"], 
            test["method"], 
            test.get("data"), 
            headers
        )
        
        result["test_name"] = test["name"]
        results.append(result)
        
        if result["success"]:
            status_icon = "✅" if result["status_code"] < 400 else "⚠️"
            print(f"    {status_icon} {result['status_code']} - {result['response_time']:.2f}s")
            
            # Show response preview for AI endpoints
            if "/ai/" in test["endpoint"] and result.get("response"):
                response = result["response"]
                if isinstance(response, dict):
                    if "response" in response:
                        print(f"    💬 AI Response: {response['response'][:100]}...")
                    elif "suggestions" in response:
                        print(f"    🎯 Suggestions: {len(response['suggestions'])} found")
                    elif "predictions" in response:
                        print(f"    🔮 Predictions: {len(response['predictions'])} risks")
        else:
            print(f"    ❌ Failed: {result['error']}")
    
    return results

def main():
    print("🚀 AI Implementation Test Suite")
    print("=" * 50)
    
    # Test local development server
    print("\n📍 Testing Local Development Server")
    local_results = test_ai_features(LOCAL_URL)
    
    # Test production server
    print("\n📍 Testing Production Server")
    production_results = test_ai_features(PRODUCTION_URL)
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    
    def print_summary(results, environment):
        successful = len([r for r in results if r["success"] and r.get("status_code", 0) < 400])
        total = len(results)
        avg_response_time = sum(r["response_time"] for r in results if r["success"]) / max(1, len([r for r in results if r["success"]]))
        
        print(f"{environment}:")
        print(f"  ✅ Success Rate: {successful}/{total} ({successful/total*100:.1f}%)")
        print(f"  ⏱️  Avg Response Time: {avg_response_time:.2f}s")
        
        # Show failed tests
        failed = [r for r in results if not r["success"] or r.get("status_code", 0) >= 400]
        if failed:
            print(f"  ❌ Failed Tests:")
            for f in failed:
                print(f"    - {f['test_name']}: {f.get('error', f.get('status_code'))}")
        print()
    
    print_summary(local_results, "Local Development")
    print_summary(production_results, "Production")
    
    # AI-specific checks
    print("🤖 AI Features Status")
    print("=" * 50)
    
    for env_name, results in [("Local", local_results), ("Production", production_results)]:
        ai_tests = [r for r in results if "/ai/" in r.get("test_name", "").lower()]
        if ai_tests:
            ai_available = any("ai_unavailable" not in str(r.get("response", "")) for r in ai_tests if r["success"])
            print(f"{env_name}: {'🟢 AI Available' if ai_available else '🟡 AI Mock Mode'}")
    
    print("\n🎯 Recommendations:")
    print("- If AI is in mock mode, set OPENAI_API_KEY in backend/.env")
    print("- Apply database migration: python backend/apply_ai_migration.py")
    print("- Check backend logs for detailed error information")
    print("- Test individual endpoints at /docs for interactive testing")

if __name__ == "__main__":
    main()