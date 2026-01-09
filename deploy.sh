#!/bin/bash

# Fast deployment script for Orka PPM
set -e

echo "🚀 Starting fast deployment..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Run this script from the project root."
    exit 1
fi

# Build and deploy frontend
echo "📦 Building frontend..."
npm run build:fast

echo "🌐 Deploying to Vercel..."
npx vercel --prod --yes

# Trigger backend deployment
echo "🔧 Triggering backend deployment..."
if [ -n "$RENDER_DEPLOY_HOOK" ]; then
    curl -X POST "$RENDER_DEPLOY_HOOK" -H "Content-Type: application/json" -d '{"clear_cache": true}'
    echo "✅ Backend deployment triggered"
else
    echo "⚠️  RENDER_DEPLOY_HOOK not set. Backend deployment skipped."
fi

echo "🎉 Deployment complete!"
echo "Frontend: https://orka-ppm.vercel.app"
echo "Backend: https://orka-ppm.onrender.com"