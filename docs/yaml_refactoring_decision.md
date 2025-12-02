# YAML Refactoring Decision & Rationale

**Date:** 2025-11-25
**Status:** Approved for future implementation (not started yet)
**Priority:** Medium - implement when ready to do heavy parameter tuning

---

## The Discovery

We identified that `claudetunes_cli.py` currently has **physics constants hardcoded** in the Python code, even though those same values exist in `ClaudeTunes v8.5.3b.yaml`. The code currently **ignores** the YAML values and uses its own hardcoded copies.

## Current Architecture (Duplication Problem)

### Physics Constants Appear in TWO Places:

**1. In Python Code (claudetunes_cli.py):**
```python
# Line 760-772: Tire compounds hardcoded
compound_map = {
    'Racing Hard': 2.85,
    'Racing Medium': 3.15,
    'Racing Soft': 3.40
}

# Line 919-927: Drivetrain bias hardcoded
bias_map = {
    'RR': {'front': 0.0, 'rear': 0.8},
    'FR': {'front': 0.3, 'rear': 0.0}
}

# Line 1328: Damping ratio hardcoded
zeta = 0.67

# Line 1347-1348: Baseline damping hardcoded
baseline_comp = 25
baseline_rebound = 35
```

**2. In YAML File (ClaudeTunes v8.5.3b.yaml):**
```yaml
base_frequency_by_compound:
  Racing_Hard: {hz: 2.85, grip: 1.12}
  Racing_Medium: {hz: 3.15, grip: 1.18}

drivetrain_bias:
  RR: {bias: "+0.8R", range: "0.6–0.9"}
  FR: {bias: "+0.3F", range: "0.2–0.4"}

damping:
  base_ratios: "0.65–0.70 damping ratio"
```

**Result:** When you change YAML values, nothing happens because Python ignores them.

---

## The Problem This Creates

### Current Workflow for Parameter Tuning:
1. Discover RR_AWD multiplier should be `0.018` instead of `0.02`
2. Open `claudetunes_cli.py` (1717 lines)
3. Search for the value in Python code
4. Edit line 1596
5. Run test
6. If it doesn't work, remember what the old value was (or check git)
7. Git commit just to track parameter changes
8. Mix code commits with tuning commits

### Issues:
- ❌ Parameter tweaks require editing Python code (risky)
- ❌ Can't easily A/B test different parameter sets
- ❌ Git history mixes algorithm fixes with constant tuning
- ❌ Can't compare "conservative" vs "aggressive" protocols side-by-side
- ❌ Hard to document WHY values are what they are

---

## Proposed Solution: YAML-Driven Configuration

### Architecture Change:

**Python Code:**
- Defines HOW to calculate (algorithms, logic, formulas)
- Reads physics constants FROM YAML at runtime
- Never hardcodes tunable values

**YAML File:**
- Defines WHAT values to use (physics constants, multipliers, baselines)
- Can be versioned independently
- Supports comments documenting discoveries

### Example Refactoring:

**BEFORE (hardcoded):**
```python
def _get_base_frequency(self):
    compound_map = {
        'Racing Hard': 2.85,
        'Racing Medium': 3.15
    }
    return compound_map[compound]
```

**AFTER (YAML-driven):**
```python
def _get_base_frequency(self):
    # Read from loaded YAML protocol
    compound_map = self.protocol['phase_B']['base_frequency_by_compound']
    compound_key = compound.replace(' ', '_')
    return compound_map[compound_key]['hz']
```

**YAML stays the same:**
```yaml
phase_B:
  base_frequency_by_compound:
    Racing_Hard: {hz: 2.85, grip: 1.12}
    Racing_Medium: {hz: 3.15, grip: 1.18}
```

---

## Benefits of YAML Refactoring

### 1. **Rapid Parameter Experimentation**
```bash
# Test different protocols without code changes
./claudetunes_cli.py --protocol v8.5.3b.yaml car.txt telemetry.json
./claudetunes_cli.py --protocol v8.5.3c.yaml car.txt telemetry.json
./claudetunes_cli.py --protocol conservative.yaml car.txt telemetry.json
```

