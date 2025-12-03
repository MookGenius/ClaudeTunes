# ClaudeTunes Project Status & Roadmap

**Date:** 2025-12-02
**Current Version:** v8.5.3b (stable, production-ready)
**Status:** Active development, stable core with planned v2 enhancements

---

## Executive Summary

ClaudeTunes is a Gran Turismo 7 physics-based suspension tuning toolkit that converts telemetry data into optimized vehicle setups. The current v1 implementation is fully functional with hardcoded physics constants. The project is preparing for a v2 architecture that will separate configuration from code logic.

---

## Current Architecture (v1 - Production)

### ✅ What Works Today

**Core Functionality:**
- Phase A→B→C→D workflow fully implemented
- OptimumG physics-based damping calculations
- Chassis bottoming vs suspension maxed detection (15mm threshold)
- AWD/4WD front differential support
- Power-to-weight spring rate calculations
- Telemetry reconciliation and anomaly detection
- Multi-format telemetry support (gt7_1r.py and gt7_2r.py outputs)

**File Structure:**
```
ClaudeTunes/
├── claudetunes_cli.py              # Main script (1697 lines) - STABLE
├── gt7_1r.py                       # Real-time telemetry logger (880 lines)
├── gt7_2r.py                       # Telemetry analyzer (983 lines)
├── CLAUDE.md                       # AI assistant development guide
├── yaml files/
│   ├── ClaudeTunes v8.5.3b.yaml    # Reference protocol (497 lines)
│   └── ClaudeTunes v8.5.3RR.yaml   # RR Edition (597 lines)
├── docs/                           # Extensive documentation
├── templates/                      # Car data templates
├── sessions/                       # Generated setup sheets
└── test_all_features.sh            # Automated testing
```

### ⚠️ Current Limitations

**Hardcoded Architecture:**
- All physics constants embedded in Python code
- YAML files are documentation-only (not read at runtime)
- Parameter tuning requires code edits
- Cannot A/B test different physics protocols easily
- Git history mixes algorithm changes with constant tuning

**Example of Current Approach:**
```python
# claudetunes_cli.py line 760-773 (HARDCODED)
def _get_base_frequency(self):
    compound_map = {
        'Racing Hard': 2.85,
        'Racing Medium': 3.15,
        # ... all values in Python
    }
    return compound_map[compound]
```

**YAML exists but is ignored at runtime:**
```yaml
# yaml files/ClaudeTunes v8.5.3b.yaml (REFERENCE ONLY)
phase_B:
  base_frequency_by_compound:
    Racing_Hard: {hz: 2.85, grip: 1.12}  # ← NOT READ BY v1
```

---

## Recent Session Summary

### Discussion Topics Covered

1. **Project Status Assessment**
   - Confirmed v1 is stable and production-ready
   - Identified that v2 (attempted YAML-driven refactoring) was incomplete and broken
   - Deleted non-functional v2 file

2. **YAML Architecture Clarification**
   - Confirmed v1 uses hardcoded values, YAML is documentation only
   - YAML was used as reference to BUILD v1, but not used AT RUNTIME
   - Reviewed `docs/yaml_refactoring_decision.md` proposal

3. **YAML File Comparison**
   - Compared v8.5.3b vs v8.5.3RR editions
   - RR edition adds 100 lines of Porsche/rear-engine specific guidance
   - Both functionally similar, RR has enhanced documentation
   - **Key difference:** Case sensitivity (`phase_A` vs `phase_a`)

4. **Bottoming Detection Logic**
   - Confirmed chassis bottoming vs suspension maxed logic EXISTS in v1 Python code
   - RR edition YAML documents what's already implemented
   - 15mm threshold fully functional in current version

5. **Git Organization**
   - Reorganized YAML files into `yaml files/` directory
   - Moved `CLAUDE.md` to root for visibility
   - Committed 11 files (2055+ lines) to GitHub
   - Clean separation of documentation from code

---

## Near-Term Roadmap for v2

### Phase 1: YAML-Driven Architecture (Immediate Priority)

**Goal:** Separate "what to calculate" (code) from "what values to use" (YAML)

**Benefits:**
- ✅ Rapid parameter experimentation without code changes
- ✅ A/B test different physics protocols side-by-side
- ✅ Version control for physics constants
- ✅ Clean git history (algorithm vs tuning commits)
- ✅ Self-documenting configuration with inline comments

