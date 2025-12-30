# Phase 0, Step 0.2: Drivetrain Bias Refactor - COMPLETE ✅

**Date:** 2025-12-30
**Status:** ✅ TESTED & VERIFIED

---

## What Was Done

Refactored `_get_drivetrain_bias()` method to read drivetrain frequency biases from YAML instead of hardcoded dictionary. Also added helper method `_parse_bias_string()` to parse YAML bias format.

### Before (Hardcoded)
```python
def _get_drivetrain_bias(self):
    """Calculate drivetrain-specific frequency bias"""
    dt = self.car_data.get('drivetrain', 'FR')

    bias_map = {
        'FF': {'front': 0.4, 'rear': 0.0},
        'FR': {'front': 0.3, 'rear': 0.0},
        'MR': {'front': 0.0, 'rear': 0.1},
        'RR': {'front': 0.0, 'rear': 0.8},
        'AWD': {'front': 0.2, 'rear': 0.2}  # Simplified
    }

    return bias_map.get(dt, {'front': 0.2, 'rear': 0.0})
```

### After (YAML-Driven)
```python
def _parse_bias_string(self, bias_str):
    """Parse YAML bias string to front/rear dict"""
    # "+0.4F" → {'front': 0.4, 'rear': 0.0}
    # "+0.2F +0.2R" → {'front': 0.2, 'rear': 0.2}
    result = {'front': 0.0, 'rear': 0.0}
    parts = bias_str.strip().split()
    for part in parts:
        if part.endswith('F'):
            result['front'] = float(part[:-1])
        elif part.endswith('R'):
            result['rear'] = float(part[:-1])
    return result

def _get_drivetrain_bias(self):
    """Calculate drivetrain-specific frequency bias (YAML-driven)"""
    # YAML: phase_B.drivetrain_bias (lines 100-108)
    dt = self.car_data.get('drivetrain', 'FR')

    # Build bias map from YAML
    bias_data = self.protocol['phase_B']['drivetrain_bias']
    bias_map = {}
    for key, value in bias_data.items():
        if isinstance(value, dict) and 'bias' in value:
            bias_map[key] = self._parse_bias_string(value['bias'])

    # Handle AWD variants
    if dt in bias_map:
        return bias_map[dt]

    # Generic AWD fallback to AWD_DEFAULT
    if dt == 'AWD' and 'AWD_DEFAULT' in bias_map:
        return bias_map['AWD_DEFAULT']

    # Fallback to FR bias (most common)
    return bias_map.get('FR', {'front': 0.2, 'rear': 0.0})
```

---

## Changes Made

| Aspect | Before | After |
|--------|--------|-------|
| **Data Source** | Hardcoded dictionary | YAML protocol |
| **Methods** | 1 (_get_drivetrain_bias) | 2 (+_parse_bias_string helper) |
| **Drivetrain Types** | 5 (FF/FR/MR/RR/AWD) | 9 (+ AWD variants) |
| **AWD Handling** | Generic 0.2/0.2 | 4 explicit variants |
| **Bias Format** | Python dicts | Parsed from YAML strings |
| **Maintainability** | Code edit required | YAML edit only |

---

## New Functionality

### AWD Variants Support (v8.5.3c)
The refactored code now supports explicit AWD categories:

| Drivetrain | Bias | Example Cars |
|------------|------|--------------|
| **AWD_FRONT** | +0.3F | Audi Quattro, Subaru WRX |
| **AWD_REAR** | +0.5R | Porsche 911 Turbo |
| **AWD_BALANCED** | +0.2F +0.2R | Nissan GT-R, Mitsubishi Evo |
| **AWD_DEFAULT** | +0.2F +0.2R | Fallback for generic "AWD" |

### Bias String Parsing
New helper method parses YAML bias format:
- `"+0.4F"` → Front bias only
- `"+0.1R"` → Rear bias only
- `"+0.2F +0.2R"` → Both front and rear bias

---

## Test Results

