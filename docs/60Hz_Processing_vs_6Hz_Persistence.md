# 60Hz Processing vs 6Hz Persistence Architecture

**Date:** 2025-12-30
**Context:** ClaudeTunes Phase 1 + 60Hz Telemetry Research Integration
**Key Insight:** Process at 60Hz internally, persist summaries at 6Hz

---

## TL;DR - The Goldmine Discovery

We can implement **all 23 professional race engineering metrics** from the 60Hz telemetry research **WITHOUT changing the current 6Hz write architecture**!

**The Pattern:**
- ✅ **Receive from GT7:** 60 Hz (every ~16.67ms)
- ✅ **Process extractors:** 60 Hz (every UDP packet)
- ✅ **Update internal buffers:** 60 Hz (histograms, ZCR, etc.)
- ✅ **Write to disk:** 6 Hz (every 10th packet = 166.7ms)

**Why This Works:**
Professional metrics like damper velocity histograms, zero-crossing rate, and G-G diagrams need to **see** 60Hz data, but only need to **output** summary statistics at 6Hz.

---

## Current Phase 1 Architecture (As Built)

### Data Flow

```
GT7 UDP Packets @ 60 Hz (PlayStation)
    ↓ every ~16.67ms
gt7_1r_phase1.py (UDP Listener)
    ↓ while True loop receives at 60 Hz
    ↓ processes every packet
Domain Extractors (6 extractors)
    ↓ extract() called at 60 Hz
    ↓ BUT...
BufferedDomainWriter (buffer_size=10)
    ↓ writes to disk every 10th packet
Domain JSON files
    ↓ updated at 6 Hz (every 166.7ms)
```

### Key Code Reference

**gt7_1r_phase1.py:263**
```python
# Buffered JSON writer (writes every 10 packets)
domain_writer = BufferedDomainWriter(session_folder, buffer_size=10)
```

**gt7_1r_phase1.py:830-839** (inside while True loop)
```python
# Phase 1: Extract all 6 domains from packet
metadata = metadata_extractor.extract(ddata, dt_now)      # Called @ 60 Hz
suspension = suspension_extractor.extract(ddata)          # Called @ 60 Hz
tires = tire_extractor.extract(ddata)                     # Called @ 60 Hz
aero = aero_extractor.extract(ddata, car_code)           # Called @ 60 Hz
drivetrain = drivetrain_extractor.extract(ddata)         # Called @ 60 Hz
balance = balance_extractor.extract(ddata)               # Called @ 60 Hz

# Update buffered writer (writes every 10th call)
domain_writer.update_domain('metadata', metadata)        # Writes @ 6 Hz
```

### Current Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| UDP Receive Rate | 60 Hz | GT7 sends at 60 FPS |
| Extractor Call Rate | 60 Hz | `extract()` methods called every packet |
| Disk Write Rate | 6 Hz | Every 10 packets (buffer_size=10) |
| JSON Update Interval | 166.7 ms | Sufficient for human perception |
| Disk I/O Load | Low | ~36 JSON writes per 6-file set per minute |

---

## The 60Hz Research Challenge

The [60Hz Telemetry Research Summary](./60hz_telemetry_research_summary.md) identified **23 high-value metrics** that work at 60Hz without FFT:

1. **Platform Dynamics** - Roll/pitch/heave angles
2. **Damper Velocity Histograms** ⭐ - Industry standard (MoTeC/AiM)
3. **G-G Diagram** - Grip utilization %
4. **Zero-Crossing Rate** ⭐ - Frequency validation without FFT
5. **Lateral Load Transfer Distribution (LLTD)**
6. **Corner Phase Detection**
7. **Plus 17 more...**

**The Question:** Do we need to change to 60Hz disk writes to implement these?

**The Answer:** NO! ✅

---

## Two Implementation Options

### Option 1: Internal 60Hz Buffers ⭐ (RECOMMENDED)

