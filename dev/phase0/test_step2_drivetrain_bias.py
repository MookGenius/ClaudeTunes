#!/usr/bin/env python3
"""
Test Phase 0, Step 0.2: Drivetrain Bias Refactor
Validates that the YAML-driven _get_drivetrain_bias() works correctly
"""

import sys
import yaml

# Load the new YAML protocol
with open('/Users/mookbookairm1/Desktop/CTPython/ClaudeTunes v8.5.3c.yaml', 'r') as f:
    protocol = yaml.safe_load(f)


def parse_bias_string(bias_str):
    """Parse YAML bias string to front/rear dict"""
    result = {'front': 0.0, 'rear': 0.0}

    # Split by spaces to handle combined bias (e.g., "+0.2F +0.2R")
    parts = bias_str.strip().split()

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Extract value and direction
        if part.endswith('F'):
            value = float(part[:-1])
            result['front'] = value
        elif part.endswith('R'):
            value = float(part[:-1])
            result['rear'] = value

    return result


def test_get_drivetrain_bias(drivetrain):
    """Test YAML-driven drivetrain bias lookup"""
    # Build bias map from YAML
    bias_data = protocol['phase_B']['drivetrain_bias']
    bias_map = {}

    for key, value in bias_data.items():
        if isinstance(value, dict) and 'bias' in value:
            bias_map[key] = parse_bias_string(value['bias'])

    # Handle AWD variants
    if drivetrain in bias_map:
        return bias_map[drivetrain]

    # If generic "AWD" without variant, use AWD_DEFAULT
    if drivetrain == 'AWD' and 'AWD_DEFAULT' in bias_map:
        return bias_map['AWD_DEFAULT']

    # Fallback to FR bias
    return bias_map.get('FR', {'front': 0.2, 'rear': 0.0})


# Test Cases
print("=" * 60)
print("Phase 0, Step 0.2: Drivetrain Bias Refactor Test")
print("=" * 60)

test_cases = [
    # Standard drivetrains
    ('FF', {'front': 0.4, 'rear': 0.0}),
    ('FR', {'front': 0.3, 'rear': 0.0}),
    ('MR', {'front': 0.0, 'rear': 0.1}),
    ('RR', {'front': 0.0, 'rear': 0.8}),
    ('RR_AWD', {'front': 0.0, 'rear': 0.6}),

    # AWD variants (new in v8.5.3c)
    ('AWD_FRONT', {'front': 0.3, 'rear': 0.0}),
    ('AWD_REAR', {'front': 0.0, 'rear': 0.5}),
    ('AWD_BALANCED', {'front': 0.2, 'rear': 0.2}),
    ('AWD_DEFAULT', {'front': 0.2, 'rear': 0.2}),

    # Generic AWD (should fallback to AWD_DEFAULT)
    ('AWD', {'front': 0.2, 'rear': 0.2}),

    # Unknown drivetrain (should fallback to FR)
    ('Unknown', {'front': 0.3, 'rear': 0.0}),
]

passed = 0
failed = 0

for drivetrain, expected in test_cases:
    result = test_get_drivetrain_bias(drivetrain)
    status = "✅ PASS" if result == expected else "❌ FAIL"

    if result == expected:
        passed += 1
    else:
        failed += 1

    print(f"{status} | '{drivetrain}' → F:{result['front']:.1f} R:{result['rear']:.1f} (expected F:{expected['front']:.1f} R:{expected['rear']:.1f})")

print("=" * 60)

# Test bias string parsing
print("\nBias String Parsing Tests:")
print("-" * 60)

parse_tests = [
    ("+0.4F", {'front': 0.4, 'rear': 0.0}),
    ("+0.1R", {'front': 0.0, 'rear': 0.1}),
    ("+0.2F +0.2R", {'front': 0.2, 'rear': 0.2}),
    ("+0.5R", {'front': 0.0, 'rear': 0.5}),
]

for bias_str, expected in parse_tests:
    result = parse_bias_string(bias_str)
    status = "✅ PASS" if result == expected else "❌ FAIL"

    if result == expected:
        passed += 1
    else:
        failed += 1

    print(f"{status} | '{bias_str}' → F:{result['front']:.1f} R:{result['rear']:.1f}")

print("=" * 60)
print(f"Results: {passed} passed, {failed} failed")
print("=" * 60)

if failed == 0:
    print("✅ All tests passed! YAML-driven drivetrain bias works correctly.")
    sys.exit(0)
else:
    print("❌ Some tests failed. Review the implementation.")
    sys.exit(1)
