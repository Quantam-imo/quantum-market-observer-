#!/bin/bash
# Quantum Market Observer - Startup Script

echo "=========================================================="
echo "🚀 Quantum Market Observer - Starting..."
echo "=========================================================="
echo ""

cd "$(dirname "$0")" || exit

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
pip install -q fastapi uvicorn pydantic python-multipart 2>/dev/null

echo ""
echo "✅ Starting FastAPI backend on http://0.0.0.0:8000"
echo "📚 API Docs: http://localhost:8000/api/docs"
echo "🔍 ReDoc: http://localhost:8000/api/redoc"
echo ""
echo "=========================================================="
echo ""

# Start the server
python -m uvicorn backend.api.server:app --host 0.0.0.0 --port 8000 --reload
