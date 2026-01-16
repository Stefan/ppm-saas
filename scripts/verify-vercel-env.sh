#!/bin/bash

# Vercel Environment Variables Verification Script
# This script helps verify and set environment variables in Vercel

echo "🔍 Vercel Environment Variables Verification"
echo "=============================================="
echo ""

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI is not installed"
    echo ""
    echo "📦 Install it with:"
    echo "   npm install -g vercel"
    echo ""
    exit 1
fi

echo "✅ Vercel CLI is installed"
echo ""

# Check if logged in
if ! vercel whoami &> /dev/null; then
    echo "❌ Not logged in to Vercel"
    echo ""
    echo "🔐 Login with:"
    echo "   vercel login"
    echo ""
    exit 1
fi

echo "✅ Logged in to Vercel as: $(vercel whoami)"
echo ""

# Read environment variables from .env.production
echo "📖 Reading environment variables from .env.production..."
echo ""

if [ ! -f ".env.production" ]; then
    echo "❌ .env.production file not found"
    exit 1
fi

# Extract variables
SUPABASE_URL=$(grep "NEXT_PUBLIC_SUPABASE_URL=" .env.production | cut -d '=' -f2)
SUPABASE_ANON_KEY=$(grep "NEXT_PUBLIC_SUPABASE_ANON_KEY=" .env.production | cut -d '=' -f2)
SUPABASE_SERVICE_KEY=$(grep "SUPABASE_SERVICE_ROLE_KEY=" .env.production | cut -d '=' -f2)
API_URL=$(grep "NEXT_PUBLIC_API_URL=" .env.production | cut -d '=' -f2)

echo "Found variables:"
echo "  - NEXT_PUBLIC_SUPABASE_URL: ${SUPABASE_URL:0:30}..."
echo "  - NEXT_PUBLIC_SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY:0:30}... (length: ${#SUPABASE_ANON_KEY})"
echo "  - SUPABASE_SERVICE_ROLE_KEY: ${SUPABASE_SERVICE_KEY:0:30}... (length: ${#SUPABASE_SERVICE_KEY})"
echo "  - NEXT_PUBLIC_API_URL: $API_URL"
echo ""

# Validate variables
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_ANON_KEY" ]; then
    echo "❌ Missing required environment variables"
    exit 1
fi

echo "✅ All required variables found"
echo ""

# Ask user what to do
echo "What would you like to do?"
echo "  1) Check current Vercel environment variables"
echo "  2) Set/Update Vercel environment variables (Production)"
echo "  3) Set/Update Vercel environment variables (All environments)"
echo "  4) Remove all Vercel environment variables"
echo "  5) Exit"
echo ""
read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "📋 Current Vercel environment variables:"
        echo ""
        vercel env ls
        ;;
    2)
        echo ""
        echo "🚀 Setting environment variables for Production..."
        echo ""
        
        echo "$SUPABASE_URL" | vercel env add NEXT_PUBLIC_SUPABASE_URL production
        echo "$SUPABASE_ANON_KEY" | vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
        echo "$SUPABASE_SERVICE_KEY" | vercel env add SUPABASE_SERVICE_ROLE_KEY production
        echo "$API_URL" | vercel env add NEXT_PUBLIC_API_URL production
        
        echo ""
        echo "✅ Environment variables set for Production"
        echo ""
        echo "🔄 Triggering production deployment..."
        vercel --prod
        ;;
    3)
        echo ""
        echo "🚀 Setting environment variables for all environments..."
        echo ""
        
        # Production
        echo "$SUPABASE_URL" | vercel env add NEXT_PUBLIC_SUPABASE_URL production
        echo "$SUPABASE_ANON_KEY" | vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
        echo "$SUPABASE_SERVICE_KEY" | vercel env add SUPABASE_SERVICE_ROLE_KEY production
        echo "$API_URL" | vercel env add NEXT_PUBLIC_API_URL production
        
        # Preview
        echo "$SUPABASE_URL" | vercel env add NEXT_PUBLIC_SUPABASE_URL preview
        echo "$SUPABASE_ANON_KEY" | vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY preview
        echo "$SUPABASE_SERVICE_KEY" | vercel env add SUPABASE_SERVICE_ROLE_KEY preview
        echo "$API_URL" | vercel env add NEXT_PUBLIC_API_URL preview
        
        # Development
        echo "$SUPABASE_URL" | vercel env add NEXT_PUBLIC_SUPABASE_URL development
        echo "$SUPABASE_ANON_KEY" | vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY development
        echo "$SUPABASE_SERVICE_KEY" | vercel env add SUPABASE_SERVICE_ROLE_KEY development
        echo "$API_URL" | vercel env add NEXT_PUBLIC_API_URL development
        
        echo ""
        echo "✅ Environment variables set for all environments"
        echo ""
        echo "🔄 Triggering production deployment..."
        vercel --prod
        ;;
    4)
        echo ""
        echo "⚠️  Removing all environment variables..."
        echo ""
        
        vercel env rm NEXT_PUBLIC_SUPABASE_URL production -y
        vercel env rm NEXT_PUBLIC_SUPABASE_ANON_KEY production -y
        vercel env rm SUPABASE_SERVICE_ROLE_KEY production -y
        vercel env rm NEXT_PUBLIC_API_URL production -y
        
        echo ""
        echo "✅ Environment variables removed"
        ;;
    5)
        echo ""
        echo "👋 Exiting..."
        exit 0
        ;;
    *)
        echo ""
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Done!"
echo ""
echo "📝 Next steps:"
echo "  1. Wait for deployment to complete"
echo "  2. Visit your production URL"
echo "  3. Try logging in"
echo ""
echo "🔗 Check deployment status:"
echo "   https://vercel.com/orka/orka-ppm"
echo ""
