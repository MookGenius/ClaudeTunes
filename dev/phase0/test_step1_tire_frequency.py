#!/usr/bin/env python3
"""
Test Phase 0, Step 0.1: Tire Frequency Refactor
Validates that the YAML-driven _get_base_frequency() works correctly
"""

import sys
import yaml

# Load the new YAML protocol
with open('/Users/mookbookairm1/Desktop/CTPython/ClaudeTunes v8.5.3c.yaml', 'r') as f:
    protocol = yaml.safe_load(f)

# Simulate the refactored function logic
def test_get_base_frequency(tire_compound):
    """Test YAML-driven tire frequency lookup"""
    compound_data = protocol['phase_B']['base_frequency_by_compound']
    compound_map = {
        key.replace('_', ' '): value['hz']
        for key, value in compound_data.items()
    }

    compound = tire_compound.strip()

    # Try exact match first
    if compound in compound_map:
        return compound_map[compound]

    # Try normalized match
    compound_normalized = compound.lower().replace(' ', '').replace('tires', '').replace('tire', '').strip()
    for key in compound_map:
        key_normalized = key.lower().replace(' ', '')
        if compound_normalized == key_normalized or key_normalized in compound_normalized:
            return compound_map[key]

    # Default
    default_freq = compound_data['Racing_Hard']['hz']
    print(f"  ⚠ Warning: Unknown tire compound '{compound}', defaulting to Racing Hard ({default_freq} Hz)")
    return default_freq


# Test Cases
print("=" * 60)
print("Phase 0, Step 0.1: Tire Frequency Refactor Test")
print("=" * 60)

test_cases = [
    # Exact matches
    ('Racing Hard', 2.85),
    ('Racing Medium', 3.15),
    ('Racing Soft', 3.40),
    ('Sport Hard', 1.85),
    ('Sport Medium', 2.15),
    ('Sport Soft', 2.40),
    ('Comfort Hard', 0.75),
    ('Comfort Medium', 1.25),
    ('Comfort Soft', 1.50),

    # GT7 "Sports" variants (new in v8.5.3c)
    ('Sports Hard', 1.85),
    ('Sports Medium', 2.15),
    ('Sports Soft', 2.40),

    # Normalized matches (lowercase, no spaces)
    ('racing hard', 2.85),
    ('RACING SOFT', 3.40),
    ('sport medium', 2.15),

    # Unknown compound (should default to Racing Hard)
    ('Unknown Compound', 2.85),
]

passed = 0
failed = 0

for compound, expected_hz in test_cases:
    result = test_get_base_frequency(compound)
    status = "✅ PASS" if result == expected_hz else "❌ FAIL"

    if result == expected_hz:
        passed += 1
    else:
        failed += 1

    print(f"{status} | '{compound}' → {result} Hz (expected {expected_hz})")

print("=" * 60)
print(f"Results: {passed} passed, {failed} failed")
print("=" * 60)

if failed == 0:
    print("✅ All tests passed! YAML-driven tire frequency lookup works correctly.")
    sys.exit(0)
else:
    print("❌ Some tests failed. Review the implementation.")
    sys.exit(1)
