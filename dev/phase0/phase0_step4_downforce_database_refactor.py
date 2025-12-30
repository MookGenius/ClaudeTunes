"""
Phase 0, Step 0.4: Downforce Database Refactor
Refactor GT7_DOWNFORCE_DATABASE class constant to read from YAML protocol
"""

# BEFORE (Lines 23-30):
# Class-level constant (loaded once when class is defined)
"""
class ClaudeTunesCLI:
    GT7_DOWNFORCE_DATABASE = {
        'formula': {'df_range': (3000, 4000), 'freq_add': (0.4, 0.5), 'gt7_impact': '0.3-0.4s/1000lbs'},
        'gr2_lmp': {'df_range': (1500, 2000), 'freq_add': (0.3, 0.4), 'gt7_impact': '0.2-0.3s/1000lbs'},
        'gr3_gt3': {'df_range': (1000, 1500), 'freq_add': (0.2, 0.3), 'gt7_impact': '0.1-0.2s/1000lbs'},
        'gr4_race': {'df_range': (400, 800), 'freq_add': (0.1, 0.2), 'gt7_impact': '0.05-0.15s/1000lbs'},
        'street_perf': {'df_range': (100, 400), 'freq_add': (0.0, 0.1), 'gt7_impact': 'Minimal'},
        'street_std': {'df_range': (0, 100), 'freq_add': (0.0, 0.0), 'gt7_impact': 'Negligible'}
    }
"""

# AFTER:
# Instance variable loaded from YAML in __init__
"""
def __init__(self, protocol_path="ClaudeTunes v8.5.3c.yaml", track_type="balanced", conservative_ride_height=False):
    '''Initialize with ClaudeTunes protocol'''
    self.protocol = self._load_protocol(protocol_path)
    self.car_data = {}
    self.telemetry = {}
    self.results = {}
    self.track_type = track_type
    self.conservative_ride_height = conservative_ride_height

    # Load downforce database from YAML (YAML: reference_tables.gt7_downforce_database)
    self.gt7_downforce_database = self._load_downforce_database()
"""


def _parse_range_string(range_str):
    """
    Parse YAML range string to tuple
    Examples:
        "3000-4000" → (3000, 4000)
        "1500-2000" → (1500, 2000)
        "0-100" → (0, 100)
    """
    # Split by dash
    parts = range_str.split('-')
    if len(parts) == 2:
        try:
            return (int(parts[0]), int(parts[1]))
        except ValueError:
            pass
    return (0, 0)


def _parse_freq_add_string(freq_str):
    """
    Parse YAML frequency add string to tuple
    Examples:
        "+0.4-0.5 Hz" → (0.4, 0.5)
        "+0.1-0.2 Hz" → (0.1, 0.2)
        "+0.0 Hz" → (0.0, 0.0)
    """
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


def _load_downforce_database(self):
    """Load GT7 downforce database from YAML protocol (YAML-driven)"""
    # YAML: reference_tables.gt7_downforce_database.classes (lines 397-441)
    yaml_db = self.protocol['reference_tables']['gt7_downforce_database']['classes']

    downforce_db = {}

    for car_class, data in yaml_db.items():
        # Parse df_lbs: "3000-4000" → (3000, 4000)
        df_range = self._parse_range_string(data['df_lbs'])

        # Parse freq_add: "+0.4-0.5 Hz" → (0.4, 0.5)
        freq_add = self._parse_freq_add_string(data['freq_add'])

        # Get gt7_impact (already a string)
        gt7_impact = data['gt7_impact']

        downforce_db[car_class] = {
            'df_range': df_range,
            'freq_add': freq_add,
            'gt7_impact': gt7_impact
        }

    return downforce_db


# CHANGES SUMMARY:
# -----------------
# BEFORE:
#   - Class-level constant GT7_DOWNFORCE_DATABASE
#   - Hardcoded 6 car classes with tuples
#   - Loaded once when class is defined (before YAML is loaded!)
#
# AFTER:
#   - Instance variable self.gt7_downforce_database
#   - Loaded from YAML in __init__ (after protocol is loaded)
#   - Parsed from YAML string format to Python tuples
#   - New helper methods: _parse_range_string(), _parse_freq_add_string()
#
# USAGE CHANGES:
#   - Before: self.GT7_DOWNFORCE_DATABASE[class_name]
#   - After:  self.gt7_downforce_database[class_name]
#   (lowercase attribute name following Python conventions)
#
# YAML REFERENCE:
#   Lines 397-441: reference_tables.gt7_downforce_database.classes
#   6 car classes: formula, gr2_lmp, gr3_gt3, gr4_race, street_perf, street_std
#
# BENEFITS:
#   - YAML is source of truth (no hardcoded values)
#   - Easy to add new car classes without code changes
#   - Easy to adjust downforce ranges and impacts
#   - Proper initialization order (YAML loaded first, then database)
