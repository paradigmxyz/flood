#!/bin/bash
# Simple test script to verify the merge functionality

echo "Creating test data..."

mkdir -p test_merge/rate_100
mkdir -p test_merge/rate_200

# Create test results for rate 100
cat > test_merge/rate_100/results.json << 'EOF'
{
  "flood_version": "0.3.1",
  "dependency_versions": {},
  "cli_args": [],
  "type": "single_test",
  "t_run_start": 1000.0,
  "t_run_end": 1010.0,
  "nodes": {"test_node": {"name": "test_node", "url": "http://localhost:8545"}},
  "results": {
    "test_node": {
      "target_rate": [100],
      "actual_rate": [100.1],
      "target_duration": [10],
      "actual_duration": [10.0],
      "requests": [1000],
      "throughput": [100.1],
      "success": [100.0],
      "min": [0.001],
      "mean": [0.002],
      "p50": [0.0015],
      "p90": [0.003],
      "p95": [0.004],
      "p99": [0.005],
      "max": [0.010],
      "status_codes": [{"200": 1000}],
      "errors": [[]],
      "first_request_timestamp": ["2024-01-01T00:00:00Z"],
      "last_request_timestamp": ["2024-01-01T00:00:10Z"],
      "last_response_timestamp": ["2024-01-01T00:00:10Z"],
      "final_wait_time": [0.0],
      "deep_raw_output": null,
      "deep_metrics": null,
      "deep_rpc_error_pairs": null
    }
  }
}
EOF

cat > test_merge/rate_100/test.json << 'EOF'
{
  "flood_version": "0.3.1",
  "type": "single_test",
  "name": "test",
  "test_parameters": {
    "flood_version": "0.3.1",
    "test_name": "test",
    "rates": [100],
    "durations": [10]
  }
}
EOF

# Create test results for rate 200
cat > test_merge/rate_200/results.json << 'EOF'
{
  "flood_version": "0.3.1",
  "dependency_versions": {},
  "cli_args": [],
  "type": "single_test",
  "t_run_start": 1020.0,
  "t_run_end": 1030.0,
  "nodes": {"test_node": {"name": "test_node", "url": "http://localhost:8545"}},
  "results": {
    "test_node": {
      "target_rate": [200],
      "actual_rate": [200.2],
      "target_duration": [10],
      "actual_duration": [10.0],
      "requests": [2000],
      "throughput": [200.2],
      "success": [99.5],
      "min": [0.002],
      "mean": [0.003],
      "p50": [0.0025],
      "p90": [0.004],
      "p95": [0.005],
      "p99": [0.006],
      "max": [0.012],
      "status_codes": [{"200": 1990, "500": 10}],
      "errors": [["timeout"]],
      "first_request_timestamp": ["2024-01-01T00:00:20Z"],
      "last_request_timestamp": ["2024-01-01T00:00:30Z"],
      "last_response_timestamp": ["2024-01-01T00:00:30Z"],
      "final_wait_time": [0.0],
      "deep_raw_output": null,
      "deep_metrics": null,
      "deep_rpc_error_pairs": null
    }
  }
}
EOF

cat > test_merge/rate_200/test.json << 'EOF'
{
  "flood_version": "0.3.1",
  "type": "single_test",
  "name": "test",
  "test_parameters": {
    "flood_version": "0.3.1",
    "test_name": "test",
    "rates": [200],
    "durations": [10]
  }
}
EOF

echo "Running merge..."
./merge_flood_results.py test_merge/merged test_merge/rate_100 test_merge/rate_200

if [[ $? -eq 0 ]]; then
    echo ""
    echo "Merged results:"
    echo "---"
    cat test_merge/merged/results.json | python3 -m json.tool
    echo ""
    echo "✓ Merge test successful!"
    echo ""
    echo "Cleaning up..."
    rm -rf test_merge
else
    echo "✗ Merge test failed"
    exit 1
fi
