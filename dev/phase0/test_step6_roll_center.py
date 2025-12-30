#!/usr/bin/env python3
"""
Test Phase 0, Step 0.6: Roll Center Compensation Refactor
Validates that the YAML-driven roll center calculation works correctly
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
    if '–' in add_str or '-' in add_str[1:]:
        # Extract range bounds
        parts = add_str.replace('–', '-').split('-')
        parts = [p for p in parts if p]

        if len(parts) >= 2:
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


def test_calculate_roll_center(cg_height, drivetrain, total_df):
    """Test YAML-driven roll center calculation"""
    # Get roll center compensation data from YAML
    rc_data = protocol['phase_B']['roll_center_compensation']

    # Determine DF level multiplier from YAML
    df_multipliers = rc_data['df_multiplier']
    if total_df > 1200:
        df_mult = parse_adjustment_value(df_multipliers['high'])
    elif total_df > 500:
        df_mult = parse_adjustment_value(df_multipliers['moderate'])
    else:
        df_mult = parse_adjustment_value(df_multipliers['low'])

    # Apply drivetrain-specific adjustments from YAML
    dt_ranges = rc_data['layout']
    dt_mult_map = {}
    for dt_name, range_str in dt_ranges.items():
        dt_mult_map[dt_name] = parse_adjustment_value(range_str)

    # Use average of DF and drivetrain multipliers
    final_mult = (df_mult + dt_mult_map.get(drivetrain, 0.20)) / 2
    rc_height = final_mult * cg_height

    return {
        'multiplier': final_mult,
        'height': rc_height,
        'cg_height': cg_height
    }


# Test Cases
print("=" * 60)
print("Phase 0, Step 0.6: Roll Center Compensation Refactor Test")
print("=" * 60)

test_cases = [
    # (cg_height, drivetrain, total_df, expected_mult, expected_rc_height)
    # High DF (>1200), FR drivetrain, 450mm CG
    # DF mult: 0.275 (0.25-0.30), DT mult: 0.225 (0.15-0.30) → avg = 0.25
    (450, 'FR', 1500, 0.25, 112.5),

    # Moderate DF (500-1200), FF drivetrain, 450mm CG
    # DF mult: 0.225 (0.20-0.25), DT mult: 0.225 (0.20-0.25) → avg = 0.225
    (450, 'FF', 800, 0.225, 101.25),

    # Low DF (<500), MR drivetrain, 400mm CG
    # DF mult: 0.175 (0.15-0.20), DT mult: 0.20 (0.15-0.25) → avg = 0.1875
    (400, 'MR', 300, 0.1875, 75.0),

    # High DF, RR drivetrain, 500mm CG
    # DF mult: 0.275, DT mult: 0.25 (0.20-0.30) → avg = 0.2625
    (500, 'RR', 1800, 0.2625, 131.25),
]

passed = 0
failed = 0

print("\nRoll Center Calculation Tests:")
print("-" * 60)

for cg_height, drivetrain, total_df, expected_mult, expected_height in test_cases:
    result = test_calculate_roll_center(cg_height, drivetrain, total_df)

    mult_match = abs(result['multiplier'] - expected_mult) < 0.001
    height_match = abs(result['height'] - expected_height) < 0.1

    if mult_match and height_match:
        status = "✅ PASS"
        passed += 1
    else:
        status = "❌ FAIL"
        failed += 1

    print(f"{status} | CG:{cg_height}mm {drivetrain} DF:{total_df}lbs → mult:{result['multiplier']:.4f} height:{result['height']:.1f}mm")
    if not mult_match:
        print(f"         Expected mult: {expected_mult:.4f}, got: {result['multiplier']:.4f}")
    if not height_match:
        print(f"         Expected height: {expected_height:.1f}mm, got: {result['height']:.1f}mm")

print("=" * 60)

# Test multiplier parsing
print("\nMultiplier Parsing Tests:")
print("-" * 60)

parse_tests = [
    ("0.25–0.30", 0.275),  # High DF range
    ("0.20–0.25", 0.225),  # Moderate DF range
    ("0.15–0.20", 0.175),  # Low DF range
    ("0.15–0.30", 0.225),  # FR layout range
]

for range_str, expected in parse_tests:
    result = parse_adjustment_value(range_str)
    status = "✅ PASS" if abs(result - expected) < 0.001 else "❌ FAIL"

    if abs(result - expected) < 0.001:
        passed += 1
    else:
        failed += 1

    print(f"{status} | parse_adjustment_value('{range_str}') → {result:.3f} (expected {expected:.3f})")

print("=" * 60)
print(f"Results: {passed} passed, {failed} failed")
print("=" * 60)

if failed == 0:
    print("✅ All tests passed! YAML-driven roll center calculation works correctly.")
    sys.exit(0)
else:
    print("❌ Some tests failed. Review the implementation.")
    sys.exit(1)
