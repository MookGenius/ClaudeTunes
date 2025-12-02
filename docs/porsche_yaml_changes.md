# Proposed YAML Refinements for RR (Porsche) Platforms

**Context:** Based on analysis of `@docs/Porsche setup_Reference.md`, the following refinements are proposed for `ClaudeTunes v8.5.3b.yaml` to better align with professional Porsche GT3/Cup car methodologies. While the core frequency bias is already correct, the ARB, Differential, and Damping strategies require "inversion" from standard logic.

## 1. Differential: The "Pendulum" Lock
**Insight:** RR platforms require higher locking on **Deceleration** to stabilize the engine mass during braking entry, preventing the rear from "overtaking" the front.
*   **Current YAML:** Ranges overlap or favor acceleration slightly (`accel: 20-35`, `brake: 20-40`).
*   **Proposed Change:** Update `RR_PURE` and `RR_AWD` baselines to explicitly favor Braking Sensitivity.
    *   **Target:** `Accel: ~30-40` | `Braking: ~45-55`
    *   **Logic:** Braking Lock > Acceleration Lock.

## 2. Anti-Roll Bars: The "Inverted" Strategy
**Insight:** Unlike FR/MR cars, RR platforms naturally understeer due to yaw moments. To fix this, they rely on **Stiffer Rear ARBs** to force rotation, while keeping the Front ARB softer for compliance.
*   **Current YAML:** Generic `+1R` bias.
*   **Proposed Change:**
    *   **Front ARB:** Bias toward lower end of stiffness (Compliance/Grip).
    *   **Rear ARB:** Bias toward higher stiffness (Rotation).
    *   **Logic:** "Stiff Rear / Soft Front" relative to spring rates.

## 3. Damping: Rear Rebound Criticality
**Insight:** Rear Rebound is the primary control for braking stability (preventing the rear lift "pop").
*   **Current YAML:** Focuses on "Rear Squat" (acceleration) for rear rebound adjustments.
*   **Proposed Change:** Add specific `telemetry_reconciliation` rule for RR layouts.
    *   **Trigger:** "Braking Instability" or "Entry Oversteer".
    *   **Action:** Increase Rear Rebound (+3-5%).
    *   **Reasoning:** Controls the rate of rear lift during weight transfer, settling the pendulum.

## 4. Validation (No Change Needed)
*   **Frequency Bias:** The document explicitly validates the current `+0.8 Hz` rear bias (`RR: {bias: "+0.8R"}`). No changes required here.