**Architecture:**
```python
class SuspensionExtractor:
    def __init__(self):
        # EXISTING: 6Hz output buffers (for JSON writes)
        self.fl_buffer = StatBuffer(10)  # Last 10 writes @ 6Hz

        # NEW: 60Hz internal accumulators
        self.fl_60hz_samples = deque(maxlen=180)  # 3 seconds @ 60Hz
        self.damper_histogram_fl = DamperHistogram()  # Accumulates ALL samples
        self.zcr_tracker = ZeroCrossingRateTracker()  # Needs 60Hz precision

        # State tracking for derivatives
        self.prev_suspension = {'FL': 0, 'FR': 0, 'RL': 0, 'RR': 0}
        self.prev_time = dt.now()

    def extract(self, ddata: bytes) -> Dict[str, Any]:
        """Called EVERY packet @ 60 Hz"""

        # Parse current suspension travel
        susp_fl = struct.unpack('f', ddata[0xC4:0xC8])[0] * 1000  # mm

        # ═══════════════════════════════════════════════════════
        # 60Hz PROCESSING (happens every packet, 60x/second)
        # ═══════════════════════════════════════════════════════
        now = dt.now()
        dt_sec = (now - self.prev_time).total_seconds()

        if dt_sec > 0:
            # Calculate damper velocity @ 60Hz
            vel_fl = (susp_fl - self.prev_suspension['FL']) / dt_sec

            # Add to 60Hz accumulator (called 60x/second!)
            self.damper_histogram_fl.add_sample(vel_fl)

            # Add to 60Hz sample buffer
            self.fl_60hz_samples.append(susp_fl)

            # Update ZCR tracker @ 60Hz
            heave = (susp_fl + susp_fr + susp_rl + susp_rr) / 4
            self.zcr_tracker.update(heave)

        self.prev_suspension['FL'] = susp_fl
        self.prev_time = now

        # ═══════════════════════════════════════════════════════
        # 6Hz PERSISTENCE (return summary, written every 10th packet)
        # ═══════════════════════════════════════════════════════
        return {
            'travel_mm': {
                'FL': self.fl_buffer.get_stats()  # 6Hz stats
            },

            # NEW: 60Hz metric summaries (written at 6Hz)
            'damper_velocity': {
                'FL': {
                    'current_mm_s': vel_fl,
                    # This distribution contains ALL 60Hz samples!
                    'histogram': self.damper_histogram_fl.get_distribution(),
                    'operating_range': self.damper_histogram_fl.get_operating_range()
                }
            },

            'frequency_validation': {
                # ZCR calculated from 180 samples @ 60Hz
                'observed_frequency_hz': self.zcr_tracker.get_frequency(),
                'confidence': self.zcr_tracker.get_confidence(),
                'sample_count': len(self.fl_60hz_samples)
            }
        }
```

**What Happens:**

| Event | Frequency | Action |
|-------|-----------|--------|
| UDP packet received | 60 Hz | Parse packet bytes |
| `extract()` called | 60 Hz | Calculate velocity, update histograms |
| `damper_histogram.add_sample()` | 60 Hz | Accumulate sample into distribution |
| `zcr_tracker.update()` | 60 Hz | Track zero crossings |
| `return {...}` executed | 60 Hz | Generate summary dict |
| JSON written to disk | 6 Hz | BufferedWriter flushes every 10th return |

**Pros:**
- ✅ **No architecture changes** - keep `buffer_size=10`
- ✅ **60Hz accuracy** - histograms see all 60 samples/second
- ✅ **Efficient disk I/O** - still 6 writes/second
- ✅ **Lightweight JSON** - summaries not raw data
- ✅ **Professional standard** - MoTeC logs at 1000Hz internally, exports at 100Hz

**Cons:**
- ⚠️ Can't retroactively re-analyze raw 60Hz data (but we don't need to!)
- ⚠️ Extractor state persists in memory (but extractors already do this)

---

### Option 2: Change to 60Hz Disk Writes

**Architecture Change:**
```python
# Change buffer_size from 10 to 1
domain_writer = BufferedDomainWriter(session_folder, buffer_size=1)
```

**Result:**
- JSON files written 60 times per second (every packet)
- 10x more disk I/O
- 10x larger JSON files (mostly redundant data)

**Pros:**
- ✅ Full 60Hz telemetry preserved on disk
- ✅ Can re-analyze with different algorithms later

**Cons:**
- ❌ **10x disk I/O** - 60 writes/sec vs 6 writes/sec
- ❌ **10x file size** - suspension.json goes from 2KB → 20KB
- ❌ **Redundant data** - most values don't change significantly frame-to-frame
- ❌ **Not necessary** - metrics only need internal 60Hz processing
- ❌ **Performance impact** - SSD wear, CPU overhead for JSON serialization