### 2. **Version Control for Physics Constants**
```
ClaudeTunes_v8.5.3b.yaml           # Current stable version
ClaudeTunes_v8.5.3c_test.yaml      # Testing RR multiplier changes
ClaudeTunes_conservative.yaml      # Safe defaults for new cars
ClaudeTunes_aggressive.yaml        # Track-day optimized
ClaudeTunes_hall_of_fame.yaml      # Best validated settings
```

### 3. **Self-Documenting Configuration**
```yaml
drivetrain_bias:
  RR:
    front_add: 0.0
    rear_add: 0.8  # Critical for 911s! Validated on 991/992 GT3 RS
                   # Don't go below 0.6 or you lose rear stability

damping:
  zeta: 0.67  # OptimumG racing standard
              # Tested: 0.65 too soft, 0.70 too stiff
              # Sweet spot for GT7 physics
```

### 4. **Clean Git History**
```
# Python commits (algorithm/logic changes)
commit abc123: "Fix chassis bottoming vs suspension maxed detection"
commit def456: "Add front differential support for AWD"

# No commits needed for parameter tuning - just swap YAML files
```

### 5. **A/B Testing Made Easy**
```bash
# Test 10 different damping baselines in 5 minutes
for config in configs/*.yaml; do
    ./claudetunes_cli.py --protocol $config car.txt telemetry.json -o results/$(basename $config .yaml).txt
done
```

---

## What Changes vs What Stays The Same

### ✅ **STAYS IDENTICAL (Algorithm Logic):**
- Physics calculations (OptimumG formulas)
- Telemetry parsing logic
- Constraint evaluation system
- Setup sheet generation
- Output format
- Command-line interface
- All core functionality

### 🔄 **CHANGES (Configuration Source):**
- Values READ from YAML instead of hardcoded
- Multiple YAML files can exist for different use cases
- Can tune parameters without touching code

### **Behavior After Refactoring:**
- ✅ Produces IDENTICAL output with same YAML values
- ✅ Just reads from file instead of hardcoded constants
- ✅ No functional changes, only architectural improvement

---

## Why YAML Instead of JSON?

### YAML Advantages:
```yaml
# YAML supports comments!
Racing_Hard:
  hz: 2.85  # Validated on 992 GT3 RS, NSX-R, 991 GT3
  grip: 1.12
  range: "2.2-4.5"

philosophy: |
  Multi-line text explanation
  of why this approach works
  and what testing validated it
```

### JSON Equivalent:
```json
{
  "Racing_Hard": {
    "hz": 2.85,
    "grip": 1.12,
    "range": "2.2-4.5"
  },
  "philosophy": "No comments allowed, can't explain why values are what they are"
}
```

**YAML wins for:**
- ✅ Comments (document discoveries)
- ✅ Cleaner syntax (less noise)
- ✅ Multi-line text support
- ✅ More human-readable
- ✅ Better for configuration files

---

## Implementation Scope

### Values That Should Move to YAML:
1. **Tire Compound Base Frequencies** (line 760-772)
2. **Drivetrain Bias Multipliers** (line 919-927)
3. **Power Platform Brackets** (line 951-956)
4. **CG Adjustment Thresholds** (line 965-973)
5. **Damping Ratios & Baselines** (line 1328, 1347-1348)
6. **ARB Multipliers** (line 1286-1290)
7. **Differential Baselines** (line 1581-1633)
8. **Camber/Toe Baselines** (line 1423-1478)
9. **Chassis Bottoming Thresholds** (line 394, 822)
10. **Track Type Adjustments** (scattered throughout)

### Values That Stay in Code:
- Formula constants (π, 4, 0.453592 kg/lb conversion)
- GT7 range limits (5-60 diff, 1-10 ARB, 20-40% damping)
- Algorithm logic conditions

---

## Evolution Story: Why We Got Here

### The Journey:
1. **Chat** → Too ephemeral, lost context
2. **26-Page Mega Prompts** → Knowledge captured but manual to use
3. **CLI Mode** → Can read files, no copy/paste
4. **Python Script** → Automated calculations, repeatable
5. **Python + YAML** → Separate logic from configuration ← **We are here**

### Each Step Solved a Real Problem:
- Mega prompt → captured ClaudeTunes methodology
- Python → automated repetitive physics calculations
- YAML → separate tunable constants from code logic