**Total Tests:** 15
**Passed:** 15 ✅
**Failed:** 0

### Test Coverage
- ✅ All 5 standard drivetrains (FF/FR/MR/RR/RR_AWD)
- ✅ All 4 new AWD variants (AWD_FRONT/REAR/BALANCED/DEFAULT)
- ✅ Generic AWD fallback to AWD_DEFAULT
- ✅ Unknown drivetrain fallback to FR
- ✅ Bias string parsing (4 formats tested)

### Sample Output
```
✅ PASS | 'FF' → F:0.4 R:0.0 (expected F:0.4 R:0.0)
✅ PASS | 'AWD_BALANCED' → F:0.2 R:0.2 (expected F:0.2 R:0.2)
✅ PASS | 'AWD' → F:0.2 R:0.2 (expected F:0.2 R:0.2)
✅ PASS | '+0.2F +0.2R' → F:0.2 R:0.2
```

---

## Files Created/Modified

| File | Status | Purpose |
|------|--------|---------|
| `claudetunes_cli_v8.5.3c.py` | ✅ Modified | Added _parse_bias_string, refactored _get_drivetrain_bias |
| `phase0_step2_drivetrain_bias_refactor.py` | ✅ Created | Reference implementation |
| `test_step2_drivetrain_bias.py` | ✅ Created | Automated test suite |
| `PHASE0_STEP2_COMPLETE.md` | ✅ Created | This document |

---

## YAML Reference

**Location:** `ClaudeTunes v8.5.3c.yaml`
**Section:** `phase_B.drivetrain_bias` (lines 100-108)

**Structure:**
```yaml
phase_B:
  drivetrain_bias:
    FF: {bias: "+0.4F", range: "0.3–0.5"}
    FR: {bias: "+0.3F", range: "0.2–0.4"}
    MR: {bias: "+0.1R", range: "0.0–0.3"}
    RR: {bias: "+0.8R", range: "0.6–0.9"}
    RR_AWD: {bias: "+0.6R", range: "0.5–0.8"}
    AWD_FRONT: {bias: "+0.3F", note: "Front-engine AWD"}
    AWD_REAR: {bias: "+0.5R", note: "Rear-engine AWD"}
    AWD_BALANCED: {bias: "+0.2F +0.2R", note: "Balanced AWD"}
    AWD_DEFAULT: {bias: "+0.2F +0.2R", note: "Fallback"}
```

---

## Benefits Achieved

1. ✅ **YAML is Source of Truth** - No more hardcoded bias values
2. ✅ **Explicit AWD Handling** - 4 AWD variants with clear examples
3. ✅ **Flexible Bias Format** - Parses "+0.4F", "+0.1R", "+0.2F +0.2R"
4. ✅ **Future-Proof** - New drivetrain types auto-included
5. ✅ **Better Documentation** - YAML includes car examples and notes
6. ✅ **Smart Fallbacks** - AWD → AWD_DEFAULT → FR

---

## Integration Notes

### Bias String Format
The YAML uses an intuitive format:
- **F** = Front bias (e.g., "+0.4F" = add 0.4 Hz to front)
- **R** = Rear bias (e.g., "+0.8R" = add 0.8 Hz to rear)
- **Combined** = Both (e.g., "+0.2F +0.2R" = add to both)

### Fallback Logic
1. Try exact match (e.g., "AWD_FRONT")
2. If generic "AWD", use AWD_DEFAULT
3. If unknown drivetrain, use FR (most common)

This ensures the code never fails, even with unusual drivetrain specifications.

---

## Next Steps

**Phase 0 Progress:** 2/7 steps complete (29%)

### Ready for Step 0.3
- ✅ Steps 0.1-0.2 complete and tested
- ✅ Pattern established for YAML-driven refactors
- ✅ Helper methods demonstrate parsing techniques

**Next:** Refactor CG adjustments (lines 965-972) to read from YAML

---

**Status:** ✅ STEP 0.2 COMPLETE - READY FOR STEP 0.3
