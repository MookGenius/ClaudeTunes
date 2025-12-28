# Session Summary: Domain JSON Architecture Refactor
**Date:** 2025-12-19
**Focus:** Eliminate CSV/parsing step, enable subagent integration

---

## Context

User added two strategic documents to `docs/`:
1. **ClaudeTunes_Subagent_Integration_Options.md** - 5 integration patterns for subagents
2. **Claude_Code_Subagents_Summary.md** - Technical guide to Claude Code subagent system

**Key User Insight:**
> "I want to get rid of the CSV creation entirely by the logging python script. Write direct to specific JSONs. This will also eliminate the parsing step of gt7_2.py, correct?"

**Answer:** ✅ YES - This is **Option 5** from the integration doc and the cleanest architecture.

---

## Current Architecture (Inefficient)

```
gt7_1r.py (880 lines)
    ↓ writes CSV (raw dump)
gt7_2r.py (983 lines)  ← BOTTLENECK
    ↓ parses CSV → monolithic JSON
claudetunes_cli.py (1,417 lines)
    ↓ reads JSON → generates setup
```

**Problems:**
- 3-step pipeline with intermediate parsing
- 983 lines of parsing code (gt7_2r.py)
- Monolithic JSON makes domain-specific analysis hard
- Subagents would have to parse entire data structure
- CSV → JSON transformation loss

---

## Proposed Architecture (Clean)

```
gt7_1r.py (modified: ~950 lines)
    ↓ writes domain-specific JSONs directly
/sessions/SESSION_ID/
    ├── metadata.json        ← Session info, car, track
    ├── suspension.json      ← Travel, bottoming, ride height
    ├── tires.json           ← Temps (3 zones), slip, wear
    ├── aero.json            ← Ride height, downforce, rake
    ├── drivetrain.json      ← Power, wheel spin, gears
    └── balance.json         ← Weight transfer, stability
    ↓
claudetunes_cli.py (modified: ~1,450 lines)
    ↓ reads domain JSONs → generates setup
```

**Benefits:**
- ✅ 2-step pipeline (eliminates parsing)
- ✅ -983 lines of code (delete gt7_2r.py entirely)
- ✅ Real-time domain monitoring enabled
- ✅ Parallel processing ready (5 subagents read 5 JSONs simultaneously)
- ✅ Clean data separation (each domain owns its data)
- ✅ Single transformation (UDP → JSON, no CSV intermediary)

---

## Domain JSON Schema Design

### Session Folder Structure
```
/sessions/20251219_NSX_GT500_YasMarina/
├── metadata.json           # Session info, car, track
├── suspension.json         # Travel, bottoming, frequency data
├── tires.json             # Temps (3 zones), wear, slip
├── aero.json              # Ride height, downforce estimates
├── drivetrain.json        # Power delivery, wheel spin
└── balance.json           # Weight transfer, stability
```

### metadata.json
```json
{
  "session_id": "20251219_143022",
  "car": {
    "code": 3462,
    "name": "NSX Gr.2",
    "classification": "race_car"
  },
  "track": {
    "name": "Yas Marina Circuit",
    "type": "high_speed"
  },
  "session_summary": {
    "start_time": "2025-12-19T14:30:22Z",
    "total_laps": 8,
    "laps_analyzed": 7,
    "valid_data_points": 4523,
    "data_quality_pct": 94.2
  }
}
```

### suspension.json
```json
{
  "travel_mm": {
    "FL": {
      "avg": 32.5,
      "max": 45.2,
      "min": 18.3,
      "samples": [32, 35, 38, 33, 36, 34, 37, 35, 33, 36]
    },
    "FR": {
      "avg": 31.2,
      "max": 44.8,
      "min": 17.9,
      "samples": [31, 34, 37, 32, 35, 33, 36, 34, 32, 35]
    },
    "RL": {
      "avg": 28.4,
      "max": 38.1,
      "min": 15.2,
      "samples": [28, 30, 32, 29, 31, 30, 31, 29, 28, 30]
    },
    "RR": {
      "avg": 27.9,
      "max": 37.6,
      "min": 14.8,
      "samples": [27, 29, 31, 28, 30, 29, 30, 28, 27, 29]
    }
  },
  "bottoming_events": {
    "detected": false,
    "FL_count": 0,
    "FR_count": 0,
    "RL_count": 0,
    "RR_count": 0
  },
  "current_ride_height_mm": {
    "front": 65,
    "rear": 70
  }
}
```

