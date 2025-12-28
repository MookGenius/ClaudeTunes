# The Agentic Race Engineer: A Sim-to-MoTeC-to-AI Pipeline

## The Concept
Traditionally, sim racing telemetry falls into two buckets:
1.  **Raw Logging:** Tools like `sim-to-motec` that dump data into complex software, requiring a human expert to interpret "squiggly lines."
2.  **Generic Advice:** AI or calculators that give broad tuning tips ("soften rear for grip") without knowing what the car is actually doing physically.

**The "Agentic Race Engineer" Pipeline** bridges this gap. It combines **hard telemetry data** with **physics-based logic (ClaudeTunes YAML)** and **LLM reasoning** to automate the loop of *Analysis -> Diagnosis -> Solution*.

---

## The Architecture

### Layer 1: Data Acquisition (The Dual Stream)
**Goal:** Capture high-fidelity raw data for both Human and Machine analysis.
*   **Stream A (Human):** `sim-to-motec`. Outputs `.ld` files for manual verification in MoTeC i2.
*   **Stream B (Machine):** `gt7_1r.py`. Outputs `.csv` files for automated processing.
*   **Input:** Both listen to the GT7 UDP Telemetry Stream (Port 33740) simultaneously.
*   **Key Data:** Suspension travel, tire surface temps, wheel speeds, G-forces, yaw rates.
*   **Status:** *Solved (Both tools exist and work in parallel).*

### Layer 2: Engineering Metrics (The "Virtual MoTeC")
**Goal:** Replicate MoTeC's analytical power within Python to feed the Agent.
*   **Tool:** `gt7_2r.py` (Enhanced).
*   **The "Virtual MoTeC" Concept:** Instead of trying to parse binary MoTeC files, we port the industry-standard **Math Channels** directly into Python logic.
    *   *MoTeC Logic:* `Damper Vel = derivative(Suspension Pos)` -> displayed as Histogram.
    *   *Python Logic:* `df['damper_vel'] = df['susp_pos'].diff()` -> summarized as statistical distribution.
*   **Calculated Metrics:**
    *   **Damper Histograms:** Summarized as asymmetry percentages (e.g., "Rear Rebound Bias: +15%").
    *   **Balance Metrics:** Understeer Gradient (deg/g), Slip Ratio Deltas.
    *   **Platform Control:** Bottoming severity count, Pitch/Roll sensitivity.
    *   **Thermal Management:** Tire heating rates and inner/outer spread.
*   **Output:** A structured JSON `EngineeringProfile`. The Agent reads this text summary, not the graph.

### Layer 3: The Agentic Core (The Race Engineer)
**Goal:** Correlate data with driver feedback and apply physics rules.
*   **Agent:** Gemini / LLM.
*   **Knowledge Base:** `ClaudeTunes v8.5.3b.yaml` (The "Laws of Physics" for GT7).
*   **Inputs:**
    1.  `EngineeringProfile` (The Data).
    2.  `DriverFeedback` (e.g., "Car feels loose on entry").
*   **Reasoning Loop:**
    1.  **Observation:** Telemetry shows Rear Slip Ratio spikes on entry + Negative Pitch (Nose dive).
    2.  **Correlation:** Matches driver feedback of "loose on entry."
    3.  **Protocol Check:** Consult YAML -> *Entry Oversteer caused by excessive weight transfer.*
    4.  **Constraint Check:** Rear Rebound is currently 40%.
    5.  **Solution:** "Increase Front Bump (resist dive) OR Increase Rear Rebound (control droop)."

### Layer 4: Execution (The Tuning)
**Goal:** Precise, quantative setup changes.
*   **Output:** Specific "Click" instructions.
    *   *Change Front Compression: 30 -> 35*
    *   *Change Rear Rebound: 40 -> 42*

---

## Future Enhancement: Visual Telemetry Correlation
**"The GT7 Spec III Integration"**

GT7's "Spec III" updates and replays often provide on-screen data visualizations that are not present in the UDP stream (or serve as a perfect validation source).

*   **Visual Ingestion:** The Agent can analyze screenshots/video frames of the GT7 replay telemetry UI.
*   **Correlation:** Compare the "Ground Truth" of the visual logs against the calculated values from the UDP stream.
*   **Benefit:**
    *   Validate "Unknown Floats" by matching them to on-screen gauges.
    *   Calibrate the `gt7_1r.py` physics models (e.g., Does our "Tire Temp" match the visual indicator color?).

## Summary
By building this pipeline, we move from **"Looking at Data"** to **"Actionable Engineering."** The AI doesn't just guess; it acts as a staff engineer analyzing MoTeC traces 24/7 to provide physics-validated setup solutions.
