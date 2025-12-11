#!/usr/bin/env python3
"""
Merge multiple separate flood rate test results into a single combined result.

This allows you to run each rate separately (with sleep between tests) and then
combine them into a single result file as if they were run together.
"""

import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, List


def load_json(filepath: str) -> Dict[str, Any]:
    """Load JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def save_json(filepath: str, data: Dict[str, Any]) -> None:
    """Save JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def merge_results(result_dirs: List[str], output_dir: str) -> None:
    """
    Merge multiple flood result directories into a single combined result.

    Args:
        result_dirs: List of directories containing individual rate results
        output_dir: Directory to save the combined results
    """
    if not result_dirs:
        print("Error: No result directories provided")
        sys.exit(1)

    # Load all results
    all_results = []
    all_tests = []

    for result_dir in result_dirs:
        results_path = os.path.join(result_dir, 'results.json')
        test_path = os.path.join(result_dir, 'test.json')

        if not os.path.exists(results_path):
            print(f"Warning: {results_path} not found, skipping")
            continue
        if not os.path.exists(test_path):
            print(f"Warning: {test_path} not found, skipping")
            continue

        results = load_json(results_path)
        test = load_json(test_path)

        all_results.append(results)
        all_tests.append(test)

    if not all_results:
        print("Error: No valid results found to merge")
        sys.exit(1)

    print(f"Merging {len(all_results)} result files...")

    # Use the first result as the base
    merged_results = all_results[0].copy()
    merged_test = all_tests[0].copy()

    # Merge the results for each node
    for node_name in merged_results['results'].keys():
        # Get the base node results
        base_node_results = merged_results['results'][node_name]

        # For each subsequent result, append the sequences
        for i, result in enumerate(all_results[1:], 1):
            if node_name not in result['results']:
                print(f"Warning: Node {node_name} not found in result {i}")
                continue

            node_results = result['results'][node_name]

            # Merge all sequence fields
            for key in base_node_results:
                if isinstance(base_node_results[key], list):
                    if isinstance(node_results.get(key), list):
                        base_node_results[key].extend(node_results[key])
                    else:
                        print(f"Warning: Field {key} is not a list in result {i}")
                elif key == 'deep_metrics' and base_node_results[key] is not None:
                    # Handle deep_metrics specially
                    if node_results.get(key) is not None:
                        for category in base_node_results[key]:
                            if category in node_results[key]:
                                for metric_key in base_node_results[key][category]:
                                    if isinstance(base_node_results[key][category][metric_key], list):
                                        base_node_results[key][category][metric_key].extend(
                                            node_results[key][category][metric_key]
                                        )

    # Update merged test parameters with all rates
    all_rates = []
    all_durations = []
    for test in all_tests:
        if 'test_parameters' in test and 'rates' in test['test_parameters']:
            rates = test['test_parameters']['rates']
            durations = test['test_parameters'].get('durations', [])
            if rates:
                all_rates.extend(rates)
            if durations:
                all_durations.extend(durations)

    if all_rates:
        merged_test['test_parameters']['rates'] = all_rates
    if all_durations:
        merged_test['test_parameters']['durations'] = all_durations

    # Update timing info
    merged_results['t_run_start'] = min(r['t_run_start'] for r in all_results)
    merged_results['t_run_end'] = max(r['t_run_end'] for r in all_results)

    # Save merged results
    os.makedirs(output_dir, exist_ok=True)

    output_results_path = os.path.join(output_dir, 'results.json')
    output_test_path = os.path.join(output_dir, 'test.json')

    save_json(output_results_path, merged_results)
    save_json(output_test_path, merged_test)

    print(f"✓ Merged results saved to {output_dir}")
    print(f"  - {output_results_path}")
    print(f"  - {output_test_path}")
    print(f"✓ Combined {len(all_rates)} rates: {all_rates}")


def main():
    if len(sys.argv) < 3:
        print("Usage: merge_flood_results.py <output_dir> <result_dir1> <result_dir2> ...")
        print()
        print("Example:")
        print("  merge_flood_results.py merged_results/ rate_250/ rate_500/ rate_1000/")
        sys.exit(1)

    output_dir = sys.argv[1]
    result_dirs = sys.argv[2:]

    merge_results(result_dirs, output_dir)


if __name__ == '__main__':
    main()