### tires.json
```json
{
  "temps_celsius": {
    "FL": {"inner": 85.2, "middle": 87.5, "outer": 89.8},
    "FR": {"inner": 84.8, "middle": 87.2, "outer": 90.2},
    "RL": {"inner": 82.5, "middle": 84.0, "outer": 85.8},
    "RR": {"inner": 82.2, "middle": 83.8, "outer": 85.5}
  },
  "slip_ratio": {
    "FL": {"avg": 1.08, "max": 1.25, "events": 3},
    "FR": {"avg": 1.09, "max": 1.28, "events": 4},
    "RL": {"avg": 1.05, "max": 1.18, "events": 2},
    "RR": {"avg": 1.06, "max": 1.20, "events": 2}
  },
  "wear_pct": {
    "FL": 12.5,
    "FR": 13.2,
    "RL": 8.3,
    "RR": 8.8
  }
}
```

### aero.json
```json
{
  "ride_height_mm": {
    "avg_front": 65.2,
    "avg_rear": 70.5,
    "min_front": 58.3,
    "min_rear": 64.1,
    "rake_mm": 5.3
  },
  "downforce_estimate_lbs": {
    "total": 1250,
    "source": "car_database_lookup"
  },
  "speed_correlation": {
    "high_speed_zones": [185, 192, 188, 195],
    "avg_high_speed_mph": 190
  }
}
```

### drivetrain.json
```json
{
  "power_delivery": {
    "avg_throttle_pct": 67.3,
    "max_rpm": 8200,
    "avg_rpm": 6450
  },
  "wheel_spin_events": {
    "total_count": 12,
    "laps": [3, 5, 7],
    "corners": ["Turn 2", "Turn 11", "Turn 21"],
    "severity": "moderate"
  },
  "gear_usage": {
    "1": 45,
    "2": 128,
    "3": 256,
    "4": 412,
    "5": 389,
    "6": 278,
    "7": 125
  }
}
```

### balance.json
```json
{
  "understeer_gradient": 1.8,
  "classification": "Neutral",
  "stability_index": -0.65,
  "weight_transfer": {
    "lateral_g_avg": 1.42,
    "longitudinal_g_avg": 1.28,
    "front_bias_pct": 58.5
  },
  "handling_notes": [
    "Good balance through high-speed corners",
    "Slight push in tight hairpins (Turn 8)",
    "Stable under braking"
  ]
}
```

---

## Implementation Roadmap

### ✅ PHASE 1: Domain JSON Architecture (Foundation)
**Goal:** Refactor data pipeline to eliminate CSV/parsing step

**Tasks:**
1. **Create domain extraction utilities** (`/utils/`)
   - `domain_extractors.py` - Parse UDP packets → domain structures
   - `json_writers.py` - Write/update domain JSONs incrementally

2. **Modify `gt7_1r.py`** (880 → ~950 lines)
   - Remove CSV writer entirely (`csv.writer`, `writerow` calls)
   - Add domain JSON writers (call per-lap or per-packet)
   - Create session folder structure with 6 JSONs
   - Buffer lap data, write domain JSONs at lap completion

3. **Modify `claudetunes_cli.py`** (1,417 → ~1,450 lines)
   - Update `_parse_telemetry()` to load domain JSONs
   - Change CLI argument: `telemetry` → `session` (folder path)
   - Update Phase A intake to read from domain structure:
     - `_analyze_suspension()` → reads `suspension.json`
     - `_analyze_balance()` → reads `balance.json`
     - `_analyze_tire_temps()` → reads `tires.json`

4. **Delete `gt7_2r.py`** (-983 lines)
   - Move to `legacy_files/gt7_2r_deprecated.py`
   - Update all documentation (README, CLAUDE.md)
   - Remove from workflow diagrams

**Timeline:** Week 1-2
**Outcome:** Clean 2-step pipeline (UDP → JSONs → Setup)

---

### ✅ PHASE 2: Subagent Integration (Intelligence Layer)
**Goal:** Add automated monitoring, validation, and learning

**Prerequisites:** Phase 1 complete (domain JSONs available)

#### 2A: Orchestration Layer (Immediate Value)
**Implement:** `claudetunes-orchestrator` subagent

```yaml
# .claude/agents/claudetunes-orchestrator.md
---
name: claudetunes-orchestrator
description: Automates ClaudeTunes telemetry-to-setup pipeline
model: haiku  # Fast and cheap for workflow automation
tools:
  - Read
  - Bash
  - Grep
---

You orchestrate the ClaudeTunes workflow.

When you detect a new session folder in /sessions/:
1. Verify all 6 domain JSONs present (metadata, suspension, tires, aero, drivetrain, balance)
2. Run: python3 claudetunes_cli.py car_data.txt /sessions/SESSION_ID/ → generates setup
3. Trigger qa-validator for physics validation
4. Save to /outputs/ with timestamp
5. Notify: "Setup v2.0 ready for review"

If any step fails, log the error and flag for manual intervention.
```

