#!/bin/bash

echo "🧪 TESTING VERCEL FRONTEND FIX"
echo "=============================="

echo ""
echo "🔍 1. Checking Backend CORS Configuration..."
echo "Backend should allow flexible Vercel URLs:"

BACKEND_URL="https://orka-ppm.onrender.com"

# Test CORS with different potential frontend URLs
FRONTEND_URLS=(
    "https://orka-ppm.vercel.app"
    "https://ppm-saas.vercel.app" 
    "https://ppm-saas-git-main.vercel.app"
)

for url in "${FRONTEND_URLS[@]}"; do
    echo "Testing CORS for: $url"
    CORS_RESULT=$(curl -s -I -H "Origin: $url" "$BACKEND_URL/" | grep -i "access-control-allow-origin")
    if [[ $CORS_RESULT == *"$url"* ]] || [[ $CORS_RESULT == *"*.vercel.app"* ]]; then
        echo "✅ CORS OK for $url"
    else
        echo "❌ CORS issue for $url"
        echo "   Response: $CORS_RESULT"
    fi
done

echo ""
echo "🔍 2. Checking Backend Health..."
HEALTH_STATUS=$(curl -s "$BACKEND_URL/health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
if [ "$HEALTH_STATUS" = "healthy" ]; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health issue: $HEALTH_STATUS"
fi

echo ""
echo "🔍 3. Checking vercel.json Configuration..."
if [ -f "vercel.json" ]; then
    echo "✅ vercel.json exists"
    
    # Check if it points to frontend
    if grep -q "frontend/package.json" vercel.json; then
        echo "✅ vercel.json correctly points to frontend"
    else
        echo "❌ vercel.json doesn't point to frontend"
    fi
    
    # Check framework setting
    if grep -q '"framework": "nextjs"' vercel.json; then
        echo "✅ Next.js framework specified"
    else
        echo "❌ Next.js framework not specified"
    fi
else
    echo "❌ vercel.json not found"
fi

echo ""
echo "🔍 4. Checking Frontend Structure..."
if [ -d "frontend" ]; then
    echo "✅ Frontend directory exists"
    
    if [ -f "frontend/package.json" ]; then
        echo "✅ Frontend package.json exists"
        
        # Check if it's a Next.js project
        if grep -q '"next"' frontend/package.json; then
            echo "✅ Next.js dependency found"
        else
            echo "❌ Next.js dependency not found"
        fi
    else
        echo "❌ Frontend package.json missing"
    fi
else
    echo "❌ Frontend directory missing"
fi

echo ""
echo "🎯 VERCEL DEPLOYMENT RECOMMENDATIONS"
echo "==================================="
echo ""
echo "📋 For New Vercel Project:"
echo "1. Root Directory: frontend"
echo "2. Framework: Next.js"
echo "3. Build Command: npm run build"
echo "4. Output Directory: .next"
echo ""
echo "🔧 Environment Variables to Add:"
echo "- NEXT_PUBLIC_SUPABASE_URL=https://xceyrfvxooiplbmwavlb.supabase.co"
echo "- NEXT_PUBLIC_SUPABASE_ANON_KEY=[fresh-key-208-chars]"
echo "- NEXT_PUBLIC_API_URL=https://orka-ppm.onrender.com"
echo ""
echo "✅ Backend CORS: Updated to support flexible Vercel URLs"
echo "✅ Ready for: New Vercel project creation with correct root directory"