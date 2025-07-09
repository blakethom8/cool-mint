#!/bin/bash

# Activity Selector Startup Script
# This script starts the full stack: backend services + frontend

set -e

echo "🚀 Starting Activity Selector Full Stack..."
echo ""

# Function to check if a service is running
check_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to start..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            echo "✅ $service_name is running"
            return 0
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            echo "❌ $service_name failed to start after $max_attempts attempts"
            return 1
        fi
        
        echo "   Attempt $attempt/$max_attempts - waiting..."
        sleep 2
        ((attempt++))
    done
}

# Step 1: Start backend services
echo "1️⃣ Starting backend services (Kong, API, Database)..."
cd docker
./start.sh

# Step 2: Wait for services to be ready
echo ""
echo "2️⃣ Waiting for services to be ready..."

# Wait for Kong (use a different check since root path requires auth)
echo "⏳ Waiting for Kong API Gateway to start..."
if docker ps | grep -q "supabase-kong"; then
    echo "✅ Kong API Gateway is running"
else
    echo "❌ Kong API Gateway is not running"
    exit 1
fi

# Wait for FastAPI
check_service "http://localhost:8080/docs" "FastAPI Backend"

# Wait for database (through Kong) - skip auth check for now
echo "⏳ Waiting for Database (PostgREST) to start..."
if curl -f -s "http://localhost:8000/rest/v1/" > /dev/null 2>&1 || [[ $(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/rest/v1/") == "401" ]]; then
    echo "✅ Database (PostgREST) is running"
else
    echo "❌ Database (PostgREST) is not running"
    exit 1
fi

# Step 3: Start frontend
echo ""
echo "3️⃣ Starting frontend..."
cd ../frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Start the frontend
echo "🎨 Starting React frontend..."
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
echo ""
check_service "http://localhost:3000" "React Frontend"

# Step 4: Success message
echo ""
echo "🎉 Activity Selector is ready!"
echo ""
echo "📋 Access Points:"
echo "  Frontend:        http://localhost:3000"
echo "  Kong Gateway:    http://localhost:8000"
echo "  FastAPI Direct:  http://localhost:8080"
echo "  Supabase Studio: http://localhost:8000 (username: supabase, password: supabase)"
echo ""
echo "🔗 API Routes:"
echo "  Activities:      http://localhost:8000/api/activities/"
echo "  Filter Options:  http://localhost:8000/api/activities/filter-options"
echo ""
echo "📚 Documentation:"
echo "  Setup Guide:     ./SETUP_GUIDE.md"
echo "  Frontend README: ./frontend/README.md"
echo ""
echo "🛑 To stop all services:"
echo "  Press Ctrl+C to stop the frontend"
echo "  Run: cd docker && ./stop.sh"
echo ""
echo "✨ Happy coding!"

# Wait for Ctrl+C
wait $FRONTEND_PID