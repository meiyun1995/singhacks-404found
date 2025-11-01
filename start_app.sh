#!/bin/bash

# Compliance Workflow Web App Startup Script

echo ""
echo "============================================================================"
echo "  🏦 COMPLIANCE WORKFLOW WEB APPLICATION"
echo "============================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Check if required packages are installed
echo "📦 Checking dependencies..."

# Install required packages if needed
pip3 install -q fastapi uvicorn websockets python-dotenv pydantic 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ All dependencies installed"
else
    echo "⚠️  Some dependencies may be missing, but continuing..."
fi

echo ""
echo "🚀 Starting backend server..."
echo "   • API Server: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Frontend: http://localhost:8000/app"
echo ""
echo "============================================================================"
echo ""

# Start the backend server
python3 app_backend.py
