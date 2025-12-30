"""
Phase 0, Step 0.1: Tire Frequency Refactor
Refactored _get_base_frequency() to read from YAML protocol
"""

def _get_base_frequency(self):
    """Get base frequency from tire compound (YAML-driven)"""
    # YAML: phase_B.base_frequency_by_compound
    # Build compound map from YAML (convert underscores to spaces for GT7 format)
    compound_data = self.protocol['phase_B']['base_frequency_by_compound']
    compound_map = {
        key.replace('_', ' '): value['hz']
        for key, value in compound_data.items()
    }

    compound = self.car_data.get('tire_compound', 'Racing Hard').strip()

    # Try exact match first
    if compound in compound_map:
        return compound_map[compound]

    # Try normalized match (remove spaces, lowercase)
    compound_normalized = compound.lower().replace(' ', '').replace('tires', '').replace('tire', '').strip()
    for key in compound_map:
        key_normalized = key.lower().replace(' ', '')
        if compound_normalized == key_normalized or key_normalized in compound_normalized:
            return compound_map[key]

    # If still no match, default to Racing Hard
    default_freq = compound_data['Racing_Hard']['hz']
    print(f"  ⚠ Warning: Unknown tire compound '{compound}', defaulting to Racing Hard ({default_freq} Hz)")
    return default_freq


# CHANGES SUMMARY:
# -----------------
# BEFORE (Lines 760-790):
#   - Hardcoded compound_map dictionary with 12 entries
#   - Hardcoded default value: 2.85
#
# AFTER (This version):
#   - Builds compound_map from YAML: self.protocol['phase_B']['base_frequency_by_compound']
#   - Converts YAML keys (Comfort_Hard → "Comfort Hard") for GT7 compatibility
#   - Extracts 'hz' value from YAML structure: {hz: 2.85, grip: 1.12, range: "2.2-4.5"}
#   - Default value read from YAML: compound_data['Racing_Hard']['hz']
#   - Same lookup logic preserved (exact match → normalized match → default)
#
# YAML REFERENCE:
#   Lines 86-98: phase_B.base_frequency_by_compound
#   12 tire compounds including Sports_* aliases
#
# BENEFITS:
#   - YAML is source of truth (no hardcoded values)
#   - Easy to adjust frequencies without code changes
#   - Automatically includes new tire compounds added to YAML
#   - Preserves all existing lookup behavior
