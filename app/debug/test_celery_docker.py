#!/usr/bin/env python3
"""
Docker-aware Celery test script
Handles different Redis URLs based on environment
"""
import os
import sys
from datetime import datetime

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Check if we're running inside Docker
IS_DOCKER = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER', False)

if IS_DOCKER:
    print("🐳 Running inside Docker container")
    # Inside Docker, use container names
    os.environ['CELERY_BROKER_URL'] = f"redis://{os.getenv('PROJECT_NAME')}_redis:6379/0"
else:
    print("💻 Running on host machine")
    # Outside Docker, use localhost with exposed port
    os.environ['CELERY_BROKER_URL'] = "redis://localhost:6379/0"

print(f"📡 Using Redis URL: {os.environ['CELERY_BROKER_URL']}")

from worker.config import celery_app
from worker.tasks import process_incoming_event


def test_docker_celery():
    """Test Celery connectivity in Docker environment"""
    print("\n" + "=" * 60)
    print("🐳 DOCKER CELERY CONNECTION TEST")
    print("=" * 60)
    
    try:
        # Test 1: Check broker connection
        print("\n1️⃣ Testing broker connection...")
        conn = celery_app.connection()
        conn.ensure_connection(max_retries=3)
        print("✅ Successfully connected to Redis broker")
        
        # Test 2: Check registered tasks
        print("\n2️⃣ Checking registered tasks...")
        tasks = list(celery_app.tasks.keys())
        print(f"✅ Found {len(tasks)} registered tasks:")
        for task in sorted(tasks):
            if not task.startswith('celery.'):
                print(f"   - {task}")
        
        # Test 3: Check workers
        print("\n3️⃣ Checking active workers...")
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            print(f"✅ Found {len(stats)} worker(s):")
            for worker, info in stats.items():
                print(f"   - {worker}")
                print(f"     Broker: {info.get('broker', {}).get('hostname', 'unknown')}")
                print(f"     Pool: {info.get('pool', {}).get('implementation', 'unknown')}")
        else:
            print("❌ No workers found!")
            print("   Workers might be in a different container or not running")
        
        # Test 4: Send a simple task
        print("\n4️⃣ Sending test task...")
        if 'process_incoming_event' in celery_app.tasks:
            # Just check if we can send it, don't wait for result
            result = celery_app.send_task('process_incoming_event', args=['test-id'])
            print(f"✅ Task sent successfully: {result.id}")
            print("   (Task will fail with 'test-id' but that's expected)")
        else:
            print("⚠️  process_incoming_event task not found")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check if Redis container is running:")
        print(f"   docker ps | grep redis")
        print("2. Check Redis logs:")
        print(f"   docker logs {os.getenv('PROJECT_NAME')}_redis")
        print("3. Try connecting manually:")
        print(f"   docker exec -it {os.getenv('PROJECT_NAME')}_redis redis-cli ping")
        return False


def test_environment_info():
    """Show environment information for debugging"""
    print("\n" + "=" * 60)
    print("🔍 ENVIRONMENT INFORMATION")
    print("=" * 60)
    
    print(f"\nEnvironment Variables:")
    print(f"  PROJECT_NAME: {os.getenv('PROJECT_NAME', 'NOT SET')}")
    print(f"  DATABASE_HOST: {os.getenv('DATABASE_HOST', 'NOT SET')}")
    print(f"  REDIS_URL: {os.getenv('REDIS_URL', 'NOT SET')}")
    print(f"  CELERY_BROKER_URL: {os.getenv('CELERY_BROKER_URL', 'NOT SET')}")
    
    print(f"\nContainer Detection:")
    print(f"  /.dockerenv exists: {os.path.exists('/.dockerenv')}")
    print(f"  Hostname: {os.uname().nodename}")
    
    print(f"\nPython Environment:")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Working Dir: {os.getcwd()}")


if __name__ == "__main__":
    # Show environment info
    test_environment_info()
    
    # Test Celery connection
    success = test_docker_celery()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Docker Celery test completed successfully!")
    else:
        print("❌ Docker Celery test failed!")
    print("=" * 60)