---

## Why Option 1 is Superior

### 60Hz Metrics Don't Need 60Hz Persistence

**Damper Velocity Histogram Example:**

```python
class DamperHistogram:
    """Accumulates samples internally, outputs distribution"""

    def __init__(self):
        # Bins: -500mm/s to +500mm/s in 50mm/s increments
        self.bins = {i: 0 for i in range(-500, 500, 50)}
        self.total_samples = 0

    def add_sample(self, velocity_mm_s):
        """Called at 60 Hz - accumulates internally"""
        bin_index = (int(velocity_mm_s) // 50) * 50
        if bin_index in self.bins:
            self.bins[bin_index] += 1
            self.total_samples += 1

    def get_distribution(self):
        """Called at 6 Hz - returns summary"""
        if self.total_samples == 0:
            return {}

        return {
            bin_vel: round(100 * count / self.total_samples, 2)
            for bin_vel, count in self.bins.items()
        }
```

**Over 10 seconds:**
- `add_sample()` called **600 times** (60 Hz × 10 sec)
- `get_distribution()` called **60 times** (6 Hz × 10 sec)
- Disk writes: **60 JSON updates** (not 600!)
- Histogram contains: **600 samples** (full 60Hz resolution!)

**Zero-Crossing Rate Example:**

```python
class ZeroCrossingRateTracker:
    """Tracks zero crossings at 60Hz, outputs frequency at 6Hz"""

    def __init__(self, window_seconds=3.0):
        self.samples = deque(maxlen=int(60 * window_seconds))  # 180 samples
        self.timestamps = deque(maxlen=180)

    def update(self, heave_mm):
        """Called at 60 Hz"""
        self.samples.append(heave_mm)
        self.timestamps.append(dt.now())

    def get_frequency(self):
        """Called at 6 Hz - calculates from 180 samples @ 60Hz"""
        if len(self.samples) < 60:
            return 0.0

        mean = sum(self.samples) / len(self.samples)
        centered = [h - mean for h in self.samples]

        # Count sign changes
        zero_crossings = sum(
            1 for i in range(1, len(centered))
            if (centered[i-1] >= 0 and centered[i] < 0) or
               (centered[i-1] < 0 and centered[i] >= 0)
        )

        time_span = (self.timestamps[-1] - self.timestamps[0]).total_seconds()
        return (zero_crossings / 2) / time_span if time_span > 0 else 0.0
```

**Key Insight:**
- ZCR calculation uses **180 samples @ 60Hz** (3 seconds)
- But we only output the **frequency result** at 6Hz
- No need to store all 180 raw samples on disk!

---

## Implementation Pattern for All 60Hz Metrics

### The Universal Pattern

```python
class DomainExtractor:
    def __init__(self):
        # Internal 60Hz accumulators
        self.internal_buffer = deque(maxlen=N)  # Raw 60Hz samples
        self.accumulator = AccumulatorClass()    # Statistics/histograms
        self.prev_value = 0.0
        self.prev_time = dt.now()

    def extract(self, ddata: bytes) -> Dict[str, Any]:
        """Called @ 60 Hz, returns summary @ 6 Hz"""

        # Parse current packet
        current_value = parse_packet(ddata)

        # ══════════════════════════════════════
        # 60Hz PROCESSING (every packet)
        # ══════════════════════════════════════
        now = dt.now()
        dt_sec = (now - self.prev_time).total_seconds()

        if dt_sec > 0:
            # Calculate derivative @ 60Hz
            derivative = (current_value - self.prev_value) / dt_sec

            # Update internal accumulators @ 60Hz
            self.internal_buffer.append(current_value)
            self.accumulator.add_sample(derivative)

        self.prev_value = current_value
        self.prev_time = now

        # ══════════════════════════════════════
        # 6Hz SUMMARY (written every 10th call)
        # ══════════════════════════════════════
        return {
            'current_value': current_value,
            'derivative_stats': self.accumulator.get_summary(),  # ← Summary only!
            'sample_count': len(self.internal_buffer)            # ← Not raw samples!
        }
```

### Metrics Using This Pattern

