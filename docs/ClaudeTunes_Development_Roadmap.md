# ClaudeTunes Development Roadmap

**Created:** 2025-12-28
**Version:** v8.5.3b
**Status:** Planning Phase

---

## Executive Summary

This roadmap outlines the prioritized development path for ClaudeTunes, ordered by dependencies and architectural impact. The current system is fully functional but has architectural improvements that will enable automation, experimentation, and advanced features.

---

## Current State

| Component | Status | Lines |
|-----------|--------|-------|
| Phase A-D Workflow | 100% complete | 1,761 |
| YAML Protocol | Fully defined | 498 |
| Telemetry Capture | Working | 880 |
| Telemetry Analyzer | Working (legacy) | 983 |

**Key Issue Identified:** The YAML protocol is loaded but values are hardcoded in Python. The protocol serves as documentation rather than the actual source of truth.

---

## Phase 0: YAML-Driven Refactor

**Priority:** HIGHEST (Do First)
**Effort:** Low-Medium
**Blocks:** Everything else benefits from this

| Step | Task | Current Location | Rationale |
|------|------|------------------|-----------|
| 0.1 | Refactor tire compound frequencies to read from YAML | Lines 760-773 | 9 compounds hardcoded |
| 0.2 | Refactor drivetrain bias to read from YAML | Lines 919, 991-996 | FF/FR/MR/RR/AWD hardcoded |
| 0.3 | Refactor CG thresholds to read from YAML | Lines 965-972 | 500mm/400mm thresholds hardcoded |
| 0.4 | Refactor downforce database to read from YAML | Lines 23-30 | GT7_DOWNFORCE_DATABASE class constant |
| 0.5 | Refactor differential baselines to read from YAML | Lines 32-38 | DIFFERENTIAL_BASELINES class constant |
| 0.6 | Refactor physics thresholds to read from YAML | Various | Bottoming, travel, slip thresholds scattered |
| 0.7 | Validate & test all refactored values | - | Ensure parity with current behavior |

### Why First
- Low risk, high value
- Makes the protocol *actually* the source of truth
- Enables tuning experimentation without code changes
- No external dependencies
- Clean foundation before larger changes

### Example Transformation
```python
# Before (current - hardcoded)
compound_map = {
    'Racing Hard': 2.85,
    'Racing Soft': 3.40,
    ...
}

# After (YAML-driven)
compound_data = self.protocol['phase_B']['base_frequency_by_compound']
compound_map = {k.replace('_', ' '): v['hz'] for k, v in compound_data.items()}
```

---

## Phase 1: Domain JSON Architecture

**Priority:** HIGH
**Effort:** Medium
**Blocks:** All subagent work

| Step | Task | Rationale |
|------|------|-----------|
| 1.1 | Create `/utils/domain_extractors.py` | Parse UDP packets into domain structures |
| 1.2 | Create `/utils/json_writers.py` | Write/update domain JSONs atomically |
| 1.3 | Modify `gt7_1r.py` to output 6 domain JSONs | metadata, suspension, tires, aero, drivetrain, balance |
| 1.4 | Modify `claudetunes_cli.py` to read domain JSONs | Replace monolithic JSON parsing |
| 1.5 | Delete `gt7_2r.py` | No longer needed (-983 lines) |
| 1.6 | Update documentation | Reflect new architecture |

### Architecture Change
```
Current (Inefficient):
gt7_1r.py → CSV → gt7_2r.py → monolithic JSON → CLI

Proposed (Clean):
gt7_1r.py → 6 domain JSONs → CLI
```

### Domain JSON Files
1. `metadata.json` - Session info, car name, track
2. `suspension.json` - Travel, compression, bottoming
3. `tires.json` - Temps, slip, wear
4. `aero.json` - Downforce, drag, ride height effects
5. `drivetrain.json` - Power delivery, wheel spin
6. `balance.json` - Weight transfer, stability metrics

### Why Second
- Requires stable CLI (Phase 0)
- Enables real-time domain monitoring
- Enables parallel subagent processing
- Simplifies pipeline: UDP → JSONs → Setup
- Net code reduction: -983 lines

---

## Phase 2: Subagent Integration

**Priority:** MEDIUM-HIGH
**Effort:** Medium-High
**Requires:** Phase 1 complete

### Phase 2A: Orchestrator Subagent

| Step | Task | Rationale |
|------|------|-----------|
| 2A.1 | Create `.claude/agents/claudetunes-orchestrator.md` | Monitor `/sessions/` for new data |
| 2A.2 | Implement auto-pipeline execution | Hands-free workflow after practice |

**Outcome:** Drop telemetry files → Setup sheet appears automatically

### Phase 2B: QA Validator Subagent

