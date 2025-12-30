"""
Phase 0, Step 0.2: Drivetrain Bias Refactor
Refactored _get_drivetrain_bias() to read from YAML protocol
"""

def _parse_bias_string(bias_str):
    """
    Parse YAML bias string to front/rear dict

    Examples:
        "+0.4F" → {'front': 0.4, 'rear': 0.0}
        "+0.1R" → {'front': 0.0, 'rear': 0.1}
        "+0.2F +0.2R" → {'front': 0.2, 'rear': 0.2}
    """
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


def _get_drivetrain_bias(self):
    """Calculate drivetrain-specific frequency bias (YAML-driven)"""
    # YAML: phase_B.drivetrain_bias (lines 100-108)
    dt = self.car_data.get('drivetrain', 'FR')

    # Build bias map from YAML
    bias_data = self.protocol['phase_B']['drivetrain_bias']
    bias_map = {}

    for key, value in bias_data.items():
        if isinstance(value, dict) and 'bias' in value:
            bias_map[key] = self._parse_bias_string(value['bias'])

    # Handle AWD variants
    # If user specified AWD_FRONT/REAR/BALANCED, use that directly
    if dt in bias_map:
        return bias_map[dt]

    # If generic "AWD" without variant, try to use AWD_DEFAULT
    if dt == 'AWD' and 'AWD_DEFAULT' in bias_map:
        return bias_map['AWD_DEFAULT']

    # Fallback to FR bias (most common)
    return bias_map.get('FR', {'front': 0.2, 'rear': 0.0})


# CHANGES SUMMARY:
# -----------------
# BEFORE (Lines 909-921):
#   - Hardcoded bias_map dictionary with 5 entries (FF/FR/MR/RR/AWD)
#   - Simple AWD handling (0.2/0.2)
#   - No support for AWD variants
#
# AFTER (This version):
#   - Builds bias_map from YAML: self.protocol['phase_B']['drivetrain_bias']
#   - Parses bias strings: "+0.4F" → {'front': 0.4, 'rear': 0.0}
#   - Supports 9 drivetrain types (FF/FR/MR/RR/RR_AWD + 4 AWD variants)
#   - AWD_DEFAULT used when generic "AWD" specified
#   - Fallback to FR bias (most common street car layout)
#
# YAML REFERENCE:
#   Lines 100-108: phase_B.drivetrain_bias
#   9 drivetrain types with explicit AWD categories
#
# BENEFITS:
#   - YAML is source of truth (no hardcoded values)
#   - Easy to adjust bias values without code changes
#   - AWD handling now explicit and documented
#   - Future drivetrain types auto-included
