#!/bin/bash
# Quantum Market Observer - Startup Script

echo "=========================================================="
echo "🚀 Quantum Market Observer - Starting..."
echo "=========================================================="
echo ""

cd "$(dirname "$0")" || exit

# Load environment variables from .env file
if [ -f .env ]; then
    echo "📋 Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Environment loaded"
else
    echo "⚠️  No .env file found"
fi

# Check Databento configuration
if [ -n "$DATABENTO_API_KEY" ]; then
    echo "✅ Databento API key configured: ${DATABENTO_API_KEY:0:12}***"
    echo "📊 Market data: Live CME orderflow (when available)"
else
    echo "⚠️  No Databento API key - using Yahoo Finance fallback"
    echo "💡 Set DATABENTO_API_KEY in .env for institutional data"
fi
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
pip install -q fastapi uvicorn pydantic python-multipart databento 2>/dev/null

echo ""
echo "✅ Starting FastAPI backend on http://0.0.0.0:8000"
echo "📚 API Docs: http://localhost:8000/api/docs"
echo "🔍 ReDoc: http://localhost:8000/api/redoc"
echo ""
echo "=========================================================="
echo ""

# Start the server
python -m uvicorn backend.api.server:app --host 0.0.0.0 --port 8000 --reload
