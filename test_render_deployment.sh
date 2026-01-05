#!/bin/bash

# Test script for Render deployment verification
# This script tests the backend deployment on Render

echo "🚀 Testing Render Backend Deployment"
echo "======================================"

BACKEND_URL="https://orka-ppm.onrender.com"

echo ""
echo "🔍 Testing Backend Endpoints..."

# Test root endpoint
echo "1. Testing root endpoint (/)..."
curl -s -w "Status: %{http_code}\n" "$BACKEND_URL/" | head -10

echo ""
echo "2. Testing health endpoint (/health)..."
curl -s -w "Status: %{http_code}\n" "$BACKEND_URL/health" | head -10

echo ""
echo "3. Testing debug endpoint (/debug)..."
curl -s -w "Status: %{http_code}\n" "$BACKEND_URL/debug" | head -10

echo ""
echo "4. Testing dashboard endpoint (/dashboard)..."
curl -s -w "Status: %{http_code}\n" "$BACKEND_URL/dashboard" | head -10

echo ""
echo "5. Testing CORS headers..."
curl -s -I -H "Origin: https://orka-ppm.vercel.app" "$BACKEND_URL/" | grep -i "access-control"

echo ""
echo "🧪 Testing Frontend Integration..."

# Test if frontend can reach backend
echo "6. Testing frontend API calls..."
curl -s -H "Origin: https://orka-ppm.vercel.app" \
     -H "Content-Type: application/json" \
     "$BACKEND_URL/dashboard" | head -5

echo ""
echo "✅ Deployment Test Complete!"
echo ""
echo "Expected Results:"
echo "- Status codes should be 200"
echo "- Root endpoint should return welcome message"
echo "- Health endpoint should return 'healthy' status"
echo "- CORS headers should include 'access-control-allow-origin'"
echo ""
echo "If any endpoint returns 503 or 500, check Render logs:"
echo "https://dashboard.render.com → Your Service → Logs"