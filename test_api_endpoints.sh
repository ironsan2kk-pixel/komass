#!/bin/bash

echo "======================================================================"
echo "KOMAS PROJECT - API ENDPOINTS TEST"
echo "======================================================================"
echo ""

API_BASE="http://localhost:8000"
PASSED=0
FAILED=0

test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local expected_status=${4:-200}

    printf "%-50s" "$description"

    response=$(curl -s -w "\n%{http_code}" -X $method "$API_BASE$endpoint" 2>/dev/null)
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$status_code" == "$expected_status" ]; then
        echo "✅ [$status_code]"
        ((PASSED++))
    else
        echo "❌ [$status_code] Expected: $expected_status"
        ((FAILED++))
        if [ ! -z "$body" ]; then
            echo "   Response: $(echo $body | head -c 100)"
        fi
    fi
}

echo "Testing Backend API Endpoints..."
echo "----------------------------------------------------------------------"

# Health & Info
test_endpoint "GET" "/health" "Health Check"
test_endpoint "GET" "/api/logs/list" "Logs List"

# Bots
test_endpoint "GET" "/api/bots/" "Get Bots List"
test_endpoint "GET" "/api/bots/stats" "Get Bots Statistics"

# Settings
test_endpoint "GET" "/api/settings/presets" "Get Presets"
test_endpoint "GET" "/api/settings/global" "Get Global Settings"

# Data
test_endpoint "GET" "/api/data/symbols" "Get Symbols List"
test_endpoint "GET" "/api/data/status" "Get Data Status"

# Indicators
test_endpoint "GET" "/api/indicator/modes" "Get Indicator Modes"
test_endpoint "GET" "/api/trg/presets" "Get TRG Presets"

# Optimizer
test_endpoint "GET" "/api/optimizer/modes" "Get Optimizer Modes"
test_endpoint "GET" "/api/optimizer/status" "Get Optimizer Status"

# Presets (Dominant)
test_endpoint "GET" "/api/presets/" "Get Dominant Presets"

# Signals
test_endpoint "GET" "/api/signal-score/timeframes" "Get Signal Timeframes"

# Calendar
test_endpoint "GET" "/api/calendar/events" "Get Calendar Events"

# Filters
test_endpoint "GET" "/api/filters/" "Get Filters"
test_endpoint "GET" "/api/filters/profiles" "Get Filter Profiles"

# Database
test_endpoint "GET" "/api/db/stats" "Get Database Stats"

# Notifications
test_endpoint "GET" "/api/notifications/channels" "Get Notification Channels"

echo ""
echo "======================================================================"
echo "SUMMARY"
echo "======================================================================"
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo ""

if [ $FAILED -gt 0 ]; then
    exit 1
fi
