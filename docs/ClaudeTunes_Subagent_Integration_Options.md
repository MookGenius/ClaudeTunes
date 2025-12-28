# ClaudeTunes + Claude Code Subagents - Integration Options

## Key Insight

**ClaudeTunes Python code already works perfectly** - it takes JSON + car data with ranges → produces tuned setup. The question isn't whether to replace this logic, but rather **where subagents add value to the existing pipeline**.

Subagents excel at:
- ✅ Monitoring for new files → triggering workflows
- ✅ Validating data quality → flagging issues  
- ✅ Analyzing patterns → learning over time
- ✅ Coordinating multi-step processes → automation

Subagents **don't replace your Python code** - they **orchestrate around it**.

---

## Current ClaudeTunes Workflow

```
gt7_1r.py → CSV telemetry capture (on Pi)
    ↓ (manual step)
gt7_2r.py → parses CSV → generates JSON
    ↓ (manual step)
ClaudeTunes Python (v8.5.3a) → JSON + car ranges → tuned setup
    ↓
Setup output (ready for GT7)
```

**Pain Points:**
- Manual handoffs between scripts
- No validation of data quality before processing
- No automated triggering
- No learning across sessions

---

## Integration Option 1: Automation Layer

**Goal:** Eliminate manual script execution

```
gt7_1r.py → CSV captured on Pi
    ↓ (automatic - subagent watches)
claudetunes-orchestrator subagent:
    ├── Detects new CSV
    ├── Runs: python3 gt7_2r.py <csv> → JSON
    ├── Runs: python3 claudetunes.py <json> <car_ranges> → setup
    └── Saves output with timestamp
    ↓
Setup ready for review
```

**Subagent Definition:**
```yaml
---
name: claudetunes-orchestrator
description: Automates ClaudeTunes telemetry-to-setup pipeline
model: haiku  # Fast and cheap for workflow automation
tools:
  - Read
  - Bash
  - Write
---

You orchestrate the ClaudeTunes workflow.

When you detect a new CSV in /telemetry/raw/:
1. Run: python3 gt7_2r.py <csv_file> → generates JSON
2. Run: python3 claudetunes.py <json_file> <car_ranges> → generates setup
3. Save to /outputs/ with timestamp
4. Notify: "Session complete - setup ready for review"

If any step fails, log the error and flag for manual intervention.
```

**Usage:**
```bash
# Set it and forget it
> Use claudetunes-orchestrator to monitor /telemetry/raw/ and auto-process any new sessions
```

**Value:**
- No more manual script execution
- Hands-free pipeline after practice session
- You only touch the final setup for review

---

## Integration Option 2: Pre-Processing Quality Gates

**Goal:** Ensure clean data enters ClaudeTunes

```
gt7_1r.py → CSV
    ↓
gt7_2r.py → JSON
    ↓ (NEW: validation before ClaudeTunes)
Domain subagents validate telemetry quality:
    ├── suspension-monitor: "Damping data clean ✓"
    ├── tire-monitor: "FL temp sensor anomaly lap 3 - excluding"
    ├── aero-monitor: "Ride height data valid ✓"
    └── balance-monitor: "Stability calculations look good ✓"
    ↓
ClaudeTunes Python → runs with validated/cleaned JSON
    ↓
Setup output
```

**Subagent Roles:**
- **suspension-monitor**: Validates damping, spring, ARB data
- **tire-monitor**: Checks for sensor anomalies, impossible temps
- **aero-monitor**: Validates downforce/drag consistency
- **balance-monitor**: Checks weight transfer calculations

**Value:**
- Catch bad sensor data before it corrupts setup calculations
- Flag specific laps to exclude
- Higher confidence in ClaudeTunes output

---

## Integration Option 3: Post-Processing Validation

**Goal:** Quality assurance on ClaudeTunes output

```
gt7_1r.py → CSV → gt7_2r.py → JSON
    ↓
ClaudeTunes Python → generates setup
    ↓ (NEW: validation layer)
qa-validator subagent checks:
    ├── Physics: "Stability index -0.65 (safe range) ✓"
    ├── Constraints: "All adjustments within car ranges ✓"
    ├── Safety: "No extreme settings detected ✓"
    └── Format: "GT7 terminology correct ✓"
    ↓
Approved setup (or flagged issues)
```

**Subagent Definition:**
```yaml
---
name: qa-validator
description: Validates ClaudeTunes setup output against safety and physics rules
model: sonnet  # Needs reasoning for physics validation
tools:
  - Read
---

You validate ClaudeTunes setup recommendations.

Check every generated setup for:
1. Stability index in safe range (-0.80 to -0.50)
2. All adjustments within car's physical ranges
3. No extreme/dangerous settings
4. Proper GT7 terminology and formatting
5. Rake rule compliance (front < rear ride height)

Output: PASS/FAIL with specific violations if any
```

**Value:**
- Catch physics calculation errors
- Ensure safe setups before you apply them
- Build confidence in automated recommendations

---

## Integration Option 4: Multi-Session Intelligence

**Goal:** Learn patterns across sessions to improve baselines

```
Session 1: ClaudeTunes → v1.0 setup
    ↓
Session 2: ClaudeTunes → v2.0 setup  
    ↓
Session 3: ClaudeTunes → v3.0 setup
    ↓ (NEW: pattern analysis)
strategy-analyzer subagent:
    "Across 3 sessions at Nürburgring:
     - Rear ARB consistently needed +3 clicks
     - Front camber always adjusted +0.5°
     - Damping ratios stable
     
     Recommendation: Update baseline car ranges:
     - Rear ARB: start at +3 for this track
     - Front camber: start at +0.5° higher
     
     This will reduce iteration time in future sessions"
```

