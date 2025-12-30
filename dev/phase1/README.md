# Phase 1: Domain JSON Architecture - Development Workspace

**Created:** 2025-12-30
**Status:** In Progress

---

## Purpose

This directory contains **working copies** of scripts being modified for Phase 1. We do NOT modify `src/` directly until Phase 1 is complete and tested.

---

## Files in This Directory

### Working Copies (Being Modified)
- `gt7_1r_phase1.py` - Copy of `src/gt7_1r.py` (telemetry logger)
- `claudetunes_cli_phase1.py` - Copy of `src/claudetunes_cli.py` (setup generator)

### New Code (Being Created)
- `utils/domain_extractors.py` - Domain extraction classes
- `utils/json_writers.py` - JSON writing utilities

### Documentation
- `PHASE1_STEP_*.md` - Step-by-step progress docs
- `PHASE1_COMPLETE_SUMMARY.md` - Final summary (when done)

### Tests
- `test_domain_extractors.py` - Test domain extraction
- `test_json_writers.py` - Test atomic JSON writing
- `test_integration.py` - End-to-end test (UDP → JSONs → Setup)

---

## What Changes in Phase 1

### gt7_1r.py Changes
**Before:** Writes CSV files from UDP packets
**After:** Writes 6 domain JSON files directly

**Strategy:**
1. Add domain extractor imports
2. Replace CSV writing with JSON writing
3. Organize data by domain (suspension, tires, aero, etc.)

### claudetunes_cli.py Changes
**Before:** Reads monolithic telemetry JSON
**After:** Reads 6 domain JSONs from session folder

**Strategy:**
1. Modify `phase_a_intake()` to read domain JSONs
2. Keep Phase B/C/D unchanged (same workflow)
3. Simplify parsing logic (domain JSONs are pre-structured)

### New Code Created
- **Domain Extractors:** Parse UDP packets into domain structures
- **JSON Writers:** Atomic, crash-safe JSON writing

---

## Phase 1 Goals

1. ✅ Eliminate CSV intermediate format
2. ✅ Delete `gt7_2r.py` (-983 lines)
3. ✅ Create clean domain separation
4. ✅ Enable real-time monitoring (foundation for Phase 2)
5. ✅ Maintain 100% feature parity with current system

---

## Workflow

```
Current (3 steps):
gt7_1r.py → CSV → gt7_2r.py → JSON → claudetunes_cli.py

Phase 1 (2 steps):
gt7_1r_phase1.py → Domain JSONs → claudetunes_cli_phase1.py
```

---

## Deployment Plan

Once Phase 1 is complete and tested:

1. Backup current production files
2. Copy Phase 1 versions to `src/`
3. Copy `utils/` to project root
4. Delete `src/gt7_2r.py`
5. Run integration tests
6. Update documentation

---

## Do NOT Modify

- `src/` directory (production code)
- `config/` directory (YAML protocol)

**All Phase 1 work happens in `dev/phase1/` until deployment!**