**Implementation Tasks:**

1. **Fix YAML Structure Compatibility** (30 minutes)
   - Standardize case sensitivity (choose `phase_a` or `phase_A`)
   - Ensure Python code and YAML use same key names
   - Add YAML schema validation

2. **Refactor Python to Read from YAML** (2-3 hours)
   - Convert all hardcoded dictionaries to YAML reads
   - Example areas to refactor:
     ```python
     # Before (hardcoded)
     compound_map = {'Racing Hard': 2.85, ...}

     # After (YAML-driven)
     compound_map = self.protocol['phase_b']['base_frequencies']
     ```

   **Functions to Refactor:**
   - `_get_base_frequency()` - Tire compound frequencies
   - `_get_drivetrain_bias()` - Drivetrain multipliers
   - `_get_power_adder()` - Power platform brackets
   - `_get_cg_adjustment()` - CG height thresholds
   - `_calculate_damping()` - Damping ratios & baselines
   - `_calculate_arb()` - ARB multipliers
   - `_calculate_diff_settings()` - Differential baselines
   - `_calculate_camber_toe()` - Alignment baselines
   - Bottoming thresholds (15mm)
   - Track type adjustments

3. **Create Comprehensive YAML Schema** (1-2 hours)
   - Document all physics constants with comments
   - Add validation ranges
   - Include references to testing/validation

   **Example YAML Enhancement:**
   ```yaml
   phase_b:
     base_frequencies:
       Racing_Hard:
         hz: 2.85
         grip: 1.12
         range: "2.2-4.5"
         validated_on:
           - "992 GT3 RS"
           - "NSX-R"
           - "991 GT3"
         note: "Primary competition tire, extensive testing"
   ```

4. **Validation Testing** (1 hour)
   - Run v1 (hardcoded) on test telemetry → save baseline output
   - Run v2 (YAML-driven) with identical values → compare output
   - **Outputs must be byte-for-byte identical**
   - Test cases:
     - 992 GT3 RS (RR layout)
     - NSX-R (MR layout)
     - Multiple tire compounds
     - High-speed vs technical track types
     - Chassis bottoming scenarios

5. **Create Protocol Variants** (ongoing)
   ```
   yaml files/
   ├── ClaudeTunes_v8.5.3b.yaml           # Current stable
   ├── ClaudeTunes_v8.5.3c_experimental.yaml  # Testing new values
   ├── ClaudeTunes_conservative.yaml      # Safe defaults
   ├── ClaudeTunes_aggressive.yaml        # Track-day optimized
   └── ClaudeTunes_RR_edition.yaml        # Porsche/RR specific
   ```

**Usage After v2:**
```bash
# Test different protocols without code changes
python3 claudetunes_cli.py --protocol yaml_files/ClaudeTunes_v8.5.3b.yaml car.txt telem.json
python3 claudetunes_cli.py --protocol yaml_files/ClaudeTunes_aggressive.yaml car.txt telem.json

# A/B test 10 variants in 5 minutes
for config in yaml_files/*.yaml; do
    ./claudetunes_cli.py --protocol $config car.txt telem.json -o results/$(basename $config .yaml).txt
done
```

**Estimated Timeline:** 4-6 hours total development + testing

---

### Phase 2: Enhanced Features (Medium Priority)

**After YAML refactoring is complete:**

1. **Multi-Car Protocol Support**
   - Car-class specific YAML files (Formula, GR3, GR4, Street)
   - Auto-detect car class from telemetry
   - Apply class-specific tuning strategies

2. **Telemetry Enhancement**
   - Improve gt7_1r.py capture rate documentation
   - Add 120Hz telemetry support if GT7 API allows
   - Better FFT analysis for suspension frequencies

3. **Setup Iteration Workflow**
   - Track setup version history (v1.0 → v2.0 → v3.0)
   - Compare before/after telemetry
   - Automated "convergence detection" (when gains < 0.1s)

4. **Advanced Diagnostics**
   - Slip angle estimation improvements
   - Platform dynamics scoring
   - Predictive lap time improvements

---

### Phase 3: Polish & Distribution (Long-Term)

1. **User Experience**
   - Interactive setup wizard
   - Web-based telemetry viewer
   - Setup comparison tool

2. **Documentation**
   - Video tutorials
   - Setup gallery (proven configurations)
   - Track-specific guides

