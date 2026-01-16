#!/bin/bash

# Dashboard Backend Connection Test Script
# This script tests the connection between frontend and backend APIs

echo "🔍 Testing Dashboard Backend Connection..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is running
echo "1. Checking if Python backend is running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is running${NC}"
    BACKEND_RUNNING=true
else
    echo -e "${YELLOW}⚠ Backend is not running (will test fallback mode)${NC}"
    BACKEND_RUNNING=false
fi
echo ""

# Check if frontend is running
echo "2. Checking if Next.js frontend is running..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is running${NC}"
    FRONTEND_RUNNING=true
else
    echo -e "${RED}✗ Frontend is not running${NC}"
    echo "Please start the frontend with: npm run dev"
    exit 1
fi
echo ""

# Test projects API
echo "3. Testing /api/projects endpoint..."
PROJECTS_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:3000/api/projects)
HTTP_CODE=$(echo "$PROJECTS_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$PROJECTS_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Projects API responded with 200${NC}"
    
    # Check data source
    DATA_SOURCE=$(curl -s -I http://localhost:3000/api/projects | grep -i "x-data-source" | cut -d' ' -f2 | tr -d '\r')
    if [ ! -z "$DATA_SOURCE" ]; then
        echo "  Data Source: $DATA_SOURCE"
    fi
    
    # Count projects
    PROJECT_COUNT=$(echo "$RESPONSE_BODY" | grep -o '"id"' | wc -l | tr -d ' ')
    echo "  Projects returned: $PROJECT_COUNT"
else
    echo -e "${RED}✗ Projects API failed with code $HTTP_CODE${NC}"
fi
echo ""

# Test dashboard quick-stats API
echo "4. Testing /api/optimized/dashboard/quick-stats endpoint..."
STATS_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:3000/api/optimized/dashboard/quick-stats)
HTTP_CODE=$(echo "$STATS_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$STATS_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Quick Stats API responded with 200${NC}"
    
    # Check data source
    DATA_SOURCE=$(curl -s -I http://localhost:3000/api/optimized/dashboard/quick-stats | grep -i "x-data-source" | cut -d' ' -f2 | tr -d '\r')
    if [ ! -z "$DATA_SOURCE" ]; then
        echo "  Data Source: $DATA_SOURCE"
    fi
    
    # Extract some stats
    TOTAL_PROJECTS=$(echo "$RESPONSE_BODY" | grep -o '"total_projects":[0-9]*' | cut -d':' -f2)
    ACTIVE_PROJECTS=$(echo "$RESPONSE_BODY" | grep -o '"active_projects":[0-9]*' | cut -d':' -f2)
    
    if [ ! -z "$TOTAL_PROJECTS" ]; then
        echo "  Total Projects: $TOTAL_PROJECTS"
        echo "  Active Projects: $ACTIVE_PROJECTS"
    fi
else
    echo -e "${RED}✗ Quick Stats API failed with code $HTTP_CODE${NC}"
fi
echo ""

# Test dashboard projects-summary API
echo "5. Testing /api/optimized/dashboard/projects-summary endpoint..."
SUMMARY_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:3000/api/optimized/dashboard/projects-summary?limit=5)
HTTP_CODE=$(echo "$SUMMARY_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$SUMMARY_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Projects Summary API responded with 200${NC}"
    
    # Check data source
    DATA_SOURCE=$(curl -s -I "http://localhost:3000/api/optimized/dashboard/projects-summary?limit=5" | grep -i "x-data-source" | cut -d' ' -f2 | tr -d '\r')
    if [ ! -z "$DATA_SOURCE" ]; then
        echo "  Data Source: $DATA_SOURCE"
    fi
    
    # Count projects
    PROJECT_COUNT=$(echo "$RESPONSE_BODY" | grep -o '"id"' | wc -l | tr -d ' ')
    echo "  Projects returned: $PROJECT_COUNT"
else
    echo -e "${RED}✗ Projects Summary API failed with code $HTTP_CODE${NC}"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$BACKEND_RUNNING" = true ]; then
    echo -e "${GREEN}✓ Backend is running - Dashboard should show REAL data${NC}"
    echo "  Check response headers for: X-Data-Source: backend-real"
else
    echo -e "${YELLOW}⚠ Backend is not running - Dashboard is using FALLBACK data${NC}"
    echo "  Check response headers for: X-Data-Source: fallback-mock"
    echo ""
    echo "To see real data, start the backend:"
    echo "  cd backend && python -m uvicorn main:app --reload --port 8000"
fi

echo ""
echo "View the dashboard at: http://localhost:3000/dashboards"
echo ""
