# CLAUDE.md - AI Assistant Guide to ClaudeTunes

## Project Overview

**ClaudeTunes** is a Gran Turismo 7 (GT7) telemetry analysis and physics-based suspension tuning toolkit. It transforms real-time racing telemetry data into optimized vehicle setup recommendations using scientific suspension frequency analysis calibrated specifically for GT7's physics engine.

### Core Purpose
Convert GT7 telemetry data → Physics-based analysis → Optimized suspension setups that improve lap times by 1.5-4.0 seconds across multiple tuning sessions.

### Version
Current: **v8.5.3b** (complete YAML protocol alignment with all subsystems integrated)

## Modes of Operation

The YAML protocol defines **three operating modes** that determine how ClaudeTunes should be used:

### 🔧 Tool Mode
**When to use:** Running the actual ClaudeTunes setup generator

**Triggers:**
- User says: "Analyze my telemetry", "Run ClaudeTunes", "Give me setup recommendation"
- User provides telemetry + car_data files
- User explicitly requests a setup sheet

**Behavior:** Execute the full Phase A→B→C→D workflow and generate GT7 setup sheets

**Example:**
```bash
python3 claudetunes_cli.py car_data.txt telemetry.json -t high_speed
```

### 💬 Conversation Mode
**When to use:** General discussions about automotive physics, GT7 strategy, tuning concepts

**Triggers:**
- Questions about suspension theory
- GT7 gameplay tips
- Physics explanations
- Setup interpretation questions

**Behavior:** Discuss concepts without running the tool. Explain principles from the YAML protocol.

**Example Questions:**
- "Why does drivetrain bias matter for suspension frequency?"
- "How does GT7's aero model differ from real-world?"
- "What's the best tire compound for my situation?"

### 🔬 Development Mode
**When to use:** Modifying the YAML protocol itself or enhancing ClaudeTunes features

**Triggers:**
- Protocol feedback or refinement requests
- Feature enhancement discussions
- Physics methodology improvements
- Code development and debugging

**Behavior:** Help develop and refine the ClaudeTunes system, update YAML protocol, modify Python code.

**Example Activities:**
- Adding new features to the YAML protocol
- Debugging physics calculations
- Enhancing the 4-phase workflow
- Updating reference tables

## Repository Structure

```
ClaudeTunes/
├── claudetunes_cli.py          # Main setup generator (1,417 lines)
├── gt7_1r.py                   # Real-time telemetry logger (880 lines)
├── gt7_2r.py                   # Telemetry analyzer (983 lines)
├── ClaudeTunes v8.5.3b.yaml    # Physics protocol definition (455 lines)
├── sessions/                   # Generated setup sheets per session
│   └── session_YYYYMMDD_HHMMSS/
├── README.md                   # User documentation
├── ENHANCEMENTS.md             # v8.5.3b changelog
├── test_all_features.sh        # Feature testing script
├── car_data_with_ranges_MASTER.txt    # Car specification template
├── car_data_template_v2.txt           # Simplified template
├── sample_telemetry.json              # Example telemetry data
├── Corvette_Nurburgring.json          # Example analysis output
└── *.txt                       # Various car setup examples
```

### File Purposes

| File | Purpose | When to Edit |
|------|---------|--------------|
| `claudetunes_cli.py` | Setup generator with 4-phase workflow | Adding features, fixing physics calculations |
| `gt7_1r.py` | UDP telemetry capture from PS5/GT7 | Network protocol changes, new telemetry fields |
| `gt7_2r.py` | Post-race telemetry analysis | New analysis algorithms, car classification |
| `ClaudeTunes v8.5.3b.yaml` | Physics protocol & reference data | Tuning methodology changes, GT7 physics updates |
| `test_all_features.sh` | Automated testing | Adding new test cases |

## Core Architecture

### The Four-Phase Workflow

ClaudeTunes follows a strict **Phase A → B → C → D** progression defined in the YAML protocol:

