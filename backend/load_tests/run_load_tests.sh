#!/bin/bash

# Enterprise Load Testing Suite
# Automated testing scenarios for 1000+ concurrent users

set -e

echo "=== Enterprise Ticket Management System Load Testing ==="
echo "Target: 1000+ concurrent users simulation"
echo "Date: $(date)"
echo ""

# Configuration
HOST=${HOST:-"http://localhost:8000"}
RESULTS_DIR="./load_test_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create results directory
mkdir -p "$RESULTS_DIR"

echo "Setting up load test environment..."

# Function to run load test scenario
run_load_test() {
    local scenario=$1
    local users=$2
    local spawn_rate=$3
    local duration=$4
    local description=$5
    
    echo ""
    echo "=== Running $scenario ==="
    echo "Description: $description"
    echo "Users: $users, Spawn Rate: $spawn_rate/s, Duration: ${duration}s"
    
    local output_file="${RESULTS_DIR}/${scenario}_${TIMESTAMP}.csv"
    
    locust \
        -f locustfile.py \
        --host="$HOST" \
        --users="$users" \
        --spawn-rate="$spawn_rate" \
        --run-time="${duration}s" \
        --headless \
        --csv="${RESULTS_DIR}/${scenario}_${TIMESTAMP}" \
        --html="${RESULTS_DIR}/${scenario}_${TIMESTAMP}.html" \
        --loglevel=INFO \
        --logfile="${RESULTS_DIR}/${scenario}_${TIMESTAMP}.log"
    
    echo "Results saved to: $output_file"
}

# Test Scenario 1: Gradual Ramp-up (Enterprise Normal Load)
run_load_test \
    "enterprise_normal" \
    500 \
    10 \
    300 \
    "Normal enterprise load - 500 concurrent users over 5 minutes"

# Test Scenario 2: Peak Load (Enterprise Peak Hours)
run_load_test \
    "enterprise_peak" \
    1000 \
    20 \
    600 \
    "Peak enterprise load - 1000 concurrent users over 10 minutes"

# Test Scenario 3: Stress Test (Beyond Normal Capacity)
run_load_test \
    "enterprise_stress" \
    1500 \
    25 \
    300 \
    "Stress testing - 1500 concurrent users to test breaking point"

# Test Scenario 4: Spike Test (Sudden Load Increase)
run_load_test \
    "enterprise_spike" \
    2000 \
    100 \
    180 \
    "Spike testing - 2000 users spawned rapidly"

# Test Scenario 5: Endurance Test (Sustained Load)
run_load_test \
    "enterprise_endurance" \
    800 \
    10 \
    1800 \
    "Endurance testing - 800 users for 30 minutes sustained load"

echo ""
echo "=== Load Testing Complete ==="
echo "All results saved to: $RESULTS_DIR"
echo ""

# Generate summary report
python3 generate_report.py "$RESULTS_DIR" "$TIMESTAMP"

echo "Load testing suite completed successfully!"
echo "Check the HTML reports for detailed performance analysis."