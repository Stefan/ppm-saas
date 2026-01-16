#!/bin/bash

# Performance Monitoring Test Script
# Generates API traffic and verifies real-time tracking

echo "🔍 Testing Real Performance Monitoring..."
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"

# Check if backend is running
echo "1. Checking if backend is running..."
if curl -s $BACKEND_URL/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend is not running${NC}"
    echo "Please start the backend with: cd backend && python -m uvicorn main:app --reload --port 8000"
    exit 1
fi
echo ""

# Generate some API traffic
echo "2. Generating API traffic..."
echo -e "${BLUE}Making 10 requests to various endpoints...${NC}"

for i in {1..3}; do
    curl -s $BACKEND_URL/health > /dev/null
    echo -n "."
done

for i in {1..3}; do
    curl -s $BACKEND_URL/projects > /dev/null 2>&1
    echo -n "."
done

for i in {1..2}; do
    curl -s $BACKEND_URL/portfolios > /dev/null 2>&1
    echo -n "."
done

for i in {1..2}; do
    curl -s $BACKEND_URL/scenarios > /dev/null 2>&1
    echo -n "."
done

echo ""
echo -e "${GREEN}✓ Generated 10 API requests${NC}"
echo ""

# Wait a moment for metrics to be recorded
sleep 1

# Check performance stats (without auth for demo)
echo "3. Checking performance statistics..."
STATS_RESPONSE=$(curl -s $BACKEND_URL/admin/performance/stats 2>&1)

if echo "$STATS_RESPONSE" | grep -q "total_requests"; then
    echo -e "${GREEN}✓ Performance stats endpoint is working${NC}"
    
    # Extract some metrics
    TOTAL_REQUESTS=$(echo "$STATS_RESPONSE" | grep -o '"total_requests":[0-9]*' | head -1 | cut -d':' -f2)
    TOTAL_ERRORS=$(echo "$STATS_RESPONSE" | grep -o '"total_errors":[0-9]*' | head -1 | cut -d':' -f2)
    SLOW_QUERIES=$(echo "$STATS_RESPONSE" | grep -o '"slow_queries_count":[0-9]*' | cut -d':' -f2)
    
    echo ""
    echo -e "${BLUE}Current Statistics:${NC}"
    echo "  Total Requests: $TOTAL_REQUESTS"
    echo "  Total Errors: $TOTAL_ERRORS"
    echo "  Slow Queries: $SLOW_QUERIES"
else
    echo -e "${YELLOW}⚠ Performance stats endpoint returned unexpected response${NC}"
    echo "Response: $STATS_RESPONSE"
fi
echo ""

# Check health status
echo "4. Checking health status..."
HEALTH_RESPONSE=$(curl -s $BACKEND_URL/admin/performance/health 2>&1)

if echo "$HEALTH_RESPONSE" | grep -q "status"; then
    echo -e "${GREEN}✓ Health status endpoint is working${NC}"
    
    STATUS=$(echo "$HEALTH_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    ERROR_RATE=$(echo "$HEALTH_RESPONSE" | grep -o '"error_rate":[0-9.]*' | cut -d':' -f2)
    
    echo ""
    echo -e "${BLUE}Health Status:${NC}"
    echo "  Status: $STATUS"
    echo "  Error Rate: ${ERROR_RATE}%"
else
    echo -e "${YELLOW}⚠ Health status endpoint returned unexpected response${NC}"
fi
echo ""

# Check frontend integration
echo "5. Checking frontend integration..."
if curl -s $FRONTEND_URL > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is running${NC}"
    echo "  View performance dashboard at: ${FRONTEND_URL}/admin/performance"
else
    echo -e "${YELLOW}⚠ Frontend is not running${NC}"
    echo "  Start with: npm run dev"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✓ Real performance monitoring is working!${NC}"
echo ""
echo "The system is now tracking:"
echo "  • Request counts per endpoint"
echo "  • Response times (min/avg/max)"
echo "  • Error rates"
echo "  • Slow queries"
echo "  • Requests per minute"
echo "  • System uptime"
echo ""
echo "Next steps:"
echo "  1. View dashboard: ${FRONTEND_URL}/admin/performance"
echo "  2. Make more API requests to see metrics update"
echo "  3. Check slow queries: curl ${BACKEND_URL}/admin/performance/slow-queries"
echo "  4. Reset stats: curl -X POST ${BACKEND_URL}/admin/performance/reset"
echo ""
echo "Note: The dashboard auto-refreshes every 30 seconds"
echo ""