```
Phase A: Telemetry Core
    ├─ Parse car data & telemetry files
    ├─ Analyze suspension travel patterns
    ├─ Diagnose balance (understeer/oversteer)
    └─ Analyze tire temperature patterns

Phase B: Physics Chain
    ├─ Base frequency from tire compound
    ├─ Apply drivetrain bias (FF/FR/MR/RR/AWD)
    ├─ Power platform control (independent of aero)
    ├─ CG height adjustments
    ├─ GT7-calibrated aero adders (~10% real-world)
    ├─ Roll center compensation
    └─ Calculate stability index

Phase C: Constraint Evaluation
    ├─ Classify severity (L1-L5: 90%→<45% achievable)
    ├─ Apply spring constraints (use max available)
    ├─ ARB compensation (+0.15 Hz per level)
    ├─ Damper compensation (+10% comp, +15% reb)
    └─ Differential compensation (+0.08 Hz per 10pts)

Phase D: Setup Sheet Output
    ├─ Generate all subsystems (damping, ARB, alignment, diff)
    ├─ Apply track-type adjustments (high_speed/technical/balanced)
    ├─ Format GT7-authentic setup sheet
    └─ Calculate performance gain estimates
```

### Data Flow

```
GT7 (PlayStation)
    ↓ UDP packets (port 33740)
gt7_1r.py (Logger)
    ↓ CSV files (per lap)
gt7_2r.py (Analyzer)
    ↓ JSON analysis report
claudetunes_cli.py + car_data.txt + YAML protocol
    ↓ Physics calculations
Setup Sheet (.txt)
    ↓ Manual entry
GT7 Tuning Menu
```

## Technology Stack

### Languages & Core Dependencies
- **Python 3.7+** - All scripts
- **pycryptodome** - Salsa20 decryption for GT7 packets
- **numpy** - Statistical analysis in gt7_2r.py
- **pyyaml** - Protocol file parsing

### GT7-Specific Technologies
- **UDP Socket Programming** - Network telemetry capture
- **Salsa20 Cipher** - GT7's proprietary encryption
- **Binary Protocol Parsing** - GT7 "Packet A" structure (296 bytes)
- **GT7 Physics Model** - Calibrated aero effectiveness (~10% real-world)

### Installation
```bash
pip install pycryptodome numpy pyyaml
```

## Key Coding Conventions

### Python Style
1. **Docstrings** - Every class and major method has descriptive docstrings
2. **Type Comments** - Inline comments document units and data types
3. **Snake_case** - All functions and variables (e.g., `calculate_base_frequency`)
4. **PascalCase** - Class names only (e.g., `ClaudeTunesCLI`)
5. **UPPERCASE** - Constants and reference tables (e.g., `GT7_DOWNFORCE_DATABASE`)

### Code Organization Patterns

#### ClaudeTunes CLI Structure
```python
class ClaudeTunesCLI:
    # Class-level constants (reference tables)
    GT7_DOWNFORCE_DATABASE = {...}
    DIFFERENTIAL_BASELINES = {...}

    def __init__(self, protocol_path, track_type):
        """Load YAML protocol and initialize"""

    def run(self, car_data_path, telemetry_path, output_path, session_folder):
        """Main workflow: A → B → C → D"""

    # Phase methods
    def phase_a_intake(self, car_data_path, telemetry_path):
    def phase_b_physics_chain(self):
    def phase_c_constraints(self):
    def phase_d_output(self):

    # Helper methods (alphabetical)
    def _calculate_xxx(self):
    def _parse_xxx(self):
```

#### File Parsing Pattern
```python
def parse_car_data(self, path):
    """Parse car_data.txt with section-based parsing"""
    current_section = None
    for line in file:
        line = line.strip()
        if line in SECTION_HEADERS:
            current_section = line
        elif current_section == "POWER OUTPUT AND WEIGHT":
            # Parse using regex patterns
            match = re.search(pattern, line)
```

#### Error Handling Pattern
```python
try:
    value = parse_function(input)
except (ValueError, KeyError) as e:
    print(f"Warning: {field} parsing failed: {e}")
    value = default_value
```

### Naming Conventions

| Pattern | Example | Usage |
|---------|---------|-------|
| `phase_x_name` | `phase_a_intake()` | Workflow phase methods |
| `_helper_name` | `_calculate_damping()` | Internal helper functions |
| `calculate_noun` | `calculate_stability_index()` | Physics calculations |
| `parse_noun` | `parse_car_data()` | File parsing functions |
| `apply_noun` | `apply_track_adjustments()` | Modification functions |
| `NOUN_DATABASE` | `GT7_DOWNFORCE_DATABASE` | Reference data constants |

