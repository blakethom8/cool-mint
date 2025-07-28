#!/bin/bash
# Docker-aware debugging script for Juno Email Assistant

echo "==================================="
echo "🐳 DOCKER DEBUG HELPER"
echo "==================================="

# Get project name from .env
PROJECT_NAME=$(grep PROJECT_NAME ../docker/.env | cut -d '=' -f2)

if [ -z "$PROJECT_NAME" ]; then
    echo "❌ PROJECT_NAME not found in docker/.env"
    exit 1
fi

echo "Project: $PROJECT_NAME"
echo ""

# Function to run commands in API container
run_in_api() {
    echo "🏃 Running in API container: $1"
    docker exec -it ${PROJECT_NAME}_api python -c "$1" 2>&1
}

# Function to run commands in Celery container
run_in_celery() {
    echo "🏃 Running in Celery container: $1"
    docker exec -it ${PROJECT_NAME}_celery_worker python -c "$1" 2>&1
}

# Function to run debug scripts in container
run_debug_script() {
    echo "🔍 Running debug script: $1"
    docker exec -it ${PROJECT_NAME}_api python /app/debug/$1
}

case "$1" in
    "check")
        echo "📦 Checking Docker containers..."
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep $PROJECT_NAME
        ;;
        
    "logs")
        echo "📋 Recent logs from Celery worker..."
        docker logs --tail 50 ${PROJECT_NAME}_celery_worker
        ;;
        
    "celery-status")
        echo "🔍 Checking Celery status..."
        docker exec -it ${PROJECT_NAME}_celery_worker celery -A worker.config inspect stats
        echo ""
        echo "📋 Active tasks:"
        docker exec -it ${PROJECT_NAME}_celery_worker celery -A worker.config inspect active
        ;;
        
    "redis-check")
        echo "🔍 Checking Redis connection..."
        docker exec -it ${PROJECT_NAME}_redis redis-cli ping
        docker exec -it ${PROJECT_NAME}_redis redis-cli info server | grep redis_version
        ;;
        
    "test-sync")
        echo "🧪 Running synchronous workflow test in container..."
        run_debug_script "test_sync_workflow.py"
        ;;
        
    "test-celery")
        echo "🧪 Testing Celery in container..."
        run_debug_script "test_celery_basic.py"
        ;;
        
    "test-async")
        echo "🧪 Testing async workflow..."
        run_debug_script "test_async_workflow.py"
        ;;
        
    "db-summary")
        echo "📊 Database summary..."
        run_debug_script "db_inspector.py summary"
        ;;
        
    "db-emails")
        echo "📧 Recent emails..."
        run_debug_script "db_inspector.py emails --limit ${2:-10}"
        ;;
        
    "process-email")
        if [ -z "$2" ]; then
            echo "❌ Usage: $0 process-email <email-id>"
            exit 1
        fi
        echo "🚀 Processing email $2..."
        run_debug_script "test_async_workflow.py --email-id $2"
        ;;
        
    "shell")
        echo "🐚 Opening shell in API container..."
        docker exec -it ${PROJECT_NAME}_api /bin/bash
        ;;
        
    "celery-shell")
        echo "🐚 Opening shell in Celery container..."
        docker exec -it ${PROJECT_NAME}_celery_worker /bin/bash
        ;;
        
    *)
        echo "Usage: $0 {check|logs|celery-status|redis-check|test-sync|test-celery|test-async|db-summary|db-emails|process-email|shell|celery-shell}"
        echo ""
        echo "Commands:"
        echo "  check         - Check Docker container status"
        echo "  logs          - Show recent Celery logs"
        echo "  celery-status - Check Celery worker status"
        echo "  redis-check   - Test Redis connection"
        echo "  test-sync     - Run synchronous workflow test"
        echo "  test-celery   - Test Celery functionality"
        echo "  test-async    - Test full async workflow"
        echo "  db-summary    - Show database summary"
        echo "  db-emails     - List recent emails"
        echo "  process-email - Process specific email by ID"
        echo "  shell         - Open shell in API container"
        echo "  celery-shell  - Open shell in Celery container"
        ;;
esac