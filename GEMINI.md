# ClaudeTunes - GT7 Telemetry & Tuning Toolkit

**ClaudeTunes** is a Gran Turismo 7 (GT7) telemetry analysis and physics-based suspension tuning toolkit. It uses a rigorous scientific approach, defined by a "YAML Protocol," to convert real-time racing data into optimized vehicle setups.

## Project Overview

*   **Core Purpose:** Transform GT7 telemetry into setups that improve lap times by 1.5-4.0 seconds.
*   **Philosophy:** Physics-based tuning calibrated specifically for GT7's unique engine quirks (e.g., aero is only ~10% effective compared to real life).
*   **Architecture:**
    *   **Logger (`gt7_1r.py`):** Captures live UDP telemetry from the console.
    *   **Analyzer (`gt7_2r.py`):** Post-processing analysis of race sessions.
    *   **Generator (`claudetunes_cli.py`):** The main engine that calculates setups based on the YAML protocol.
    *   **Protocol (`ClaudeTunes v8.5.3b.yaml`):** The single source of truth for all physics calculations and constants.

### The 4-Phase Workflow
The system follows a strict pipeline defined in the YAML protocol:
1.  **Phase A (Intake):** Parse telemetry, analyze suspension travel and tire temps.
2.  **Phase B (Physics):** Calculate natural frequencies, apply drivetrain bias (FF/FR/MR/RR/AWD), and compute stability index.
3.  **Phase C (Constraints):** Evaluate achievability within car limits and apply compensations (ARB, dampers, diff) if needed.
4.  **Phase D (Output):** Format the final GT7 setup sheet and estimate performance gains.

## Building and Running

### Prerequisites
*   Python 3.7+
*   Dependencies: `pip install pycryptodome numpy pyyaml`

### Key Commands

**1. Telemetry Capture (Live)**
Connects to PS5/PS4 on port 33740.
```bash
python3 gt7_1r.py
```

**2. Session Analysis (Post-Race)**
Analyzes a folder of captured telemetry CSVs.
```bash
python3 gt7_2r.py /path/to/session/folder
```

**3. Generate Setup (The Core Tool)**
Generates a tuning sheet. Requires a car data file (specs) and optional telemetry.
```bash
# Standard balanced setup
python3 claudetunes_cli.py templates/car_data_with_ranges_MASTER.txt templates/sample_telemetry.json

# Optimize for High Speed tracks (e.g., Monza)
python3 claudetunes_cli.py car_data.txt telemetry.json -t high_speed

# Optimize for Technical tracks (e.g., Monaco)
python3 claudetunes_cli.py car_data.txt telemetry.json -t technical

# Save to file
python3 claudetunes_cli.py car_data.txt telemetry.json -o setup.txt
```

**4. Running Tests**
Validates the CLI against different track types and ensures consistent output.
```bash
./test_all_features.sh
```

## Development Conventions

### The YAML Protocol is Law
*   **File:** `ClaudeTunes v8.5.3b.yaml`
*   **Rule:** All physics constants, formulas, and tuning logic **must** originate from this file. Do not hardcode physics values in Python files.
*   **Modifying:** If you change a physics calculation, update the YAML first, then the Python code to reference it.

### Critical Safety Constraints (NEVER VIOLATE)
1.  **Rake Rule:** Front ride height must always be ≤ Rear ride height (Positive Rake). Negative rake causes instability in GT7.
2.  **Stability Index:** Must be between **-0.90** and **-0.40**.
    *   `> 0.00`: Dangerous Snap Oversteer.
    *   `< -1.00`: Extreme Understeer.
3.  **Drivetrain Bias:** strict frequency biases per type (e.g., FF is front-heavy, RR is rear-heavy). Mixing these up results in massive performance penalties.

### GT7 Physics Quirks
*   **Aero:** Effectiveness is calibrated to ~10% of real-world values. Max frequency adder is restricted to 0.5 Hz.
*   **Power Platform:** Calculated independently of aero.
*   **Ride Height:** Geometric benefits (CG reduction) vastly outweigh aerodynamic benefits in this game engine.

### Interaction Modes
*   **Tool Mode:** Running the scripts to generate output.
*   **Conversation Mode:** Discussing tuning theory using the YAML protocol as a knowledge base.
*   **Development Mode:** Modifying the codebase or protocol.

### File Map
*   `claudetunes_cli.py`: Main logic (edit this for feature changes).
*   `ClaudeTunes v8.5.3b.yaml`: Physics definition (edit this for tuning methodology changes).
*   `templates/`: Contains standard input formats for car data.
*   `docs/`: Extensive documentation on philosophy and specific features.
