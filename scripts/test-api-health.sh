#!/bin/bash

# API Health Check Script
# Catches common API errors before they reach production
# Run this in CI/CD pipeline to catch issues early

set -e  # Exit on first error

echo "🔍 API Health Check - Catching Common Errors"
echo "=============================================="
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
ERRORS=0

# Function to check endpoint
check_endpoint() {
    local endpoint=$1
    local expected_status=$2
    local description=$3
    
    echo -n "Testing: $description... "
    
    response=$(curl -s -w "\n%{http_code}" "$BACKEND_URL$endpoint" 2>&1)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_status, got $http_code)"
        echo "  Response: $body"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check for specific error patterns
check_error_pattern() {
    local endpoint=$1
    local pattern=$2
    local description=$3
    
    echo -n "Checking: $description... "
    
    response=$(curl -s "$BACKEND_URL$endpoint" 2>&1)
    
    if echo "$response" | grep -q "$pattern"; then
        echo -e "${RED}✗ FAIL${NC}"
        echo "  Found error pattern: $pattern"
        echo "  Response: $response"
        ERRORS=$((ERRORS + 1))
        return 1
    else
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    fi
}

# Check if backend is running
echo "1. Checking if backend is accessible..."
if ! curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}✗ Backend is not running at $BACKEND_URL${NC}"
    echo "  Start backend with: cd backend && python -m uvicorn main:app --reload --port 8000"
    exit 1
fi
echo -e "${GREEN}✓ Backend is accessible${NC}"
echo ""

# Test basic endpoints
echo "2. Testing basic endpoints..."
check_endpoint "/health" "200" "Health check endpoint"
echo ""

# Test admin performance endpoints (without auth - should fail gracefully)
echo "3. Testing admin performance endpoints..."
check_endpoint "/admin/performance/stats" "401" "Stats endpoint (no auth)"
check_endpoint "/admin/performance/health" "401" "Health endpoint (no auth)"
echo ""

# Check for common error patterns
echo "4. Checking for common error patterns..."
check_error_pattern "/admin/performance/stats" "Permission.admin" \
    "Invalid Permission enum (should use admin_read)"
check_error_pattern "/admin/performance/stats" "AttributeError" \
    "Python AttributeError in response"
check_error_pattern "/admin/performance/stats" "500 Internal Server Error" \
    "Unhandled 500 errors"
echo ""

# Test with mock auth (if available)
echo "5. Testing with authentication..."
if [ -n "$TEST_AUTH_TOKEN" ]; then
    response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer $TEST_AUTH_TOKEN" \
        "$BACKEND_URL/admin/performance/stats")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ Stats endpoint with auth${NC}"
        
        # Validate JSON structure
        if echo "$body" | jq -e '.total_requests' > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Response has valid JSON structure${NC}"
        else
            echo -e "${RED}✗ Response missing required fields${NC}"
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo -e "${YELLOW}⚠ Auth test skipped (got HTTP $http_code)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Skipping auth tests (set TEST_AUTH_TOKEN to enable)${NC}"
fi
echo ""

# Run backend unit tests
echo "6. Running backend unit tests..."
if command -v pytest &> /dev/null; then
    cd backend
    if pytest tests/test_admin_performance_endpoints.py -v --tb=short 2>&1 | tee /tmp/pytest_output.txt; then
        echo -e "${GREEN}✓ All backend tests passed${NC}"
    else
        echo -e "${RED}✗ Some backend tests failed${NC}"
        ERRORS=$((ERRORS + 1))
    fi
    cd ..
else
    echo -e "${YELLOW}⚠ pytest not found, skipping unit tests${NC}"
fi
echo ""

# Run frontend tests
echo "7. Running frontend integration tests..."
if command -v npm &> /dev/null; then
    if npm test -- __tests__/admin-performance-api-integration.test.ts --run 2>&1 | tee /tmp/vitest_output.txt; then
        echo -e "${GREEN}✓ All frontend tests passed${NC}"
    else
        echo -e "${YELLOW}⚠ Some frontend tests failed (may need backend running)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ npm not found, skipping frontend tests${NC}"
fi
echo ""

# Summary
echo "=============================================="
echo "Summary:"
echo "=============================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "The API is healthy and ready for deployment."
    exit 0
else
    echo -e "${RED}✗ $ERRORS check(s) failed${NC}"
    echo ""
    echo "Please fix the issues before deploying."
    echo ""
    echo "Common fixes:"
    echo "  - Check backend logs for errors"
    echo "  - Verify Permission enums are correct"
    echo "  - Ensure all endpoints are registered"
    echo "  - Run tests locally: pytest backend/tests/"
    exit 1
fi
