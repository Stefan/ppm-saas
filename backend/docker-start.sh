#!/bin/bash
# Ultra-fast startup script for simple server
set -e
echo "🚀 Starting simple FastAPI server..."
exec uvicorn simple_server:app --host 0.0.0.0 --port ${PORT:-8000}