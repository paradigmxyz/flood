#!/bin/bash
# Run flood tests with each rate separately (with sleep between rates)
# Then merge all results into a single combined output

FLOOD_IMAGE="ghcr.io/paradigmxyz/flood:0.3.1"
DURATION=60
OUTPUT_DIR="./results"
NODE=""
TESTS="eth_call eth_feeHistory eth_getBlockByNumber eth_getLogs trace_block trace_replayBlockTransactions"
RATES="250 500 750 1000 1500 2000 2500 5000 7500 10000"
METRICS="success throughput min mean p50 p90 p95 p99 max"
DEEP_CHECK="--deep-check"
SLEEP_BETWEEN_RATES=5
SLEEP_BETWEEN_TESTS=10

usage() {
    echo "Usage: $(basename "$0") -n name=url [options]"
    echo ""
    echo "This script runs each RPS rate as a separate test with sleep between them,"
    echo "then merges all results into a single combined output."
    echo ""
    echo "Options:"
    echo "  -n, --node NAME=URL      Node to test (required)"
    echo "  -t, --tests TESTS        Space-separated test names"
    echo "  -r, --rates RATES        Space-separated RPS rates"
    echo "  -d, --duration SECONDS   Duration for each rate test"
    echo "  -o, --output DIR         Output directory"
    echo "  -m, --metrics METRICS    Space-separated metrics to collect"
    echo "  --sleep-rates SECONDS    Sleep between rate tests (default: 5)"
    echo "  --sleep-tests SECONDS    Sleep between test types (default: 10)"
    echo "  --no-deep-check          Disable deep checking"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Example:"
    echo "  $(basename "$0") -n mynode=http://localhost:8545 --sleep-rates 10"
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -n|--node) NODE="$2"; shift 2;;
        -t|--tests) TESTS="$2"; shift 2;;
        -r|--rates) RATES="$2"; shift 2;;
        -d|--duration) DURATION="$2"; shift 2;;
        -o|--output) OUTPUT_DIR="$2"; shift 2;;
        -m|--metrics) METRICS="$2"; shift 2;;
        --sleep-rates) SLEEP_BETWEEN_RATES="$2"; shift 2;;
        --sleep-tests) SLEEP_BETWEEN_TESTS="$2"; shift 2;;
        --no-deep-check) DEEP_CHECK=""; shift;;
        -h|--help) usage;;
        *) echo "Unknown option: $1"; usage;;
    esac
done

[[ -z "$NODE" ]] && usage

NODE_NAME="${NODE%%=*}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_DIR="$OUTPUT_DIR/${NODE_NAME}_${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR="$(cd "$OUTPUT_DIR" && pwd)"

echo "=========================================="
echo "Flood Separate Rate Test Runner"
echo "=========================================="
echo "Node:            $NODE"
echo "Tests:           $TESTS"
echo "Rates:           $RATES"
echo "Duration:        ${DURATION}s per rate"
echo "Sleep (rates):   ${SLEEP_BETWEEN_RATES}s"
echo "Sleep (tests):   ${SLEEP_BETWEEN_TESTS}s"
echo "Output:          $OUTPUT_DIR"
echo "=========================================="
echo ""

# Convert to arrays
TEST_ARRAY=($TESTS)
RATE_ARRAY=($RATES)
METRIC_ARRAY=($METRICS)

TOTAL_TESTS=${#TEST_ARRAY[@]}
TOTAL_RATES=${#RATE_ARRAY[@]}

for TEST in "${TEST_ARRAY[@]}"; do
    echo "=========================================="
    echo "Test: $TEST"
    echo "=========================================="
    echo ""

    TEST_OUTPUT_DIR="$OUTPUT_DIR/$TEST"
    mkdir -p "$TEST_OUTPUT_DIR"

    # Track all rate result directories for this test
    RATE_RESULT_DIRS=()

    # Run each rate separately
    for i in "${!RATE_ARRAY[@]}"; do
        RATE="${RATE_ARRAY[$i]}"
        RATE_NUM=$((i + 1))

        echo "[$RATE_NUM/$TOTAL_RATES] Running rate: $RATE rps"

        RATE_OUTPUT_DIR="$TEST_OUTPUT_DIR/rate_${RATE}"
        mkdir -p "$RATE_OUTPUT_DIR"

        # Build docker command
        CMD=(docker run --privileged --rm
            --network host
            --ulimit nofile=1000000:1000000
            -v "$RATE_OUTPUT_DIR:/results"
            "$FLOOD_IMAGE"
            "$TEST"
            "$NODE"
            --rates "$RATE"
            --duration "$DURATION"
            --metrics)

        for METRIC in "${METRIC_ARRAY[@]}"; do
            CMD+=("$METRIC")
        done

        if [[ -n "$DEEP_CHECK" ]]; then
            CMD+=("$DEEP_CHECK")
        fi

        CMD+=(--output "/results")

        # Run the test
        if "${CMD[@]}"; then
            echo "  ✓ Rate $RATE completed"
            RATE_RESULT_DIRS+=("$RATE_OUTPUT_DIR")
        else
            echo "  ✗ Rate $RATE failed"
        fi

        # Sleep between rates (except after last one)
        if [[ $RATE_NUM -lt $TOTAL_RATES ]] && [[ $SLEEP_BETWEEN_RATES -gt 0 ]]; then
            echo "  Sleeping ${SLEEP_BETWEEN_RATES}s..."
            sleep $SLEEP_BETWEEN_RATES
        fi

        echo ""
    done

    # Merge all rate results for this test
    if [[ ${#RATE_RESULT_DIRS[@]} -gt 0 ]]; then
        echo "Merging ${#RATE_RESULT_DIRS[@]} rate results..."

        MERGED_OUTPUT_DIR="$TEST_OUTPUT_DIR/combined"

        python3 merge_flood_results.py "$MERGED_OUTPUT_DIR" "${RATE_RESULT_DIRS[@]}"

        if [[ $? -eq 0 ]]; then
            # Generate summary for the merged results
            echo ""
            echo "Generating summary for merged results..."
            docker run --rm \
                -v "$MERGED_OUTPUT_DIR:/results" \
                "$FLOOD_IMAGE" \
                report /results \
                --output /results 2>/dev/null || true

            echo "✓ Combined results: $MERGED_OUTPUT_DIR"
        else
            echo "✗ Failed to merge results"
        fi
    fi

    echo ""
    echo "Sleep ${SLEEP_BETWEEN_TESTS}s before next test..."
    sleep $SLEEP_BETWEEN_TESTS
    echo ""
done

echo "=========================================="
echo "All Tests Complete!"
echo "=========================================="
echo "Results directory: $OUTPUT_DIR"
echo ""
echo "Combined results for each test:"
for TEST in "${TEST_ARRAY[@]}"; do
    MERGED_DIR="$OUTPUT_DIR/$TEST/combined"
    if [[ -d "$MERGED_DIR" ]]; then
        echo "  ✓ $TEST: $MERGED_DIR"
    else
        echo "  ✗ $TEST: merge failed"
    fi
done
echo "=========================================="
