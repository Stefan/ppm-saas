#!/bin/bash

# Remove existing Vercel configuration
rm -rf .vercel

# Create a new deployment
echo "Deploying to Vercel..."
vercel --prod --yes --force

echo "Deployment complete!"