| Step | Task | Rationale |
|------|------|-----------|
| 2B.1 | Create `.claude/agents/qa-validator.md` | Safety checks on every setup |
| 2B.2 | Implement all safety constraint checks | Stability, rake, ranges, danger flags |

**Safety Checks:**
- Stability index in safe range (-0.90 to -0.40)
- Rake rule enforced (front ≤ rear)
- No danger flags (oversteer/extreme understeer)
- All values within car_data ranges
- Proper GT7 formatting

### Phase 2C: Domain Monitor Subagents

| Step | Task | Focus Area |
|------|------|------------|
| 2C.1 | Create `suspension-monitor.md` | Damping, springs, ARB analysis |
| 2C.2 | Create `tire-monitor.md` | Temps, slip, wear analysis |
| 2C.3 | Create `aero-monitor.md` | Downforce, drag, ride height |
| 2C.4 | Create `drivetrain-monitor.md` | Power delivery, wheel spin |
| 2C.5 | Create `balance-monitor.md` | Weight transfer, stability |

**Outcome:** <2s latency from telemetry to recommendation, parallel analysis

### Phase 2D: Strategy Analyzer Subagent

| Step | Task | Rationale |
|------|------|-----------|
| 2D.1 | Create `.claude/agents/strategy-analyzer.md` | Multi-session learning |
| 2D.2 | Implement pattern recognition | Identify consistent tuning trends |

**Outcome:** Setup convergence in 2 sessions vs 3

### Why Third
- Requires clean domain JSONs (Phase 1)
- Each subagent monitors its specific domain JSON
- Parallel processing enabled by clean architecture

---

## Phase 3: Screenshot Integration

**Priority:** LOWER (Future)
**Effort:** High
**Requires:** Phases 1 & 2 stable

| Step | Task | Rationale |
|------|------|-----------|
| 3.1 | GT7 Data Logger screenshot OCR | Extract visual data from screenshots |
| 3.2 | Spatial correlation with UDP telemetry | Index physics data by track position |
| 3.3 | Corner-specific diagnostics | Move from lap-level to corner-level precision |
| 3.4 | Integration with domain monitors | Feed screenshot insights to subagents |

### Why Last
- Most complex, highest effort
- Requires stable foundation
- Advanced feature, not core functionality
- Professional MoTeC-like analysis capability

---

## Visual Dependency Chart

```
Phase 0: YAML-Driven Refactor
    │
    ▼
Phase 1: Domain JSON Architecture
    │
    ├──────────────────────┐
    ▼                      ▼
Phase 2A: Orchestrator   Phase 2B: QA Validator
    │                      │
    ▼                      ▼
Phase 2C: Domain Monitors (5 parallel)
    │
    ▼
Phase 2D: Strategy Analyzer
    │
    ▼
Phase 3: Screenshot Integration
```

---

## Quick Reference Summary

| Phase | Name | Priority | Effort | Key Outcome |
|-------|------|----------|--------|-------------|
| **0** | YAML-Driven | HIGHEST | Low-Med | Protocol becomes source of truth |
| **1** | Domain JSON | HIGH | Medium | Clean 2-step pipeline, delete gt7_2r.py |
| **2A** | Orchestrator | MED-HIGH | Low | Hands-free workflow |
| **2B** | QA Validator | MED-HIGH | Low | Safety net on all setups |
| **2C** | Domain Monitors | MEDIUM | Medium | Real-time analysis |
| **2D** | Strategy Analyzer | MEDIUM | Medium | Multi-session learning |
| **3** | Screenshots | LOWER | High | Corner-specific diagnostics |

---

## Expected Outcomes

### After Phase 0
- Protocol is true source of truth
- Easy experimentation with physics values
- No code changes needed for tuning adjustments

### After Phase 1
- Clean 2-step pipeline (UDP → JSONs → Setup)
- 983 lines deleted (gt7_2r.py removed)
- Ready for subagent integration

### After Phase 2
- Fully automated workflow
- Real-time coaching during practice
- Multi-session learning
- Safety validation on every setup

### After Phase 3
- Corner-specific problem diagnosis
- Professional-grade analysis
- Spatial physics correlation

---

## Notes

- Each phase builds on the previous
- Do not skip phases (especially 0 and 1)
- Phase 0 is low-risk and provides immediate value
- Phases 2A-2D can be done incrementally
- Phase 3 is optional advanced functionality

---

## Related Documentation

- [CLAUDE.md](../CLAUDE.md) - AI assistant development guide
- [ClaudeTunes v8.5.3b.yaml](../ClaudeTunes%20v8.5.3b.yaml) - Complete protocol specification
- [session_2025_12_19_domain_json_architecture.md](session_2025_12_19_domain_json_architecture.md) - Domain JSON details
- [ClaudeTunes_Subagent_Integration_Options.md](ClaudeTunes_Subagent_Integration_Options.md) - Subagent patterns
