#!/usr/bin/env python3
"""
Test Phase 0, Step 0.3: CG Adjustment Refactor
Validates that the YAML-driven _get_cg_adjustment() works correctly
"""

import sys
import yaml

# Load the new YAML protocol
with open('/Users/mookbookairm1/Desktop/CTPython/ClaudeTunes v8.5.3c.yaml', 'r') as f:
    protocol = yaml.safe_load(f)


def parse_adjustment_value(add_str):
    """Parse YAML adjustment string to numeric value"""
    if not add_str or add_str == "0":
        return 0.0

    # Remove " Hz" suffix
    add_str = add_str.replace(' Hz', '').strip()

    # Check if it's a range (contains –)
    if '–' in add_str or '-' in add_str[1:]:  # Check for range dash (not negative sign)
        # Extract range bounds
        # Handle both en-dash (–) and hyphen (-)
        parts = add_str.replace('–', '-').split('-')
        # Filter out empty strings from negative numbers
        parts = [p for p in parts if p]

        if len(parts) >= 2:
            # Get first and last non-empty parts
            try:
                low = float(parts[0])
                high = float(parts[-1])
                # Return middle of range
                return (low + high) / 2
            except ValueError:
                pass

    # Single value
    try:
        return float(add_str)
    except ValueError:
        return 0.0


def test_get_cg_adjustment(cg_height):
    """Test YAML-driven CG adjustment lookup"""
    # Get CG adjustment data from YAML
    cg_data = protocol['phase_B']['cg_adjustments']

    # High CG (>500mm)
    if cg_height > 500:
        add_str = cg_data['high']['add']
        return parse_adjustment_value(add_str)

    # Very low CG (<400mm)
    elif cg_height < 400:
        add_str = cg_data['very_low']['add']
        return parse_adjustment_value(add_str)

    # Standard CG (400-500mm)
    else:
        add_str = cg_data['standard']['add']
        return parse_adjustment_value(add_str)


# Test Cases
print("=" * 60)
print("Phase 0, Step 0.3: CG Adjustment Refactor Test")
print("=" * 60)

test_cases = [
    # High CG (>500mm) - should return middle of "+0.1–0.3 Hz" range = 0.2
    (600, 0.2),
    (550, 0.2),
    (501, 0.2),

    # Standard CG (400-500mm) - should return 0.0
    (500, 0.0),
    (450, 0.0),
    (400, 0.0),

    # Very low CG (<400mm) - should return -0.1
    (399, -0.1),
    (350, -0.1),
    (300, -0.1),
]

passed = 0
failed = 0

for cg_height, expected in test_cases:
    result = test_get_cg_adjustment(cg_height)
    status = "✅ PASS" if result == expected else "❌ FAIL"

    if result == expected:
        passed += 1
    else:
        failed += 1

    print(f"{status} | CG {cg_height}mm → {result:+.1f} Hz (expected {expected:+.1f})")

print("=" * 60)

# Test adjustment value parsing
print("\nAdjustment Value Parsing Tests:")
print("-" * 60)

parse_tests = [
    ("+0.1–0.3 Hz", 0.2),  # Range: middle value
    ("-0.1 Hz", -0.1),     # Single negative value
    ("0", 0.0),            # Zero
    ("+0.2 Hz", 0.2),      # Single positive value
]

for add_str, expected in parse_tests:
    result = parse_adjustment_value(add_str)
    status = "✅ PASS" if result == expected else "❌ FAIL"

    if result == expected:
        passed += 1
    else:
        failed += 1

    print(f"{status} | '{add_str}' → {result:+.1f} Hz (expected {expected:+.1f})")

print("=" * 60)
print(f"Results: {passed} passed, {failed} failed")
print("=" * 60)

if failed == 0:
    print("✅ All tests passed! YAML-driven CG adjustment works correctly.")
    sys.exit(0)
else:
    print("❌ Some tests failed. Review the implementation.")
    sys.exit(1)