**Subagent Definition:**
```yaml
---
name: strategy-analyzer
description: Analyzes patterns across multiple ClaudeTunes sessions
model: sonnet  # Needs reasoning for pattern detection
tools:
  - Read
  - Grep
---

You analyze ClaudeTunes output history to find patterns.

Given multiple sessions for the same car/track combination:
1. Compare suspension adjustments across versions
2. Identify consistent trends (always adjusting X in Y direction)
3. Recommend baseline updates to car range files
4. Suggest track-specific starting points

Output: Strategic recommendations for baseline improvements
```

**Value:**
- Reduce iteration time (start closer to optimal)
- Build track-specific knowledge base
- Personalize baselines to your driving style

---

## Integration Option 5: Structured Data Pipeline

**Goal:** Eliminate CSV→JSON conversion entirely

```
gt7_1r.py (modified) → writes structured domain JSONs directly
    ↓ (no gt7_2r.py needed)
/telemetry/sessions/SESSION_NAME/
    ├── metadata.json
    ├── suspension.json
    ├── tires.json
    ├── aero.json
    ├── drivetrain.json
    └── balance.json
    ↓
ClaudeTunes Python (modified) → reads domain JSONs directly
    ↓
Setup output
```

**Subagent Role:**
```yaml
---
name: telemetry-splitter
description: Splits monolithic CSV into domain-specific JSONs
model: haiku
tools:
  - Read
  - Write
  - Bash
---

If CSV workflow must be kept for compatibility:
1. Monitor for new CSVs
2. Parse CSV
3. Split by domain (suspension, tires, aero, drivetrain, balance)
4. Write 5 separate JSONs to session folder
5. Trigger ClaudeTunes with structured data
```

**Value:**
- Cleaner data structure
- Easier for domain subagents to analyze
- Parallel processing becomes possible
- Eliminates gt7_2r.py parsing step

---

## Recommended Starting Point

### Phase 1: Simple Orchestration (Immediate Value)
Implement **Option 1** - automation layer with `claudetunes-orchestrator`

**Why:**
- Easiest to implement (doesn't modify existing code)
- Immediate time savings (no manual script execution)
- Low risk (just wraps existing workflow)

**Implementation:**
1. Create `.claude/agents/claudetunes-orchestrator.md`
2. Test with one session
3. Set to monitor mode

### Phase 2: Quality Gates (Build Confidence)
Add **Option 3** - post-processing validation with `qa-validator`

**Why:**
- Builds confidence in automated recommendations
- Catches edge cases/errors
- Minimal code changes

### Phase 3: Learning System (Long-term Value)
Add **Option 4** - multi-session intelligence with `strategy-analyzer`

**Why:**
- Continuous improvement
- Personalization to your driving style
- Reduces iteration time over seasons

---

## Key Decision Points

### Question 1: What's the biggest pain point?
- **Manual script execution?** → Option 1 (Orchestration)
- **Bad telemetry data?** → Option 2 (Pre-validation)
- **Trusting setup output?** → Option 3 (Post-validation)
- **Too many iterations needed?** → Option 4 (Pattern learning)

### Question 2: Where is ClaudeTunes most fragile?
- **Garbage in, garbage out** → Option 2 helps
- **Physics edge cases** → Option 3 helps
- **Not learning from history** → Option 4 helps

### Question 3: What's the manual work you want to eliminate?
If you said: **"The only manual work I want to do is adjust car setup files with ranges"**

Then the answer is: **Option 1 (Orchestration) + Option 3 (Validation)**

This gives you:
```
Practice session ends
    ↓ (automatic)
Subagent detects CSV → runs pipeline → validates output
    ↓
YOU: Review final setup + adjust your preferred ranges → done
```

---

## Architecture Diagram: Recommended Hybrid Approach

```
┌─────────────────────────────────────────────────┐
│ Raspberry Pi (trackside)                        │
│ gt7_1r.py → CSV to network share               │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│ Laptop (Claude Code + ClaudeTunes Python)      │
│                                                 │
│ claudetunes-orchestrator subagent:             │
│   ├── Monitors /telemetry/raw/                 │
│   ├── Detects new CSV                          │
│   ├── Runs gt7_2r.py → JSON                    │
│   ├── Runs claudetunes.py → setup v2.0         │
│   └── Triggers validation                       │
│                                                 │
│ qa-validator subagent:                          │
│   ├── Checks physics (stability index)         │
│   ├── Validates constraints (ranges)           │
│   ├── Safety checks (no extremes)              │
│   └── Approves or flags issues                 │
│                                                 │
│ Output: /outputs/SESSION_setup_v2.md            │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│ YOU (only manual step)                          │
│ Review setup → adjust ranges → apply to GT7    │
└─────────────────────────────────────────────────┘
```

---

## Next Steps

1. **Decide which pain point to solve first** (see Question 1 above)
2. **Create the corresponding subagent(s)** in `.claude/agents/`
3. **Test with one historical session** to validate behavior
4. **Deploy to monitor mode** for automatic processing
5. **Iterate based on results**

---

## Key Reminder

**Subagents don't replace ClaudeTunes Python** - they make it fully automated.

Your Python code is the **engine**.  
Subagents are the **automation layer** around it.

You keep doing what you do best (tuning car ranges).  
Subagents handle everything else (monitoring, triggering, validating).

---

**Document Created:** 2024-12-17  
**For:** ClaudeTunes v8.5.3a+ Integration Planning  
**Status:** Decision Framework - Implementation Pending
