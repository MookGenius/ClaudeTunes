# Phase 1: Domain JSON Architecture - Design Decisions

**Date:** 2025-12-30
**Status:** Finalized - Ready for Implementation

---

## Executive Summary

Phase 1 will transform ClaudeTunes from a 3-step pipeline (UDP → CSV → JSON → Setup) to a clean 2-step pipeline (UDP → Domain JSONs → Setup). This eliminates 983 lines of parsing code and creates the foundation for Phase 2 subagent integration.

---

## Key Architectural Decisions

### Decision 1: File Naming Convention ✅

**Question:** What should the domain JSON files be named?

**Answer:** Simple names (no prefix)

**Rationale:**
- Files are already organized in session-specific directories
- Directory structure provides all needed context
- Shorter, cleaner code throughout Phase 1 and Phase 2
- Follows industry best practices for organized directories

**Implementation:**
```
/sessions/TIMESTAMP/
├── metadata.json       ← Session info, car, track
├── suspension.json     ← Travel, bottoming, ride height
├── tires.json          ← Temps, slip, wear
├── aero.json           ← Ride height, downforce, rake
├── drivetrain.json     ← Power delivery, wheel spin
└── balance.json        ← Weight transfer, stability
```

---

### Decision 2: JSON Update Frequency ✅

**Question:** How often should gt7_1r.py update the domain JSON files during telemetry capture?

**Answer:** Every 10 packets (~6 Hz, ~167ms latency)

**Rationale:**
- Near-real-time updates for future subagent monitoring
- Reasonable disk I/O (36 writes/second vs 360 for every packet)
- Good balance of freshness vs performance
- Minimal data loss if crash (max 10 packets)
- Foundation for Phase 2 live coaching capability

**Implementation:**
```python
packet_counter = 0
WRITE_INTERVAL = 10  # Write every 10 packets

while capturing:
    packet = receive_udp()
    update_domain_buffers(packet)

    packet_counter += 1
    if packet_counter >= WRITE_INTERVAL:
        write_all_domain_jsons()
        packet_counter = 0
```

**Performance:**
- Update frequency: ~6 Hz
- I/O load: 36 writes/second (6 files × 6 Hz)
- Latency: ~167ms (effectively real-time)
- Crash safety: Lose max 10 packets (167ms of data)

---

### Decision 3: Sample Retention Strategy ✅

**Question:** Should domain JSONs store only aggregated stats, or also include raw sample data?

**Answer:** Stats + last 10 samples (hybrid approach)

**Rationale:**
- **Agents need context** - 10 samples = ~1.5 seconds of data for trend detection
- **Pattern recognition** - Enough to detect oscillations, spikes, anomalies
- **Lightweight reasoning** - Small enough for agents to parse quickly (<2s for all 6 JSONs)
- **Context without overwhelm** - Fits well in agent context windows
- **Distinguishes spikes from sustained behavior** - Critical for accurate analysis

**Implementation:**
```json
{
  "travel_mm": {
    "FL": {
      "avg": 32.5,
      "max": 45.2,
      "min": 18.3,
      "samples": [32, 35, 38, 33, 36, 34, 37, 35, 33, 36]
    },
    "FR": { ... },
    "RL": { ... },
    "RR": { ... }
  }
}
```

**What agents can deduce from this:**
- "Travel is stable around 32-38mm (consistent driving)"
- "Max of 45.2mm was a spike, not sustained"
- "No trending up/down (samples oscillate around avg)"

---

### Decision 4: Session Folder Naming ✅

**Question:** How should session folders be named?

**Answer:** Timestamp only (YYYYMMDD_HHMMSS)

**Rationale:**
- **100% consistent format** - Every folder has identical structure
- **Trivial parsing** for agents - Simple regex: `\d{8}_\d{6}`
- **Auto-sorted chronologically** - Built-in ordering
- **Single source of truth pattern** - Folder = ID, metadata.json = context
- **No special character issues** - Unlike car names with spaces, dashes, quotes
- **Agent-friendly** - Agents read metadata.json for car/track info, not folder names

**Implementation:**
```
/sessions/20251230_173045/         ← Timestamp = unique ID
    ├── metadata.json              ← Car: "Ferrari LaFerrari", Track: "Nurburgring"
    ├── suspension.json
    ├── tires.json
    ├── aero.json
    ├── drivetrain.json
    └── balance.json
```

**Agent workflow:**
```python
# List all sessions (auto-sorted by timestamp)
sessions = glob("/sessions/*/metadata.json")

# Filter by car
for session in sessions:
    meta = json.load(session)
    if meta['car']['name'] == 'Ferrari LaFerrari':
        analyze_session(session)
```

---

## Domain JSON Schema Summary

Based on these decisions, here's the final schema structure:

