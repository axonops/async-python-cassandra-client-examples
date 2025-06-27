#!/bin/bash

# Performance testing script for comparing async vs sync Cassandra clients

set -e

echo "=== Cassandra Performance Testing Framework ==="
echo

# Check if services are running
check_services() {
    echo "Checking if services are running..."
    
    if ! curl -s http://localhost:8001/health > /dev/null; then
        echo "❌ Async app not responding on http://localhost:8001"
        exit 1
    fi
    
    if ! curl -s http://localhost:8002/health > /dev/null; then
        echo "❌ Sync app not responding on http://localhost:8002"
        exit 1
    fi
    
    echo "✅ Both services are healthy"
    echo
}

# Run Locust tests
run_locust_test() {
    local target=$1
    local users=$2
    local spawn_rate=$3
    local duration=$4
    local test_name=$5
    
    echo "Running Locust test: $test_name"
    echo "Target: $target, Users: $users, Duration: $duration"
    
    locust \
        --headless \
        --host "$target" \
        --users "$users" \
        --spawn-rate "$spawn_rate" \
        --run-time "$duration" \
        --html "results/locust_${test_name}_$(date +%Y%m%d_%H%M%S).html" \
        --csv "results/locust_${test_name}_$(date +%Y%m%d_%H%M%S)"
    
    echo "✅ Locust test completed"
    echo
}

# Run k6 tests
run_k6_test() {
    local target=$1
    local test_name=$2
    
    echo "Running k6 test: $test_name"
    echo "Target: $target"
    
    k6 run \
        --env BASE_URL="$target" \
        --out json="results/k6_${test_name}_$(date +%Y%m%d_%H%M%S).json" \
        --summary-export="results/k6_${test_name}_$(date +%Y%m%d_%H%M%S)_summary.json" \
        k6-script.js
    
    echo "✅ k6 test completed"
    echo
}

# Create results directory
mkdir -p results

# Check services
check_services

# Test scenarios
echo "=== Starting Performance Tests ==="
echo

# Test 1: Baseline performance - Async app
echo "Test 1: Baseline Performance - Async App"
run_locust_test "http://localhost:8001" 10 1 "60s" "async_baseline"

# Test 2: Baseline performance - Sync app
echo "Test 2: Baseline Performance - Sync App"
run_locust_test "http://localhost:8002" 10 1 "60s" "sync_baseline"

# Test 3: Load test - Async app
echo "Test 3: Load Test - Async App"
run_locust_test "http://localhost:8001" 100 10 "5m" "async_load"

# Test 4: Load test - Sync app
echo "Test 4: Load Test - Sync App"
run_locust_test "http://localhost:8002" 100 10 "5m" "sync_load"

# Test 5: Stress test with k6 - Async app
if command -v k6 &> /dev/null; then
    echo "Test 5: k6 Stress Test - Async App"
    run_k6_test "http://localhost:8001" "async_stress"
    
    echo "Test 6: k6 Stress Test - Sync App"
    run_k6_test "http://localhost:8002" "sync_stress"
else
    echo "⚠️  k6 not installed, skipping k6 tests"
fi

echo
echo "=== All tests completed ==="
echo "Results saved in ./results/"
echo
echo "To view results:"
echo "- Locust HTML reports: open results/locust_*.html"
echo "- Raw data: results/*.csv and results/*.json"
echo
echo "To visualize in Grafana:"
echo "- Open http://localhost:3000"
echo "- Login with admin/admin"
echo "- Import dashboards from monitoring/grafana/dashboards/"