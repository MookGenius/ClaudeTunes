# Phase 0: Minor Discrepancy Resolutions

**Created:** 2025-12-30
**Purpose:** Resolve 3 minor discrepancies between YAML protocol and Python implementation

---

## Discrepancy #1: "Sports" vs "Sport" Tire Naming

### The Issue
GT7 inconsistently uses both "Sport Hard" and "Sports Hard" (with an 's') in different menus.

### Current State

**YAML (Lines 84-92):**
```yaml
phase_B:
  base_frequency_by_compound:
    Sport_Hard: {hz: 1.85, grip: 0.95, range: "1.3-2.8"}
    Sport_Medium: {hz: 2.15, grip: 1.00, range: "1.5-3.2"}
    Sport_Soft: {hz: 2.40, grip: 1.05, range: "1.8-3.6"}
```

**Python (Lines 765-769):**
```python
compound_map = {
    'Sport Hard': 1.85,
    'Sports Hard': 1.85,  # GT7 uses "Sports" sometimes
    'Sport Medium': 2.15,
    'Sports Medium': 2.15,
    'Sport Soft': 2.40,
    'Sports Soft': 2.40,
}
```

### Proposed Resolution

**Option A: Add Variants to YAML** ✅ RECOMMENDED
```yaml
phase_B:
  base_frequency_by_compound:
    # Sport tires (GT7 uses both "Sport" and "Sports" naming)
    Sport_Hard: {hz: 1.85, grip: 0.95, range: "1.3-2.8"}
    Sports_Hard: {hz: 1.85, grip: 0.95, range: "1.3-2.8"}  # Alias for GT7 quirk
    Sport_Medium: {hz: 2.15, grip: 1.00, range: "1.5-3.2"}
    Sports_Medium: {hz: 2.15, grip: 1.00, range: "1.5-3.2"}  # Alias
    Sport_Soft: {hz: 2.40, grip: 1.05, range: "1.8-3.6"}
    Sports_Soft: {hz: 2.40, grip: 1.05, range: "1.8-3.6"}  # Alias
```

**Option B: Document Normalization Rule in YAML**
```yaml
phase_B:
  base_frequency_by_compound:
    note: "GT7 uses both 'Sport' and 'Sports' - normalize in code to 'Sport_*'"
    Sport_Hard: {hz: 1.85, grip: 0.95, range: "1.3-2.8"}
    Sport_Medium: {hz: 2.15, grip: 1.00, range: "1.5-3.2"}
    Sport_Soft: {hz: 2.40, grip: 1.05, range: "1.8-3.6"}
```

**Recommendation:** **Option A** - Explicit is better than implicit. YAML contains the variants.

---

## Discrepancy #2: AWD Drivetrain Bias

### The Issue
YAML says "Follow engine orientation" but doesn't specify numeric values. Python hardcodes 0.2 front, 0.2 rear.

### Current State

**YAML (Lines 94-100):**
```yaml
phase_B:
  drivetrain_bias:
    FF: {bias: "+0.4F", range: "0.3–0.5"}
    FR: {bias: "+0.3F", range: "0.2–0.4"}
    MR: {bias: "+0.1R", range: "0.0–0.3"}
    RR: {bias: "+0.8R", range: "0.6–0.9"}
    RR_AWD: {bias: "+0.6R", range: "0.5–0.8"}
    AWD: "Follow engine orientation"
```

**Python (Line 924):**
```python
'AWD': {'front': 0.2, 'rear': 0.2}  # Simplified
```

### Analysis
AWD systems vary widely:
- **Front-biased AWD** (e.g., Audi Quattro, Subaru): Engine in front, power primarily to front → follow FF logic
- **Rear-biased AWD** (e.g., Porsche 911 Turbo): Engine in rear, power primarily to rear → follow RR_AWD logic
- **Balanced AWD** (e.g., Nissan GT-R): 50/50 torque split → balanced bias

### Proposed Resolution

**Option A: Explicit AWD Categories** ✅ RECOMMENDED
```yaml
phase_B:
  drivetrain_bias:
    FF: {bias: "+0.4F", range: "0.3–0.5"}
    FR: {bias: "+0.3F", range: "0.2–0.4"}
    MR: {bias: "+0.1R", range: "0.0–0.3"}
    RR: {bias: "+0.8R", range: "0.6–0.9"}
    RR_AWD: {bias: "+0.6R", range: "0.5–0.8"}

    # AWD systems follow engine layout
    AWD_FRONT: {bias: "+0.3F", range: "0.2–0.4", note: "Front-engine AWD (Audi, Subaru)"}
    AWD_REAR: {bias: "+0.5R", range: "0.4–0.6", note: "Rear-engine AWD (911 Turbo)"}
    AWD_BALANCED: {bias: "+0.2F +0.2R", range: "0.1–0.3", note: "Balanced AWD (GT-R, Evo)"}

    # Fallback if engine position unknown
    AWD_DEFAULT: {bias: "+0.2F +0.2R", range: "0.1–0.3", note: "Use when engine position uncertain"}
```

**Option B: Use Engine Position for AWD**
```yaml
phase_B:
  drivetrain_bias:
    AWD:
      rule: "Follow engine orientation + AWD compensation"
      front_engine_awd: {bias: "+0.3F", note: "Use FF bias reduced 25%"}
      rear_engine_awd: {bias: "+0.5R", note: "Use RR_AWD values"}
      balanced_awd: {bias: "+0.2F +0.2R", note: "Symmetric platform"}
      default: {bias: "+0.2F +0.2R", note: "When uncertain"}
```

**Recommendation:** **Option A** - Clear categories, easy to reference in code.