### Comment Style
```python
# Phase B: Power Platform Control (YAML lines 102-109)
# Independent of aero - for torque delivery platform stability
power_add = self.protocol['phase_B']['power_platform_control']

# Calculate using sqrt formula
freq_multiplier = math.sqrt(horsepower / 400)  # Units: Hz multiplier
```

## YAML Protocol System

### Protocol Structure
The `ClaudeTunes v8.5.3b.yaml` file is the **single source of truth** for all physics calculations.

#### Key Sections
```yaml
claudetunes:
  version: "8.5.3a-lite-hybrid"
  purpose:              # Protocol purpose and scope
  modes:                # Tool/Conversation/Development mode triggers
  gt7_physics_model:    # What to trust vs calibrate
  workflow:             # Phase definitions

phase_A:                # Telemetry analysis rules
  file_intake:
  suspension_analysis:
  balance_diagnosis:
  tire_patterns:

phase_B:                # Physics chain calculations
  base_frequency_by_compound:  # 9 tire compounds
  drivetrain_bias:             # FF/FR/MR/RR/AWD rules
  power_platform_control:
  aero_adders_gt7:            # GT7-calibrated (~10% real)
  cg_adjustments:
  roll_center_compensation:

phase_C:                # Constraint handling
  severity_levels:      # L1-L5 classification
  compensation:         # ARB/damper/diff recovery

tuning_subsystems:      # Phase D calculations
  damping:
  arb:
  alignment:
  differential:
  ride_height:

safety_constraints:     # Critical rules (rake, stability, compliance)
quality_gates:          # Format/physics/technical validation
phase_D:               # Output formatting and iteration rules

reference_tables:       # Quick lookup data
  gt7_downforce_database:
  differential_baselines:
  performance_expectations:

version_context:        # v8.5.3a changes and rationale
```

### YAML Usage in Code
```python
# Always reference YAML sections with comments
base_freq = self.protocol['phase_B']['base_frequency_by_compound']
tire_data = base_freq[tire_compound]  # e.g., 'Racing_Hard'
hz = tire_data['hz']  # 2.85 Hz for Racing Hard
```

### Protocol Philosophy
- **Trust Real-World Physics**: Suspension frequency, weight transfer, CG dynamics
- **GT7-Calibrate**: Aero effectiveness, platform effects, sensitivity
- **Reverse-Engineer**: Spring rate ↔ frequency, damper % ↔ force curves

## Quality Gates and Safety Constraints

The YAML protocol defines strict **quality gates** that every generated setup must pass. These are non-negotiable validation rules.

### Format Quality Gates (YAML: quality_gates.format)
Every setup output must:
- ✅ Use markdown code block formatting
- ✅ Use GT7 terminology and exact menu structure
- ✅ Right-align all numeric values
- ✅ Place tire section at top
- ✅ Include physics summary at bottom
- ✅ Use ▼ for toe out, ▲ for toe in
- ✅ Never rename GT7 menu items

### Physics Quality Gates (YAML: quality_gates.physics)
Every setup must satisfy:
- ✅ **No unjustified negative rake** (front > rear is invalid)
- ✅ **Correct drivetrain bias applied** (FF/FR/MR/RR/AWD-specific)
- ✅ **CG effects applied** where applicable
- ✅ **All values within car_data ranges** (spring/damper/ARB limits)
- ✅ **Aero frequency ≤ 0.5 Hz** (GT7 calibration limit)
- ✅ **Stability index in safe band** (-0.90 to -0.40)

### Technical Quality Gates (YAML: quality_gates.technical)
All calculations must meet:
- ✅ **Accurate frequency calculations** per tire compound
- ✅ **Damping ratios 0.50-0.85** (compression:rebound)
- ✅ **ARB consistent with frequency philosophy**
- ✅ **Differential matches drivetrain type**
- ✅ **Power platform separated from aero** (independent calculations)

### Safety Constraints (YAML: safety_constraints)

**Critical Rules - NEVER VIOLATE:**