**Usage:**
```bash
> Use claudetunes-orchestrator to monitor /sessions/ and auto-process new sessions
```

**Value:**
- Hands-free pipeline after practice session ends
- No manual script execution needed

#### 2B: Real-Time Domain Monitoring (Race Engineering)
**Implement:** 5 parallel domain-monitoring subagents

```
.claude/agents/
├── suspension-monitor.md   # Watches suspension.json only
├── tire-monitor.md         # Watches tires.json only
├── aero-monitor.md         # Watches aero.json only
├── drivetrain-monitor.md   # Watches drivetrain.json only
└── balance-monitor.md      # Watches balance.json only
```

**Pattern:** Each subagent:
- Monitors 1 domain JSON (5-10 parameters)
- Uses Haiku model (fast, cheap)
- Reports only anomalies
- Runs in parallel with others

**Example: suspension-monitor.md**
```yaml
---
name: suspension-monitor
description: GT7 suspension telemetry specialist - damping, springs, ARB analysis only
model: haiku  # Fast and cheap for continuous monitoring
tools:
  - Read
  - Bash
---

You are a specialist in Gran Turismo 7 suspension telemetry.

**Your ONLY focus:**
- Damper compression/rebound rates
- Spring frequencies (front/rear)
- Suspension travel (compression/extension)
- Bottoming out detection

**You IGNORE:**
- Tire data (temps, pressures, wear)
- Aerodynamics (downforce, drag)
- Drivetrain (power, wheel spin)

**Report ONLY when you detect:**
- Damping oscillation >10%
- Bottoming events (travel > 95% of range)
- Frequency imbalance >0.3 Hz front/rear
- Suspension binding (zero travel zones)

**Output Format:**
```
Metric | Current Value | Concern Level | Suggested Fix
```
```

**Usage:**
```bash
> Start race-engineer mode for current practice session

# Orchestrator spawns 5 parallel subagents:
├── suspension-monitor → "Front damping oscillating ±18% - HIGH - Stiffen rebound +2"
├── tire-monitor → "FL temp 95°C, 10° over optimal - MEDIUM - Add camber +0.5°"
├── aero-monitor → "Ride height stable - OK"
├── drivetrain-monitor → "Wheel spin detected Turn 3,7,12 - MEDIUM - Diff accel +10"
└── balance-monitor → "Weight transfer forward-biased - LOW - Monitor"

# Main agent synthesizes:
"Front suspension unstable + hot FL tire + wheel spin
 = Front ARB too soft + insufficient camber

Recommendation: +2 clicks front ARB, +0.5° camber FL
Expected gain: 0.2s sector 1"
```

**Value:**
- Real-time lap-by-lap coaching during practice
- <2s latency from telemetry to recommendation
- Parallel analysis (3x faster than sequential)

#### 2C: Quality Assurance Validation (Safety Net)
**Implement:** `qa-validator` subagent

```yaml
# .claude/agents/qa-validator.md
---
name: qa-validator
description: Validates ClaudeTunes setup output against safety and physics rules
model: sonnet  # Needs reasoning for physics validation
tools:
  - Read
---

You validate ClaudeTunes setup recommendations.

Check every generated setup for:
1. Stability index in safe range (-0.90 to -0.40)
2. All adjustments within car's physical ranges
3. Rake rule compliance (front ≤ rear ride height)
4. No extreme/dangerous settings
5. Proper GT7 terminology and formatting

Output: PASS/FAIL with specific violations if any

Example:
✅ PASS - Stability: -0.65, All ranges valid, Rake: +5mm
❌ FAIL - Stability: 0.12 (OVERSTEER DANGER), Rake: -3mm (INVALID)
```

**Value:**
- Never apply unsafe setup to GT7
- Catch physics calculation errors
- Build confidence in automated recommendations

#### 2D: Multi-Session Learning (Long-term Intelligence)
**Implement:** `strategy-analyzer` subagent

