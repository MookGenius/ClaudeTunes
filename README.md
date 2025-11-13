# ClaudeTunes GT7 Telemetry & Tuning System

A comprehensive Gran Turismo 7 telemetry analysis and physics-based suspension tuning toolkit.

## Components

### 1. **gt7_1r.py** - Real-Time Telemetry Logger
Captures live telemetry data from Gran Turismo 7 via UDP network connection.

**Features:**
- Connects to PlayStation console over network (port 33740)
- Decrypts GT7's proprietary Salsa20-encrypted telemetry packets
- Records 100+ data points per frame (vehicle dynamics, tires, suspension, engine metrics)
- Saves data to CSV files (one per lap)
- Real-time terminal display of key metrics
- Comprehensive car database (220+ GT7 vehicles)

**Usage:**
```bash
python3 gt7_1r.py
```

### 2. **gt7_2r.py** - Telemetry Analyzer
Post-race analysis of captured telemetry data.

**Features:**
- Auto-classifies car type (kart, formula, race car, rally, drift, street, prototype)
- Analyzes lap consistency, tire degradation, suspension behavior, slip patterns
- Generates setup recommendations based on data
- Outputs detailed JSON analysis reports

**Usage:**
```bash
python3 gt7_2r.py /path/to/session/folder
```

### 3. **claudetunes_cli.py** - Physics-Based Setup Generator (v8.5.3b Enhanced)
Generates optimized GT7 suspension setups from telemetry data and car specifications following the ClaudeTunes protocol.

**Features:**
- Physics-based natural frequency approach to suspension tuning
- Calibrated specifically for GT7's physics engine quirks
- Drivetrain-specific frequency biases (FF, FR, MR, RR, AWD)
- **NEW:** CG height optimization with frequency adjustments
- **NEW:** Track-type optimization (high-speed/technical/balanced)
- **NEW:** Roll center compensation calculations
- **NEW:** Differential compensation for frequency deficits
- **NEW:** Bottoming detection integration
- Power platform control and aero adjustment
- Multi-layer constraint compensation system (ARB, dampers, diff)
- Generates GT7-formatted setup sheets ready to copy into game

**Track Types:**
- `high_speed` - Optimized for Monza, Le Mans (stiffer, stable)
- `technical` - Optimized for Monaco, Suzuka (softer, rotational)
- `balanced` - Default for mixed circuits

**Usage:**
```bash
# Basic usage (balanced setup)
python3 claudetunes_cli.py car_data.txt telemetry.json

# High-speed track optimization (Monza, Le Mans)
python3 claudetunes_cli.py car_data.txt telemetry.json -t high_speed

# Technical track optimization (Monaco, Suzuka)
python3 claudetunes_cli.py car_data.txt telemetry.json -t technical

# Save output to file
python3 claudetunes_cli.py car_data.txt telemetry.json -o setup_sheet.txt

# Use custom protocol file
python3 claudetunes_cli.py car_data.txt telemetry.json --protocol custom_protocol.yaml

# Show help
python3 claudetunes_cli.py --help
```

## Installation

### Requirements
- Python 3.7+
- Required packages:
  ```bash
  pip install pycryptodome numpy pyyaml
  ```

### Network Setup (for telemetry capture)
1. Connect your PlayStation and computer to the same network
2. Note your computer's IP address
3. Configure GT7 to send telemetry to your computer's IP on port 33740

## Workflow

### Complete Analysis & Tuning Workflow

1. **Capture Telemetry** (gt7_1r.py)
   ```bash
   python3 gt7_1r.py
   # Drive laps in GT7
   # Data automatically saved to CSV files
   ```

2. **Analyze Performance** (gt7_2r.py)
   ```bash
   python3 gt7_2r.py ./session_folder
   # Generates comprehensive analysis JSON
   ```

3. **Generate Optimized Setup** (claudetunes_cli.py)
   ```bash
   python3 claudetunes_cli.py car_data.txt telemetry_analysis.json -o my_setup.txt
   # Creates GT7 setup sheet with physics-based recommendations
   ```

4. **Apply in GT7**
   - Copy setup values from generated sheet
   - Apply in GT7's tuning menu
   - Test and iterate

## File Formats

### Car Data File Format
```
CAR NAME
2013 Ferrari LaFerrari

DRIVETRAIN
MR

POWER OUTPUT AND WEIGHT
1043 hp 543 ft-lbs 2767 lbs weight, 41:59 f:r balance

TIRE COMPOUND
Racing Hard Tires

CENTER OF GRAVITY HEIGHT
420 mm

SUSPENSION SETUP Front/Rear
BODY HEIGHT ADJUSTMENT
xx/xx mm
(range: front: 85-140mm rear: 110-165mm)

ARB
x/x (range: 1-10)

NATURAL FREQUENCY x.xx hz/x.xx hz
(range: front: 2.50-3.40 hz rear: 2.60-3.50 hz)

...
```
See [car_data_with_ranges_MASTER.txt](car_data_with_ranges_MASTER.txt) for complete template.

### Telemetry JSON Format
```json
{
  "suspension_travel": {
    "FL": [0.32, 0.35, ...],
    "FR": [0.31, 0.34, ...],
    "RL": [0.28, 0.30, ...],
    "RR": [0.27, 0.29, ...]
  },
  "balance": {
    "understeer_gradient": 1.8,
    "classification": "Neutral"
  },
  "tire_temps": {
    "FL_I": 85.2, "FL_M": 87.5, "FL_O": 89.8,
    ...
  },
  "bottoming_detected": false
}
```
See [sample_telemetry.json](sample_telemetry.json) for complete example.