| Metric | 60Hz Internal Processing | 6Hz Output |
|--------|-------------------------|-----------|
| **Damper Velocity Histogram** | `add_sample(velocity)` 60x/sec | Distribution percentages |
| **Zero-Crossing Rate** | `append(heave)` to 180-sample buffer | Observed frequency Hz |
| **G-G Diagram** | `update_envelope(lat_g, long_g)` | Max envelope + utilization % |
| **Platform Dynamics** | `calculate_roll_pitch_heave()` | Current angles + rates |
| **Corner Phase Detection** | `detect_phase(inputs)` | Current phase + duration |
| **LLTD** | `calculate_load_transfer()` | Front % distribution |
| **Coefficient of Variation** | `append(value)` to buffer | CV % + consistency rating |

**All use the same pattern:** Process every packet, output summaries.

---

## Performance Comparison

### Option 1: Internal 60Hz Buffers (Recommended)

**10-Second Session:**
- UDP packets received: **600** (60 Hz × 10 sec)
- `extract()` calls: **600** (every packet)
- Internal accumulator updates: **600** (every call)
- JSON writes: **60** (6 Hz × 10 sec)
- Disk I/O: **360 writes** (6 domains × 60 writes)
- suspension.json size: **~2-3 KB** (summary stats only)

**60Hz metrics available:**
- ✅ Damper histogram with 600 samples
- ✅ ZCR frequency from 180 samples
- ✅ G-G envelope from 600 samples
- ✅ All professional race engineering metrics

---

### Option 2: 60Hz Disk Writes (Not Recommended)

**10-Second Session:**
- UDP packets received: **600** (60 Hz × 10 sec)
- `extract()` calls: **600** (every packet)
- Internal accumulator updates: **600** (every call)
- JSON writes: **600** (60 Hz × 10 sec)
- Disk I/O: **3,600 writes** (6 domains × 600 writes)
- suspension.json size: **~20-30 KB** (raw samples)

**60Hz metrics available:**
- ✅ Damper histogram with 600 samples (same as Option 1!)
- ✅ ZCR frequency from 180 samples (same as Option 1!)
- ✅ G-G envelope from 600 samples (same as Option 1!)

**Analysis:** Same metrics, 10x more I/O. No benefit.

---

## Real-World Analogy: Professional Telemetry Systems

### MoTeC i2 Pro (Industry Standard)

**How MoTeC Works:**
1. **Acquisition Rate:** 1000 Hz (1ms resolution)
2. **Processing Rate:** 1000 Hz (internal calculations)
3. **Display Rate:** 100 Hz (screen refresh)
4. **Export Rate:** 100 Hz or user-defined

**Key Insight:** MoTeC processes at 1000Hz internally but doesn't need to *display* or *export* every sample. Math channels (derivatives, histograms, FFT) consume 1000Hz data but output summary statistics.

**Our Architecture:**
- **Acquisition:** 60 Hz (GT7 UDP)
- **Processing:** 60 Hz (internal accumulators)
- **Persistence:** 6 Hz (JSON writes)
- **Phase 2 Monitoring:** 6 Hz (Python agents read JSONs)

This mirrors professional systems! ✅

---

## Implementation Checklist

### Phase 1 Enhancement with 60Hz Research

- [ ] **Keep `buffer_size=10`** - no change to BufferedDomainWriter
- [ ] **Add internal 60Hz accumulators** to extractors:
  - [ ] `SuspensionExtractor`: DamperHistogram, ZeroCrossingRateTracker, platform dynamics
  - [ ] `BalanceExtractor`: GGDiagramTracker, CornerPhaseDetector
  - [ ] `TireExtractor`: Slip ratio histograms, temperature gradients
- [ ] **Create accumulator helper classes:**
  - [ ] `DamperHistogram` (bins -500 to +500 mm/s)
  - [ ] `ZeroCrossingRateTracker` (deque with 180 samples)
  - [ ] `GGDiagramTracker` (max envelope tracker)
  - [ ] `CornerPhaseDetector` (state machine)
- [ ] **Update `extract()` methods:**
  - [ ] Process every packet @ 60Hz
  - [ ] Update internal accumulators @ 60Hz
  - [ ] Return summaries (written @ 6Hz by BufferedWriter)
