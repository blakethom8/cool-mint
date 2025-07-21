#!/bin/bash

# Complete Activity Selector Test Script

echo "🧪 Testing Complete Activity Selector Setup..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local url=$1
    local description=$2
    local expected_status=${3:-200}
    local headers=$4
    
    echo -n "Testing $description... "
    
    if [ -n "$headers" ]; then
        response=$(curl -s -w "%{http_code}" -H "$headers" "$url")
    else
        response=$(curl -s -w "%{http_code}" "$url")
    fi
    
    http_code="${response: -3}"
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL ($http_code)${NC}"
        return 1
    fi
}

# Test 1: Kong Gateway
echo "1️⃣ Testing Kong Gateway..."
test_endpoint "http://localhost:8000/" "Kong root access" 401

# Test 2: Kong with auth
echo "2️⃣ Testing Kong with auth..."
if curl -f -u supabase:supabase http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "Kong with auth... ${GREEN}✅ PASS${NC}"
else
    echo -e "Kong with auth... ${RED}❌ FAIL${NC}"
fi

# Test 3: FastAPI Direct
echo "3️⃣ Testing FastAPI Direct..."
test_endpoint "http://localhost:8080/api/activities/" "FastAPI direct access" 200

# Test 4: Activities API through Kong
echo "4️⃣ Testing Activities API through Kong..."
test_endpoint "http://localhost:8000/activities/" "Activities through Kong" 200 "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyAgCiAgICAicm9sZSI6ICJhbm9uIiwKICAgICJpc3MiOiAic3VwYWJhc2UtZGVtbyIsCiAgICAiaWF0IjogMTY0MTc2OTIwMCwKICAgICJleHAiOiAxNzk5NTM1NjAwCn0.dc_X5iR_VP_qT0zsiyj_I_OZ2T9FtRU2BBNWN8Bu4GE"

# Test 5: Filter Options
echo "5️⃣ Testing Filter Options..."
test_endpoint "http://localhost:8000/activities/filter-options" "Filter options" 200 "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyAgCiAgICAicm9sZSI6ICJhbm9uIiwKICAgICJpc3MiOiAic3VwYWJhc2UtZGVtbyIsCiAgICAiaWF0IjogMTY0MTc2OTIwMCwKICAgICJleHAiOiAxNzk5NTM1NjAwCn0.dc_X5iR_VP_qT0zsiyj_I_OZ2T9FtRU2BBNWN8Bu4GE"

# Test 6: Frontend
echo "6️⃣ Testing Frontend..."
test_endpoint "http://localhost:3000/" "Frontend accessibility" 200

echo ""
echo "🎯 Testing Complete!"
echo ""
echo "📋 Access Points:"
echo "  Frontend:        http://localhost:3000"
echo "  Kong Gateway:    http://localhost:8000"
echo "  FastAPI Direct:  http://localhost:8080"
echo "  Activities API:  http://localhost:8000/activities/"
echo ""
echo "🔑 API Authentication:"
echo "  Use header: apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyAgCiAgICAicm9sZSI6ICJhbm9uIiwKICAgICJpc3MiOiAic3VwYWJhc2UtZGVtbyIsCiAgICAiaWF0IjogMTY0MTc2OTIwMCwKICAgICJleHAiOiAxNzk5NTM1NjAwCn0.dc_X5iR_VP_qT0zsiyj_I_OZ2T9FtRU2BBNWN8Bu4GE"
echo ""
echo "✨ Ready to use! Open http://localhost:3000 in your browser."