```python
# Rake Rule (YAML line 259)
RAKE_RULE = "Front ≤ Rear (positive rake always)"

# Stability Range (YAML line 260)
STABILITY_SAFE = (-0.90, -0.40)  # Front-biased safe window

# Danger Flags (YAML lines 261-263)
DANGER_FLAGS = {
    'oversteer': 'stability > 0.00',      # Snap oversteer risk
    'extreme_understeer': 'stability < -1.00'  # Unmanageable push
}

# Compliance (YAML line 264)
RANGE_COMPLIANCE = "All values within car_data ranges"

# Telemetry Match (YAML line 265)
VALIDATION = "Setup must match observed balance + temps"
```

**What happens when violated:**
- **Negative rake**: GT7 handling instability, potential setup rejection
- **Stability out of range**: 2-5 second lap time penalty
- **Values out of range**: GT7 menu won't accept the values
- **Wrong drivetrain bias**: Proven 2-5s per lap penalty in testing

## Version Context

Understanding what changed between versions helps maintain consistency and avoid regressions.

### v8.5.3a Changes (YAML: version_context.v8_5_3a_changes)

The protocol documents these major changes from earlier versions:

1. **Aero Frequency Reduction** (75% decrease)
   - **Before:** +0.8-1.5 Hz aero adders
   - **After:** +0.2-0.5 Hz max
   - **Reason:** GT7 aero is ~10% real-world effectiveness

2. **Power Platform Control Separated**
   - **Before:** Power effects combined with aero
   - **After:** Independent high-power adders (Phase B.power_platform_control)
   - **Reason:** Torque delivery platform ≠ aerodynamic platform

3. **GT7 Downforce Database Added**
   - **New:** Complete reference by car class (Formula, GR2, GR3, GR4, Street)
   - **Purpose:** Quick lookup for DF levels and expected GT7 impact

4. **Ride Height Priority Reordered**
   - **Before:** Equal weighting of physics/mechanical/aero
   - **After:** CG/geometry 80%, mechanical 15%, aero 5%
   - **Reason:** Geometric benefits >> aero in GT7

5. **Aero Balance Simplified**
   - **Before:** Complex aero balance calculations
   - **After:** Use ~40% front convention, minor adjustments only
   - **Reason:** Minimal GT7 aero impact means less tuning needed

### Rationale (YAML line 452)
> "GT7 aero deliberately nerfed (~10% real-world effectiveness). Occam's validation: 1300 lbs DF = 0.115s vs 3-5s real-world."

### Philosophy (YAML line 453)
> "Mechanical grip optimization >> Aerodynamic tuning in GT7"