- [ ] **Test with real GT7 session:**
  - [ ] Verify histogram gets ~600 samples over 10 seconds
  - [ ] Verify ZCR uses 180 samples for frequency calculation
  - [ ] Verify JSON file size stays reasonable (~2-3 KB)

---

## Expected Benefits

### After Implementation

**Professional Race Engineering Metrics:**
- ✅ Damper velocity histograms (MoTeC/AiM standard)
- ✅ Zero-crossing rate frequency validation
- ✅ Platform dynamics (roll/pitch/heave @ 60Hz)
- ✅ G-G diagram / grip utilization
- ✅ Corner phase detection
- ✅ LLTD (lateral load transfer distribution)
- ✅ 17+ additional statistical metrics

**Performance:**
- ✅ Same 6Hz disk I/O as current Phase 1
- ✅ Full 60Hz resolution for all metrics
- ✅ Lightweight JSON files (~2-3 KB)
- ✅ No architecture changes needed

**Integration with Phase 2:**
- ✅ Python agents read enhanced 6Hz JSONs
- ✅ Professional metrics enable better anomaly detection
- ✅ Haiku AI receives richer context (damper histograms, frequency validation)
- ✅ Real-time coaching uses pro race engineering data

---

## Code Examples

### Complete DamperHistogram Class

```python
class DamperHistogram:
    """
    Professional damper tuning tool (MoTeC/AiM standard)

    Accumulates damper velocity samples @ 60Hz internally,
    outputs distribution summary @ 6Hz for JSON persistence.
    """

    def __init__(self, bin_width=50, range_limit=500):
        """
        Initialize histogram

        Args:
            bin_width: mm/s per bin (default: 50)
            range_limit: ±mm/s range (default: ±500)
        """
        self.bin_width = bin_width
        self.range_limit = range_limit

        # Create bins: -500, -450, -400, ..., 0, ..., 450, 500
        self.bins = {
            i: 0 for i in range(-range_limit, range_limit + 1, bin_width)
        }
        self.total_samples = 0

    def add_sample(self, velocity_mm_s):
        """
        Add damper velocity sample (called @ 60 Hz)

        Args:
            velocity_mm_s: Damper velocity in mm/s
        """
        # Clamp to range
        velocity_mm_s = max(-self.range_limit, min(self.range_limit, velocity_mm_s))

        # Find bin (round down to nearest bin_width)
        bin_index = (int(velocity_mm_s) // self.bin_width) * self.bin_width

        if bin_index in self.bins:
            self.bins[bin_index] += 1
            self.total_samples += 1

    def get_distribution(self):
        """
        Get percentage distribution (called @ 6 Hz for JSON write)

        Returns:
            Dict[int, float]: Bin velocity → percentage
        """
        if self.total_samples == 0:
            return {}

        return {
            bin_vel: round(100 * count / self.total_samples, 2)
            for bin_vel, count in self.bins.items()
        }

    def get_operating_range(self):
        """
        Calculate operating range diagnostics (called @ 6 Hz)

        Returns:
            Dict with optimal/high_speed/hitting_limits percentages
        """
        if self.total_samples == 0:
            return {
                'optimal_pct': 0,
                'high_speed_pct': 0,
                'hitting_limits_pct': 0,
                'interpretation': 'No data'
            }

        # Optimal: -200 to +200 mm/s
        optimal = sum(c for v, c in self.bins.items() if -200 <= v <= 200)

        # High speed: 200-400 mm/s (abs)
        high_speed = sum(c for v, c in self.bins.items() if 200 < abs(v) <= 400)

        # Hitting limits: >400 mm/s (abs)
        limits = sum(c for v, c in self.bins.items() if abs(v) > 400)

        optimal_pct = round(100 * optimal / self.total_samples, 1)
        high_speed_pct = round(100 * high_speed / self.total_samples, 1)
        limits_pct = round(100 * limits / self.total_samples, 1)

        # Interpretation
        if limits_pct > 5:
            interpretation = "WARNING: Dampers hitting limits - too soft or excessive motion"
        elif optimal_pct > 70:
            interpretation = "GOOD: Dampers in optimal operating range"
        elif high_speed_pct > 50:
            interpretation = "REVIEW: High-speed damper activity - check ARB/springs"
        else:
            interpretation = "OK: Normal damper operation"

        return {
            'optimal_pct': optimal_pct,
            'high_speed_pct': high_speed_pct,
            'hitting_limits_pct': limits_pct,
            'interpretation': interpretation,
            'total_samples': self.total_samples
        }
```