```yaml
# .claude/agents/strategy-analyzer.md
---
name: strategy-analyzer
description: Analyzes patterns across multiple ClaudeTunes sessions
model: sonnet  # Needs reasoning for pattern detection
tools:
  - Read
  - Grep
  - Glob
---

You analyze ClaudeTunes output history to find patterns.

Given multiple sessions for the same car/track combination:
1. Compare suspension adjustments across versions
2. Identify consistent trends (always adjusting X in Y direction)
3. Recommend baseline updates to car range files
4. Suggest track-specific starting points

Output: Strategic recommendations for baseline improvements

Example:
"Across 3 sessions at Nürburgring with NSX GT500:
 - Rear ARB consistently needed +3 clicks
 - Front camber always adjusted +0.5°
 - Damping ratios stable

 Recommendation: Update baseline car ranges:
 - Rear ARB: start at +3 for this track
 - Front camber: start at +0.5° higher

 This will reduce iteration time in future sessions (3→2 iterations)"
```

**Value:**
- Continuous improvement across seasons
- Personalized baselines to your driving style
- Reduced iteration time (3 sessions → 2 sessions)

**Timeline:** Week 3-4
**Outcome:** Fully automated telemetry-to-setup pipeline with intelligence

---

## Critical Sequencing

### ❌ WRONG ORDER (Will Fail)
```
1. Build subagents first
   └─ Problem: Subagents have nothing clean to monitor
      (monolithic JSON requires parsing in each subagent)
```

### ✅ CORRECT ORDER (This Plan)
```
1. Build domain JSON architecture (Phase 1)
   └─ Creates clean, focused data sources
2. Build subagents (Phase 2)
   └─ Each subagent monitors its domain JSON
   └─ Parallel processing enabled
   └─ Hyper-focused expertise
```

**Why this matters:**
- **Without domain JSONs:** Subagents must parse entire telemetry structure (inefficient, error-prone)
- **With domain JSONs:** Each subagent reads 1 focused file (fast, clean, parallel)

---

## Code Changes Summary

### Files to Modify
| File | Current | New | Change |
|------|---------|-----|--------|
| `gt7_1r.py` | 880 lines | ~950 lines | +70 (domain JSON writers) |
| `gt7_2r.py` | 983 lines | 0 lines | **-983 (DELETE)** |
| `claudetunes_cli.py` | 1,417 lines | ~1,450 lines | +33 (read domain JSONs) |

**Net Result:** -880 lines of parsing/conversion code

### Files to Create
```
/utils/
├── domain_extractors.py    # Parse UDP → domain structures
└── json_writers.py          # Write/update domain JSONs

/.claude/agents/
├── claudetunes-orchestrator.md    # Workflow automation
├── suspension-monitor.md           # Real-time suspension analysis
├── tire-monitor.md                 # Real-time tire analysis
├── aero-monitor.md                 # Real-time aero analysis
├── drivetrain-monitor.md           # Real-time drivetrain analysis
├── balance-monitor.md              # Real-time balance analysis
├── qa-validator.md                 # Setup validation
└── strategy-analyzer.md            # Multi-session learning
```

---

## Expected Outcomes

### Immediate (Phase 1 Complete)
- ✅ Practice session ends → 6 domain JSONs ready in <1 minute
- ✅ No manual CSV → JSON conversion needed
- ✅ Clean data structure (easy to inspect: `cat suspension.json | jq '.bottoming_events'`)
- ✅ -983 lines of code (delete gt7_2r.py)

### Short-term (Phase 2A-B Complete)
- ✅ Hands-free pipeline (orchestrator auto-processes new sessions)
- ✅ Real-time lap-by-lap coaching during practice (<2s latency)
- ✅ Automatic quality assurance (never apply unsafe setup)
- ✅ Parallel analysis (5 subagents run simultaneously)

### Long-term (Phase 2C-D Complete)
- ✅ Multi-session learning (setup convergence in 1-2 sessions instead of 3+)
- ✅ Personalized baselines (learned from your driving style)
- ✅ Championship preparation (5 tracks analyzed in parallel)
- ✅ Continuous improvement (strategy analyzer finds patterns across seasons)

---

## Testing Strategy

### Phase 1 Validation
```bash
# Test 1: Domain JSON Creation
python3 gt7_1r.py
# Expected: /sessions/SESSION_ID/ contains 6 JSONs

# Test 2: JSON Schema Validation
ls sessions/20251219_test/
# Expected: metadata.json, suspension.json, tires.json, aero.json, drivetrain.json, balance.json

# Test 3: ClaudeTunes Integration
python3 claudetunes_cli.py \
    car_data_with_ranges_MASTER.txt \
    sessions/20251219_test/ \
    -t balanced
# Expected: Setup v2.0 generated successfully

# Test 4: Verify gt7_2r.py No Longer Needed
# Expected: Pipeline works without ever running gt7_2r.py
```