## ClaudeTunes Protocol

The ClaudeTunes protocol ([ClaudeTunes v8.5.3b.yaml](ClaudeTunes%20v8.5.3b.yaml)) implements a physics-based approach to suspension tuning:

### Four-Phase Workflow

**Phase A: Telemetry Core**
- Parse car data and telemetry
- Analyze suspension travel patterns
- Diagnose balance (understeer/oversteer)
- Analyze tire temperature patterns

**Phase B: Physics Chain**
- Calculate base frequency from tire compound
- Apply drivetrain-specific bias
- Add power platform control
- Apply GT7-calibrated aero adjustments
- Calculate stability index

**Phase C: Constraint Evaluation**
- Check achievability within car's ranges
- Classify severity level (L1-L5)
- Apply ARB/damper/diff compensation
- Recover performance where springs limited

**Phase D: Setup Sheet Output**
- Generate complete GT7-formatted setup
- Calculate all subsystems (damping, ARB, alignment, diff, aero)
- Apply safety constraints (rake rule, stability range)
- Format for direct copy into GT7

### Key Concepts

**Natural Frequency Approach**
- Each tire compound has optimal suspension frequency
- Drivetrain layout determines front/rear frequency bias
- Power platform control independent of aero
- GT7 aero effectiveness ~10% of real-world

**Drivetrain Biases**
- FF: Front-biased (+0.4Hz front)
- FR: Slight front bias (+0.3Hz front)
- MR: Slight rear bias (+0.1Hz rear)
- RR: Heavy rear bias (+0.8Hz rear)
- AWD: Balanced approach

**Stability Index**
- Formula: `(F_rear - F_front) / F_front`
- Safe range: -0.40 to -0.90 (front-biased)
- Positive values indicate oversteer tendency
- Below -1.00 indicates extreme understeer

## Expected Performance Gains

Based on ClaudeTunes methodology:

- **Session 1 (Physics Baseline):** 1.0-3.0s improvement
- **Session 2 (Driver Refinement):** 0.2-0.8s additional
- **Session 3 (System Optimization):** 0.1-0.3s additional
- **Total:** 1.5-4.0s across 3 sessions

Specific improvements:
- Frequency corrections: 0.3-2.0s
- Drivetrain architecture fixes: 2.0-5.0s (when bias wrong)
- Ride height optimization: 0.3-0.8s
- CG improvement: 5-8% per 25mm reduction

## Examples

### Example 1: LaFerrari Setup
```bash
# Generate setup for Ferrari LaFerrari at Spa
python3 claudetunes_cli.py car_data_with_ranges_MASTER.txt sample_telemetry.json

# Output shows:
# - Base frequency: 2.85 Hz (Racing Hard)
# - MR drivetrain bias: +0.1 Hz rear
# - Power platform: +0.61 Hz (1043 HP)
# - Target: F=3.61 Hz, R=3.71 Hz
# - Stability: 0.03 (slight oversteer tendency)
# - Complete setup sheet ready for GT7
```

### Example 2: Analyzing Telemetry Session
```bash
# After running gt7_1r.py during race session
python3 gt7_2r.py ./spa_session_20250113

# Generates analysis showing:
# - Lap consistency score
# - Tire degradation patterns
# - Suspension behavior
# - Balance characteristics
# - Setup recommendations
```

## Troubleshooting

### ClaudeTunes CLI Issues

**"Protocol file not found"**
- Ensure `ClaudeTunes v8.5.3b.yaml` is in the same directory
- Or specify path with `-p` flag

**"Error parsing car data"**
- Check car data file format matches template
- Ensure all required sections are present
- Verify range formatting: `(range: front: X-Y rear: A-B)`

**"No telemetry data"**
- Telemetry JSON optional for basic setup generation
- CLI will use defaults and skip telemetry-based adjustments
- For full analysis, provide JSON from gt7_2r.py

### Telemetry Capture Issues

**No data received**
- Verify PlayStation and computer on same network
- Check firewall allows UDP on port 33740
- Confirm GT7 telemetry enabled in game settings

**Decryption errors**
- Update pycryptodome: `pip install --upgrade pycryptodome`
- Verify GT7 is running and on track (not in menus)

## Technical Details

### Technologies Used
- **Python 3** with pycryptodome, numpy, pyyaml
- **UDP socket programming** for GT7 network communication
- **Salsa20 decryption** for GT7 packet protocol
- **Binary protocol parsing** (GT7 Packet A structure)
- **Statistical analysis** with coefficient of variation
- **YAML-based protocol definition**

### GT7 Physics Calibration
- Aero effectiveness: ~10% of real-world
- Minimal aero platform effect
- Reduced aero sensitivity to ride height
- Spring rate → frequency reverse engineering
- Damper % → force curves mapping

## Version History

**v8.5.3a-lite-hybrid** (Current)
- Aero frequency adders reduced 75% (GT7 calibration)
- Power platform control separated from aero
- GT7 Downforce Database added
- Ride height priority reordered (CG/geometry focus)
- Improved constraint compensation system

## Contributing

This toolkit is designed for competitive GT7 racers, esports teams, and sim racing enthusiasts seeking data-driven performance optimization.

## License

Educational and personal use.

---

**For support or questions:**
- Check [ClaudeTunes v8.5.3b.yaml](ClaudeTunes%20v8.5.3b.yaml) for protocol details
- Review sample files: [car_data_with_ranges_MASTER.txt](car_data_with_ranges_MASTER.txt), [sample_telemetry.json](sample_telemetry.json)
- Examine generated setup sheets for physics methodology