### Complete ZeroCrossingRateTracker Class

```python
from collections import deque
from datetime import datetime as dt

class ZeroCrossingRateTracker:
    """
    Frequency estimation without FFT (60Hz Research)

    Tracks zero crossings in heave signal @ 60Hz internally,
    outputs frequency estimate @ 6Hz for JSON persistence.
    """

    def __init__(self, window_seconds=3.0):
        """
        Initialize ZCR tracker

        Args:
            window_seconds: Analysis window (default: 3.0 seconds)
        """
        self.window_seconds = window_seconds

        # 60Hz × 3 seconds = 180 samples
        max_samples = int(60 * window_seconds)
        self.samples = deque(maxlen=max_samples)
        self.timestamps = deque(maxlen=max_samples)

    def update(self, heave_mm):
        """
        Add heave sample (called @ 60 Hz)

        Args:
            heave_mm: Current heave position in mm
        """
        self.samples.append(heave_mm)
        self.timestamps.append(dt.now())

    def get_frequency(self):
        """
        Calculate observed frequency (called @ 6 Hz for JSON write)

        Returns:
            float: Observed suspension frequency in Hz
        """
        if len(self.samples) < 60:
            return 0.0

        # Remove mean (center signal)
        mean = sum(self.samples) / len(self.samples)
        centered = [h - mean for h in self.samples]

        # Count zero crossings (sign changes)
        zero_crossings = 0
        for i in range(1, len(centered)):
            if (centered[i-1] >= 0 and centered[i] < 0) or \
               (centered[i-1] < 0 and centered[i] >= 0):
                zero_crossings += 1

        # Calculate frequency
        time_span = (self.timestamps[-1] - self.timestamps[0]).total_seconds()
        if time_span > 0:
            # Divide by 2: full cycle = 2 zero crossings
            observed_frequency = (zero_crossings / 2) / time_span
            return round(observed_frequency, 2)

        return 0.0

    def get_confidence(self):
        """
        Get confidence level (called @ 6 Hz)

        Returns:
            str: 'high', 'medium', or 'low'
        """
        sample_count = len(self.samples)
        if sample_count >= 180:
            return 'high'
        elif sample_count >= 120:
            return 'medium'
        else:
            return 'low'

    def get_stats(self):
        """
        Get complete ZCR statistics (called @ 6 Hz for JSON write)

        Returns:
            Dict with frequency, confidence, sample_count
        """
        return {
            'observed_frequency_hz': self.get_frequency(),
            'confidence': self.get_confidence(),
            'sample_count': len(self.samples),
            'window_seconds': self.window_seconds
        }
```

---

## Conclusion

**The Architectural Insight:**

We don't need to change Phase 1's 6Hz write architecture to implement professional 60Hz race engineering metrics. We just need to add internal accumulators that process at 60Hz and output summaries at 6Hz.

**The Pattern:**
```
Receive @ 60 Hz → Process @ 60 Hz → Accumulate @ 60 Hz → Persist summaries @ 6 Hz
```

**The Result:**
- ✅ Professional telemetry metrics (MoTeC/AiM standard)
- ✅ Full 60Hz resolution for histograms, ZCR, platform dynamics
- ✅ Efficient 6Hz disk I/O (no performance impact)
- ✅ Lightweight JSON files (~2-3 KB)
- ✅ Perfect for Phase 2 Python agent monitoring

**This is production-grade race engineering at consumer-grade efficiency!** 🏎️💨

---

**Next Steps:**
1. Implement accumulator classes (DamperHistogram, ZeroCrossingRateTracker, etc.)
2. Enhance extractors with internal 60Hz buffers
3. Test with real GT7 session to validate metrics
4. Integrate with Phase 2 Python agents for real-time monitoring

**Files to Create/Modify:**
- `dev/phase1/utils/accumulators.py` (new - accumulator classes)
- `dev/phase1/utils/domain_extractors.py` (enhance - add 60Hz processing)
- `dev/phase1/test_60hz_metrics.py` (new - validation tests)
