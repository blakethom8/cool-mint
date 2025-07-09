#!/bin/bash

# Activity API Testing Script
# This script tests all the new activity API endpoints

set -e

echo "🧪 Testing Activity API Endpoints..."
echo ""

# Test URLs
KONG_URL="http://localhost:8000"
DIRECT_URL="http://localhost:8080"

# Function to test an endpoint
test_endpoint() {
    local url=$1
    local description=$2
    local expected_status=${3:-200}
    
    echo "Testing: $description"
    echo "URL: $url"
    
    response=$(curl -s -w "\n%{http_code}" "$url")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_status" ]; then
        echo "✅ SUCCESS ($http_code)"
        if [ "$http_code" = "200" ]; then
            echo "📄 Response preview:"
            echo "$body" | head -c 200
            echo "..."
        fi
    else
        echo "❌ FAILED ($http_code)"
        echo "Response: $body"
    fi
    
    echo ""
}

# Test 1: Check Kong Gateway
echo "1️⃣ Testing Kong Gateway..."
test_endpoint "$KONG_URL" "Kong health check"

# Test 2: Check FastAPI Direct
echo "2️⃣ Testing FastAPI Direct..."
test_endpoint "$DIRECT_URL" "FastAPI health check"

# Test 3: Activities List (through Kong)
echo "3️⃣ Testing Activities API through Kong..."
test_endpoint "$KONG_URL/api/activities/" "Activities list through Kong"

# Test 4: Activities List (direct)
echo "4️⃣ Testing Activities API direct..."
test_endpoint "$DIRECT_URL/api/activities/" "Activities list direct"

# Test 5: Filter Options (through Kong)
echo "5️⃣ Testing Filter Options through Kong..."
test_endpoint "$KONG_URL/api/activities/filter-options" "Filter options through Kong"

# Test 6: Filter Options (direct)
echo "6️⃣ Testing Filter Options direct..."
test_endpoint "$DIRECT_URL/api/activities/filter-options" "Filter options direct"

# Test 7: Test with query parameters
echo "7️⃣ Testing with query parameters..."
test_endpoint "$KONG_URL/api/activities/?page=1&page_size=10" "Activities with pagination"

# Test 8: Test selection endpoint
echo "8️⃣ Testing selection endpoint..."
curl -s -X POST "$KONG_URL/api/activities/selection" \
  -H "Content-Type: application/json" \
  -d '{"activity_ids": []}' > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Selection endpoint accessible"
else
    echo "❌ Selection endpoint failed"
fi

echo ""
echo "🎯 Testing Complete!"
echo ""
echo "💡 If you see errors:"
echo "  - Make sure backend services are running: cd docker && ./start.sh"
echo "  - Check Kong configuration includes custom API routes"
echo "  - Verify database has activity data"
echo ""
echo "🔍 To debug further:"
echo "  - Check Kong logs: docker logs supabase-kong"
echo "  - Check API logs: docker logs launchpad_api"
echo "  - Test database: docker exec -it supabase-db psql -U postgres"