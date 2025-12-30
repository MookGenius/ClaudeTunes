#!/usr/bin/env python3
"""
Test Phase 0, Step 0.5: Differential Baselines Refactor
Validates that the YAML-driven differential baselines loader works correctly
"""

import sys
import yaml

# Load the new YAML protocol
with open('/Users/mookbookairm1/Desktop/CTPython/ClaudeTunes v8.5.3c.yaml', 'r') as f:
    protocol = yaml.safe_load(f)


def parse_range_string(range_str):
    """Parse YAML range string to tuple"""
    parts = range_str.split('-')
    if len(parts) == 2:
        try:
            return (int(parts[0]), int(parts[1]))
        except ValueError:
            pass
    return (0, 0)


def test_load_differential_baselines():
    """Test YAML-driven differential baselines loading"""
    yaml_diff = protocol['reference_tables']['differential_baselines']

    diff_baselines = {}

    # Map YAML drivetrain names to Python names
    drivetrain_map = {
        'FWD': 'FF',
        'RWD': 'FR',  # Use FR for generic RWD
        'RR_AWD': 'RR_AWD',
        'RR_PURE': 'RR'
    }

    for yaml_name, python_name in drivetrain_map.items():
        if yaml_name in yaml_diff:
            data = yaml_diff[yaml_name]

            # Check if this entry has baseline values (AWD might not)
            if 'initial' in data and 'accel' in data and 'brake' in data:
                # Parse ranges: "10-15" → (10, 15)
                initial = parse_range_string(data['initial'])
                accel = parse_range_string(data['accel'])
                brake = parse_range_string(data['brake'])

                diff_baselines[python_name] = {
                    'initial': initial,
                    'accel': accel,
                    'brake': brake
                }

    # Add MR (same as RWD/FR)
    if 'FR' in diff_baselines:
        diff_baselines['MR'] = diff_baselines['FR'].copy()

    # Add AWD (use RR_AWD as baseline - rear-biased AWD)
    if 'RR_AWD' in diff_baselines:
        diff_baselines['AWD'] = diff_baselines['RR_AWD'].copy()

    return diff_baselines


# Test Cases
print("=" * 60)
print("Phase 0, Step 0.5: Differential Baselines Refactor Test")
print("=" * 60)

# Expected baselines structure
expected = {
    'FF': {'initial': (10, 15), 'accel': (30, 50), 'brake': (5, 10)},
    'FR': {'initial': (5, 20), 'accel': (15, 35), 'brake': (15, 40)},
    'MR': {'initial': (5, 20), 'accel': (15, 35), 'brake': (15, 40)},  # Same as RWD/FR
    'RR': {'initial': (10, 20), 'accel': (20, 35), 'brake': (20, 40)},
    'RR_AWD': {'initial': (5, 15), 'accel': (15, 30), 'brake': (15, 35)},
    'AWD': {'initial': (5, 15), 'accel': (15, 30), 'brake': (15, 35)}
}

result_baselines = test_load_differential_baselines()

passed = 0
failed = 0

print("\nDifferential Baselines Tests:")
print("-" * 60)

# Test that all expected drivetrains are present
for drivetrain, expected_data in expected.items():
    if drivetrain in result_baselines:
        result_data = result_baselines[drivetrain]

        # Check initial
        if result_data['initial'] == expected_data['initial']:
            print(f"✅ PASS | {drivetrain}: initial {result_data['initial']}")
            passed += 1
        else:
            print(f"❌ FAIL | {drivetrain}: initial {result_data['initial']} (expected {expected_data['initial']})")
            failed += 1

        # Check accel
        if result_data['accel'] == expected_data['accel']:
            print(f"✅ PASS | {drivetrain}: accel {result_data['accel']}")
            passed += 1
        else:
            print(f"❌ FAIL | {drivetrain}: accel {result_data['accel']} (expected {expected_data['accel']})")
            failed += 1

        # Check brake
        if result_data['brake'] == expected_data['brake']:
            print(f"✅ PASS | {drivetrain}: brake {result_data['brake']}")
            passed += 1
        else:
            print(f"❌ FAIL | {drivetrain}: brake {result_data['brake']} (expected {expected_data['brake']})")
            failed += 1
    else:
        print(f"❌ FAIL | {drivetrain}: missing from result baselines")
        failed += 3

print("=" * 60)
print(f"Results: {passed} passed, {failed} failed")
print("=" * 60)

if failed == 0:
    print("✅ All tests passed! YAML-driven differential baselines work correctly.")
    sys.exit(0)
else:
    print("❌ Some tests failed. Review the implementation.")
    sys.exit(1)