### Implementation Note
Code should:
1. Check for specific AWD variant (AWD_FRONT, AWD_REAR, AWD_BALANCED)
2. Fall back to AWD_DEFAULT if variant not specified
3. Log which AWD bias was used

---

## Discrepancy #3: Power Platform Control Formula

### The Issue
YAML has simple HP brackets. Python uses sophisticated power-to-weight ratio (PWR) formula.

### Current State

**YAML (Lines 102-108):**
```yaml
phase_B:
  power_platform_control:
    base_formula: "Base × sqrt(HP / 400)"
    high_power_add:
      "600–700HP": "+0.1 Hz"
      "700–850HP": "+0.2 Hz"
      ">850HP": "+0.3 Hz"
    note: "Independent of aero; for torque delivery platform"
```

**Python (Lines 930-958):**
```python
def _get_power_adder(self):
    hp = self.car_data.get('hp', 400)
    weight_lbs = self.car_data.get('weight', 3000)
    base_freq = self._get_base_frequency()

    # Power-to-weight ratio approach
    power_to_weight = hp / weight_lbs
    reference_ratio = 0.154  # HP/lb baseline

    # Formula: Base × (sqrt(PWR / reference_ratio) - 1.0)
    pwr_multiplier = math.sqrt(power_to_weight / reference_ratio)
    adder = base_freq * (pwr_multiplier - 1.0)

    # High absolute power brackets (even for heavy cars)
    if hp > 850:
        adder += 0.2
    elif hp > 700:
        adder += 0.1

    return max(0, adder)
```

### Analysis

**YAML Simple Approach:**
- Only considers absolute HP
- Easy to understand and tune
- Ignores weight (700HP Viper vs 700HP Bentley treated same)

**Python PWR Approach:**
- Considers both power AND weight
- More accurate (700HP / 3000lbs ≠ 700HP / 5000lbs)
- Uses physics-based sqrt scaling (diminishing returns)
- Still adds extra for very high HP (>700, >850)

**Example Comparison:**
```
Car A: 700HP / 3000lbs = 0.233 PWR
  YAML:  +0.2 Hz
  Python: base × (sqrt(0.233/0.154) - 1) + 0.1 = ~0.55 Hz (more accurate)

Car B: 700HP / 5000lbs = 0.140 PWR (heavy luxury car)
  YAML:  +0.2 Hz (same as Car A - wrong!)
  Python: base × (sqrt(0.140/0.154) - 1) + 0.1 = ~0.05 Hz (lighter springs needed)
```

### Proposed Resolution

**Option A: Document Full PWR Formula in YAML** ✅ RECOMMENDED
```yaml
phase_B:
  power_platform_control:
    note: "Independent of aero; for torque delivery platform stability"

    formula: "Base_Freq × (sqrt(PWR / Reference_PWR) - 1.0) + High_Power_Bracket"

    reference_pwr: 0.154  # HP/lb (baseline: 400HP / 2600lbs balanced sports car)

    calculation_steps:
      1: "Calculate PWR = Horsepower / Weight_lbs"
      2: "Calculate multiplier = sqrt(PWR / 0.154)"
      3: "Calculate base_adder = Base_Freq × (multiplier - 1.0)"
      4: "Add high_power_bracket if applicable"
      5: "Return max(0, total_adder)"

    high_power_brackets:
      # Additional stiffness for extremely powerful cars (even if heavy)
      "700-850HP": "+0.1 Hz"
      ">850HP": "+0.2 Hz"

    examples:
      sports_car_400hp_2600lbs:
        pwr: 0.154
        result: "0.0 Hz (baseline, no adjustment)"

      sports_car_700hp_3000lbs:
        pwr: 0.233
        calculation: "sqrt(0.233/0.154) = 1.226, adder = base × 0.226 + 0.1"
        result: "~0.55 Hz"

      luxury_700hp_5000lbs:
        pwr: 0.140
        calculation: "sqrt(0.140/0.154) = 0.952, adder = base × -0.048 + 0.1"
        result: "~0.05 Hz (weight offsets power)"
```

**Option B: Keep YAML Simple, Document in Code**
```yaml
phase_B:
  power_platform_control:
    note: "Uses power-to-weight ratio formula (see code for details)"
    simplified_brackets:  # Approximations for reference
      "600–700HP": "~+0.1–0.2 Hz"
      "700–850HP": "~+0.2–0.4 Hz"
      ">850HP": "~+0.3–0.6 Hz"
    actual_implementation: "See _get_power_adder() in claudetunes_cli.py"
```

**Recommendation:** **Option A** - YAML should be the source of truth. Document the full formula.

---

## Summary of Resolutions

| Discrepancy | Resolution | YAML Changes Required |
|-------------|-----------|----------------------|
| **1. Sports/Sport** | Add explicit aliases | Add Sports_Hard, Sports_Medium, Sports_Soft |
| **2. AWD Bias** | Create AWD subcategories | Add AWD_FRONT, AWD_REAR, AWD_BALANCED, AWD_DEFAULT |
| **3. Power Formula** | Document full PWR formula | Replace simple brackets with complete formula + examples |

---

## Next Steps

1. **User approves resolutions** ← YOU ARE HERE
2. **Update YAML protocol** with resolved values
3. **Test YAML loads correctly** (no syntax errors)
4. **Proceed to Phase 0, Step 0.1** (refactor tire frequencies)

---

## Questions for User

1. **Sports/Sport naming**: Approve Option A (add explicit aliases)?
2. **AWD bias**: Approve Option A (explicit AWD categories)?
3. **Power formula**: Approve Option A (document full PWR formula in YAML)?

Once approved, I'll update the YAML protocol with these resolutions.