### When Developing
- **Always check version_context** before modifying aero-related code
- **Preserve the 10% calibration** (don't revert to real-world values)
- **Keep power platform independent** from aero calculations
- **Prioritize mechanical grip** over aero in all decisions

## Common Development Tasks

### Adding a New Feature

1. **Update YAML Protocol First**
   ```yaml
   # Add to appropriate phase section
   phase_B:
     new_feature:
       description: "What it does"
       formula: "Mathematical definition"
       adjustments: {...}
   ```

2. **Implement in Python**
   ```python
   def phase_b_physics_chain(self):
       # ... existing code ...

       # New feature (YAML lines XXX-YYY)
       new_param = self.protocol['phase_B']['new_feature']
       result = self._calculate_new_feature(new_param)
       self.results['new_feature'] = result
   ```

3. **Update Documentation**
   - Add to README.md "Features" section
   - Update ENHANCEMENTS.md with rationale
   - Update this CLAUDE.md if it changes workflow

4. **Add Test Case**
   ```bash
   # In test_all_features.sh
   echo "TEST N: New Feature"
   python3 claudetunes_cli.py ... | grep -E "(NewFeature)"
   ```

### Modifying Physics Calculations

**IMPORTANT**: All physics changes must maintain these safety constraints:

```python
# Safety Constraints (YAML: safety_constraints)
RAKE_RULE = "Front ≤ Rear (positive rake always)"
STABILITY_RANGE = (-0.90, -0.40)  # Safe window
DANGER_FLAGS = {
    'oversteer': lambda s: s > 0.00,
    'extreme_understeer': lambda s: s < -1.00
}

# Stability Index Formula (never change this)
stability_index = (freq_rear - freq_front) / freq_front
```

### Adding Support for New Car Classes

1. **Update gt7_2r.py car classification**:
   ```python
   CAR_THRESHOLDS = {
       'new_class': {
           'braking_threshold': XX,
           'cornering_speed_min': XX,
           'acceleration_threshold': XX,
           'high_speed_threshold': XX,
           'slip_traction_loss': X.XX,
           'description': 'Description'
       }
   }
   ```

2. **Update YAML differential baselines** if needed
3. **Test with telemetry from that car class**

### Fixing Bugs

1. **Identify Phase** - Which phase (A/B/C/D) has the issue?
2. **Check YAML Alignment** - Does code match protocol?
3. **Verify Units** - Are all values in correct units (Hz, mm, degrees, %)?
4. **Test with Sample Data**:
   ```bash
   python3 claudetunes_cli.py \
       car_data_with_ranges_MASTER.txt \
       sample_telemetry.json \
       -o test_output.txt
   ```

## Important GT7-Specific Rules

### GT7 Physics Quirks (NEVER VIOLATE)

1. **Aero Effectiveness**: GT7 aero is ~10% of real-world
   ```python
   # Aero frequency adders (YAML phase_B.aero_adders_gt7)
   MAX_AERO_ADD = 0.5  # Hz maximum (was 1.5 Hz before calibration)
   REAL_WORLD_FACTOR = 0.10  # GT7 aero is 10% effective
   ```

2. **Rake Rule**: Always maintain positive rake
   ```python
   # Front ride height must be ≤ Rear ride height
   if front_height > rear_height:
       # INVALID - will cause issues in GT7
       raise ValueError("Negative rake detected")
   ```

3. **Stability Index Safe Range**
   ```python
   # (F_rear - F_front) / F_front
   SAFE_MIN = -0.90  # Below = extreme understeer
   SAFE_MAX = -0.40  # Above = oversteer tendency
   DANGER = 0.00     # Positive = snap oversteer
   ```

4. **Frequency Range Validation**
   ```python
   # Every car has specific spring ranges
   if target_freq < min_achievable or target_freq > max_achievable:
       # Trigger Phase C compensation
       apply_arb_compensation()
       apply_damper_compensation()
       apply_diff_compensation()
   ```

### Drivetrain-Specific Biases (NEVER MIX)

```python
# YAML: phase_B.drivetrain_bias
DRIVETRAIN_BIAS = {
    'FF': '+0.4 Hz front',   # Front-heavy for torque steer
    'FR': '+0.3 Hz front',   # Slight front bias
    'MR': '+0.1 Hz rear',    # Slight rear bias (balanced)
    'RR': '+0.8 Hz rear',    # Heavy rear bias (911-style)
    'AWD': 'Follow engine orientation'
}
```

**Wrong bias = 2-5 second penalty per lap** (proven in testing)

### Track Type Adjustments

```python
# YAML: tuning_subsystems adjustments
TRACK_TYPES = {
    'high_speed': {  # Monza, Le Mans
        'philosophy': 'Stability over rotation',
        'arb': '+1 both',
        'damping': '+3%',
        'camber': '+0.3°',
        'diff_accel': '+12'
    },
    'technical': {  # Monaco, Suzuka
        'philosophy': 'Rotation over stability',
        'arb': '-1 rear',
        'damping': '-2%',
        'camber': '-0.2°',
        'diff_accel': '-7',
        'diff_brake': '+7'
    },
    'balanced': {  # Default
        'philosophy': 'Mixed circuits',
        'adjustments': 'baseline'
    }
}
```

## Testing Strategy

### Manual Testing
```bash
# Basic test
python3 claudetunes_cli.py \
    car_data_with_ranges_MASTER.txt \
    sample_telemetry.json

# Track type test
python3 claudetunes_cli.py \
    car_data_with_ranges_MASTER.txt \
    sample_telemetry.json \
    -t high_speed -o test.txt

# Session folder test
python3 claudetunes_cli.py \
    car_data.txt telemetry.json \
    -s sessions/my_session --auto-session
```

### Automated Testing
```bash
./test_all_features.sh
```

This script tests:
- Balanced setup generation
- High-speed track optimization
- Technical track optimization
- Parameter comparison across track types
- Verification of expected differences

### Expected Output Validation

Every setup must include:
```
✓ Phase A: Parsed car data and telemetry
✓ Phase B: Calculated target frequencies
✓ Phase C: Applied constraints (if any)
✓ Phase D: Generated GT7-formatted sheet

PHYSICS: [Philosophy] | Stability: -0.XX | Gain: X.X-X.Xs
```

## Development Workflow

### Before Making Changes
1. Read the YAML protocol section you're modifying
2. Check if similar functionality exists elsewhere
3. Review ENHANCEMENTS.md for recent changes
4. Understand which phase (A/B/C/D) you're working in

### While Coding
1. Add YAML reference comments: `# YAML: phase_X.section_name`
2. Document units inline: `# Units: Hz`, `# Units: mm`
3. Preserve existing formatting patterns
4. Follow the established naming conventions

### After Changes
1. Test with sample data
2. Run `test_all_features.sh`
3. Verify output format matches GT7 menu structure
4. Check stability index is in safe range
5. Update documentation if user-facing

### Git Commit Messages
Follow this pattern:
```
Area: Brief description

- Detailed change 1
- Detailed change 2

YAML Reference: phase_X.section
Tested: description of tests run
```

Example:
```
Phase B: Add CG height adjustments

- Implement frequency adjustments for high/standard/low CG
- Add CG effects on damping, camber, toe
- Integrate with existing power platform control

YAML Reference: phase_B.cg_adjustments (lines 127-132)
Tested: LaFerrari with 420mm CG, verified +0.0 Hz (standard range)
```

## Session Management

### Session Folder Structure
```
sessions/
└── session_20251113_151156/
    ├── 2001_Corvette_Z06_setup.txt
    ├── 2001_Corvette_Z06_high_speed_setup.txt
    └── 2001_Corvette_Z06_technical_setup.txt
```

### Auto-Session Mode
```bash
# Creates timestamped session folder automatically
python3 claudetunes_cli.py car_data.txt telemetry.json --auto-session

# Use existing session folder
python3 claudetunes_cli.py car_data.txt telemetry.json -s sessions/my_session
```

## Performance Expectations

### Expected Gains (YAML: reference_tables.performance_expectations)
- **Frequency Corrections**: 0.3-2.0s per lap
- **Drivetrain Architecture Fixes**: 2.0-5.0s (when bias was wrong)
- **Ride Height Optimization**: 0.3-0.8s (CG/geometry benefits)
- **CG Improvement**: 5-8% per 25mm reduction
- **Track-Type Optimization**: 0.2-0.5s track-specific

### Three-Session Convergence (YAML: iteration)

The YAML protocol defines a systematic iteration workflow:

**Workflow (YAML line 340):**
```
v1.0 → v2.0: Adjust highest-impact constrained parameter
Stop when: <0.1s gain OR stability confirmed in safe band
```

**Versioning Rule (YAML line 342):**
- Generate NEW complete setup sheet with version incremented
- Never modify existing setup sheets (preserve v1.0 as baseline)

**Expected Pattern (YAML lines 344-347):**
1. **Session 1 (Physics Baseline 80-90%)**: 1.0-3.0s improvement
2. **Session 2 (Driver Refinement 95-98%)**: 0.2-0.8s additional
3. **Session 3 (System Optimization 99%+)**: 0.1-0.3s additional
4. **Total**: 1.5-4.0s across all sessions

**When to Stop:**
- Gain drops below 0.1s per iteration
- Stability index confirmed in safe band (-0.90 to -0.40)
- Driver reports setup feels balanced and predictable

## Troubleshooting Guide

### "Protocol file not found"
```bash
# Ensure YAML file is in same directory or specify path
python3 claudetunes_cli.py car_data.txt telemetry.json \
    --protocol "path/to/ClaudeTunes v8.5.3b.yaml"
```

### "Error parsing car data"
- Check file format matches `car_data_with_ranges_MASTER.txt`
- Verify all required sections present
- Ensure range formatting: `(range: front: X-Y rear: A-B)`

### "Stability index out of safe range"
- Review drivetrain bias (might be inverted)
- Check if frequency targets are achievable
- Verify aero adder not too high (max 0.5 Hz)

### "Setup doesn't improve lap times"
1. Verify correct drivetrain selected (FF/FR/MR/RR/AWD)
2. Check track type matches circuit (high_speed/technical/balanced)
3. Confirm telemetry data is from representative laps
4. Validate CG height is accurate

## AI Assistant Best Practices

### When Analyzing Code
1. Always check YAML protocol alignment first
2. Trace through phase workflow (A→B→C→D)
3. Verify units in calculations
4. Check safety constraints are preserved
5. Look for existing patterns before creating new ones

### When Suggesting Changes
1. Quote relevant YAML sections
2. Show before/after code with line references
3. Explain GT7 physics implications
4. Provide testing commands
5. Update documentation if needed

### When Debugging Issues
1. Identify which phase has the problem
2. Check input data format (car_data.txt, telemetry.json)
3. Verify intermediate calculations
4. Test with known-good sample data
5. Compare against YAML protocol expected behavior

### Code Review Checklist

**Quality Gates (YAML: quality_gates):**
- [ ] Format: Markdown blocks, GT7 terminology, right-aligned values
- [ ] Physics: Rake rule, drivetrain bias, CG effects, stability in safe band
- [ ] Technical: Frequency accuracy, damping ratios, power/aero separation

**Safety Constraints (YAML: safety_constraints):**
- [ ] Rake rule enforced (Front ≤ Rear)
- [ ] Stability index in safe range (-0.90 to -0.40)
- [ ] No danger flags triggered (oversteer/extreme understeer)
- [ ] All values within car_data ranges

**Code Quality:**
- [ ] YAML protocol alignment maintained
- [ ] Units documented in comments (Hz, mm, degrees, %)
- [ ] Existing naming conventions followed
- [ ] Phase A/B/C/D separation preserved
- [ ] YAML line references in comments
- [ ] GT7-specific quirks respected (10% aero, etc.)

**Testing & Documentation:**
- [ ] Test cases updated if needed
- [ ] Documentation updated if user-facing
- [ ] Version context respected (no aero regression)

## Quick Reference

### File Locations
- Protocol: `ClaudeTunes v8.5.3b.yaml`
- Main CLI: `claudetunes_cli.py`
- Logger: `gt7_1r.py`
- Analyzer: `gt7_2r.py`
- Templates: `car_data_with_ranges_MASTER.txt`, `car_data_template_v2.txt`
- Sample Data: `sample_telemetry.json`, `Corvette_Nurburgring.json`

### Command Examples
```bash
# Basic setup
python3 claudetunes_cli.py car_data.txt telemetry.json

# Track-optimized
python3 claudetunes_cli.py car_data.txt telemetry.json -t high_speed -o setup.txt

# Session management
python3 claudetunes_cli.py car_data.txt telemetry.json --auto-session

# Custom protocol
python3 claudetunes_cli.py car_data.txt telemetry.json -p custom.yaml
```

### Key Formulas

**Stability Index**:
```
SI = (F_rear - F_front) / F_front
Safe: -0.90 to -0.40 (front-biased)
```

**Power Platform Add**:
```
add = base_freq × sqrt(HP / 400)
```

**ARB Compensation**:
```
ARB = Normal + (FreqDeficit × 2.5)
Max: +3 levels, Recovery: 0.15 Hz per level
```

**CG Weight Transfer**:
```
ΔW = (Mass × lateral_accel × CG_height) / track_width
```

---

**Version**: v8.5.3b
**Last Updated**: 2025-11-13
**Protocol Coverage**: 100% (All phases A/B/C/D implemented)
**YAML Alignment**: Complete (modes, quality_gates, version_context documented)

## Related Documentation

- **User Guide**: [README.md](README.md) - End-user documentation
- **Changelog**: [ENHANCEMENTS.md](ENHANCEMENTS.md) - v8.5.3b feature additions
- **Physics Protocol**: [ClaudeTunes v8.5.3b.yaml](ClaudeTunes%20v8.5.3b.yaml) - Complete methodology reference
- **This Guide**: CLAUDE.md - AI assistant development guide

## Documentation Hierarchy

```
README.md           → User-facing: How to use ClaudeTunes
ENHANCEMENTS.md     → User-facing: What's new in v8.5.3b
CLAUDE.md (this)    → Developer-facing: How to develop ClaudeTunes
YAML Protocol       → Reference: Single source of truth for all calculations
```