3. **Community**
   - Share validated YAML protocols
   - Leaderboard of fastest setups
   - GT7 update tracking

---

## Key Decisions & Rationale

### ✅ Decisions Made

1. **Keep v1 as stable baseline**
   - Don't break what works
   - v2 must match v1 output exactly before experimenting

2. **Delete broken v2 attempt**
   - Had case sensitivity bugs (`phase_b` vs `phase_B`)
   - Wrong key names (`base_frequencies` vs `base_frequency_by_compound`)
   - Never validated against actual YAML structure

3. **Organize YAML files into subdirectory**
   - Cleaner root directory
   - Room for multiple protocol variants
   - Clear separation from code

4. **YAML-driven architecture is next priority**
   - Approved in `docs/yaml_refactoring_decision.md`
   - Clear benefits for parameter tuning
   - Low risk (can validate byte-for-byte identical output)

### 📋 Open Questions

1. **Case sensitivity standard?**
   - Current YAML has `phase_B` (capital)
   - RR edition has `phase_a` (lowercase)
   - **Recommendation:** Choose one and standardize

2. **Multiple YAML file support?**
   - Allow `--protocol` to accept multiple files?
   - Merge/override strategy?
   - **Recommendation:** Start with single-file, add multi-file later

3. **YAML validation?**
   - Add schema validation on load?
   - Catch typos/missing keys early?
   - **Recommendation:** Yes, using pyyaml + custom validator

---

## Testing Strategy

### Current Test Coverage
- ✅ `test_all_features.sh` - Automated feature testing
- ✅ Manual validation with known cars
- ✅ Sample telemetry data included

### v2 Testing Requirements

**Phase 1: YAML Refactoring Validation**
```bash
# Test 1: Byte-for-byte identical output
python3 claudetunes_cli.py car.txt telem.json > v1_output.txt
python3 claudetunes_cli_v2.py --protocol yaml_files/ClaudeTunes_v8.5.3b.yaml car.txt telem.json > v2_output.txt
diff v1_output.txt v2_output.txt  # Must be IDENTICAL

# Test 2: All tire compounds
for compound in "Racing Hard" "Racing Medium" "Racing Soft"; do
    # Test each compound
done

# Test 3: All drivetrain types
for dt in FF FR MR RR AWD; do
    # Test each drivetrain
done

# Test 4: Track type variations
for track in balanced high_speed technical; do
    # Test each track type
done

# Test 5: Bottoming scenarios
# - Chassis bottoming (min_body_height < 15mm)
# - Suspension maxed (travel > 280mm but body_height OK)
```

**Phase 2: Protocol Variant Testing**
- Create conservative vs aggressive YAML variants
- Measure lap time differences
- Validate stability indices in safe ranges

---

## Performance Expectations

### Current v1 Performance
- **Frequency Corrections:** 0.3-2.0s per lap
- **Drivetrain Architecture Fixes:** 2.0-5.0s (when bias was wrong)
- **Ride Height Optimization:** 0.3-0.8s
- **Track-Type Optimization:** 0.2-0.5s
- **Three-Session Convergence:** 1.5-4.0s total improvement

### v2 Goals
- ✅ Maintain identical performance to v1 initially
- ✅ Enable rapid experimentation to find better constants
- ✅ Target additional 0.2-0.5s through optimized protocols

---

## Development Environment

### Requirements
```bash
# Python 3.7+
pip install pycryptodome numpy pyyaml

# Optional: For development
pip install pytest black pylint
```

### Running Tests
```bash
# Full feature test
./test_all_features.sh

# Quick validation
python3 claudetunes_cli.py templates/car_data_with_ranges_MASTER.txt examples/sample_telemetry.json
```

### Git Workflow
```bash
# Current stable version
git checkout main

# Future v2 development
git checkout -b feature/yaml-driven-architecture

# Test changes
./test_all_features.sh

# Commit with detailed messages
git commit -m "Refactor: Convert tire compound frequencies to YAML-driven

- Move hardcoded compound_map to YAML protocol
- Add validation for missing compounds
- Maintain backward compatibility with v1

YAML Reference: phase_b.base_frequencies
Tested: All 9 tire compounds, byte-for-byte identical output"
```

---

## References

