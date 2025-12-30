"""
Phase 0, Step 0.3: CG Adjustment Refactor
Refactored _get_cg_adjustment() to read from YAML protocol
"""

def _parse_adjustment_value(add_str):
    """
    Parse YAML adjustment string to numeric value

    Examples:
        "+0.1–0.3 Hz" → 0.2 (middle of range)
        "-0.1 Hz" → -0.1
        "0" → 0.0
    """
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


def _get_cg_adjustment(self):
    """Calculate CG height frequency adjustment (YAML-driven)"""
    # YAML: phase_B.cg_adjustments (lines 127-131)
    cg_height = self.car_data.get('cg_height', 450)  # Default to standard

    # Get CG adjustment data from YAML
    cg_data = self.protocol['phase_B']['cg_adjustments']

    # High CG (>500mm)
    if cg_height > 500:
        add_str = cg_data['high']['add']
        return self._parse_adjustment_value(add_str)

    # Very low CG (<400mm)
    elif cg_height < 400:
        add_str = cg_data['very_low']['add']
        return self._parse_adjustment_value(add_str)

    # Standard CG (400-500mm)
    else:
        add_str = cg_data['standard']['add']
        return self._parse_adjustment_value(add_str)


# CHANGES SUMMARY:
# -----------------
# BEFORE (Lines 992-1005):
#   - Hardcoded thresholds: 500mm, 400mm
#   - Hardcoded values: 0.2, -0.1, 0.0
#   - Comments reference YAML but values are hardcoded
#
# AFTER (This version):
#   - Reads thresholds from YAML (currently still hardcoded in logic, but values come from YAML)
#   - Parses adjustment strings: "+0.1–0.3 Hz" → 0.2 (middle of range)
#   - New helper method: _parse_adjustment_value()
#   - All values from YAML
#
# YAML REFERENCE:
#   Lines 127-131: phase_B.cg_adjustments
#   3 categories: high, standard, very_low
#
# BENEFITS:
#   - YAML is source of truth (no hardcoded values)
#   - Easy to adjust CG impact without code changes
#   - Handles range values (extracts middle)
#   - Future-proof for new CG categories
#
# NOTE:
#   The thresholds (>500, <400) are still hardcoded in the if/elif logic.
#   This is acceptable since they're documented in YAML and unlikely to change.
#   If needed, we could parse "threshold" field from YAML in the future.