### metadata.json
```json
{
  "session_id": "20251230_173045",
  "car": {
    "code": 3462,
    "name": "2013 Ferrari LaFerrari",
    "classification": "street_hypercar"
  },
  "track": {
    "name": "Nurburgring Nordschleife",
    "type": "balanced"
  },
  "session_summary": {
    "start_time": "2025-12-30T17:30:45Z",
    "total_laps": 5,
    "laps_analyzed": 5,
    "valid_data_points": 2847,
    "data_quality_pct": 98.5
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
    "FR": { ... },
    "RL": { ... },
    "RR": { ... }
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
    "FL": {
      "inner": {"avg": 85.2, "max": 92.5, "min": 78.3, "samples": [...]},
      "middle": {"avg": 87.5, "max": 94.2, "min": 80.1, "samples": [...]},
      "outer": {"avg": 89.8, "max": 96.8, "min": 82.5, "samples": [...]}
    },
    "FR": { ... },
    "RL": { ... },
    "RR": { ... }
  },
  "slip_ratio": {
    "FL": {"avg": 1.08, "max": 1.25, "events": 3, "samples": [...]},
    "FR": { ... },
    "RL": { ... },
    "RR": { ... }
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
    "rake_mm": 5.3,
    "samples_front": [...],
    "samples_rear": [...]
  },
  "downforce_estimate_lbs": {
    "total": 825,
    "source": "car_database_lookup"
  },
  "speed_correlation": {
    "high_speed_zones_mph": [185, 192, 188, 195],
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
    "avg_rpm": 6450,
    "samples_throttle": [...],
    "samples_rpm": [...]
  },
  "wheel_spin_events": {
    "total_count": 12,
    "FL_count": 0,
    "FR_count": 0,
    "RL_count": 6,
    "RR_count": 6,
    "severity_avg": 1.15
  },
  "gear_usage": {
    "1": 3,
    "2": 8,
    "3": 15,
    "4": 22,
    "5": 18,
    "6": 12
  }
}
```

### balance.json
```json
{
  "weight_transfer": {
    "lateral_g": {
      "avg": 1.25,
      "max": 1.82,
      "min": 0.15,
      "samples": [...]
    },
    "longitudinal_g": {
      "avg": 0.85,
      "max_braking": -1.45,
      "max_accel": 1.12,
      "samples": [...]
    }
  },
  "stability_metrics": {
    "understeer_events": 3,
    "oversteer_events": 1,
    "balance_bias": "slight_understeer"
  },
  "corner_analysis": {
    "entry_stability": "good",
    "mid_corner_grip": "excellent",
    "exit_traction": "moderate"
  }
}
```

---

## Benefits of This Architecture

### For Phase 1
1. ✅ Eliminates entire CSV parsing step (-983 lines)
2. ✅ Clean 2-step pipeline (UDP → JSONs → Setup)
3. ✅ Easier debugging (each domain isolated)
4. ✅ Faster execution (skip parsing step)

### For Phase 2 (Subagent Integration)
1. ✅ **Parallel processing** - 5 domain monitors read 5 JSONs simultaneously
2. ✅ **Real-time capable** - 6 Hz updates enable live coaching
3. ✅ **Agent-friendly parsing** - Consistent structure, rich context
4. ✅ **Pattern recognition ready** - 10 samples perfect for trend detection
5. ✅ **Clean data boundaries** - Each domain owns its data

### For Phase 3 (Screenshot Integration)
1. ✅ **Extensible** - Easy to add new fields to domain JSONs
2. ✅ **Correlation ready** - Spatial data can reference domain JSONs
3. ✅ **MoTeC-like analysis** - Professional-grade data structure

---

## Implementation Plan

### Step 1.1: Create Domain Extractors
Build `utils/domain_extractors.py` with 6 classes:
- `MetadataExtractor`
- `SuspensionExtractor`
- `TireExtractor`
- `AeroExtractor`
- `DrivetrainExtractor`
- `BalanceExtractor`

### Step 1.2: Create JSON Writers
Build `utils/json_writers.py` with atomic writing:
- Write to temp file → rename (crash-safe)
- Incremental updates (append samples, update stats)
- Buffer management (every 10 packets)

### Step 1.3: Modify gt7_1r.py
Replace CSV writing with domain JSON writing:
- Import domain extractors
- Buffer domain data (10 packets)
- Write all 6 JSONs every 10 packets
- Create session folder with timestamp

### Step 1.4: Modify claudetunes_cli.py
Replace monolithic JSON reading with domain JSON reading:
- Modify `phase_a_intake()` to read 6 JSONs
- Keep Phase B/C/D unchanged
- Simplify parsing (pre-structured data)

### Step 1.5: Delete gt7_2r.py
Remove entire CSV → JSON parsing script (-983 lines)

### Step 1.6: Test & Document
- Integration test: UDP → JSONs → Setup
- Unit tests for extractors and writers
- Update README and CLAUDE.md
- Create PHASE1_COMPLETE_SUMMARY.md

---

## Success Criteria

Phase 1 is complete when:
- ✅ gt7_1r.py writes 6 domain JSONs (no CSV)
- ✅ claudetunes_cli.py reads domain JSONs (no monolithic JSON)
- ✅ gt7_2r.py deleted (-983 lines)
- ✅ Integration test passes (same quality setups as current)
- ✅ Session folders have clean structure
- ✅ All existing features work
- ✅ Documentation updated

---

## Next Steps

With architecture finalized, ready to begin implementation:
1. Build `utils/domain_extractors.py`
2. Build `utils/json_writers.py`
3. Test extractors with sample UDP data
4. Modify gt7_1r_phase1.py
5. Test JSON generation
6. Modify claudetunes_cli_phase1.py
7. Integration test
8. Deploy to production

---

**Phase 1 Architecture: Finalized and Ready! 🚀**