### Key Documentation Files
- `CLAUDE.md` - AI assistant development guide (complete protocol coverage)
- `docs/yaml_refactoring_decision.md` - v2 architecture proposal
- `docs/60hz_telemetry_research_summary.md` - GT7 telemetry limitations
- `docs/Porsche setup_Reference.md` - RR platform tuning
- `yaml files/ClaudeTunes v8.5.3b.yaml` - Current physics protocol (497 lines)
- `yaml files/ClaudeTunes v8.5.3RR.yaml` - RR Edition (597 lines)

### External Resources
- OptimumG Racing School - Damping theory
- GT7 Physics Model - ~10% real-world aero effectiveness
- Professional Race Team Data - 996 GT3 Cup baselines

---

## Version History

### v8.5.3b (Current - Stable)
- ✅ Complete Phase A→B→C→D workflow
- ✅ OptimumG physics-based damping
- ✅ Chassis bottoming vs suspension maxed detection
- ✅ AWD/4WD front differential support
- ✅ Power-to-weight spring calculations
- ✅ Multi-format telemetry support
- ⚠️ Hardcoded physics constants (not YAML-driven)

### v8.5.3RR (Variant)
- ✅ All v8.5.3b features
- ✅ Enhanced RR platform documentation
- ✅ Porsche GT3/Cup methodologies
- ✅ Counter-intuitive RR strategies documented
- ℹ️ YAML-only variant (documentation enhancement)

### v2 (Planned - Not Started)
- 🔄 YAML-driven architecture
- 🔄 Runtime protocol selection
- 🔄 A/B testing capability
- 🔄 Parameter versioning
- 🔄 Self-documenting configuration
- ⏳ Target: 4-6 hours development

---

## Success Criteria

### v2 Release Requirements

**Must Have:**
- ✅ Byte-for-byte identical output to v1 with default YAML
- ✅ All hardcoded values moved to YAML
- ✅ YAML schema validation
- ✅ Backward compatibility with existing car_data files
- ✅ All tests passing (test_all_features.sh)
- ✅ Documentation updated (CLAUDE.md, README.md)

**Nice to Have:**
- 📋 Multiple protocol variants included
- 📋 YAML merge/override capability
- 📋 Interactive protocol builder
- 📋 Web-based YAML editor

**Long-Term Goals:**
- 🎯 1000+ validated setups
- 🎯 Community protocol sharing
- 🎯 Track-specific protocol database
- 🎯 AI-assisted protocol optimization

---

## Contact & Contribution

**Repository:** https://github.com/MookGenius/ClaudeTunes
**Current Status:** Active development, stable v1 in production
**Next Milestone:** v2 YAML-driven architecture
**Estimated v2 Release:** TBD (4-6 hours development + validation)

---

**Last Updated:** 2025-12-02
**Document Version:** 1.0
**Author:** Christopher Marino
**AI Assistant:** Claude (Anthropic)

---

## Quick Start for v2 Development

### Step-by-Step Guide

1. **Create feature branch**
   ```bash
   git checkout -b feature/yaml-driven-architecture
   ```

2. **Standardize YAML case sensitivity**
   - Choose `phase_a` or `phase_A` (recommend lowercase)
   - Update all YAML files to match
   - Update Python code to expect chosen case

3. **Refactor first function (proof of concept)**
   ```python
   # Start with _get_base_frequency() as test case
   def _get_base_frequency(self):
       compound_map = self.protocol['phase_b']['base_frequencies']
       # ... rest of logic
   ```

4. **Test proof of concept**
   ```bash
   python3 claudetunes_cli_v2.py --protocol yaml_files/ClaudeTunes_v8.5.3b.yaml \
       templates/car_data_with_ranges_MASTER.txt \
       examples/sample_telemetry.json > test_output.txt

   # Compare to v1
   python3 claudetunes_cli.py \
       templates/car_data_with_ranges_MASTER.txt \
       examples/sample_telemetry.json > v1_output.txt

   diff test_output.txt v1_output.txt  # Should be identical
   ```

5. **Refactor remaining functions systematically**
   - One function at a time
   - Test after each refactoring
   - Commit frequently with clear messages

6. **Final validation**
   ```bash
   ./test_all_features.sh  # All tests must pass
   ```

7. **Merge to main**
   ```bash
   git checkout main
   git merge feature/yaml-driven-architecture
   git push
   ```

---

**Ready to start v2 development whenever you are!** 🚀
