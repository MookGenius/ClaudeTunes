#!/usr/bin/env python3
"""
Test Phase 0, Step 0.4: Downforce Database Refactor
Validates that the YAML-driven downforce database loader works correctly
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


def parse_freq_add_string(freq_str):
    """Parse YAML frequency add string to tuple"""
    # Remove " Hz" suffix and "+" prefix
    freq_str = freq_str.replace(' Hz', '').replace('+', '').strip()

    # Check if it's a range
    if '-' in freq_str:
        parts = freq_str.split('-')
        if len(parts) == 2:
            try:
                return (float(parts[0]), float(parts[1]))
            except ValueError:
                pass
    else:
        # Single value
        try:
            val = float(freq_str)
            return (val, val)
        except ValueError:
            pass

    return (0.0, 0.0)


def test_load_downforce_database():
    """Test YAML-driven downforce database loading"""
    yaml_db = protocol['reference_tables']['gt7_downforce_database']['classes']

    downforce_db = {}

    for car_class, data in yaml_db.items():
        # Parse df_lbs: "3000-4000" → (3000, 4000)
        df_range = parse_range_string(data['df_lbs'])

        # Parse freq_add: "+0.4-0.5 Hz" → (0.4, 0.5)
        freq_add = parse_freq_add_string(data['freq_add'])

        # Get gt7_impact (already a string)
        gt7_impact = data['gt7_impact']

        downforce_db[car_class] = {
            'df_range': df_range,
            'freq_add': freq_add,
            'gt7_impact': gt7_impact
        }

    return downforce_db


# Test Cases
print("=" * 60)
print("Phase 0, Step 0.4: Downforce Database Refactor Test")
print("=" * 60)

# Expected database structure
expected = {
    'formula': {'df_range': (3000, 4000), 'freq_add': (0.4, 0.5), 'gt7_impact': '~0.3-0.4s per 1000lbs'},
    'gr2_lmp': {'df_range': (1500, 2000), 'freq_add': (0.3, 0.4), 'gt7_impact': '~0.2-0.3s per 1000lbs'},
    'gr3_gt3': {'df_range': (1000, 1500), 'freq_add': (0.2, 0.3), 'gt7_impact': '~0.1-0.2s per 1000lbs'},
    'gr4_race': {'df_range': (400, 800), 'freq_add': (0.1, 0.2), 'gt7_impact': '~0.05-0.15s per 1000lbs'},
    'street_perf': {'df_range': (100, 400), 'freq_add': (0.0, 0.1), 'gt7_impact': 'Minimal'},
    'street_std': {'df_range': (0, 100), 'freq_add': (0.0, 0.0), 'gt7_impact': 'Negligible'}
}

result_db = test_load_downforce_database()

passed = 0
failed = 0

print("\nDatabase Structure Tests:")
print("-" * 60)

# Test that all expected classes are present
for class_name, expected_data in expected.items():
    if class_name in result_db:
        result_data = result_db[class_name]

        # Check df_range
        if result_data['df_range'] == expected_data['df_range']:
            print(f"✅ PASS | {class_name}: df_range {result_data['df_range']}")
            passed += 1
        else:
            print(f"❌ FAIL | {class_name}: df_range {result_data['df_range']} (expected {expected_data['df_range']})")
            failed += 1

        # Check freq_add
        if result_data['freq_add'] == expected_data['freq_add']:
            print(f"✅ PASS | {class_name}: freq_add {result_data['freq_add']}")
            passed += 1
        else:
            print(f"❌ FAIL | {class_name}: freq_add {result_data['freq_add']} (expected {expected_data['freq_add']})")
            failed += 1

        # Check gt7_impact
        if result_data['gt7_impact'] == expected_data['gt7_impact']:
            print(f"✅ PASS | {class_name}: gt7_impact '{result_data['gt7_impact']}'")
            passed += 1
        else:
            print(f"❌ FAIL | {class_name}: gt7_impact '{result_data['gt7_impact']}' (expected '{expected_data['gt7_impact']}')")
            failed += 1
    else:
        print(f"❌ FAIL | {class_name}: missing from result database")
        failed += 3

print("=" * 60)

# Test parsing functions
print("\nParsing Function Tests:")
print("-" * 60)

range_tests = [
    ("3000-4000", (3000, 4000)),
    ("1500-2000", (1500, 2000)),
    ("0-100", (0, 100)),
]

for range_str, expected_tuple in range_tests:
    result = parse_range_string(range_str)
    status = "✅ PASS" if result == expected_tuple else "❌ FAIL"
    if result == expected_tuple:
        passed += 1
    else:
        failed += 1
    print(f"{status} | parse_range_string('{range_str}') → {result}")

freq_tests = [
    ("+0.4-0.5 Hz", (0.4, 0.5)),
    ("+0.0 Hz", (0.0, 0.0)),
    ("+0.1-0.2 Hz", (0.1, 0.2)),
]

for freq_str, expected_tuple in freq_tests:
    result = parse_freq_add_string(freq_str)
    status = "✅ PASS" if result == expected_tuple else "❌ FAIL"
    if result == expected_tuple:
        passed += 1
    else:
        failed += 1
    print(f"{status} | parse_freq_add_string('{freq_str}') → {result}")

print("=" * 60)
print(f"Results: {passed} passed, {failed} failed")
print("=" * 60)

if failed == 0:
    print("✅ All tests passed! YAML-driven downforce database works correctly.")
    sys.exit(0)
else:
    print("❌ Some tests failed. Review the implementation.")
    sys.exit(1)