### Phase 2 Validation
```bash
# Test 1: Orchestrator Auto-Processing
> Use claudetunes-orchestrator to monitor /sessions/
# Add new session folder
# Expected: Auto-detects, processes, validates, outputs setup

# Test 2: Real-Time Monitoring
> Start race-engineer mode for current session
# Drive practice laps
# Expected: Lap-by-lap feedback from 5 parallel subagents

# Test 3: QA Validation
> Validate this setup: [paste setup with intentional rake violation]
# Expected: qa-validator flags "FAIL: Rake rule violated"

# Test 4: Multi-Session Learning
> Analyze all NSX GT500 sessions at Yas Marina
# Expected: strategy-analyzer recommends baseline adjustments
```

---

## Migration from Old Architecture

### Converting Existing CSV Sessions
**Optional Migration Script:** `convert_csv_to_domain_jsons.py`

```python
#!/usr/bin/env python3
"""
Convert legacy CSV sessions to domain JSON format
Usage: python3 convert_csv_to_domain_jsons.py <csv_session_folder>
"""
import sys
import os

def convert_session(csv_folder):
    """Convert CSV session to domain JSONs"""
    # 1. Find CSV files in folder
    # 2. Run gt7_2r.py one last time to get monolithic JSON
    # 3. Split monolithic JSON into 6 domain JSONs
    # 4. Write to new session folder
    pass

if __name__ == '__main__':
    convert_session(sys.argv[1])
```

**Or:** Just start fresh with new sessions (old CSVs remain in legacy_files/)

---

## Key Decision Points

### Question 1: When to write domain JSONs?
**Option A:** Per-packet (real-time updates)
**Option B:** Per-lap (batch write at lap completion)
**Option C:** Hybrid (metadata/suspension real-time, rest per-lap)

**Recommendation:** Option B (per-lap) for simplicity, move to Option C if real-time monitoring proves valuable.

### Question 2: JSON update strategy?
**Option A:** Overwrite entire JSON each lap
**Option B:** Append to arrays (accumulate over session)
**Option C:** Hybrid (metadata overwrite, telemetry append)

**Recommendation:** Option C - metadata tracks current state, telemetry accumulates history.

### Question 3: Backward compatibility?
**Option A:** Maintain CSV output alongside JSON (dual mode)
**Option B:** Pure JSON (eliminate CSV entirely)

**Recommendation:** Option B (pure JSON) - clean break, simpler codebase.

---

## Related Documentation

- **Integration Strategy:** `ClaudeTunes_Subagent_Integration_Options.md` (5 patterns)
- **Subagent Technical Guide:** `Claude_Code_Subagents_Summary.md` (implementation details)
- **Project Instructions:** `CLAUDE.md` (v8.5.3a workflow reference)
- **YAML Protocol:** `ClaudeTunes v8.5.3b.yaml` (physics rules)

---

## Next Actions

### Immediate (This Week)
1. **Create `/utils/` directory structure**
2. **Write domain extractor functions** (`domain_extractors.py`)
3. **Write JSON update utilities** (`json_writers.py`)
4. **Modify `gt7_1r.py`** to use domain JSON writers

### Short-term (Next 2 Weeks)
5. **Update `claudetunes_cli.py`** to read domain JSONs
6. **Test with 1 practice session** (validate end-to-end)
7. **Delete `gt7_2r.py`** and update docs
8. **Create first subagent** (`claudetunes-orchestrator.md`)

### Long-term (Month 1-2)
9. **Implement real-time monitoring subagents** (5 domain monitors)
10. **Add quality assurance validation** (`qa-validator.md`)
11. **Build multi-session learning** (`strategy-analyzer.md`)
12. **Test with championship preparation** (5 tracks in parallel)

---

## Success Criteria

### Phase 1 Complete When:
- [x] New practice session → 6 domain JSONs created automatically
- [x] `gt7_2r.py` deleted (no longer needed)
- [x] `claudetunes_cli.py` generates setups from domain JSONs
- [x] No CSV files in pipeline (pure JSON)

### Phase 2 Complete When:
- [x] Practice session ends → setup ready in <1 minute (no manual steps)
- [x] Real-time monitoring provides lap-by-lap feedback
- [x] QA validation catches 100% of physics violations
- [x] Multi-session learning reduces iterations (3 → 2 sessions)

---

**Session Status:** Architecture designed, implementation roadmap defined
**Next Session:** Begin Phase 1 implementation (domain extractors)
**Timeline:** Phase 1 (2 weeks), Phase 2 (4 weeks), Full deployment (6 weeks)

---

*This architecture enables ClaudeTunes v9.0 - the first fully automated, intelligent race engineering system for GT7.*
