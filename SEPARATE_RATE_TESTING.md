# Running Flood Tests with Separate Rates and Sleep

This guide explains how to run flood tests with each RPS rate separately (with sleep between tests) and then combine the results into a single output file.

## Why Run Rates Separately?

Running each rate as a separate test with sleep between them can be useful for:
- Allowing the system to recover between tests
- Preventing thermal throttling on hardware
- Collecting system metrics between tests
- Debugging specific rate failures
- More granular control over test timing

## Solution Overview

This solution consists of two components:

1. **`run_flood_separate_rates.sh`** - Bash script that runs each rate separately with configurable sleep
2. **`merge_flood_results.py`** - Python script that merges separate rate results into a single combined output

## Quick Start

### Basic Usage

```bash
./run_flood_separate_rates.sh -n mynode=http://localhost:8545
```

This will:
1. Run each rate (250, 500, 750, ...) as a separate flood test
2. Sleep 5 seconds between each rate
3. Sleep 10 seconds between each test type
4. Merge all rate results into a single combined output

### Custom Configuration

```bash
./run_flood_separate_rates.sh \
    -n mynode=http://localhost:8545 \
    -r "100 500 1000 2000" \
    -d 30 \
    --sleep-rates 10 \
    --sleep-tests 15
```

## Script Options

### run_flood_separate_rates.sh

```
-n, --node NAME=URL      Node to test (required)
-t, --tests TESTS        Space-separated test names
-r, --rates RATES        Space-separated RPS rates
-d, --duration SECONDS   Duration for each rate test (default: 60)
-o, --output DIR         Output directory (default: ./results)
-m, --metrics METRICS    Space-separated metrics to collect
--sleep-rates SECONDS    Sleep between rate tests (default: 5)
--sleep-tests SECONDS    Sleep between test types (default: 10)
--no-deep-check          Disable deep checking
-h, --help               Show help message
```

### merge_flood_results.py

```bash
./merge_flood_results.py <output_dir> <result_dir1> <result_dir2> ...
```

Example:
```bash
./merge_flood_results.py merged_results/ rate_250/ rate_500/ rate_1000/
```

## Output Structure

```
results/
└── mynode_20251211_123456/
    ├── eth_call/
    │   ├── rate_250/           # Individual rate results
    │   │   ├── results.json
    │   │   ├── test.json
    │   │   └── summary.txt
    │   ├── rate_500/
    │   │   ├── results.json
    │   │   ├── test.json
    │   │   └── summary.txt
    │   ├── ...
    │   └── combined/           # Merged results (all rates)
    │       ├── results.json    # ← Use this for analysis
    │       ├── test.json
    │       └── summary.txt
    ├── eth_getBlockByNumber/
    │   ├── rate_250/
    │   ├── rate_500/
    │   ├── ...
    │   └── combined/
    └── ...
```

## Merged Results

The `combined/` directory contains results as if all rates were run in a single flood command:

```json
{
  "results": {
    "mynode": {
      "target_rate": [250, 500, 750, 1000, ...],
      "throughput": [250.1, 500.2, 749.8, 1000.5, ...],
      "success": [100.0, 100.0, 99.8, 99.5, ...],
      "p50": [0.001, 0.002, 0.003, 0.004, ...],
      ...
    }
  }
}
```

## Generating Reports

You can use flood's built-in report command on the combined results:

```bash
docker run --rm \
    -v "$PWD/results/mynode_20251211_123456:/results" \
    ghcr.io/paradigmxyz/flood:0.3.1 \
    report /results/*/combined \
    --output /results/final_report
```

This creates a report showing all test types with their combined rate data.

## Comparison: Separate vs Combined Rates

### Option A: Separate Rates (This Solution)
```bash
# Each rate runs separately with sleep between
flood test node --rates 250 --duration 60    # sleep 5s
flood test node --rates 500 --duration 60    # sleep 5s
flood test node --rates 750 --duration 60
# Then merge all results
```

**Pros:**
- System recovery time between tests
- Fine-grained control over timing
- Can interrupt/resume testing
- Easier to isolate failures

**Cons:**
- Longer total test time
- More complex setup
- Requires merge step

### Option B: Combined Rates (Standard)
```bash
# All rates in one command
flood test node --rates 250 500 750 --duration 60
```

**Pros:**
- Faster (no sleep between rates)
- Simpler - one command
- Results already combined

**Cons:**
- No recovery time between rates
- Can't interrupt mid-test
- All-or-nothing execution

## Examples

### Test a single rate to verify setup:
```bash
docker run --privileged --rm \
    --network host \
    --ulimit nofile=1000000:1000000 \
    ghcr.io/paradigmxyz/flood:0.3.1 \
    eth_getBlockByNumber \
    mynode=http://localhost:8545 \
    --rates 250 \
    --duration 30 \
    --metrics success throughput p50 p90 p99 \
    --output /tmp/test
```

### Run full test suite with custom rates:
```bash
./run_flood_separate_rates.sh \
    -n mynode=http://localhost:8545 \
    -r "100 250 500 1000 2500 5000" \
    -d 60 \
    --sleep-rates 10
```

### Run single test type:
```bash
./run_flood_separate_rates.sh \
    -n mynode=http://localhost:8545 \
    -t "eth_call" \
    -r "500 1000 2000"
```

## Troubleshooting

### Merge fails with "No valid results found"
- Check that flood tests completed successfully
- Verify `results.json` and `test.json` exist in each rate directory

### Empty results in merged output
- Individual rate tests may have failed
- Check the individual rate directories for errors
- Look at summary.txt in each rate directory

### Docker permission errors
- Ensure you have docker permissions
- Use `--privileged` flag (already in script)
- Check volume mount paths are correct

## Advanced Usage

### Manual merge of existing results:
```bash
# If you already have separate rate results, merge them manually
./merge_flood_results.py output_merged/ \
    existing_results/rate_100/ \
    existing_results/rate_500/ \
    existing_results/rate_1000/
```

### Custom sleep schedules:
```bash
# Longer sleep for high-rate tests
./run_flood_separate_rates.sh \
    -n mynode=http://localhost:8545 \
    -r "100 500 1000" \
    --sleep-rates 5 \
    -r "2000 5000 10000" \
    --sleep-rates 30
```
Note: This would require script modification for per-rate sleep configuration.

## Testing the Merge Script

Run the test script to verify the merge functionality:

```bash
./test_merge.sh
```

This creates synthetic test data, merges it, and verifies the output is correct.