---

## When to Implement This

### ✅ **Good Time to Refactor:**
- When you're about to do heavy parameter experimentation
- When you have multiple car types needing different baselines
- When you want to version/test protocol variations
- When you're confident core algorithms are stable

### ⏸️ **Wait If:**
- Core physics calculations still being debugged
- Major algorithm changes expected soon
- Values are already stable and working well

### **Current Status (2025-11-25):**
- Decision approved
- Implementation postponed until ready for heavy tuning phase
- Core functionality still being refined

---

## Testing Plan (When Implemented)

### Validation Approach:
1. Run current version on test telemetry → save output as baseline
2. Implement YAML refactoring
3. Run refactored version with identical YAML values → compare output
4. **Outputs must be byte-for-byte identical**
5. Then start testing new YAML variations

### Test Cases:
- 992 GT3 RS (RR layout)
- NSX-R (MR layout)
- Multiple tire compounds
- High-speed vs technical track types
- Chassis bottoming scenarios

---

## Reference Implementation Example

### Current Code (claudetunes_cli.py:760-790):
```python
def _get_base_frequency(self):
    """Get base frequency from tire compound"""
    compound_map = {
        'Comfort Hard': 0.75,
        'Racing Hard': 2.85,
        'Racing Medium': 3.15,
        'Racing Soft': 3.40
    }

    compound = self.car_data.get('tire_compound', 'Racing Hard').strip()

    if compound in compound_map:
        return compound_map[compound]

    # Fallback
    print(f"  ⚠ Warning: Unknown tire compound '{compound}', defaulting to Racing Hard")
    return 2.85
```

### Refactored Version:
```python
def _get_base_frequency(self):
    """Get base frequency from tire compound (YAML-driven)"""
    # Load tire compound map from YAML protocol
    compounds = self.protocol['phase_B']['base_frequency_by_compound']

    compound = self.car_data.get('tire_compound', 'Racing Hard').strip()
    compound_key = compound.replace(' ', '_')

    # Try exact match
    if compound_key in compounds:
        return compounds[compound_key]['hz']

    # Try fuzzy match
    for key in compounds:
        if key.lower().replace('_', '') in compound_key.lower().replace(' ', ''):
            return compounds[key]['hz']

    # Fallback to Racing Hard default
    default = compounds['Racing_Hard']['hz']
    print(f"  ⚠ Warning: Unknown tire compound '{compound}', defaulting to Racing Hard ({default} Hz)")
    return default
```

### YAML Structure (phase_B section):
```yaml
phase_B:
  base_frequency_by_compound:
    Comfort_Hard:
      hz: 0.75
      grip: 0.75
      range: "0.5-1.2"
      note: "Validated for street cars"

    Racing_Hard:
      hz: 2.85
      grip: 1.12
      range: "2.2-4.5"
      note: "Primary competition tire, extensive testing"

    Racing_Medium:
      hz: 3.15
      grip: 1.18
      range: "2.5-5.0"

    Racing_Soft:
      hz: 3.40
      grip: 1.25
      range: "2.8-5.5"
      note: "Highest grip, shorter life"
```

---

## Summary

**The Goal:** Separate "what to calculate" (code) from "what values to use" (YAML)

**The Benefit:** Rapid experimentation without touching code

**The Risk:** None - behavior stays identical, just reads from different source

**The Timeline:** Implement when ready for heavy parameter tuning phase

**Estimated Effort:** 30-45 minutes of refactoring + testing

---

## Questions Answered

**Q: Will this change how the program works?**
A: No. Same calculations, same output, just reads values from YAML instead of hardcoded.

**Q: Why not JSON?**
A: YAML supports comments, cleaner syntax, better for human-edited config files.

**Q: Can we still use git for version control?**
A: Yes! But git commits will be cleaner (algorithm changes only). YAML files can be versioned separately.

**Q: What if we break something?**
A: We'll test that refactored version produces identical output before changing any values.

---

**Next Steps (When Ready):**
1. Create comprehensive YAML schema with all physics constants
2. Refactor Python code to read from YAML
3. Validate identical output with current hardcoded values
4. Start creating YAML variants for different use cases

**Decision:** Approved but implementation postponed until heavy tuning phase begins.
