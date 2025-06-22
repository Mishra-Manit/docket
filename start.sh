#!/bin/bash

echo "🚀 Starting Computer Use Claude Agent Full Stack Application"
echo "============================================================="

# Function to start backend
start_backend() {
    echo "🐍 Starting Flask Backend Server..."
    cd backend
    
    # Ensure virtual environment exists
    if [ ! -d "env" ]; then
        echo "📦 Creating Python virtual environment..."
        python3 -m venv env
    fi

    # Activate the virtual environment
    echo "📦 Activating virtual environment..."
    source env/bin/activate

    # Install / update backend dependencies (uses pinned versions)
    echo "🔍 Installing backend Python dependencies..."
    pip install --upgrade pip >/dev/null 2>&1
    pip install --requirement requirements.txt --quiet

    echo "🌐 Starting Flask server on http://localhost:5000 (press Ctrl-C to quit)"
    python app.py server
}

# Function to start frontend (if it exists)
start_frontend() {
    if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
        echo "⚛️  Starting Next.js Frontend Server..."
        cd frontend
        if [ ! -d "node_modules" ]; then
            echo "📦 Installing frontend dependencies..."
            npm install
        fi
        npm run dev
    else
        echo "ℹ️  No frontend found, running backend only"
    fi
}

# Check what the user wants to run
case "$1" in
    "backend")
        start_backend
        ;;
    "frontend")
        start_frontend
        ;;
    "full")
        echo "🔄 Starting both backend and frontend..."
        # Start backend in background
        start_backend &
        BACKEND_PID=$!
        
        # Wait a moment for backend to start
        sleep 3
        
        # Start frontend
        start_frontend
        
        # Clean up background process when script exits
        trap "kill $BACKEND_PID" EXIT
        ;;
    *)
        echo "Usage: $0 [backend|frontend|full]"
        echo ""
        echo "Commands:"
        echo "  backend   - Start only the Flask backend server"
        echo "  frontend  - Start only the Next.js frontend server"
        echo "  full      - Start both backend and frontend servers"
        echo ""
        echo "Default: Starting backend only..."
        start_backend
        ;;
esac 